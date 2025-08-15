import pprint
import networkx as nx
import parser
from parser import rel, dpower

# --- Helpers
"""
Find an alias if it exists.
"""
def lookup_alias(alias_registry: dict[str, str], name: str):
  alias_name = alias_registry.get(name, None)
  if alias_name is not None:
    return alias_name
  return name

"""
Convert a relation to source ilk.
If an object is the source to a relation, it implies that the source is of a
certain ilk.
NOTE: let's assume that there must be a single ilk and see if we run into trouble.
"""
def convert_relation_to_ilk(relation: rel):
  match relation:
    case rel.MAPTO | rel.SUBSET | rel.ALIAS | rel.TBD | rel.GROUP | rel.GROUP_FOREACH:
      return None
    
    # TODO: this will collide with affects for linear etc. so need to think it through
    # case rel.GROUP | rel.GROUP_FOREACH:
    #   return 'group'

    case rel.AFFECTS | rel.COVERS:
      return 'structure'
    
    case rel.TYPE:
      return 'type-definition'
  assert False, f'Relation has not matching ilk. {relation=}'

# --- Compile
def compile(file_path: str, verbose=False, ignore_decl_strength=False):
  spec = parser.spec_from_file(file_path)
  interp = parser.make_relations(spec)
  if verbose:
    print('\n --- Parsing spec ---')
    parser.print_interp(interp)

  return compile_interp(interp, verbose=verbose, ignore_decl_strength=ignore_decl_strength)

def compile_interp(interp: list, verbose=False, ignore_decl_strength=False):
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
  
  type_registry = {}  # node: type
  ilk_registry = {}   # node: ilk
  

  # --- Alias Pass.
  # Use a different data structure for alias. Keys are original names, 
  # a = b = c =>
  #   alias_registry = {
  #     a: 'a = b = c'
  #     b: 'a = b = c'
  #     c: 'a = b = c'
  #   }
  # We do a pass on interp to get the aliases, since we'll use them for the other
  # graphs after.
  for declaration in interp:
    source = parser.get_declaration_source(declaration)
    relation = parser.get_declaration_relation(declaration)
    target = parser.get_declaration_target(declaration)
    # NOTE: This ignores declaration power

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


  # --- Strong Declaration Pass
  # Add each nodes and edges of strong declarations to the appropriate relation graph.
  # NOTE: since these are DiGraphs, there is at most one directed edge between 
  # two nodes. This means that duplicate relations are automatically delt with.
  for declaration in interp:
    # Skip Weak and Question declarations.
    if parser.get_declaration_power(declaration) is not dpower.STRONG and not ignore_decl_strength:
      continue

    source = lookup_alias(alias_registry, parser.get_declaration_source(declaration))
    relation = parser.get_declaration_relation(declaration)
    target = lookup_alias(alias_registry, parser.get_declaration_target(declaration))

    if relation in (rel.TBD, rel.ALIAS):
      vprint('Skipping due to relation type: ', declaration)
      continue

    if relation == rel.TYPE:
      # Tagging types as nodes reduces proliferating vertices (expensive)
      # but it's just as expressive as using edges.
      # NOTE: rel.TYPE is added to the graph after compose_all to avoid
      # losing attributes to the graph composition.

      # Tag node (target) with the type (source)
      type_registry[target] = source
      continue    

    vprint(f'{source} -{relation.name}-> {target}')
    rel_graph = graphs[relation]

    # Add Ilk to the node
    # NOTE: ilk is added to the graph after compose_all to avoid
    # losing attributes to the graph composition.
    source_ilk = convert_relation_to_ilk(relation)
    if source_ilk is not None:
      assert ilk_registry.get(source) is None or ilk_registry.get(source) == source_ilk, f'Node already has an ilk (node={source}, ilk={ilk_registry.get(source)}) cannot give it another ilk (ilk={source_ilk})'
      ilk_registry[source] = source_ilk

    # Finally add edge
    rel_graph.add_edge(source, target, relation=relation.name)


  # --- Weak Declaration Pass.
  # If the source and target were declared in the Strong pass, then we add the weak relation.
  # This helps prevent the proliferation of vertices that the user doesn't actually care about
  # eg. (view/encoding.vstack, rel.SUBSET, view/encoding, dpower.WEAK) doesn't mean we care about view/encoding
  if not ignore_decl_strength:
    strong_nodes = nx.compose_all(
      [nx.MultiDiGraph(graph) for graph in graphs.values()]
    ).nodes()
    for declaration in interp:
      if parser.get_declaration_power(declaration) is not dpower.WEAK:
        # Skip Weak and Question declarations.
        continue

      source = lookup_alias(alias_registry, parser.get_declaration_source(declaration))
      relation = parser.get_declaration_relation(declaration)
      target = lookup_alias(alias_registry, parser.get_declaration_target(declaration))

      if source in strong_nodes and target in strong_nodes:
        vprint(f'{source} -{relation.name}-> {target}')
        rel_graph = graphs[relation]
        # Finally add edge
        rel_graph.add_edge(source, target, relation=relation.name)
  

  # --- Question Declartion Pass.
  # Do the Question declarations actually check out?
  # TODO: first need to figure out when question declarations are made and
  #       figure out how `def` stuff will work.


  # --- Combine Graphs.
  # NOTE: if multiple graphs use the same node-attribute, then compose_all will
  # use the last one. Seems like a footgun to me!
  combined_graph = nx.compose_all(
    [nx.MultiDiGraph(graph) for graph in graphs.values()]
  )

  # - Assign types
  for node, node_type in type_registry.items():
    combined_graph.add_node(node, type=node_type)
  
  # - Assign ilk
  for node, node_type in ilk_registry.items():
    combined_graph.add_node(node, ilk=node_type)

  return combined_graph


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
  # test_graph = compile('test-specs.yaml', verbose=True)
  test_graph = compile('video-editor.yaml', verbose=True, ignore_decl_strength=False)
  mermaid_graph(test_graph, verbose=True)
