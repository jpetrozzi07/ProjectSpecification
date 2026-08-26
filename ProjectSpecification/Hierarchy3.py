import pandas as pd

def find_related(term_id, df, id_col='id', link_col='is_a'):
    """Find all terms directly linked to a given ID"""
    
    # Get the term itself
    term = df[df[id_col] == term_id]
    if term.empty:
        return f"ID {term_id} not found"
    
    # Get parents (where this term is a child)
    parents = term[link_col].iloc[0] if not pd.isna(term[link_col].iloc[0]) else []
    if not isinstance(parents, list):
        parents = [parents]  # Handle single values
    
    # Get children (where this term appears as a parent)
    children = df[df[link_col].apply(
        lambda x: term_id in x if isinstance(x, list) else x == term_id
    )][id_col].tolist()
    
    return {
        'term': term_id,
        'name': term['name'].iloc[0],
        'parents': parents,
        'children': children,
        'all_related': parents + children
    }

# Usage
df = obo_to_dataframe("go-basic.obo")
result = find_related('GO:0001', df)
print(f"Parents: {result['parents']}")   # ['GO:0002']
print(f"Children: {result['children']}") # ['GO:0004', 'GO:0005']
