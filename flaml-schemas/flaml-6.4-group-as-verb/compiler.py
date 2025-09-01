"""
The compiler produces a directed graph representation of a spec from a list of
declarations.
TODO: 'interp' should be renamed to 'declarations' or 'decls' because it now
      also includes path information. The compiler only cares about declarations
      so from its perspective, that's all the interp is. Not really worth the
      rename right now, but it'd be nice "when there's time".

"""

import pprint
import networkx as nx
import parser
from parser import rel, dpower

import argparse
import os

argp = argparse.ArgumentParser(
                    prog='Interface Schema Compiler',
                    description='Prints mermaid diagram for provided files. Default is calendar.yaml.')
argp.add_argument('filenames', action='append')
argp.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output.")

# --- Helpers
"""
Find an alias if it exists.
"""
def lookup_alias(alias_registry: dict[str, str], name: str):
  return alias_registry.get(name, name)  # return name if it wasn't found in the registry

# --- Compile
"""
Construct an extension to a type_registry based on type_interps.
type_interps declares a bunch of stuff. This include declaring an instance of something else.
When that happens, we want to add that instantiation to the type_registry.

For example, if we define (gui) view and gui declares (linear) /encoding.vstack,
we want to infer that view/encoding.vstack is also (linear).

Inputs:
type_registry = {instance_name: type_name}
type_interps  = {type_name: [type_declarations]}
"""
def make_type_registry_extension(type_registry: dict[str, str], type_interps: dict[str, list], valid_nodes: list[str], get_alias: callable):
  # Find type and add instances when used, including when nested
  if len(type_registry.keys()) == 0:  # base case
    return {}

  type_registry_extension = {}
  for spec_inst_name, spec_type_name in type_registry.items():
    type_interp = type_interps.get(spec_type_name, None)
    assert type_interp is not None, f'Type `{spec_type_name}` was used with `{spec_inst_name}` but not declared.'

    for type_declaration in type_interp:
      type_declaration = parser.substitute_instance_name_in_decl(type_declaration, spec_inst_name)
      
      source = get_alias(parser.get_declaration_source(type_declaration))  # type name
      relation = parser.get_declaration_relation(type_declaration)
      target = get_alias(parser.get_declaration_target(type_declaration))  # declaration instance node

      # parser.print_declaration(type_declaration)  # DEBUG
      if relation == rel.TYPE and target in valid_nodes:
        # Tag node (target) with the type (source)
        type_registry_extension[target] = source
  
  return type_registry_extension | make_type_registry_extension(type_registry_extension, type_interps, valid_nodes, get_alias)


"""
Expand type_interp with the parent's type_interp. type_interp is modified in place.
For example, (presentation) is (gui)'s parent, so we add (presentation)'s interp to (gui)'s interp.

Input:
type_interps_lists: {type_name: [type_declarations]}
type_parents      : nx.digraph where edges are (type->parent)
"""
def expand_type_interps(type_interps_lists: dict[str, list], type_parents: nx.digraph, verbose=False):
  nodes_with_parents = type_parents.nodes()
  for type_name, type_interp in type_interps_lists.items():
    if type_name not in nodes_with_parents:
      # Type does not have a parent.
      continue

    parents_list = nx.descendants(type_parents, type_name)
    for parent_name in parents_list:
      if parent_name not in type_interps_lists.keys():
        # This type was probably not defined with declarations eg. (structure)
        continue
    
      if verbose:
        print(f'extending ({type_name}) with ({parent_name})')
      type_interps_lists[type_name].extend(type_interps_lists[parent_name])
  
  # DEBUG
  # pprint.pprint(type_interps_lists)


def compile(file_path: str, verbose=False):
  spec = parser.spec_from_file(file_path)
  return compile_spec(spec, verbose)

def compile_spec(spec: list, verbose=False):
  # TODO: technically I should rename all "interp" decl, but that's not a priority.
  std_spec = parser.spec_from_file('standard.yaml')
  interp = parser.make_relations(spec)
  if verbose:
    print('\n--- Parsing spec ---')
    parser.print_interp(interp)
  
  if verbose:
    print('\n--- Parsing standard library ---')
  standard_type_interps, standard_type_parents = parser.parse_type_definitions(std_spec, verbose)
  standard_types = set(standard_type_interps.keys())

  if verbose:
    print('\n--- Parsing spec types ---')
  type_interps, type_parents = parser.parse_type_definitions(spec, verbose)
  type_interps = type_interps | standard_type_interps
  type_parents = type_parents | standard_type_parents
  
  return compile_interp(interp[0], type_interps, type_parents, standard_types, verbose=verbose)

def compile_interp(interp: list, type_interps: dict[str,list], type_parents: dict[str,str], standard_types: set[str], verbose=False):
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

  # --- Alias Pass.
  vprint('\n-- Alias Pass')
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
  
  def get_alias(node_name):
    return lookup_alias(alias_registry, node_name)
  
  if verbose:
    for node, alias_name in alias_registry.items():
      vprint(f'{node:>25} : {alias_name}')

  # Alias graph is no longer needed, so we delete it. This means it doesn't get
  # combined in the final multigraph.
  graphs.pop(rel.ALIAS)


  # --- Strong Declaration Pass
  # Add each nodes and edges of strong declarations to the appropriate relation graph.
  # NOTE: since these are DiGraphs, there is at most one directed edge between 
  # two nodes. This means that duplicate relations are automatically delt with.
  vprint('\n-- Strong Declaration Pass')
  for declaration in interp:
    # Skip Weak and Question declarations.
    if parser.get_declaration_power(declaration) != dpower.STRONG:
      continue

    source = get_alias(parser.get_declaration_source(declaration))
    relation = parser.get_declaration_relation(declaration)
    target = get_alias(parser.get_declaration_target(declaration))

    if relation in (rel.TBD, rel.ALIAS):
      vprint('Skipping due to relation type: ', declaration)
      continue

    if relation == rel.TYPE:
      # Tagging types as nodes reduces proliferating vertices (expensive)
      # but it's just as expressive as using edges.
      # NOTE: rel.TYPE is added to the graph after compose_all to avoid
      # losing attributes to the graph composition.

      # Tag node (target) with the type (source)
      # TODO: When dealing with an alias, there are potentially multiple types.
      #       Right now, it will essentially pick the last one that was defined.
      #       It would be better to do fuzzy type matching (eg. for structures).
      if type_registry.get(target) is not None:
        # TODO: fuzzy type matching here if required
        assert type_registry[target] == source, f'Double type assignment: Trying to assign `({source})` to `{target}`, but it already has type ({type_registry[target]}). Is this an alias problem?'
      type_registry[target] = source
      continue    

    vprint(f'{source} -{relation.name}-> {target}')
    rel_graph = graphs[relation]

    # Finally add edge
    rel_graph.add_edge(source, target, relation=relation.name)

  # --- TYPE Declaration Pass.
  vprint('\n-- Type Declaration Pass --')
  num_strong_declarations = len(interp)
  
  # Any instance of a type might used the type's attributes. This includes maybe
  # adding instances of other types and their attributes (recursively). However,
  # We only want to add stuff if it's actually used in the spec.
  strong_nodes = nx.compose_all(
    [nx.MultiDiGraph(graph) for graph in graphs.values()]
  ).nodes()

  # Add parent declarations to type declarations
  type_ancestry = nx.DiGraph([(type_name, type_parent_name) for type_name, type_parent_name in type_parents.items()])
  assert nx.is_directed_acyclic_graph(type_ancestry), f'Type ancestry graph contains a cycle. {type_ancestry=}'
  expand_type_interps(type_interps, type_ancestry, verbose=verbose)

  # Find type and add instances when used, including when nested
  type_registry = type_registry | make_type_registry_extension(type_registry, type_interps, strong_nodes, get_alias)

  # Add declaration from type to instances
  for spec_inst_name, spec_type_name in type_registry.items():
    type_interp = type_interps.get(spec_type_name, None)
    assert type_interp is not None, f'Type `{spec_type_name}` was used with `{spec_inst_name}` but not declared.'

    for type_declaration in type_interp:
      type_declaration = parser.substitute_instance_name_in_decl(type_declaration, spec_inst_name)
      source = get_alias(parser.get_declaration_source(type_declaration))  # declaration type
      relation = parser.get_declaration_relation(type_declaration)
      target = get_alias(parser.get_declaration_target(type_declaration))  # declaration instance node
      if relation == rel.TYPE and target in strong_nodes:
        continue  # already dealt with types

      interp.append(parser.substitute_instance_name_in_decl(type_declaration, spec_inst_name))

  vprint('\n- These declarations were added from type definitions:')
  if verbose:
    for decl in interp[num_strong_declarations:]:
      parser.print_declaration(decl)

  # --- Weak Declaration Pass.
  vprint('\n-- Weak Declaration Pass --')
  # If the source and target were declared in the Strong pass, then we add the weak relation.
  # This helps prevent the proliferation of vertices that the user doesn't actually care about
  # eg. (view/encoding.vstack, rel.SUBSET, view/encoding, dpower.WEAK) doesn't mean we care about view/encoding

  for declaration in interp:
    if parser.get_declaration_power(declaration) is not dpower.WEAK:
      # Skip Strong and Question declarations.
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
  vprint('\n-- Combine Graphs')
  # NOTE: if multiple graphs use the same node-attribute, then compose_all will
  # use the last one. Seems like a footgun to me!
  combined_graph = nx.compose_all(
    [nx.MultiDiGraph(graph) for graph in graphs.values()]
  )

  # - Assign types
  vprint('- Assign Types')
  for node, node_type in type_registry.items():
    vprint(f'({node_type}) {node}')
    combined_graph.add_node(node, type=node_type)
  
  # - Assign whether type is from standard library or not
  vprint('- Assign whether type is standard')
  for node_name, attr in combined_graph.nodes(data=True):
    is_standard = False
    type_name = attr.get('type', None)
    if type_name is not None and type_name in standard_types:
      is_standard = True
    combined_graph.add_node(node_name, is_standard=is_standard)
    

  for node, node_type in type_registry.items():
    # vprint(f'({node_type}) {node}')
    is_standard = node_type in standard_types
    combined_graph.add_node(node, is_standard=is_standard)

  # - Assign Layer
  # We tag nodes depending on whether they are in the conceptual, presentation,
  # or behavior layer. They are mutually exclusive, and depend entirely on type.
  vprint('\n- Assign Layer')

  # First pass assigns layer based on type.
  # print_graph(type_ancestry) # TODO: RM
  for node_name, attr in combined_graph.nodes(data=True):
    type_name = attr.get('type')
    node_layer = 'conceptual'
    if type_name is None or type_name not in type_ancestry.nodes:
      # no type and no parents
      pass
    else:
      is_presentation_layer = type_name == 'presentation' or 'presentation' in nx.descendants(type_ancestry, type_name)
      is_action_layer = type_name == 'action' or 'action' in nx.descendants(type_ancestry, type_name)
      assert not (is_presentation_layer and is_action_layer), f'Error: `({type_name}) {node_name}` is somehow both in the presentation and action layer. \n          nodes:{type_ancestry.nodes}\n          edges:{type_ancestry.edges}'

      node_layer = 'conceptual'
      if is_presentation_layer:
        node_layer = 'presentation'
      elif is_action_layer:
        node_layer = 'action'
    
    # DEBUG
    # vprint(f'({type_name}) {node_name} => {node_layer}')
    combined_graph.add_node(node_name, layer=node_layer)

  # Second pass looks at the items that are grouped by presentation and action items.
  for node_name, attr in combined_graph.nodes(data=True):
    node_layer = attr.get('layer')
    if node_layer == 'conceptual':
      continue

    if node_name not in graphs[rel.GROUP_FOREACH].nodes():
      continue

    for grouped_node in nx.descendants(graphs[rel.GROUP_FOREACH], node_name):
      combined_graph.add_node(grouped_node, layer=node_layer)
      # DEBUG
      # vprint(f'converting {grouped_node} to {node_layer} layer')
  
  if verbose:
    for node_name, attr in combined_graph.nodes(data=True):
      type_name = attr.get('type')
      node_layer = attr.get('layer')
      type_str = f'({type_name}) ' if type_name is not None else ''
      vprint(f'{node_layer}: {type_str}{node_name}')

  # Label edges based which layer it comes from/gets to
  for edge in combined_graph.edges:
    source, target, key = edge
    source_layer = combined_graph.nodes[source].get('layer')
    target_layer = combined_graph.nodes[target].get('layer')
    nx.set_edge_attributes(combined_graph, {
      edge: {'layers': (source_layer, target_layer)}
    })

  return combined_graph

# ---- Presenting Results ----
# --- Printing Graphs
def print_graph(graph: nx.MultiDiGraph):
  nodes = graph.nodes().data()
  edges = graph.edges.data()
  print(f'-- {len(nodes)} nodes, {len(edges)} edges')
  print('-- Nodes')
  for node in nodes:
    name, attr = node
    type_name = attr.get('type')
    type_name = '' if type_name is None else f'({type_name}) '
    print(type_name+name)
  
  print('-- Edges')
  for edge in edges:
    source, target, attr = edge
    relation = attr.get('relation')
    print(f'{source} -{relation}-> {target}')

def get_type_stats(graph: nx.MultiDiGraph, verbose=False):
  if verbose:
    print(f'nodes: {len(graph.nodes())}, edges: {len(list(graph.edges))}')

  node_types = {} # {str(node): int(count)}
  non_standard_types = set()
  for node, attr in graph.nodes().items():
    node_type = attr.get('type')
    if attr.get('is_standard'):
      node_types[node_type] = 1 + node_types.get(node_type, 0)
    else:
      non_standard_types.add(node_type)
  
  if verbose:
    print('-- Node types')
    pprint.pprint(node_types)

    print('-- Nonstandard types')
    print(non_standard_types)
  
  edge_types = {}  # {relation type: count}
  for edge in graph.edges.data():
    source, target, attr = edge
    relation = attr.get('relation')
    edge_types[relation] = 1 + edge_types.get(relation, 0)
  
  if verbose:
    print('-- Edge Relations')
    pprint.pprint(edge_types)


# --- Mermaid Visualization ---
def mermaid_graph_core(
    graph: nx.MultiDiGraph,
    should_color_node: callable,
    should_color_edge: callable,
    pad: str,
    start_index: int,
    ):
  id_dict = {}  # {graph_node_id: number_id}
  id_gen = start_index    # generated id for each node
  
  mermaid = f"{pad}classDef Highlighted fill:#fbcef6,stroke:#8353e4;\n\n"
  # --- List nodes
  for node_name, attributes in graph.nodes.data():
    # Prefix (type) if it exists.
    node_type = attributes.get('type', None)
    type_prefix = ''
    if node_type is not None:
      type_prefix = f'({node_type}) '
    
    style_suffix = ''
    if callable(should_color_node) and should_color_node(node_name):
      style_suffix = ':::Highlighted'

    # Define node name with id.
    mermaid += f'{pad}{id_gen}["{type_prefix}{node_name}"]{style_suffix}\n'
    id_dict[node_name] = id_gen
    id_gen += 1

  # --- List edges
  # Keep track of links highlighted links because you have to list them by order
  # of appearance: https://mermaid.js.org/syntax/flowchart.html#styling-links
  highlighted_links = []
  link_count = 0
  for source, target, attributes in graph.edges.data():
    assert (
      source in id_dict.keys()
    ), f"missing source from edge: {source} (~~> {target})"
    assert (
      target in id_dict.keys()
    ), f"missing target from edge: ({source} ~~>) {target}"

    rel = attributes.get("relation", "None")
    if callable(should_color_edge) and should_color_edge((source, target)):
      highlighted_links.append(link_count)

    source_id = id_dict.get(source)
    target_id = id_dict.get(target)
    mermaid += f"{pad}{source_id} -->|{rel}| {target_id}\n"
    link_count += 1
  
  # Style links
  # NOTE: mermaid parser complains if there are no nodes
  if len(highlighted_links) > 0:
    highlighted_links_str = ",".join([str(n) for n in highlighted_links])
    mermaid += f"{pad}linkStyle {highlighted_links_str} color:purple,stroke:purple,stroke-width:2px;\n"

  return (mermaid, id_dict)
  

def mermaid_graph(
    graph: nx.MultiDiGraph,
    should_color_node: callable = None,
    should_color_edge: callable = None,
    verbose=False):
  if verbose:
    print('\n--- Making Mermaid Graph ---')

  mermaid = "flowchart LR\n"
  mermaid_core, _ = mermaid_graph_core(
    graph,
    should_color_node=should_color_node,
    should_color_edge=should_color_edge,
    pad = '  ',
    start_index=0
  )
  mermaid += mermaid_core

  if verbose:
    print(mermaid)
  return mermaid

if __name__ == '__main__':
  # test_graph = compile('test-specs.yaml', verbose=True)
  files = ['calendar.yaml']

  args = argp.parse_args()
  if len(args.filenames) > 0:
    files = args.filenames
  
  for spec_file in files:
    assert type(spec_file) is str
    if spec_file[-5:] != '.yaml':
      print(f'Skipping `{spec_file}` because it\'s not yaml')
      continue

    if not os.path.exists(spec_file):
      print(f'Skipping `{spec_file}` because it does not exist.')
      continue

    test_graph = compile(spec_file, verbose=args.verbose)
    mermaid_graph(test_graph, verbose=True)
