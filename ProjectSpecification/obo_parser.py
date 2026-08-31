import pandas as pd
from abc import ABC, abstractmethod

class base_searcher(ABC):   #re-used abstract class searcher from gaf parser / re-used search methods
    
    def __init__(self, df):
        self.df = df
        self.results = None
    
    @abstractmethod
    def search(self, query):
        pass
    
    @abstractmethod
    def get_description(self):
        pass


class id_searcher(base_searcher): 
    def search(self, query):
        
        if self.df.empty:
            return pd.DataFrame()
            
        query = query.strip().upper()
        self.results = self.df[self.df['id'] == query]
        return self.results
    
    
    def get_description(self):
        return "Search by GO ID (e.g., GO:0006915)"


class name_searcher(base_searcher):
    def search(self, query):
    
        if self.df.empty:
            return pd.DataFrame()
        
        query = query.strip().lower()
        self.results = self.df[self.df['name'].str.lower() == query]
        return self.results
    
    def get_description(self):
        return "Search by exact term name (e.g., apoptotic process)"
    
class namespace_searcher(base_searcher):
    def search(self, query):
    
        if self.df.empty:
            return pd.DataFrame()
        
        aspect_map = {'p': 'biological_process', 'f': 'molecular_function', 'c': 'cellular_component'}
        
        query_lower = query.strip().lower()
        namespace = aspect_map.get(query_lower)
        self.results = self.df[self.df['namespace'].str.lower() == namespace]
        return self.results
    
    def get_description(self):
        return "Search by Namespace/Aspect(e.g., Biological Process (P))"
    
    
class obsolete_searcher(base_searcher):
    def search(self, query=None): #query denied to avoid problem with abstract class when viewing obsolete terms
        if self.df.empty:
            return pd.DataFrame()
    
        if 'is_obsolete' in self.df.columns:
            self.results = self.df[self.df['is_obsolete'] == True]
            
        else:
            self.results = pd.DataFrame()
            
        return self.results
            
    def get_description(self):
        return "Shows Obsolete Terms"
    

class partial_name_searcher(base_searcher):
    def search(self, query):
        if self.df.empty:
            return pd.DataFrame()
        
        query = query.strip().lower()
        self.results = self.df[self.df['name'].str.lower().str.contains(query, na=False)]
        return self.results
    
    def get_description(self):
        return "Search by partial name (e.g., 'apoptosis')"

class OboParser:

    def __init__(self, filepath):

        self.filepath = filepath
        self.terms = {} #information is displayed in rows, not columns, so we search in between the terms and displayh them as columns
        self.df, self.load_messages = self._load_obo()
        self.searchers = {'GO_ID': id_searcher(self.df),'Name': name_searcher(self.df),'Obsolete Terms': obsolete_searcher(self.df),'Namespace': namespace_searcher(self.df), 'Partial Name': partial_name_searcher(self.df)}
        
        
    def _load_obo(self): #protected from external code
        
        messages = []
        def _log(msg):
            messages.append(str(msg))
            print(msg)

        _log(f"Loading OBO file: {self.filepath}")     #pandas method avoided because obo file functions in rows, not columns unlike gaf file, leading to differfent reading
       
        terms_data = []
        current_term = {}
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                 
                    if not line or line.startswith('!'):
                        continue
                    
                  
                    if line == '[Term]':
                        if current_term:
                            terms_data.append(current_term)
                        current_term = {}
                        continue
                    
             
             
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                       
                       
                        if key == 'id':
                            current_term['id'] = value
                        elif key == 'name':
                            current_term['name'] = value
                        elif key == 'namespace':
                            current_term['namespace'] = value
                        elif key == 'def':
                       
                       
                            if '[' in value:
                                current_term['definition'] = value.split('[')[0].strip()
                            else:
                                current_term['definition'] = value
                        elif key == 'is_a':
                
                
                            parent_id = value.split('!')[0].strip()
                            if 'is_a' not in current_term:
                                current_term['is_a'] = []
                            current_term['is_a'].append(parent_id)
                        elif key == 'relationship':
                
                
                            parts = value.split('!')[0].strip().split(' ', 1)
                            if len(parts) == 2:
                                rel_type, target_id = parts
                                if 'relationships' not in current_term:
                                    current_term['relationships'] = []
                                current_term['relationships'].append({
                                    'type': rel_type,
                                    'target': target_id
                                })
                        elif key == 'is_obsolete':
                            current_term['is_obsolete'] = value == 'true'
                        elif key == 'alt_id':
                            if 'alt_ids' not in current_term:
                                current_term['alt_ids'] = []
                            current_term['alt_ids'].append(value)
            
            
            if current_term:
                terms_data.append(current_term)

            df = pd.DataFrame(terms_data) #dataframe created
            

            if 'is_a' in df.columns:
                df['is_a'] = df['is_a'].apply(lambda x: '|'.join(x) if isinstance(x, list) else '')
            
            if 'alt_ids' in df.columns:
                df['alt_ids'] = df['alt_ids'].apply(lambda x: '|'.join(x) if isinstance(x, list) else '')
            
            if 'relationships' in df.columns:
                df['relationships'] = df['relationships'].apply(
                    lambda x: '|'.join([f"{r['type']}:{r['target']}" for r in x]) if isinstance(x, list) else ''
                )
            

            for col in ['definition', 'is_a', 'relationships', 'alt_ids']:    #add missing columns with empty values
                if col not in df.columns:
                    df[col] = ''
            
            _log(f"Loaded {len(df)} GO terms")
            
            if 'namespace' in df.columns:
                namespaces = df['namespace'].value_counts()
                _log("Namespace distribution:")
                for ns, count in namespaces.items():
                    _log(f"      {ns}: {count:,}")
            
            string = "\n".join(messages)
            return df, string
            
        except FileNotFoundError:
            _log(f"❌ File not found: {self.filepath}")
            string = "\n".join(messages)
            return pd.DataFrame(), string
        except Exception as e:
            _log(f"❌ Error loading OBO file: {e}")
            string = "\n".join(messages)
            return pd.DataFrame(), string
    
            
        # except FileNotFoundError:
        #     print(f"❌ File not found: {self.filepath}")
        #     return pd.DataFrame()
        # except Exception as e:
        #     print(f"❌ Error loading OBO file: {e}")
        #     return pd.DataFrame()
    
    
    def get_term(self, term_id):
        results = self.df[self.df['id'] == term_id]
        
        if results.empty:
            
            return None
        
        return results.iloc[0]
    
    def get_children(self, term_id): #gets all children

        if self.df.empty:
            
            return pd.DataFrame()
        
        return self.df[self.df['is_a'].str.contains(term_id, na=False)]
    
    def get_ancestors(self, term_id, visited=None): #gets ancestors
        if visited is None:
            
            visited = set()
        
        term = self.get_term(term_id)
        if term is None or pd.isna(term.get('is_a')):
            return visited
        
        parent_ids = term['is_a'].split('|') if isinstance(term['is_a'], str) else []
        
        for parent_id in parent_ids:
            if parent_id not in visited:
                visited.add(parent_id)
                self.get_ancestors(parent_id, visited)
        
        return visited
    
    def search_menu(self): #main inteeractive menu for searching data inside the df
        
        print('OBO FILE EXPLORER')
        print('WHAT WOULD YOU LIKE DOING:')
        print('')
        print('1. SEARCH FOR TERMS')
        print('2. VIEW ONTOLOGY HIERARCHYC RELATIONS')
        print('')
        
        
        #subdivison of menus for better understanding
        
        while True:
            selection = input('Select 1 (Searcher) or 2 (Ontology viewer) (input an integer number): ').strip()
            
            if selection == '1':
                
                print('OBO TERM SEARCHER')
                print('')
                print('YOU CAN SEARCH BY:')
                print('')
                print('1. GO_ID')
                print('2. Name')
                print('3. Obsolete terms')
                print('4. Namespace/Aspect')
                print('5. View Statistics of the DataFrame')
                print('6. Partial Name Search')
                print('7. GO BACK TO MAIN MENU')
                print('')
        
        
                while True:
                    selection = input('Select one option from 1 to 7 (input an integer number): ').strip()
            
                    if selection == '1':
                        query = input('Enter the GO_ID to be searched: ')
                        searcher = self.searchers['GO_ID']
                        results = searcher.search(query)
                        self._display_results(results, searcher, query)
                
                    elif selection == '2':
                        query = input('Enter the Name to be searched: ')
                        searcher = self.searchers['Name']
                        results = searcher.search(query)
                        self._display_results(results, searcher, query)
                
                    elif selection == '3':
                        searcher = self.searchers['Obsolete Terms']
                        results = searcher.search() #no  need for query because obsolete is just true or false
                        self._display_results(results, searcher, "Obsolete Terms")
                
                    elif selection == '4':
                        query = input('Enter the Namespace/Aspect to be searched: ')
                        searcher = self.searchers['Namespace']
                        results = searcher.search(query)
                        self._display_results(results, searcher, query)
                                
                    elif selection == '5':
                
                        self._display_statistics()
                        
                    elif selection == '6':                      
                        query = input('Enter the Partial Name to be searched: ')
                        searcher = self.searchers['Partial Name']
                        results = searcher.search(query)
                        self._display_results(results, searcher, query)
                        
                    elif selection == '7':
                        
                        break #returning to main menu
                
                    else:
                        print('Invalid option, please insert a number from 1 to 6')
                    
            
            elif selection == '2':
                
                print('OBO ONTOLOGY VIEWER')
                print('')
                print('VIEW:')
                print('')
                print('1. HIERCHYCAL RELATIONSHIPS OF A TERM (INPUT GO_ID, SHOWS ENTIRE DETAILS OF SUCH TERM)')
                print('2. PARENT OF A TERM')
                print('3. CHILDREN OF A TERM')
                print('4. GO BACK TO MAIN MENU')
                print('')
                
                
                while True:
                    selection = input('Select 1 or 4 (input an integer number): ').strip()
                    
                    if selection == '1':
                        query = input('Enter GO_ID: ')
                        self._display_term_details(query)
                
                    elif selection == '2':
                        query = input('Enter GO_ID: ')
                        ancestors = self.get_ancestors(query)
                        
                        if ancestors:
                            print(f'\n Parents of {query}:')
                            
                            for ancestor in sorted(ancestors):
                                term = self.get_term(ancestor)
                                
                                if term is not None:
                                    print(f"   {ancestor} - {term.get('name', 'N/A')}")
                                    
                        else:
                            print(f'This term has no parents present in this DataFrame')
                
                    elif selection == '3':
                        query = input('Enter GO_ID: ')
                        children = self.get_children(query)
                        
                        if not children.empty:
                            print(f'Children of {query}:')
                            print(children[['id', 'name']].to_string(index=False))
                            
                        else:
                            print(f'This term has no children in this DataFrame')
                    
                    elif selection == '4':
                        
                        break #returning to main menu
                
                
    def _display_results(self, results, searcher, query):

        if results.empty:
            print(f'No terms found for: {query}')
            return
        
        print(f'Found {len(results)} terms for: {query}')
        print(f"Search type: {searcher.get_description()}")
        
        display_cols = ['id', 'name', 'namespace', 'definition']
        available_cols = [col for col in display_cols if col in results.columns]
        
        if len(results) > 10:
            print(f'Showing first 10 of {len(results)} results:')
            print(results[available_cols].head(10).to_string(index=False))
            print(f'and {len(results) - 10} more results')
        else:
            print(results[available_cols].to_string(index=False))
            print('')
    
        if not results.empty:
            # show_details = input('Enter a GO ID to view full details (or press Enter to skip): ').strip()
            # if show_details:
                self._display_term_details(query)
 
    def _display_term_details(self, term_id):
        
        term = self.get_term(term_id)
        if term is None:
            print(f'Term not found: {term_id}')
            return
        
        print('')
        print(f"TERM: {term.get('id', 'N/A')}")
        print('')
        print(f"Name: {term.get('name', 'N/A')}")
        print('')
        print(f"Namespace: {term.get('namespace', 'N/A')}")
        print('')
        print(f"Definition: {term.get('definition', 'N/A')}")
        print('')
        print(f"Parents: {term.get('is_a', 'None')}")
        print('')
        print(f"Relationships: {term.get('relationships', 'None')}")
        print('')
        print(f"Alt IDs: {term.get('alt_ids', 'None')}")
        print('')
        
        children = self.get_children(term_id)
        if not children.empty:
            print(f"Direct Children ({len(children)}):")
            print('')
            print(children[['id', 'name']].to_string(index=False))
        
        # explore = input('Enter a GO ID to explore (or press Enter to return): ').strip() #option to keep searching after a filtration is done
        # if explore:
        # self._display_term_details(term_id)
    
    def _display_statistics(self):
    
        if self.df.empty:
            print('No data loaded')
            return
        
        print('ONTOLOGY STATISTICS')
        print(f"Total terms: {len(self.df):,}")
        print(f"Terms with definitions: {self.df['definition'].notna().sum():,}")
        
        if 'is_a' in self.df.columns: 
            has_parents = self.df['is_a'].notna().sum()
            print(f"Terms with parents: {has_parents:,}")
        
        if 'namespace' in self.df.columns: #namespace statistics, shown in percentage
            namespaces = self.df['namespace'].value_counts()
            print('Namespace Distribution:')
            for ns, count in namespaces.items():
                percentage = (count / len(self.df)) * 100
                print(f"      {ns}: {count:,} ({percentage:.1f}%)")

if __name__ == "__main__":
    
    parser = OboParser('go-basic.obo')

    parser.search_menu()
