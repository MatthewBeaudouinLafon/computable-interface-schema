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
def parse_str(statement: str, interp: list, depth: int):
  print(' '*depth+"TODO: interpret string:", statement)

def parse_list(statements: list, interp: list, depth: int):
  assert type(statements) is list, f'{statements=}'
  for statement in statements:
    if type(statement) is str:
      parse_str(statement, interp, depth+1)
    elif type(statement) is dict:
      parse_dict(statement, interp, depth+1)

def parse_dict(statement: dict, interp: list, depth: int):
  assert type(statement) is dict

  for key, value in statement.items():
    if type(value) is str:
      parse_str(value, interp, depth+1)
    elif type(value) is list:
      parse_list(value, interp, depth+1)
    elif type(value) is dict:
      parse_dict(value, interp, depth+1)
    parse_str(key, interp, depth)
  return

def make_relations(spec):
  assert type(spec) is list, 'Top level of YAML specification must be a string.'
  print(pformat(spec))

  interp = []
  parse_list(spec, interp, 0)

  return
