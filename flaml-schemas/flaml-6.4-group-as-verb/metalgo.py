"""
Find the graph-edit-distance between two compiled specifications and present the
overlap as the analogy in the user interface.
Analogies are presented as from a source domain (sinister) to a
target domain (dexter). This is to avoid confusion with source and targets of 
edges in individual graphs.

"""
import networkx as nx
import compiler

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
  sinister_edge: tuple[str, str] | None,
  dexter_edge: tuple[str, str] | None,
):
  # If either side is deleted, just leave it out of the analogy. This might not
  # be ideal, because we won't be able to distinguish between deleted edges and
  # edges that never existed.
  if sinister_edge is None or dexter_edge is None:
    return

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
  if n1.get('ilk') == n2.get('ilk'):
    return 1
  return MAX_COST

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
    edge_subst_cost=edge_subst_cost,
    #  node_match=node_match,
    #  edge_match=edge_match,
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
        edge_lhs, edge_rhs, _ = lhs
        lhs = f"{edge_lhs} ~ {edge_rhs}"
        sinister_edge = (edge_lhs, edge_rhs)

      dexter_edge = None
      if rhs is not None:
        # NOTE: the last unpacked item is used by the multigraph to keep track
        # of different edges, so we don't need it.s
        edge_lhs, edge_rhs, _ = rhs
        rhs = f"{edge_lhs} ~ {edge_rhs}"
        dexter_edge = (edge_lhs, edge_rhs)

      add_analogous_edges(analogy, sinister_edge, dexter_edge)

    if verbose:
      print_analogy(analogy)

  return analogy, cost

if __name__ == '__main__':
  sinister_graph = compiler.compile('calendar.yaml')
  dexter_graph = compiler.compile('video-editor.yaml')
  analogy = compute_analogy(sinister_graph, dexter_graph, verbose=True)
