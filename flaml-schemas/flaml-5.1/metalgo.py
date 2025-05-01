"""
This file is adapted from metaphor3.ipynb
"""

import yaml
import re
import enum
from pprint import pprint, pformat
from tabulate import tabulate
import itertools
import random
import math
import time
import json

import networkx as nx

from dataclasses import dataclass
from typing import List, Tuple, Set
from copy import copy, deepcopy

# NOTE: Test with 
# pytest flaml-schemas/flaml-5.1/tests.py

# ---- Helpers
# Return a list even if it's a single thing, so you can always loop through it
def listable(content):
  if type(content) in [str, dict]:
    return [content]
  elif type(content) is list:
    return content
  elif content is None:
    return []
  else:
    print('Listable item is of type:', type(content))
    assert(False)

# TODO: refactor to use listable instead of this function
def process_listable(target, func):
  if target is None:
    return

  if type(target) == list:
    for target_item in target:
      func(target_item)
  else:
    func(target)


# ---- Parsing Functions
def parse_spec(file_path):
  with open(file_path, 'r') as file_handle:
    spec = yaml.safe_load(file_handle)
  return spec


def split_object_signature(obj_signature: str):
  # NOTE: assumes that the signature doesn't start with a punctuation. 
  assert '->' not in obj_signature, 'Object signature cannot have `->` in it (yet).'
  # TODO: trivial to add -> as a separator, just don't need to yet.
  return list(zip(
        re.split(r"[\w\-_ ]+", obj_signature)[:-1], # get all the `.` and `/` (last is empty)
        re.split(r"\.|/", obj_signature)         # get all the words
      ))

def recombine_object_signature(split_object: list[tuple[str, str]]):
  res = ''
  for punct, term in split_object:
    res += punct + term
  return res

def strip_type(obj):
  return re.sub(r'\((\w|-)*\) ', '', obj)

# NOTE: This is mostly used as a parser to get all of the objects. It was previously used to do more stuff, but it's not
# really worth the refactor right now.
class ObjectRegistry(object):
  # obj mapto obj registry
  # {obj name: set(obj names)}
  registry: dict[str, Set[str]] = {}
  structures: set = set()
  
  # # registry for structures between structures, repr, etc.
  # # {obj name: set((entity-name, connection-type), etc...) }
  # connections: dict[str, Set[Tuple[str, str]]] = {}

  def __init__(self, spec=None):
    self.registry = {}
    self.structures = set()
    if spec is not None:
      self.register_spec_objects(spec)

  def __str__(self):
    return pformat(self.registry)

  def register_object(self, obj):
    # in order of priority
    # -> means mapto
    # . means subset
    # / means component
    assert(type(obj) is str)
    obj = strip_type(obj)

    arrow_array = obj.split('->')
    for arrow_idx, arrow_term in enumerate(arrow_array):
      
      # dot_array = arrow_term.split('.')
      # dot_array = re.split(r"\.|/", arrow_term) # split on `.` and `/`
      dot_array = split_object_signature(arrow_term)
      for dot_idx, dot_term in enumerate(dot_array):

        # subject = '.'.join(dot_array[:dot_idx + 1]) # join up to idx
        subject = recombine_object_signature(dot_array[:dot_idx + 1]) # join up to idx
        if not self.registry.get(subject):
          self.registry[subject] = set()
        
        if dot_idx > 0:
          # every sequence maps to the previous element eg. a.b.c => {a.b.c: {a.b}, a.b: {a}}
          # previous = '.'.join(dot_array[:dot_idx])
          previous = recombine_object_signature(dot_array[:dot_idx])
          self.registry[subject].add(previous)
      
      if arrow_idx > 0:
        # a pair of arrows lhs->rhs => {lhs: {rhs}}
        lhs = self.registry[arrow_array[arrow_idx - 1]]
        rhs = arrow_array[arrow_idx]
        lhs.add(rhs)

  def register_struct_objects(self, struct, process_func):
    if struct.get('type') == 'group':
      # Groups also behave as objects, so register them
      name = struct.get('name')
      if name is None:
        print('Warning! No name provided for group. Using `NO NAME PROVIDED` instead. TODO: generate ID.')
        name = 'NO NAME PROVIDED'

      if self.registry.get(name) is None:
        self.registry[name] = set()
      
      # TODO: do groups map to their elements? Really, does the transitive property apply? My hunch is no, but need to think more

    process_listable(struct.get('affects'), process_func)
    process_listable(struct.get('covered-by'), process_func)
    # TODO: relate all of the objects affected/covered by a structure. 

    for derivative in struct.get('structures', []):
      self.register_struct_objects(derivative, process_func=process_func)

  def register_repr_objects(self, repr, process_func):
    repr_type = repr.get('type', '')
    # print(repr_type)
    for repr_item in repr.get('objects', []):
      assert(type(repr_item) is dict)
      assert(len(list(repr_item.keys())) == 1)
      repr_obj = list(repr_item.keys())[0]


      if type(repr_item[repr_obj]) is str:
        # turn str into list to iterate through it properly
        repr_item[repr_obj] = [repr_item[repr_obj]]

      # assert(len(repr_item.values()) == 1)
      # repr_obj, target_objs = list(repr_item.items())[0]
      for target_obj in repr_item[repr_obj]:
        process_func(target_obj)
        # Map every item to the associated representational object
        # eg. {message: {textbox}, author: {textbox}}
        if self.registry.get(target_obj) is None:
          self.registry[target_obj] = set()
        self.registry[target_obj].add(repr_obj)
        # objects[target].add(repr_type + '/' + repr_obj)  # when we prefix the core stuff
        # note: this is a bit backwards compared to the syntax!


  def register_spec_objects(self, spec): # {object: [mapto-targets]}
    def register_object_here(target):
      self.register_object(target)
    
    process_listable(spec.get('objects'), register_object_here)
    # TODO: deal with `objects` block

    for struct in spec.get('structures', []):
      struct_name = struct.get('name', None)
      if struct_name is not None:
        self.structures.add('struct_name')
      self.register_struct_objects(struct, register_object_here)
      
    for repr in spec.get('representations', []):
      self.register_repr_objects(repr, register_object_here)

    self.register_action_objects(spec)

  def register_action_objects(self, spec):
    # NOTE: this needs to be called after register_spec_objects
    if len(spec.get('structures', [])) > 0:
      assert self.structures != set(), "didn't collect structures"

    for behavior in listable(spec.get('behavior', [])):
      # - input → action
      # - triggers ← action (transitive)
      # NOTE: these aren't objects, so don't deal with them here
      
      # - edits → object | struct
      for edited in listable(behavior.get('edits', [])):
        if edited not in self.structures:
          # edit blocks can apply to structures, so don't add these to 
          self.register_object(edited)

      # - moves → obj | cover
      for move in listable(behavior.get('moves', [])):
        if move_target := move.get('object'):
          self.register_object(move_target)

# ----- Graph Creation

def make_spec_graphs(spec):
  graphs = {
    'mapto': nx.DiGraph(),
    'affects': nx.DiGraph(),
    'covers': nx.DiGraph(),
    'behavior': nx.DiGraph(),
  }

  obj_registry = ObjectRegistry(spec)
  
  for lhs, rhs_set in obj_registry.registry.items():
    # lhs = sanitize_name(lhs)
    for rhs in rhs_set:
      # rhs = sanitize_name(rhs)
      # Add mapto
      # print(f'adding: {lhs} -mapto-> {rhs}')
      graphs['mapto'].add_nodes_from([lhs, rhs], ilk='object')
      graphs['mapto'].add_edge(lhs, rhs, rel='mapto')

  # # Add representational object relations
  # # NOTE: right now this only adds computational time, doesn't get better results
  # # so I'll keep it commented for now.
  # add_repr_obj_maps(graphs['mapto'])

  # Rule: Transitive closure on mapto
  graphs['mapto'] = nx.transitive_closure(graphs['mapto'])

  # Transitive closure doesn't transfer attributes, so they need to be added back.
  # If we want to label these newly added edges, we could do it hear by looping through something like
  # [(u, v, attr) for (u, v, attr) in test_graph.edges.data() if attr == {}]
  for (source, target, attr) in graphs['mapto'].edges.data():
    if attr == {}: # edges that were added by transitive closure
      graphs['mapto'][source][target]['rel'] = 'mapto'
      graphs['mapto'][source][target]['inference'] = 'mapto-transitive'

  # nx.set_edge_attributes(graphs['mapto'], 'mapto', 'rel')
 
  # NOTE: this is to deal with `types` eventually
  for obj in listable(spec.get('objects', [])):
    match = re.search("\(([\w-]+)\) (.*)", obj) # matches: (obj_type) obj_name
    if match is None:
      continue
    obj_type, obj_name = match.groups()
    obj_name = obj_name.split('->')[0].split('.')[0] 
    # prolog.append(f'type({obj_name}, {obj_type}).')
    # TODO: add type to a graph


  for struct in spec.get('structures', []):
    # struct_name = sanitize_name(struct.get('name', None))
    struct_name = struct.get('name', None)
    graphs['affects'].add_node(struct_name, ilk='structure')

    if struct_type := struct.get('type'):
      # prolog.append(f'type({struct_name}, {struct_type}).')
      # TODO
      pass

    for affected in listable(struct.get('affects', [])):
      # prolog.append(f'affects({struct_name}, {affected}).')
      graphs['affects'].add_node(affected, ilk='object')
      graphs['affects'].add_edge(struct_name, affected, rel='affects')
      
      # Rule: S affects A & A mapto B => S affects B
      if affected in graphs['mapto'].nodes:
        for knock_on_affected in graphs['mapto'].neighbors(affected):
          # TODO: right now, this doesn't propagate to subsets
          # that rule would be something like S affects B & A mapto B => S affects A
          # print(f'affected-mapto Rule adds: {struct_name} -affects-> {knock_on_affected}')
          graphs['affects'].add_node(knock_on_affected, ilk='object')
          graphs['affects'].add_edge(struct_name, knock_on_affected, rel='affects', inference='affect-mapto-composition')
    
    for cover in listable(struct.get('covered-by', [])):
      # prolog.append(f'covered_by({struct_name}, {cover}).')
      graphs['covers'].add_node(cover, ilk='object')
      graphs['covers'].add_node(struct_name, ilk='structure')
      graphs['covers'].add_edge(cover, struct_name, rel='covers')
  
  for behavior in spec.get('behavior', []):
    # There may be multiple actions with the same spec, so they each have the same relations.
    for action_name in listable(behavior.get('name', [])):
      pass
      # graphs['behavior'].add_node(action_name, ilk='action')
      
      # input → action
      # NOTE: how useful is this for matching? not really...
      # for input_ref in listable(behavior.get('input', [])):
      #   input_name = input_ref.get('name', None)

      #   # NOTE: this should probably be removed, depends on the syntax.
      #   if 'when' in input_name:
      #     old_input_name = input_name
      #     input_name = input_name.split(' when ')[0]
      #     print(f'warning: spliting input name on when: `{old_input_name}` -> `{input_name}`')

      #   assert input_name is not None, 'input name not defined'
      #   graphs['behavior'].add_node(input_ref, ilk='action', input_action=True) # TODO: this should be defined by core somehow
      #   graphs['behavior'].add_edge(input_ref, action_name, rel='triggers')

      # triggers ← action (transitive)
      # TODO: not really used yet

      # # edits → object | struct
      # for edited in listable(behavior.get('edits')):
      #   graphs['behavior'].add_edge(action_name, edited, rel='edits')

      # # moves → obj | cover
      # # moves → struct
      # for move in listable(behavior.get('moves')):
      #   if target := move.get('object', None):
      #     graphs['behavior'].add_edge(action_name, target, rel='move-object')
      #   else:
      #     print('move is missing a target')
        
      #   if along := move.get('along', None):
      #     graphs['behavior'].add_edge(action_name, along, rel='move-structure')
      #   else:
      #     print('move is missing a structure')

  return graphs

def make_graph(spec_name):
  spec = parse_spec(spec_name)
  graphs = make_spec_graphs(spec)

  composed = nx.compose_all([nx.MultiDiGraph(graph) for graph in graphs.values()])
  # label representation nodes to facilitate matching
  # HACK: this should come core.yaml or should be in the name like `core/gui/icons`
  repr_objs = ['regions', 'rects', 'vlines', 'hlines', 'icons']
  for node_name in composed.nodes:
    composed.nodes[node_name]['repr_obj'] = node_name in repr_objs

  # NOTE: input_action is defined in the main function, since we know when it's an input there. It should also be 
  # refactored into a core thing.

  return composed


# ----- Analogy Computation

# NOTE: could make this parametrized, but eh I don't expect to change this much.
MAX_COST = 100 

def node_subst_cost(n1, n2):
  if n1.get('ilk') is None or n2.get('ilk') is None:
    print('missing ilk')
    return MAX_COST
  
  if n1.get('repr_obj', False) != n2.get('repr_obj', False):
    # don't match representation objects to non-representation objects
    return MAX_COST
  
  if n1['ilk'] != n2['ilk']:
    return MAX_COST
  else:
    return 0

def edge_subst_cost(e1, e2):
  if e1.get('rel') is None or e2.get('rel') is None:
    print('missing rel')
    return MAX_COST
  
  if e1['rel'] == e2['rel']:
    return 0
  else:
    return MAX_COST

"""
Compute analogy. This can terminate on its own, but it'll stop at the timeout
provided in the prep_analogy
"""
def compute_analogy(left_graph, right_graph, timeout: int=10*60):
  # TODO: return something meaningful

  geds = nx.optimize_edit_paths(left_graph, right_graph, 
                       timeout=timeout,
                       node_subst_cost=node_subst_cost,
                       edge_subst_cost=edge_subst_cost
                      #  node_match=node_match,
                      #  edge_match=edge_match,
                      #  strictly_decreasing=True,
                       )

  for ged in geds:
    node_edit_path, edge_edit_path, cost = ged
    print('\n\n-- cost:', cost)
    
    print('- nodes')
    for node_edit in node_edit_path:
      lhs, rhs = node_edit
      print(f'{lhs} = {rhs}')

    print('\n- edges')
    for edge_edit in edge_edit_path:
      lhs, rhs = edge_edit

      if lhs is not None:
        edge_lhs, edge_rhs, _ = lhs
        lhs = f'{edge_lhs} ~ {edge_rhs}'

      if rhs is not None:
        edge_lhs, edge_rhs, _ = rhs
        rhs = f'{edge_lhs} ~ {edge_rhs}'
      
      print(f'{lhs} = {rhs}')
