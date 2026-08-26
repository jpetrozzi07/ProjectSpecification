import pandas as pd

def obo_to_dataframe(file_path):
    terms = []
    current_term = {}
    in_term = False

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            # Signal the start of a new Term block
            if line == '[Term]':
                if current_term:
                    terms.append(current_term)
                current_term = {}
                in_term = True
            # Signal entry into a non-Term block (e.g., [Typedef], [Instance])
            elif line.startswith('[') and line.endswith(']'):
                if current_term:
                    terms.append(current_term)
                current_term = {}
                in_term = False
            # Extract tags and values inside [Term] stanzas
            elif in_term and ':' in line:
                tag, val = line.split(':', 1)
                tag, val = tag.strip(), val.strip()
                
                # Handle tags that appear multiple times per term (like 'is_a' or 'synonym')
                if tag in current_term:
                    if isinstance(current_term[tag], list):
                        current_term[tag].append(val)
                    else:
                        current_term[tag] = [current_term[tag], val]
                else:
                    current_term[tag] = val

        # Append the final block if it exists
        if current_term:
            terms.append(current_term)

    return pd.DataFrame(terms)

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

df = obo_to_dataframe("go-basic.obo")
print(df[['id', 'name', 'namespace']].head(7))

result = find_related('GO:0032501', df)
print(f"Nodo:'GO:0032501'")
print(f"Parents: {result['parents']}")   # ['GO:0002']
print(f"Children: {result['children']}") # ['GO:0004', 'GO:0005']
