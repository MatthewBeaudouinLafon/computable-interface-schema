"""
Find the graph-edit-distance between two compiled specifications and present the
overlap as the analogy in the user interface.
Analogies are presented as from a source domain (sinister) to a
target domain (dexter). This is to avoid confusion with source and targets of 
edges in individual graphs.

"""
import enum
import pprint
import timeit

import networkx as nx
import compiler
import analogylib
from analogylib import Analogy, Hand
from parser import rel

# ----- Analogy Computation
# The networkx algorithm tries to minimize costs. 
# So lower is better, higher is penalized.


MAX_COST = 10000
BASE_COST = 10

NODE_BASE_COST = BASE_COST
EDGE_BASE_COST = BASE_COST


"""
Cost incurred from making an analogy between two nodes.
"""
def node_subst_cost(n1, n2):
  n1_pref = n1.get('preference_id')
  n2_pref = n2.get('preference_id')
  if n1_pref is not None and n2_pref is not None and n1_pref == n2_pref:
    # if preferences are set on both sides and equal to each other, it's free!
    return 0

  n1_type = n1.get('type')
  n1_is_standard = n1.get('is_standard')

  n2_type = n2.get('type')
  n2_is_standard = n2.get('is_standard')
  
  if n1.get('layer') != n2.get('layer'):
    # different layers shouldn't match
    return MAX_COST

  if n1_is_standard or n2_is_standard:
    # TODO: do "type" "casting" for things like linear->tree
    if n1_type == n2_type:
      return NODE_BASE_COST # same (standard) type, no cost
    else:
      return NODE_BASE_COST + 30 # different type, there's a cost
  else:
    pass # ignore type if they're both custom

  # Otherwise, deemphasize this pairing by maximizing costs.
  return NODE_BASE_COST + 5


"""
Cost of inserting or deleting a node
Used for both node_del_cost and node_ins_cost, since it should be symmetric.
"""
def node_diff_cost(n1):
  return NODE_BASE_COST

"""
Cost incurred from making an analogy between two edges.
"""
def edge_subst_cost(e1, e2):
  assert e1.get('relation') is not None, f'Sinister edge has no relation.'
  assert e2.get('relation') is not None, f'Dexter edge has no relation.'

  # TODO: maybe subset can stand in for mapto? Or is that done with transitive
  # rules?
  if e1.get('relation') == e2.get('relation'):
    return EDGE_BASE_COST
  else:
    return MAX_COST

"""
Cost of deleting or inserting a edge
Used for both edge_del_cost and edge_ins_cost, since it should be symmetric.
"""
def edge_diff_cost(edge):
  relation = rel[edge.get('relation')]
  match relation:
    case rel.AFFECTS | rel.COVERS | rel.DIRECTION:
      return EDGE_BASE_COST
    case rel.CREATE | rel.DELETE | rel.UPDATE:
      return EDGE_BASE_COST
    case rel.UPDATE_SRC | rel.UPDATE_TRG:
      # TODO: is there a way to reward both at the same time?
      # Noteably, these edges can be deleted if the action also uses a direction
      # because 
      return EDGE_BASE_COST
    case rel.GROUP | rel.MAPTO | rel.SUBSET:
      return EDGE_BASE_COST + 1
    case rel.GROUP_FOREACH:
      return EDGE_BASE_COST + 5
 
  return EDGE_BASE_COST

"""
Compute analogy. This can terminate on its own, but it'll stop at the timeout
provided in the prep_analogy
"""
def compute_analogy(
  sinister_graph: nx.MultiDiGraph, dexter_graph: nx.MultiDiGraph, preferred_matches:dict|None = None, timeout: int = 1 * 60, verbose=False
):
  if verbose:
    print('\n---- Starting Analogy ----')

  # Prepare preferred matches for "efficient" matching
  # Really it's mostly massaging aliases so the user can input any of the names.
  if preferred_matches is not None:
    assert isinstance(preferred_matches, dict), 'Type Error'

    # The user should be able to use any of the names for an alias, so we need to
    # correct the name. The alias name's order is not fixed so this is required.
    sinister_aliases = {}
    for sinister_node in sinister_graph.nodes():
      if ' = ' in sinister_node:
        for alias in sinister_node.split(' = '):
          sinister_aliases[alias] = sinister_node
    
    dexter_aliases = {}
    for dexter_node in dexter_graph.nodes():
      if ' = ' in dexter_node:
        for alias in dexter_node.split(' = '):
          dexter_aliases[alias] = dexter_node

    print(dexter_aliases)
    
    if verbose:
      print('-- User defined preferred pairings')
 
    fixed_preferred_matches = {}
    preference_id = 0  # the node_subst_cost function will match based on this id
    # NOTE: a slightly crazier thing would be to add the node's name as an attribute
    # but that seems excessive, and not useful for anything else.
    for sinister_node, dexter_node in preferred_matches.items():
      if ' = ' in sinister_node:
        # If the order is wrong, pick the first name and rely on the alias lookup
        sinister_node = sinister_node.split(' = ')[0]
      
      if ' = ' in dexter_node:
        # If the order is wrong, pick the first name and rely on the alias lookup
        dexter_node = dexter_node.split(' = ')[0]

      # Replace name with looked up name
      print(dexter_node)
      sinister_node = sinister_aliases.get(sinister_node, sinister_node)
      dexter_node = dexter_aliases.get(dexter_node, dexter_node)
      fixed_preferred_matches[sinister_node] = dexter_node
      print(dexter_node)

      assert sinister_node in sinister_graph.nodes, f'Could not find node `{sinister_node}` in sinister graph.'
      assert dexter_node in dexter_graph.nodes, f'Could not find node `{dexter_node}` in dexter graph.'

      sinister_graph.add_node(sinister_node, preference_id=preference_id)
      dexter_graph.add_node(dexter_node, preference_id=preference_id)

      if verbose:
        print(f"{sinister_node:>30} <=> {dexter_node:<30}")
    

  geds = nx.optimize_edit_paths(
    sinister_graph,
    dexter_graph,
    timeout=timeout,
    node_subst_cost=node_subst_cost,
    node_ins_cost=node_diff_cost,
    node_del_cost=node_diff_cost,
    edge_subst_cost=edge_subst_cost,
    edge_ins_cost=edge_diff_cost,
    edge_del_cost=edge_diff_cost,
    # strictly_decreasing=False,
  )

  analogy = analogylib.new()
  costs = []
  timings = []
  start_time = timeit.default_timer()
  for ged in geds:
    analogy = analogylib.new()
    node_edit_path, edge_edit_path, cost = ged

    if verbose:
      print("\n\n-- cost:", cost)

    for node_edit in node_edit_path:
      lhs, rhs = node_edit
      analogylib.add_analogous_nodes(analogy, lhs, rhs)

    for edge_edit in edge_edit_path:
      lhs, rhs = edge_edit

      sinister_edge = None
      if lhs is not None:
        # NOTE: the last unpacked item is used by the multigraph to keep track
        # of different edges, so we don't need it.
        edge_src, edge_trg, edge_key = lhs
        lhs = f"{edge_src} ~ {edge_trg}"
        sinister_edge = (edge_src, edge_trg, edge_key)

      dexter_edge = None
      if rhs is not None:
        # NOTE: the last unpacked item is used by the multigraph to keep track
        # of different edges, so we don't need it.s
        edge_src, edge_trg, edge_key = rhs
        rhs = f"{edge_src} ~ {edge_trg}"
        dexter_edge = (edge_src, edge_trg, edge_key)

      analogylib.add_analogous_edges(analogy, sinister_edge, dexter_edge)

    # Nodes that are isolated at the end (ie. not connected to any edge) could be
    # mapped in anyway. Their lack of connect with anything else in the analogy suggests
    # that it's not a very structurally minded mapping.
    # Therefore, we prune them.
    if verbose:
      print('---- Pruning isolated nodes')

    analogy_graph = analogylib.graph_from_analogy(analogy, Hand.SINISTER)
    for node_name in nx.isolates(analogy_graph):
      if verbose:
        dexter_node_name = analogylib.get_analogous_node(analogy, node_name)
        print(f'pruning isolate: {node_name:>30} <=> {dexter_node_name:<30}')

      analogylib.set_is_pruned(analogy, node_name, True)

    if verbose:
      analogylib.print_analogy(analogy)

    elapsed_time = timeit.default_timer() - start_time
    timings.append(elapsed_time)
    costs.append(cost)
    if verbose:
      print(f'Iteration took {elapsed_time:.2f}s.')
    start_time = timeit.default_timer()
    # NOTE: Restart here rather than at the top of the loop since the iteration
    # is the expensive call (because geds is a generator, not a list of results)

  return analogy, {'costs': costs, 'times': timings}

"""
Calculate the cost of a given analogy.
"""
def calculate_cost(analogy: Analogy, sinister: nx.MultiDiGraph, dexter: nx.MultiDiGraph, itemized=False, verbose=False) -> int:
  cost = 0
  def vprint(*args):
    if verbose:
      print(*args)

  if itemized or verbose:
    vprint('-------- Cost breakdown')
  
  vprint('-- Nodes in analogy / nodes in graph:')
  num_analogy_nodes = len(analogylib.get_nodes(analogy, None))
  vprint(f'sinister: {num_analogy_nodes} / {len(sinister.nodes())}')
  vprint(f'  dexter: {num_analogy_nodes} / {len(dexter.nodes())}')


  vprint('\n-- Edges in analogy / edges in graph:')
  num_analogy_edges = len(analogylib.get_edges(analogy, None))
  vprint(f'sinister: {num_analogy_edges} / {len(sinister.edges())}')
  vprint(f'  dexter: {num_analogy_edges} / {len(dexter.edges())}')
  vprint()

  # pruned nodes
  # NOTE: by definition, these should not have edges.
  prune_cost = 0
  for sinister_name, dexter_name in analogylib.get_nodes(analogy, side=None, include_pruned=True):
    sinister_node = sinister[sinister_name]
    dexter_node = dexter[dexter_name]
    if analogylib.get_is_pruned(analogy, sinister_name, side=Hand.SINISTER):
      prune_cost += node_subst_cost(sinister_node, dexter_node)
      vprint(f'Pruned: {sinister_name}  <=>  {dexter_name}')
  
  if itemized or verbose:
    # NOTE: technically this is the cost of substitution (which could depend on eg. types)
    print('---- Node pruning (no cost):', prune_cost)

  # node deletion
  node_deletion_cost = 0
  for node in sinister.nodes():
    if analogylib.get_is_pruned(analogy, node, side=Hand.SINISTER):
      # Ignore cost of pruning, since in practice the algorithm will find a random vertex to match.
      continue

    elif not analogylib.is_node_in_sinister(analogy, node):
      res = node_diff_cost(sinister[node])
      vprint(f'Deleted ({res}): {node}')
      node_deletion_cost += res
  
  if itemized or verbose:
    print('---- Node deletion cost:', node_deletion_cost)
  vprint()
  cost += node_deletion_cost

  # node insertion
  node_insertion_cost = 0
  for node in dexter.nodes():
    if analogylib.get_is_pruned(analogy, node, side=Hand.DEXTER):
      # Ignore cost of pruning, since in practice the algorithm will find a random vertex to match.
      continue

    elif not analogylib.is_node_in_dexter(analogy, node):
      res = node_diff_cost(dexter[node])
      vprint(f'Inserted ({res}): {node}')
      node_insertion_cost += res
  
  if itemized or verbose:
    print('---- Node insertion cost:', node_insertion_cost)
  vprint()
  cost += node_insertion_cost

  # node substitution
  # loop through analogy
  node_substitution_cost = 0
  for sinister_node, dexter_node in analogylib.get_nodes(analogy, side=None):
    res = node_subst_cost(sinister.nodes[sinister_node], dexter.nodes[dexter_node])
    vprint(f'Substitution ({res}): {sinister_node} ==> {dexter_node}')
    vprint(f'                  {str(sinister.nodes[sinister_node])} ==> {str(dexter.nodes[dexter_node])}')
    node_substitution_cost += res

  if itemized or verbose:
    print('---- Node substitution cost:', node_substitution_cost)
  vprint()
  cost += node_substitution_cost

  # remainding dexter nodes. 
  # They are unmatched and not inserted. They would be deleted in the reverse analogy.
  remaining_dexter_nodes = set(dexter.nodes) - set(analogylib.get_nodes(analogy, Hand.DEXTER))

  for dexter_node in remaining_dexter_nodes:
    vprint('Remaining dexter node:', dexter_node)
  vprint('---- Remaining node cost: 0 (always)')
  vprint()

  # edge deletion
  edge_deletion_cost = 0
  for edge in sinister.edges(keys=True):
    if not analogylib.is_edge_in_sinister(analogy, edge):
      res = edge_diff_cost(sinister.edges[edge])
      vprint(f'Deleted edge ({res}): {edge[:2]}')
      edge_deletion_cost += res
  
  if itemized or verbose:
    print('---- Edge Deletion cost:', edge_deletion_cost)
  vprint()
  cost += edge_deletion_cost

  # edge insertion
  edge_insertion_cost = 0
  for edge in dexter.edges(keys=True):
    if not analogylib.is_edge_in_dexter(analogy, edge):
      res = edge_diff_cost(dexter.edges[edge])
      vprint(f'Inserted edge ({res}): {edge[:2]}')
      edge_insertion_cost += res
  
  if itemized or verbose:
    print('---- Edge Deletion cost:', edge_insertion_cost)
  vprint()
  cost += edge_insertion_cost

  # edge substitution
  edge_substition_cost = 0
  for sinister_edge, dexter_edge in analogylib.get_edges(analogy, side=None):
    res = edge_subst_cost(sinister.edges[sinister_edge], dexter.edges[dexter_edge])
    sinister_relation = sinister.edges[sinister_edge].get('relation')
    dexter_relation = dexter.edges[dexter_edge].get('relation')
    vprint(f'Substitution ({res}): {sinister_edge[0]} -{sinister_relation}-> {sinister_edge[1]}')
    vprint(f'              ==> {dexter_edge[0]} -{dexter_relation}-> {dexter_edge[1]}')
    vprint(f'')
    edge_substition_cost += res

  if itemized or verbose:
    print('---- Edge substitution cost:', edge_substition_cost)
  vprint()
  cost += edge_substition_cost


  if itemized or verbose:
    print(f'------------------\nTotal Cost: {cost}\n')
  return cost

"""
Computes conceptual connectivity of an analogy as measured by the number of edges
between nodes in the conceptual layer found in the analogy. 

NOTE: this does count relation> updates as 2 individual edges, which is a bit
      distorted basically fine.
"""
def conceptual_connectivity(analogy: Analogy, graph: nx.MultiDiGraph, side=Hand.SINISTER, verbose=False):
  assert isinstance(side, Hand), f'Type Error. Expected Hand, got {type(side)} instead'
  analogy_graph = analogylib.graph_from_analogy(analogy, side)

  def is_node_conceptual(node):
    attributes = graph.nodes().get(node)
    assert node is not None, 'how could this happen'

    layer = attributes.get('layer')
    assert layer is not None, 'how does the node not have a layer?'

    if verbose and layer == 'conceptual':
      print(f'{node}')

    return layer == 'conceptual'

  if verbose:
    print('-- Conceptual Nodes in the Analogy:')
  
  # Filter analogy nodes
  conceptual_nodes = [node for node in analogy_graph.nodes() if is_node_conceptual(node)]
  
  # Filter analogy subgraph for conceptual nodes
  conceptual_analogy_graph = analogy_graph.subgraph(conceptual_nodes)

  # Get subgraph from the actual graph (with edge information)
  conceptual_graph = graph.edge_subgraph(conceptual_analogy_graph.edges)
  conceptual_edges = conceptual_graph.edges(data=True)
  
  if verbose:
    print('\n-- Conceptual Edges in the Analogy:')
    for source, target, attr in conceptual_edges:
      relation = attr['relation']
      print(f'{source} -{relation}-> {target}')

    print(f'\n-- Total: {len(conceptual_edges)}')
  
  return len(conceptual_edges)
  


# --- Show analogy results as mermaid diagrams
def mermaid_graph_in_analogy(analogy: Analogy, graph: nx.MultiDiGraph, side: str):
  # side_index = 0
  # if side
  assert side == 'dexter' or side == 'sinister', f'Side should be `sinister` or `dexter`, got `{side}` instead.'

  def is_node_in_analogy(node):
    assert type(node) is str, f'Type Error: expected `str`, got `{type(node)}` instead. {node=}'
    if side == 'sinister':
      return analogylib.is_node_in_sinister(analogy=analogy, node_id=node)
    elif side == 'dexter':
      return analogylib.is_node_in_dexter(analogy=analogy, node_id=node)

  def is_edge_in_analogy(edge):
    assert type(edge) is tuple, f'Type Error: expected `tuple`, got `{type(edge)}` instead. {edge=}'
    if side == 'sinister':
      return analogylib.is_edge_in_sinister(analogy=analogy, edge=edge)
    elif side == 'dexter':
      return analogylib.is_edge_in_dexter(analogy=analogy, edge=edge)
  
  return compiler.mermaid_graph(
    graph,
    should_color_node=is_node_in_analogy,
    should_color_edge=is_edge_in_analogy,
    verbose=True
  )


def mermaid_analogy_with_graphs(analogy: Analogy,
                                sinister_name: str, sinister_graph: nx.MultiDiGraph,
                                dexter_name: str, dexter_graph: nx.MultiDiGraph):
  mermaid = 'flowchart LR\n'
  pad = '  '
  # -- Sinister graph
  mermaid += f'{pad}subgraph {sinister_name}\n'
  sinister_merm, sinister_ids = compiler.mermaid_graph_core(
    sinister_graph,
    should_color_node=lambda node: analogylib.is_node_in_sinister(analogy=analogy, node_id=node),
    should_color_edge=lambda edge: analogylib.is_edge_in_sinister(analogy=analogy, edge=edge),
    pad='  ',
    start_index=0
  )
  max_sinister_id = max(sinister_ids.values())
  mermaid += sinister_merm
  mermaid += f'{pad}end\n\n'

  # -- Dexter graph
  mermaid += f'{pad}subgraph {dexter_name}\n'
  dexter_merm, dexter_ids = compiler.mermaid_graph_core(
    dexter_graph,
    should_color_node=lambda node: analogylib.is_node_in_dexter(analogy=analogy, node_id=node),
    should_color_edge=lambda edge: analogylib.is_edge_in_dexter(analogy=analogy, edge=edge),
    pad='  ',
    start_index=max_sinister_id + 1
  )
  mermaid += dexter_merm
  mermaid += f'{pad}end\n\n'

  # -- Links between domains
  for sinister_node, dexter_node in analogy[0].items():
    assert sinister_node in sinister_ids.keys()
    assert dexter_node in dexter_ids.keys()
    
    source_id = sinister_ids.get(sinister_node)
    target_id = dexter_ids.get(dexter_node)
    mermaid += f"{pad}{source_id} -.- {target_id}\n"

  return mermaid

if __name__ == '__main__':
  preferred_matches = None
  timeout = 3*60
  # sinister_graph = compiler.compile('calendar.yaml')
  # dexter_graph = compiler.compile('video-editor.yaml')
  # analogy, cost = compute_analogy(sinister_graph, dexter_graph, timeout=5, verbose=True)
  # sinister_name = 'imessage'
  # dexter_name = 'slack'
  # dexter_name = 'imessage'

  sinister_name = 'calendar'
  dexter_name = 'video-editor'
  preferred_matches = {
    'events': 'editors/videos'
  }
  
  sinister_graph = compiler.compile(sinister_name + '.yaml')
  dexter_graph = compiler.compile(dexter_name + '.yaml')

  start = timeit.default_timer()
  analogy, attr = compute_analogy(sinister_graph, dexter_graph, preferred_matches=preferred_matches, timeout=timeout, verbose=True)
  elapsed = timeit.default_timer() - start
  pprint.pprint(attr)
  print(f'Took {elapsed:.2f}s')

  calculate_cost(analogy, sinister_graph, dexter_graph, itemized=True)

  # mermaid_graph_in_analogy(analogy, sinister_graph, side='sinister')
  # mermaid_graph_in_analogy(analogy, dexter_graph, side='dexter')
  # print(mermaid_analogy_with_graphs(analogy, sinister_name=sinister_name, sinister_graph=sinister_graph,dexter_name=dexter_name, dexter_graph=dexter_graph))

  # pprint.pprint(analogy)
  # print(mermaid_analogy_with_graphs(analogy,
  #                             sinister_name='imessage', sinister_graph=sinister_graph,
  #                             dexter_name='slack', dexter_graph=dexter_graph))
