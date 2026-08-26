import networkx as nx
import obonet
import matplotlib.pyplot as plt

# Read the taxrank ontology
url = 'https://current.geneontology.org/ontology/go-basic.obo'
graph = obonet.read_obo(url)


# Number of nodes
print(len(graph))

# Number of edges
graph.number_of_edges()

# Check if the ontology is a DAG
nx.is_directed_acyclic_graph(graph)

# Mapping from term ID to name
id_to_name = {id_: data.get('name') for id_, data in graph.nodes(data=True)}
id_to_name['GO:0044231']  # TAXRANK:0000006 is species

# Find all superterms of species. Note that networkx.descendants gets
# superterms, while networkx.ancestors returns subterms.
nx.descendants(graph, 'GO:0044231')

# Include parsed OBO clauses to preserve comments and trailing modifiers
graph = obonet.read_obo(url, include_clauses=True)
graph.nodes['GO:0044231']['_clauses']['is_a'][0]
print(graph.nodes['GO:0044231']['_clauses']['is_a'][0])
# output preserves the OBO trailing comment after "!":
# {
#     'tag': 'is_a',
#     'value': 'TAXRANK:0000000',
#     'trailing_modifier': None,
#     'comment': 'taxonomic_rank',
# }
pos = nx.spring_layout(graph, k=0.15, iterations=20)
nx.draw(graph, pos=pos, node_size=10, with_labels=False, arrows=True, linewidths=0.1)

plt.show()