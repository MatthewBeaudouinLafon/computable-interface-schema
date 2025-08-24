"""
Analogy is a data structure for structure matches. This file contains a bunch
of helpful functions to deal with them.

----- Match Representation
forward_match = (
  # nodes
  {
    sinister_node: dexter_node
  },

  # edges
  {
    (sinister_source_node, sinister_target_node):  # sinister edge
      (dexter_source_node, dexter_target_node)     # dexter edge
  }
)
"""
import enum

Analogy = tuple[dict[str, str]]

"""
Hand refers to the side of the analogy.

Since a lot of things have sources, targets, and left/right hand sides, we call
this Sinister and Dexter in analogies. 
An analogy goes from Sinister to Dexter.
"""
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
def new() -> Analogy:
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


def remove_node(analogy: Analogy, node_name: str, side=Hand.SINISTER):
  assert isinstance(side, Hand), f'Type Error. Expected `Hand`, got `{type(side)}` instead from `{side}`.'
  assert side != Hand.DEXTER, 'Removing Dexter nodes is not supported yet. If you see this, time to do it!'

  analogy[0].pop(node_name)

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

def remove_edge(analogy: Analogy, edge_name: str, side=Hand.SINISTER):
  assert isinstance(side, Hand), f'Type Error. Expected `Hand`, got `{type(side)}` instead from `{side}`.'
  assert side != Hand.DEXTER, 'Removing Dexter edges is not supported yet. If you see this, time to do it!'

  analogy[1].pop(edge_name)

"""
Reverse the source (sinister) and target (dexter) domain.
ie. sinister->dexter, dexter->sinister
"""
def flip(analogy: Analogy) -> Analogy:
  reverse = new()

  # nodes
  for sinister_node, dexter_node in analogy[0].items():
    add_analogous_nodes(reverse, dexter_node, sinister_node)

  for sinister, dexter in analogy[1].items():
    add_analogous_edges(reverse, dexter, sinister)
  
  return reverse

def copy(analogy: Analogy) -> Analogy:
  return (
    analogy[0].copy(),
    analogy[1].copy(),
  )

# Getters
def get_analogous_node(analogy: Analogy, sinister_node: str):
  # Returns None if there is no analogous node. This might be because the source,
  # node doesn't exist, or it is "deleted" in the analogy.
  return analogy[0].get(sinister_node, None)

def get_analogous_edge(analogy: Analogy, sinister_edge: tuple[str, str]):
  # Returns None if there is no analogous edge. This might be because the source,
  # edge doesn't exist, or it is "deleted" in the analogy.
  return analogy[1].get(sinister_edge, None)

def get_nodes(analogy: Analogy, side: Hand|None):
  match side:
    case Hand.SINISTER:
      return analogy[0].keys()
    case Hand.DEXTER:
      return analogy[0].values()
    case None:
      return analogy[0].items()

def get_edges(analogy: Analogy, side: Hand):
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
  print("- nodes")
  for sinister_node, dexter_node in analogy[0].items():
    print(f"{sinister_node:>30} <=> {dexter_node:<30}")

  print("\n- edges")
  for sinister_node, dexter_node in analogy[1].items():
    lhs = f"{sinister_node[0]} ~ {sinister_node[1]}"
    rhs = f"{dexter_node[0]} ~ {dexter_node[1]}"
    print(f"{lhs:>50} <=> {rhs:<50}")

"""
Returns the differences in node matches between the analogies.
Recto and Verso should be two analogies for the same pair of specs.
"""
def compare(recto: Analogy, verso: Analogy, nodes_only=True, verbose=False):
  def vprint(*args):
    if verbose:
      print(*args)

  changes = []
  recto_nodes = set(get_nodes(recto, None))
  verso_nodes = set(get_nodes(verso, None))
  unchanged_nodes = recto_nodes & verso_nodes
  
  for pair in recto_nodes - unchanged_nodes:
    vprint('deleted node', pair) # TODO: should probably be an enum.
    changes.append(('deleted node', pair))
  
  for pair in verso_nodes - unchanged_nodes:
    vprint('  added node', pair)
    changes.append(('  added node', pair))
  
  if nodes_only:
    return changes
  
  recto_edges = set(get_edges(recto, None))
  verso_edges = set(get_edges(verso, None))
  unchanged_edges = recto_edges & verso_edges

  for pair in recto_edges - unchanged_edges:
    vprint('deleted edge', pair)
    changes.append(('deleted edge', pair))
  
  for pair in verso_edges - unchanged_edges:
    vprint('  added edge', pair)
    changes.append(('  added edge', pair))
  
  return changes

"""
Are the analogies the same, at least within a threshold?
"""
def check_match(recto: Analogy, verso: Analogy, allowed_edits=0, nodes_only=True, verbose=False):
  changes = compare(recto, verso, nodes_only, verbose=verbose)
  passes = len(changes) <= allowed_edits
  if not passes:
    print(f'{len(changes)} changes, but only {allowed_edits} are allowed.')
    for change in changes:
      print(change)
  elif verbose:
    print(f'{len(changes)} changes, {allowed_edits} are allowed.')

  return passes
