from Gaf_parser_finished import GafParser
from obo_parser import OboParser
import numpy as np
import pandas as pd


class GO_Tools:
    
    def __init__(self, gaf_file, obo_file):
        self.gaf = GafParser(gaf_file)
        self.loadGafMessage = self.gaf.load_messages
        
        self.obo = OboParser(obo_file)
        self.loadOboMessage = self.obo.load_messages
        
    
    def search_gaf(self):
        self.gaf.search_menu()
        
    def search_obo(self):
        self.obo.search_menu()
        
    
    def _jaccard(self, term1, term2): #jaccard similarity, encapsulated helper. calculates by intersection over union

        genes1 = set(self.gaf.df[self.gaf.df['GO_ID'] == term1]['DB_Object_Symbol'])
        genes2 = set(self.gaf.df[self.gaf.df['GO_ID'] == term2]['DB_Object_Symbol'])
        
        if len(genes1 | genes2) == 0:
            return 0.0
        return len(genes1 & genes2) / len(genes1 | genes2)
    
    def _overlap(self, term1, term2): #calculates by dividing their size of intersection by the size of the smallest set

        genes1 = set(self.gaf.df[self.gaf.df['GO_ID'] == term1]['DB_Object_Symbol'])
        genes2 = set(self.gaf.df[self.gaf.df['GO_ID'] == term2]['DB_Object_Symbol'])
        
        if min(len(genes1), len(genes2)) == 0:
            return 0.0
        return len(genes1 & genes2) / min(len(genes1), len(genes2))
    
    
    def calculate_similarity(self, term1, term2, method='jaccard'):

        if method == 'jaccard':
            return self._jaccard(term1, term2)
        
        elif method == 'overlap':
            return self._overlap(term1, term2)

        else:
            raise ValueError(f"Unknown method: {method}. Available: jaccard or overlap")
    
    def compare_similarity_methods(self, term1, term2):

        print('')
        print('Results:')
        print(f"Term 1: {term1}")
        print(f"Term 2: {term2}")
        print('')
        
        results = {}
        for method in ['jaccard', 'overlap']:
            sim = self.calculate_similarity(term1, term2, method)
            results[method] = sim
            print(f"   {method.capitalize():10} -> {sim:.4f}")
        
        print('')
        print("This is polymorphism:")
        print("Same method name: calculate_similarity()")
        print("Same parameters: term1, term2")
        print("Different behaviors: Jaccard and Overlap")
        print("Different results: Each method produces a different value")
        
        return results

    def create_annotation_matrix(self): #creation of a binary matrix between annotations and genes
       
        genes = self.gaf.df['DB_Object_Symbol'].unique()[:100]
        go_terms = self.gaf.df['GO_ID'].value_counts().head(100).index.tolist()
        
        matrix = np.zeros((len(genes), len(go_terms)), dtype=int)
        
        for i, gene in enumerate(genes):
            gene_terms = set(self.gaf.df[self.gaf.df['DB_Object_Symbol'] == gene]['GO_ID'])
            
            for j, term in enumerate(go_terms):
                if term in gene_terms:
                    matrix[i, j] = 1
        
        return matrix, genes, go_terms
    
    
    def analyze_matrix(self):  #basic analysis of the annotation matrix 

        matrix, genes, go_terms = self.create_annotation_matrix()
    
        print('Annotation matrix analysis')

        gene_counts = matrix.sum(axis=1) #most annotated genes in the file
        print('Top 5 Most Annotated Genes:')
        for idx in np.argsort(gene_counts)[::-1][:5]:
            print(f"{genes[idx]}: {gene_counts[idx]} annotations")
    
        term_counts = matrix.sum(axis=0) #most common GO Terms
        print('')
        print('Top 5 Most Common GO Terms:')
        for idx in np.argsort(term_counts)[::-1][:5]:
            term = self.obo.get_term(go_terms[idx])
            name = term.get('name', 'N/A') if term is not None else 'N/A'
            print(f"{go_terms[idx]} ({name}): {term_counts[idx]} genes")
    
        print('')
        print('Density Distribution:') #gene density analysis
        gene_annotations = matrix.sum(axis=1)
        print(f"Genes with 0-5 annotations: {np.sum(gene_annotations <= 5):,}")
        print(f"Genes with 6-20 annotations: {np.sum((gene_annotations > 5) & (gene_annotations <= 20)):,}")
        print(f"Genes with >20 annotations: {np.sum(gene_annotations > 20):,}")
        
        
    def get_neighborhood(self, term_id, distance=1):

        if self.obo.df.empty: #gets all neighbor terms, this is quite similar to finding parents or children, but it also can find the parents and childer of such parents and children...
            return set()
        
        neighbors = set()
        current_level = {term_id}
        
        for _ in range(distance): #loops to search neighbor
            next_level = set()
            for term in current_level:
                children = self.obo.get_children(term)
                if not children.empty:
                    next_level.update(children['id'].tolist())
                ancestors = self.obo.get_ancestors(term)
                next_level.update(ancestors)
            neighbors.update(next_level - {term_id})
            current_level = next_level
        
        return neighbors - {term_id}
    
    def get_neighborhood_info(self, term_id, distance=1):

        neighbors = self.get_neighborhood(term_id, distance)
        
        info = []
        for neighbor in neighbors:
            term = self.obo.get_term(neighbor)
            if term is not None:
                info.append({
                    'term_id': neighbor,
                    'name': term.get('name', 'N/A'),
                    'namespace': term.get('namespace', 'N/A') #just to display information about the neighborhood
                })
        
        return info

    def main_search_menu(self): #interactive menu that return obo and gaf analyzers aswell as similarty showcaser
    
        print('-'*50)
        print('')
        print('GO TOOL MENU')
        print('What would you like doing?')
        print('')
        print('1. Column filtering from GAF file.')
        print('2. Ontology Menu from OBO file.')
        print('3. Viewing Similarity between terms.')
        print('4. Checking Term neighborhood in OBO file.')
        print('5. View Annotation Matrices.')
        print('6. Exit')
        print('')
    
    
        while True:
            selection = input('Select one option from 1 to 6 (input an integer): ')
        
            if selection == '1':  #re-use of gaf menu
                self.search_gaf()
            
            elif selection == '2': #re-use of obo menu
                self.search_obo()
            
            elif selection == '3':
            
                print('Similarity calculations')
                
                term1 = input('Enter first GO term: ').strip()
                term2 = input('Enter second GO term: ').strip()
                
                self.compare_similarity_methods(term1, term2)

                
                
            elif selection == '4':
                
                term_id = input('Enter GO term ID: ').strip()
                distance = input('Enter distance (1-3, default=1): ').strip()
                distance = int(distance) if distance.isdigit() else 1
                
                neighbors = self.get_neighborhood_info(term_id, distance)
                
                if neighbors:
                    print(f'Neighbors of {term_id} (distance {distance}):')
                    print('-'*40)
                    for neighbor in neighbors[:20]:
                        print(f"   {neighbor['term_id']} - {neighbor['name']}")
                    if len(neighbors) > 20:
                        print(f'... and {len(neighbors) - 20} more')
                    print(f'\nTotal: {len(neighbors)} neighbors')
                else:
                        print(f'No neighbors found for {term_id}')
                
            elif selection == '5':
                matrix, genes, go_terms = self.create_annotation_matrix()
                print(f'Matrix: {matrix.shape[0]} genes × {matrix.shape[1]} GO terms')
                print(f'Sparsity: {1 - (matrix.sum() / matrix.size):.1%}')
                print('Preview (5x5):')
                print(matrix[:5, :5])
                print('')
                print('This is a 100x100 matrix truncated to 5x5')
                print('What does this matrix mean?')
                print('')
                print('0 values are written if a gene is NOT annotated to the GO Term')
                print('1 values are written if a gene IS annotated to the GO Term')
                print('X-Axis: Go Terms')
                print('Y-Axis: Gene Names')
                print('')
                self.analyze_matrix() #returns matrix analysis
            
        
            elif selection == '6':
                break
        
            else:
                print('Invalid option, please insert a number from 1 to 6')
            
            
            
            
            
if __name__ == "__main__":
    tools = GO_Tools('goa_human.gaf', 'go-basic.obo')
    tools.main_search_menu()
