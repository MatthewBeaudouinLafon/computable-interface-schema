"""
Find the graph-edit-distance between two compiled specifications and present the
overlap as the analogy in the user interface.
Analogies are presented as from a source domain (sinister) to a
target domain (dexter). This is to avoid confusion with source and targets of 
edges in individual graphs.

"""
import enum
import networkx as nx
import compiler
import pprint

# ----- Match Representation
# forward_match = (
#   # nodes
#   {
#     sinister_node: dexter_node
#   },

#   # edges
#   {
#     (sinister_source_node, sinister_target_node):  # sinister edge
#       (dexter_source_node, dexter_target_node)     # dexter edge
#   }
# )

Analogy = tuple[dict[str, str]]
class Hand(enum.Enum):
  SINISTER = enum.auto()
  DEXTER = enum.auto()

def parse_side(input: str):
  match input:
    case 'sinister':
      return Hand.SINISTER
    case 'dexter':
      return Hand.DEXTER
  
  assert False, f'Invalid Side: expected `sinister` or `dexter`, got `{input}` instead.'

"""
Create a new analogy object.
"""
def new_analogy() -> Analogy:
  return (
    # nodes
    # eg. sinister_node: dexter_node
    {},
    # edges
    {},
  )


"""
Insert nodes to analogy object.
"""
def add_analogous_nodes(
  analogy: Analogy, sinister_node: str | None, dexter_node: str | None
):
  # If either side is deleted, just leave it out of the analogy. This might not
  # be ideal, because we won't be able to distinguish between deleted nodes and
  # nodes that never existed.
  if sinister_node is None or dexter_node is None:
    return

  analogy[0][sinister_node] = dexter_node


"""
Insert edges to analogy object.
"""
def add_analogous_edges(
  analogy: Analogy,
  sinister_edge: tuple[str, str, int] | None,
  dexter_edge: tuple[str, str, int] | None,
):
  # If either side is deleted, just leave it out of the analogy. This might not
  # be ideal, because we won't be able to distinguish between deleted edges and
  # edges that never existed.
  if sinister_edge is None or dexter_edge is None:
    return
  
  assert len(sinister_edge) == 3 and len(dexter_edge) == 3, f'Edges are malformed, should have length 3. {sinister_edge=}, {dexter_edge=}'

  # NOTE: this doesn't include the edge type, but we may want to eventually.
  analogy[1][sinister_edge] = dexter_edge


"""
Reverse the source (sinister) and target (dexter) domain.
ie. sinister->dexter, dexter->sinister
"""
def flip_analogy(analogy: Analogy) -> Analogy:
  reverse = new_analogy()

  # nodes
  for sinister_node, dexter_node in analogy[0].items():
    add_analogous_nodes(reverse, dexter_node, sinister_node)

  for sinister, dexter in analogy[1].items():
    add_analogous_edges(reverse, dexter, sinister)
  
  return reverse

# Getters
def get_analogous_node(analogy: Analogy, sinister_node: str):
  # Returns None if there is no analogous node. This might be because the source,
  # node doesn't exist, or it is "deleted" in the analogy.
  return analogy[0].get(sinister_node, None)

def get_analogous_edge(analogy: Analogy, sinister_edge: tuple[str, str]):
  # Returns None if there is no analogous edge. This might be because the source,
  # edge doesn't exist, or it is "deleted" in the analogy.
  return analogy[1].get(sinister_edge, None)

def get_analogy_nodes(analogy: Analogy, side: Hand):
  match side:
    case Hand.SINISTER:
      return analogy[0].keys()
    case Hand.DEXTER:
      return analogy[0].values()
    case None:
      return analogy[0].items()

def get_analogy_edges(analogy: Analogy, side: Hand):
  match side:
    case Hand.SINISTER:
      return analogy[1].keys()
    case Hand.DEXTER:
      return analogy[1].values()
    case None:
      return analogy[1].items()


# Checkers
def is_node_in_sinister(analogy: Analogy, node_id) -> bool:
  return analogy[0].get(node_id, None) is not None

def is_node_in_dexter(analogy: Analogy, node_id) -> bool:
  return node_id in analogy[0].values()

def is_edge_in_sinister(analogy: Analogy, edge) -> bool:
  return analogy[1].get(edge, None) is not None

def is_edge_in_dexter(analogy: Analogy, edge) -> bool:
  return edge in analogy[1].values()


def print_analogy(analogy: Analogy):
  # TODO: take the graphs as parameters to list the insertions and deletions
  print("- nodes")
  for sinister_node, dexter_node in analogy[0].items():
    print(f"{sinister_node:>30} <=> {dexter_node:<30}")

  print("\n- edges")
  for sinister_node, dexter_node in analogy[1].items():
    lhs = f"{sinister_node[0]} ~ {sinister_node[1]}"
    rhs = f"{dexter_node[0]} ~ {dexter_node[1]}"
    print(f"{lhs:>50} <=> {rhs:<50}")

# ----- Analogy Computation
# The networkx algorithm tries to minimize costs. 
# So lower is better, higher is penalized.

# NOTE: could make this parametrized, but eh I don't expect to change this much.
MAX_COST = 100

"""
Cost incurred from making an analogy between two nodes.
"""
def node_subst_cost(n1, n2):    
  if n1.get('type') == n2.get('type'):
    # TODO: check that they're both standard library types
    return 1
  # TODO: do "type" "casting" for things like linear->tree

  # Ilks are structures, groups, and type definitions.
  # NOTE: Simple objects aren't labeled yet. 
  #       Presumably None => objects, but not 100% sure.

  # NOTE: is this even necessary if the edges wouldn't match anyway? 
  # I think it speeds up the algo significantly, since you can avoid pairing nodes
  # and complexity depends way more on nodes.
  
  # Otherwise, deemphasize this pairing by maximizing costs.
  return MAX_COST

"""
Cost of inserting or deleting a node
Used for both node_del_cost and node_ins_cost, since it should be symmetric.
"""
def node_diff_cost(n1):
  return 1

"""
Cost incurred from making an analogy between two edges.
"""
def edge_subst_cost(e1, e2):
  assert e1.get('relation') is not None, f'Sinister edge has no relation.'
  assert e2.get('relation') is not None, f'Dexter edge has no relation.'

  # TODO: maybe subset can stand in for mapto? Or is that done with transitive
  # rules?
  if e1.get('relation') == e2.get('relation'):
    return 1
  else:
    return MAX_COST

"""
Cost of inserting or deleting a edge
Used for both edge_del_cost and edge_ins_cost, since it should be symmetric.
"""
def edge_diff_cost(edge):
  # return 1
  match edge.get('relation'):
    case 'GROUP_FOREACH':
      return 1
 
  return 1

"""
Compute analogy. This can terminate on its own, but it'll stop at the timeout
provided in the prep_analogy
"""
def compute_analogy(
  sinister_graph, dexter_graph, timeout: int = 1 * 60, verbose=False
):
  if verbose:
    print('\n-- Starting Analogy --')

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
    #  strictly_decreasing=True,
  )

  analogy = new_analogy()
  for ged in geds:
    analogy = new_analogy()
    node_edit_path, edge_edit_path, cost = ged

    if verbose:
      print("\n\n-- cost:", cost)

    for node_edit in node_edit_path:
      lhs, rhs = node_edit
      add_analogous_nodes(analogy, lhs, rhs)

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

      add_analogous_edges(analogy, sinister_edge, dexter_edge)

    if verbose:
      print_analogy(analogy)

  return analogy, cost

"""
Create an analogy based off a pairing of nodes.
Basically finds all of the edges to make the analogy work. This is useful to get calculate it's hypothetical cost.
"""
def analogy_from_node_pairing(node_pairing: dict[str, str], sinister: nx.MultiDiGraph, dexter: nx.MultiDiGraph) -> Analogy:
  result = new_analogy()
  for sini, dex in node_pairing.items():
    add_analogous_nodes(result, sini, dex)

  analogy_sinister_nodes = node_pairing.keys()
  for sinister_edge in sinister.edges(keys=True):
    sinister_source, sinister_target, _ = sinister_edge

    if sinister_source not in analogy_sinister_nodes or sinister_target not in analogy_sinister_nodes:
      # source or target is not part of the analogy
      continue

    dexter_source = node_pairing.get(sinister_source, None)
    dexter_target = node_pairing.get(sinister_target, None)
    if dexter_source is None or dexter_target is None:
      # sinister source or dexter doesn't have a dexter
      continue

    # print(f'sinister: {sinister_source} -{sinister_relation}-> {sinister_target}')
    # print(f'dexter  : {dexter_source} -????????-> {dexter_target}')

    dexter_edges = dexter[dexter_source].get(dexter_target)
    if dexter_edges is None:
      # dexter doesn't have a matching edge
      continue
      
    if len(dexter_edges.keys()) > 1:
      # oops this is a multi-edge
      print('WARNING: dexter has a multi-edge, we just picked the first one. edges:', dexter_edges)
    
    dexter_edge_key = 0
    add_analogous_edges(result, sinister_edge, (dexter_source, dexter_target, dexter_edge_key))
  
  return result

"""
Calculate the cost of a given analogy.
"""
def calculate_cost(analogy: Analogy, sinister: nx.MultiDiGraph, dexter: nx.MultiDiGraph, itemized=False, verbose=False) -> int:
  cost = 0
  def vprint(*args):
    if verbose:
      print(*args)

  # node deletion
  node_deletion_cost = 0
  for node in sinister.nodes():
    if not is_node_in_sinister(analogy, node):
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
    if not is_node_in_dexter(analogy, node):
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
  for sinister_node, dexter_node in get_analogy_nodes(analogy, side=None):
    res = node_subst_cost(sinister.nodes[sinister_node], dexter.nodes[dexter_node])
    vprint(f'Substitution ({res:3>}): {sinister_node} ==> {dexter_node}')
    vprint(f'                  {str(sinister.nodes[sinister_node])} ==> {str(dexter.nodes[dexter_node])}')
    node_substitution_cost += res

  if itemized or verbose:
    print('---- Node substitution cost:', node_substitution_cost)
  vprint()
  cost += node_substitution_cost

  # remainding dexter nodes. 
  # They are unmatched and not inserted. They would be deleted in the reverse analogy.
  remaining_dexter_nodes = set(dexter.nodes) - set(get_analogy_nodes(analogy, Hand.DEXTER))

  for dexter_node in remaining_dexter_nodes:
    vprint('Remaining dexter node:', dexter_node)
  vprint('---- Remaining node cost: 0 (always)')
  vprint()

  # edge deletion
  edge_deletion_cost = 0
  for edge in sinister.edges(keys=True):
    if not is_edge_in_sinister(analogy, edge):
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
    if not is_edge_in_dexter(analogy, edge):
      res = edge_diff_cost(dexter.edges[edge])
      vprint(f'Inserted edge ({res}): {edge[:2]}')
      edge_insertion_cost += res
  
  if itemized or verbose:
    print('---- Edge Deletion cost:', edge_insertion_cost)
  vprint()
  cost += edge_insertion_cost

  # edge substitution
  edge_substition_cost = 0
  for sinister_edge, dexter_edge in get_analogy_edges(analogy, side=None):
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
  

# --- Show analogies as mermaid diagrams
def mermaid_graph_in_analogy(analogy: Analogy, graph: nx.MultiDiGraph, side: str):
  # side_index = 0
  # if side
  assert side == 'dexter' or side == 'sinister', f'Side should be `sinister` or `dexter`, got `{side}` instead.'

  def is_node_in_analogy(node):
    assert type(node) is str, f'Type Error: expected `str`, got `{type(node)}` instead. {node=}'
    if side == 'sinister':
      return is_node_in_sinister(analogy=analogy, node_id=node)
    elif side == 'dexter':
      return is_node_in_dexter(analogy=analogy, node_id=node)

  def is_edge_in_analogy(edge):
    assert type(edge) is tuple, f'Type Error: expected `tuple`, got `{type(edge)}` instead. {edge=}'
    if side == 'sinister':
      return is_edge_in_sinister(analogy=analogy, edge=edge)
    elif side == 'dexter':
      return is_edge_in_dexter(analogy=analogy, edge=edge)
  
  return compiler.mermaid_graph(graph, should_color_node=is_node_in_analogy, should_color_edge=is_edge_in_analogy, verbose=True)

def mermaid_analogy_only(analogy: Analogy):
  pad = "  "
  ret = "flowchart LR\n"

  id_gen = 0    # generated id for each node
  id_dict = {}  # {graph_node_id: number_id}

  for s_node, d_node in analogy[0].items():
    # TODO: add ilk to get the right shape
    node_id = f"{s_node} <> {d_node}"
    id_dict[node_id] = id_gen
    ret += f"{pad}{id_gen}[{node_id}]\n"

    id_gen += 1

  for s_edge, d_edge in analogy[1].items():
    s_src, s_trg = s_edge
    d_src, d_trg = d_edge

    src = f"{s_src} <> {d_src}"
    trg = f"{s_trg} <> {d_trg}"

    src_id = id_dict.get(src)
    trg_id = id_dict.get(trg)

    # TODO: tag with relation
    ret += f"{pad}{src_id} --> {trg_id}\n"

  return ret

def mermaid_analogy_with_graphs(analogy: Analogy,
                                sinister_name: str, sinister_graph: nx.MultiDiGraph,
                                dexter_name: str, dexter_graph: nx.MultiDiGraph):
  mermaid = 'flowchart LR\n'
  pad = '  '
  # -- Sinister graph
  mermaid += f'{pad}subgraph {sinister_name}\n'
  sinister_merm, sinister_ids = compiler.mermaid_graph_core(
    sinister_graph,
    should_color_node=lambda node: is_node_in_sinister(analogy=analogy, node_id=node),
    should_color_edge=lambda edge: is_edge_in_sinister(analogy=analogy, edge=edge),
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
    should_color_node=lambda node: is_node_in_dexter(analogy=analogy, node_id=node),
    should_color_edge=lambda edge: is_edge_in_dexter(analogy=analogy, edge=edge),
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
  # sinister_graph = compiler.compile('calendar.yaml')
  # dexter_graph = compiler.compile('video-editor.yaml')
  # analogy, cost = compute_analogy(sinister_graph, dexter_graph, timeout=5, verbose=True)
  sinister_name = 'imessage'
  dexter_name = 'slack'
  # dexter_name = 'imessage'
  # sinister_name = 'calendar'
  # dexter_name = 'video-editor'
  
  sinister_graph = compiler.compile(sinister_name + '.yaml')
  dexter_graph = compiler.compile(dexter_name + '.yaml')
  analogy, cost = compute_analogy(sinister_graph, dexter_graph, timeout=1*60, verbose=True)

  calculate_cost(analogy, sinister_graph, dexter_graph, verbose=True)

  # mermaid_graph_in_analogy(analogy, sinister_graph, side='sinister')
  # mermaid_graph_in_analogy(analogy, dexter_graph, side='dexter')
  print(mermaid_analogy_with_graphs(analogy, sinister_name=sinister_name, sinister_graph=sinister_graph,dexter_name=dexter_name, dexter_graph=dexter_graph))

  # print(mermaid_analogy_with_graphs(analogy,
  #                             sinister_name='imessage', sinister_graph=sinister_graph,
  #                             dexter_name='slack', dexter_graph=dexter_graph))
