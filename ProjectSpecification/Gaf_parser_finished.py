import pandas as pd
from abc import ABC, abstractmethod

class base_searcher(ABC):
    
    def __init__(self, df):
        self.df = df
        self.results = None
    
    @abstractmethod
    def search(self, query):
        pass
    
    @abstractmethod
    def get_description(self):
        pass

class go_id_searcher(base_searcher): #upgraded search method 1 using inheritance brom abstracted class
    def search(self, query):
           
        if self.df.empty:
            return pd.DataFrame()
            
        query = query.strip().upper()
        self.results = self.df[self.df['GO_ID'] == query]
        return self.results
    
    def get_description(self):
        return "Search by GO ID (e.g., GO:0006915)"
            
   
  #def go_id_search(self, go_id):    #search method 1 (old)
        #if self.df.empty:
            #return pd.DataFrame()
        
        #go_id = go_id.strip().upper()
        #return self.df[self.df['GO_ID'] == go_id]
        
    
class evidence_code_searcher(base_searcher):
    def search(self, query):
            
        if self.df.empty:
            return pd.DataFrame()
            
        query = query.strip().upper()
        self.results = self.df[self.df['Evidence_Code'] == query]
        return self.results
    
    def get_description(self):
        return "Search by Evidence Code (e.g., EXP)"
    
    
    #def evidence_code_search(self, evidence_code):  #search method 2
        #if self.df.empty:
            #return pd.DataFrame()
        
        #evidence_code = evidence_code.strip().upper()
        #return self.df[self.df['Evidence_Code'].str.upper() == evidence_code]
        
class db_symbol_searcher(base_searcher):
    def search(self, query):
        
        if self.df.empty:
            return pd.DataFrame()
            
        query = query.strip().upper()
        self.results = self.df[self.df['DB_Object_Symbol'] == query]
        return self.results
    
    def get_description(self):
        return "Search by Gene Symbol (e.g., TP53)"
    

    #def db_symbol_search(self, gene_symbol):   #search method 3
        #if self.df.empty:
            #return pd.DataFrame()
        
        #gene_symbol = gene_symbol.strip().upper()
        #return self.df[self.df['DB_Object_Symbol'].str.upper() == gene_symbol]
    
    
class aspect_searcher(base_searcher):
    def search(self, query):
        
        if self.df.empty:
            return pd.DataFrame()
            
        aspect_map = {'biological process': 'P', 'molecular function': 'F', 'cellular component': 'C'}
         
        query_lower = query.strip().lower()
        aspect_code = aspect_map.get(query_lower, query.strip().upper())
        self.results = self.df[self.df['Aspect'] == aspect_code]
        return self.results
    
    def get_description(self):
        return "Search by Aspect(e.g., Biological Process (P))"

    #def aspect_search(self, aspect): search method #4
        #if self.df.empty:
            #return pd.DataFrame()
        
        #aspect_map = {'biological process': 'P', 'molecular function': 'F', 'cellular component': 'C'}
         
        #aspect = aspect.strip().upper()
        
        #return self.df[self.df['Aspect'] == aspect]
    
    #polymorphism shown as the search() method works in all searchers
        
class GafParser:   #class for gaf parser

    def __init__(self, filepath):  #constructor of the gaf parser class
        
        self.filepath = filepath         #attributes for the gaf parser class
        self.df, self.load_messages = self._load_gaf()       #self is used by convention to reference the object currently being created
        self.searchers = {'GO_ID': go_id_searcher(self.df),'Gene Symbol': db_symbol_searcher(self.df),'Evidence Code': evidence_code_searcher(self.df),'Aspect': aspect_searcher(self.df)}
        
    COLUMNS = [
        'DB', 'DB_Object_ID', 'DB_Object_Symbol', 'Qualifier',
        'GO_ID', 'DB_Reference', 'Evidence_Code', 'With',
        'Aspect', 'DB_Object_Name', 'DB_Object_Synonym',
        'DB_Object_Type', 'Taxon', 'Date', 'Assigned_By',
        'Annotation_Extension', 'Gene_Product_Form_ID'
    ] #names for the 17 columns present in gaf files


    def _load_gaf(self): #protected from external code
       
        messages = []
        def _log(msg):
            messages.append(str(msg))
            print(msg)
        
        try:
            _log(f" Loading GAF file: {self.filepath}")
            
            df = pd.read_csv(
                self.filepath,
                comment='!',           
                delimiter='\t',         
                compression='gzip',     
                header=None,           
                dtype=str,             
                low_memory=False       
            )
            
            _log(f"Loaded {len(df)} rows with {len(df.columns)} columns")
            
            if len(df.columns) == len(self.COLUMNS):
                df.columns = self.COLUMNS
                _log("gaf 2.2 format detected")
            elif len(df.columns) == 15:  #older versions of gaf files contains less columns, with this we can detect if the gaf files inserted is the newest version (2.2)
                _log(f"Older gaf version detected ({len(df.columns)} columns)")
                df.columns = self.COLUMNS[:len(df.columns)]
            else:
                _log(f"Unexpected columns: {len(df.columns)}, expected: {len(self.COLUMNS)}")
                df.columns = [f'col_{i}' for i in range(len(df.columns))]
                
            # return both the dataframe and the concatenated log messages
            return df, "\n".join(messages)
        
        except Exception as e:
            _log(f"Error loading GAF file: {e}")
            return pd.DataFrame(), "\n".join(messages)
   
    
    def statistics(self):
        if self.df.empty:
            return {}
        else:
            
            return {
        
                'Total amount of genes reported: ' + str(len(self.df)) + ', of which ' + self.df['DB_Object_Symbol'].nunique() + ' are unique.' ,
                'Total amount of Unique GO ID(s): ' + self.df['GO_ID'].nunique()

            }
    
            
    def search_menu(self): #main inteeractive menu for searching data inside the df
        
        print('-'*50)
        print('')
        print('GAF ANNOTATION SEARCH')
        print('You can search by:')
        print('')
        print('1. GO_ID')
        print('2. Evidence_code')
        print('3. DB_OBJECT_SYMBOL')
        print('4. Aspect.')
        print('')
        print('Or you can')
        print('')
        print('5. View Statistics of the DataFrame.')
        print('6. Return to GO_Tools menu.')
        print('')
        
        
        while True:
            selection = input('Select one option from 1 to 6 (input an integer number): ').strip()
            
            if selection == '1':
                query = input('Enter the GO_ID to be searched: ')
                searcher = self.searchers['GO_ID']
                results = searcher.search(query)
                self._display_results(results, searcher, query)
                
            elif selection == '2':
                query = input('Enter the Evidence Code to be searched: ')
                searcher = self.searchers['Evidence Code']
                results = searcher.search(query)
                self._display_results(results, searcher, query)
                
            elif selection == '3':
                query = input('Enter the DB_Object_Symbol to be searched: ')
                searcher = self.searchers['Gene Symbol']
                results = searcher.search(query)
                self._display_results(results, searcher, query)
                
            elif selection == '4':
                query = input('Enter the Aspect to be searched: ')
                searcher = self.searchers['Aspect']
                results = searcher.search(query)
                self._display_results(results, searcher, query)
                
                
                #aspect = input('Enter the aspect to be searched: ')        example of how previous search method worked without inheritance and abstraction
                #results = self.aspect_searcher(aspect)
                #self._display_results(results, f'Aspect: {aspect}')
                
            elif selection == '5':
                
                print('Annotation Statistics: ')
                print('')
                print('Total amount of genes reported: ' + str(len(self.df)) + ', of which ' + str(self.df['DB_Object_Symbol'].nunique()) + ' are unique.')
                print('Total amount of Unique GO ID(s): ' + str(self.df['GO_ID'].nunique()))
                
            elif selection == '6': #returning to menu
                
                break
                
            else:
                print('Invalid option, please insert a number from 1 to 6 (6 to exit to menu)')
                
                
                
    def _display_results(self, results, searcher, query):  #encapsulated so it cant be changed by external code and so i can change the displays format without breaking the code
        if results.empty:
            print('No annotations found for the desired search')
            
        else:
            print('Found ' + str(len(results)) + ' annotations for the desired search.')
            print(f"Search type: {searcher.get_description()}")
            
            display_cols = ['DB_Object_ID', 'DB_Object_Symbol','GO_ID','Evidence_Code', 'Aspect', 'DB_Object_Name', 'DB_Object_Synonym',  'DB_Object_Type', 'Date'] #display of all the columns
            available_cols = [col for col in display_cols if col in results.columns]
            
        
            if len(results) > 10: #reducing results shown to only 10 because program takes a lot of time to run otherwise, it would also be hard to read
                print(results[available_cols].head(10).to_string(index=False))
                print('Due to a great amount of results obtained, only 10 were returned for readabilty and optimizations sake')
            
            else:
                print(results[available_cols].to_string(index=False))
            
           
            


if __name__ == "__main__":
        
    parser = GafParser('goa_human.gaf')
    print(parser.load_messages)
    parser.search_menu()
            