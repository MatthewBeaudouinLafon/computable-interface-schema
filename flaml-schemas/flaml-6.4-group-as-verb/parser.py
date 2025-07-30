"""
This file aims to ingest a yaml specification and spit out a list of relations.

A YAML file looks like this:
- object-expression  # includes a.b->c/d
- source-expression:
    left-hand-side: target-expression


"""
import yaml
from pprint import pformat
from pathlib import Path
import re
import enum
from enum import Enum

def parse_yaml(file_path):
  real_path = Path(__file__).with_name(file_path)  # https://stackoverflow.com/a/65174822
  with open(real_path, "r") as file_handle:
    spec = yaml.safe_load(file_handle)
  return spec

# --- interpreted relations
class rel(Enum):
  # objects
  MAPTO = enum.auto()
  SUBSET = enum.auto()
  ALIAS = enum.auto()

  # structures
  GROUP = enum.auto()
  GROUP_FOREACH = enum.auto()
  AFFECTS = enum.auto()
  COVERS = enum.auto()

def make_node(name):
  # TODO: maybe not needed?
  return name

def make_edge(source: str, relation: rel, target: str):
  return {
    'source': source,
    'relation': relation,
    'target': target
  }

# --- Parse spec
def parse_str(statement: str, parent: str|None, interp: list, depth: int) -> str:
  """
  Parses the string and returns an identifier for the parent to use in a relation.
  """
  if statement[:3] == "def":
    print(' '*depth+"TODO: interpret definition:", statement)
  elif re.match(r'^\([\w\-]+\) .*', statement):
    print(' '*depth+"TODO: interpret instantiation:", statement)
    # TODO: extract type with regex
    statement = re.sub(r'^\([\w\-]+\)', '', statement)  # remove type
  elif statement[0] == '/':
    assert parent is not None, 'The statement starts with `/`, but it does not have a parent.'
    print(' '*depth+"TODO: interpret attribute:", parent+statement)
    statement = parent+statement

  
  if '.' in statement or '->' in statement or '/' in statement or ' and ' in statement:
    print(' '*depth+"TODO: interpret component string:", statement)
  else:
    print(' '*depth+"TODO: interpret simple string:", statement)
    
  return statement

def parse_relation(statement: str, depth: int) -> rel:
  if statement in ('mapto', '->'):
    return rel.MAPTO
  elif statement in ('subset', '.'):
    return rel.SUBSET
  elif statement in ('affects'):
    return rel.AFFECTS
  elif statement in ('covers'):
    return rel.COVERS
  elif statement in ('groups'):
    return rel.GROUP
  elif statement in ('groups foreach'):
    return rel.GROUP_FOREACH
  else:
    assert False, f'Statement `{statement}` is not a relation.'

def parse_list(statements: list, parent: str|None, interp: list, depth: int):
  """
  Parses every item in the list and returns a list of identifiers for the parent to use.
  It passes its parent down to its items.
  """
  assert type(statements) is list, f'{statements=}'
  for statement in statements:
    if type(statement) is str:
      parse_str(statement, parent=parent, interp=interp, depth=depth+1)
    elif type(statement) is dict:
      parse_dict(statement, parent=parent, interp=interp, depth=depth+1)

def parse_dict(statement: dict, parent: str|None, interp: list, depth: int):
  """

  """
  assert type(statement) is dict

  for key, value in statement.items():
    key_interp = parse_str(key, parent=parent, interp=interp, depth=depth)
    if type(parent) is str:
      parent_for_children = parent + key_interp
    elif parent is None:
      parent_for_children = key_interp
    else:
      assert False, f'dict parent is the wrong type somehow: {type(parent)}'

    if type(value) is str:
      parse_str(value, parent=parent, interp=interp, depth=depth+1)
    elif type(value) is list:
      parse_list(value, parent=parent_for_children, interp=interp, depth=depth+1)
    elif type(value) is dict:
      parse_dict(value, parent=parent_for_children, interp=interp, depth=depth+1)
  return

def make_relations(spec):
  assert type(spec) is list, 'Top level of YAML specification must be a string.'
  print(pformat(spec))

  interp = []
  parse_list(spec, parent=None, interp=interp, depth=0)

  return
