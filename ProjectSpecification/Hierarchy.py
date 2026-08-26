def parse_obo(file_path):
    terms = {}
    current_term = {}
    isterm = False
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            isterm = isterm or line.startswith('id:')
            if isterm and ": " in line:
                key, value = line.split(': ', 1)
                if key == "id":
                    current_term = terms.setdefault(value, {})
                    current_term["id"] = value
                else:
                    current_term.setdefault(key, []).append(value)
    return terms

def make_hierarchy(terms):
    for term in list(terms.values()):
        term.setdefault("children", [])
        if "is_a" in term:
            for is_a in term["is_a"]:
                parent = is_a.split()[0]
                terms.setdefault(parent, { 'id': parent }).setdefault("children", []).append(term)
    return [term for term in terms.values() if "is_a" not in term]
    
def display_hierarchy(terms, indent=""):
    for term in terms:
        print(f"{indent}{term['id']}")
        display_hierarchy(term['children'], indent + "  ")

if __name__ == "__main__":
    file_path = 'go-basic.obo'
    terms = parse_obo(file_path)
    roots = make_hierarchy(terms)
    display_hierarchy(roots)
