import pprint
import networkx as nx
import parser
from parser import rel

# --- Helpers
def lookup_alias(alias_registry: dict[str, str], name: str):
  alias_name = alias_registry.get(name, None)
  if alias_name is not None:
    return alias_name
  return name

# --- Compile
def compile(file_path: str, verbose=False):
  spec = parser.parse_yaml(file_path)
  interp = parser.make_relations(spec)
  if verbose:
    print('\n --- Parsing spec ---')
    for line in interp:
      pretty_source = line['source']
      pretty_relation = line['relation'].name
      pretty_target = line['target']
      print(f'{pretty_source}  -{pretty_relation}->  {pretty_target}')

  return compile_interp(interp, verbose=verbose)

def compile_interp(interp: list, verbose=False):
  """
  Takes a list of interpreted relations (from the parser) and produces a networkx
  MultiGraph which represents this list. It also applies various transitive rules
  to complete the graph. 
  """
  def vprint(*args):
    if verbose:
      print(*args)
  
  vprint('\n--- Compiling interp ---')

  # --- Initialize graphs
  # NOTE: we make a graph for each type of relation for closures
  graphs: dict[nx.DiGraph] = {}
  for relation_enum in list(rel):
    if relation_enum in (rel.TBD, rel.TYPE):
      # ignore unparsed relations
      continue

    graphs[relation_enum] = nx.DiGraph()
  
  # Use a different data structure for alias. Keys are original names, 
  # a = b = c =>
  #   alias_registry = {
  #     a: 'a = b = c'
  #     b: 'a = b = c'
  #     c: 'a = b = c'
  #   }
  # We do a pass on interp to get the aliases, since we'll use them for the other
  # graphs after.
  for line in interp:
    source = line['source']
    relation = line['relation']
    target = line['target']

    if relation == rel.ALIAS:
      graphs[rel.ALIAS].add_edge(source, target, relation=rel.ALIAS)
  
  alias_registry = {}
  for connected in nx.connected_components(graphs[rel.ALIAS].to_undirected()):
    combined_name = ' = '.join(list(connected))
    for node in connected:
      alias_registry[node] = combined_name
  
  # Alias graph is no longer needed, so we delete it. This means it doesn't get
  # combined in the final multigraph.
  graphs.pop(rel.ALIAS)
  
  # --- Add each edge to the appropriate relation graph.
  # NOTE: since these are DiGraphs, there is at most one directed edge between 
  # two nodes. This means that duplicate relations are automatically delt with.
  for line in interp:
    source = lookup_alias(alias_registry, line['source'])
    relation = line['relation']
    target = lookup_alias(alias_registry, line['target'])

    if relation in (rel.TBD, rel.ALIAS):
      vprint('Skipping: ', line)
      continue

    vprint(f'{source} -{relation.name}-> {target}')

    # Tag node (target) with the type (source)
    # NOTE: This helps prevent the proliferation of nodes and is just as powerful.
    if relation == rel.TYPE:
      rel_graph.add_node(target, type=source)
      continue

    rel_graph = graphs[relation]
    # NOTE: the relation attribute is then carried through to the composed graph at the end
    rel_graph.add_edge(source, target, relation=relation.name)

  # --- Combine graphs
  # NOTE: if multiple graphs use the same node-attribute, then compose_all will
  # use the last one. Seems like a footgun to me!
  return nx.compose_all(
    [nx.MultiDiGraph(graph) for graph in graphs.values()]
  )

def mermaid_graph(graph: nx.MultiDiGraph, verbose=False):
  if verbose:
    print('\n--- Making Mermaid Graph ---')

  pad = "  "

  id_gen = 0    # generated id for each node
  id_dict = {}  # {graph_node_id: number_id}
  mermaid = "flowchart LR\n"

  for node_name, attributes in graph.nodes.data():
    # Prefix (type) if it exists.
    node_type = attributes.get('type', None)
    type_prefix = ''
    if node_type is not None:
      type_prefix = f'({node_type}) '

    # Define node name with id.
    mermaid += f'{pad}{id_gen}["{type_prefix}{node_name}"]\n'
    id_dict[node_name] = id_gen
    id_gen += 1

  for source, target, attributes in graph.edges.data():
    assert (
      source in id_dict.keys()
    ), f"missing source from edge: {source} (~~> {target})"
    assert (
      target in id_dict.keys()
    ), f"missing target from edge: ({source} ~~>) {target}"

    rel = attributes.get("relation", "None")

    source_id = id_dict.get(source)
    target_id = id_dict.get(target)
    mermaid += f"{pad}{source_id} -->|{rel}| {target_id}\n"
  
  if verbose:
    print(mermaid)
  return mermaid

if __name__ == '__main__':
  test_graph = compile('test-specs.yaml', verbose=True)
  mermaid_graph(test_graph, verbose=True)
