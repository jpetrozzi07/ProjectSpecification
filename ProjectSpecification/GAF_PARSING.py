import pandas as pd

df = pd.read_csv('goa_human.gaf', comment='!', delimiter='\t', compression='gzip', header=None)

ID_informations = None

def GAFPARSING(df):  #parsing command

    print('GAF ANNOTATION SEARCH')
    print('YOU CAN SEARCH BY:')
    print('')
    print('1. GO_ID')
    print('2. DB_OBJECT_SYMBOL')
    print('3. Evidence_code')
    print('')

    type_of_input = input('Select searching category: ').strip()

#case sensitive

    if type_of_input == 'GO_ID':
        go_id = input('Insert the GO ID to be analyzed: ').strip()
        ID_informations = df[df[4] == go_id] # GO:0006457 example for quick testing
    
#case sensitive
    
    if type_of_input == 'DB_OBJECT_SYMBOL':
        db_object_symbol = input('Insert DB_OBJECT_SYMBOL to be analyzed: ').strip()
        ID_informations = df[df[2] == db_object_symbol].str.upper() 
    
#not case sensitive    
 
    if type_of_input == 'Evidence_code':
        evidence_code = input('Insert Evidence_code to be analyzed: ').strip()
        ID_informations = df[df[6] == evidence_code].str.upper()
    
#not case sensitive
    if ID_informations.empty:
        print('No annotations were found in this DataFrame for the requested definition.')

    else:
        print('Annotation Search Results:')
        print(ID_informations)
        
        
def RESULTSTATISTICS(ID_informations): #Statistics for the obtained results
    
    print(f'Total amount of genes reported: ' + str(len(ID_informations)) + ', of which ' + str(ID_informations[2].nunique()) + ' are unique.')
    print(f'Total amount of Unique GO ID(s): ' + str(ID_informations[4].nunique()))
    
    
    
GAFPARSING(df)

RESULTSTATISTICS(ID_informations)