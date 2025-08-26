"""
Analogy is a data structure for structure matches. This file contains a bunch
of helpful functions to deal with them.

----- Match Representation
forward_match = (
  # nodes
  {
    sinister_node: (dexter_node, is_pruned)
  },

  # edges
  {
    (sinister_source_node, sinister_target_node):  # sinister edge
      (dexter_source_node, dexter_target_node)     # dexter edge
  }
)
"""
import enum
import networkx as nx
import pprint

import compiler

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
    # eg. sinister_node: (dexter_node, is_pruned)
    {},
    # edges
    {},
  )

"""
Insert nodes to analogy object.
"""
def add_analogous_nodes(
  analogy: Analogy, sinister_node: str | None, dexter_node: str | None, is_pruned=False
):
  # If either side is deleted, just leave it out of the analogy. This might not
  # be ideal, because we won't be able to distinguish between deleted nodes and
  # nodes that never existed.
  if sinister_node is None or dexter_node is None:
    return

  analogy[0][sinister_node] = (dexter_node, is_pruned)


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
  for sinister_node, dexter in analogy[0].items():
    dexter_node, is_pruned = dexter
    add_analogous_nodes(reverse, dexter_node, sinister_node, is_pruned=is_pruned)

  for sinister, dexter in analogy[1].items():
    add_analogous_edges(reverse, dexter, sinister)
  
  return reverse

def copy(analogy: Analogy) -> Analogy:
  return (
    analogy[0].copy(),
    analogy[1].copy(),
  )

"""
Takes an analogy where dexter nodes don't have is_pruned, and populates it.
If it's already there, it will not be overwritten.

This is useful for tests where I only want to write unpruned analogies.
TODO: there should probably be a different type for this...
"""
def populate_is_pruned(analogy: Analogy, is_pruned=False):
  for sinister, dexter in analogy[0].items():
    dexter_node = None
    node_pruned = is_pruned
    if isinstance(dexter, str):
      dexter_node = dexter
    elif isinstance(dexter, tuple):
      dexter_node,  node_pruned = dexter
    else:
      assert False, f'Type Error. Expected str or tuple, got {type(dexter)} from: {dexter}'
    analogy[0][sinister] = (dexter_node, node_pruned)


# Getters
def get_analogous_node(analogy: Analogy, sinister_node: str):
  # Returns None if there is no analogous node. This might be because the source,
  # node doesn't exist, or it is "deleted" in the analogy.
  dexter = analogy[0].get(sinister_node, None)
  if dexter is None:
    return None
  node, is_pruned = dexter
  return node

def get_analogous_edge(analogy: Analogy, sinister_edge: tuple[str, str]):
  # Returns None if there is no analogous edge. This might be because the source,
  # edge doesn't exist, or it is "deleted" in the analogy.
  return analogy[1].get(sinister_edge, None)

def get_nodes(analogy: Analogy, side: Hand|None, include_pruned=False):
  match side:
    case Hand.SINISTER:
      return analogy[0].keys()
    case Hand.DEXTER:
      dexter_side = list(analogy[0].values())
      if include_pruned:
        dexter_nodes = [node for node, _ in dexter_side]
      else:
        dexter_nodes = [node for node, is_pruned in dexter_side if not is_pruned]
      return dexter_nodes
    case None:
      return list(zip(get_nodes(analogy, Hand.SINISTER), get_nodes(analogy, Hand.DEXTER)))

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
  # NOTE: this uses get_nodes because dexter otherwise has is_pruned info
  return node_id in get_nodes(analogy, side=Hand.DEXTER)

def is_edge_in_sinister(analogy: Analogy, edge) -> bool:
  return analogy[1].get(edge, None) is not None

def is_edge_in_dexter(analogy: Analogy, edge) -> bool:
  return edge in analogy[1].values()


def print_analogy(analogy: Analogy, show_pruned=False):
  print("- nodes")
  for sinister_node, dexter in analogy[0].items():
    dexter_node, is_pruned = dexter
    if not is_pruned:
      print(f"{sinister_node:>30} <=> {dexter_node:<30}")
    elif is_pruned and show_pruned:
      print(f"{sinister_node:>30} <=> {dexter_node:<30}")

  print("\n- edges")
  for sinister_edge, dexter_edge in analogy[1].items():
    lhs = f"{sinister_edge[0]} ~ {sinister_edge[1]}"
    rhs = f"{dexter_edge[0]} ~ {dexter_edge[1]}"
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
    # # TODO: haven't thought through how to report this well besides making compare verbose
    # # so it's a bit inelegant. 
    # for change in changes:
    #   print(change)
  elif verbose:
    print(f'{len(changes)} changes, {allowed_edits} are allowed.')

  return passes



"""
Create an analogy based off a pairing of nodes.
Basically finds all of the edges to make the analogy work. This is useful to get calculate it's hypothetical cost.
"""
def analogy_from_node_pairing(node_pairing: dict[str, str], sinister: nx.MultiDiGraph, dexter: nx.MultiDiGraph) -> Analogy:
  result = new()
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
Greate a networkx graph from an analogy.
"""
def graph_from_analogy(analogy: Analogy, side: Hand):
  analogy_graph = nx.MultiDiGraph()

  nodes = get_nodes(analogy, side)
  edges = get_edges(analogy, side)

  for node in nodes:
    analogy_graph.add_node(node)

  for edge in edges:
    analogy_graph.add_edge(*edge)

  return analogy_graph


"""
Mermaid graph representing the subgraph outlined by the analogy, labeled in terms of the given side.
"""
# TODO: maybe pass None to label nodes with the analogy pairing.
def mermaid_analogy_only(analogy: Analogy, side: Hand):
  analogy_graph = graph_from_analogy(analogy, side)
  return compiler.mermaid_graph(analogy_graph)
