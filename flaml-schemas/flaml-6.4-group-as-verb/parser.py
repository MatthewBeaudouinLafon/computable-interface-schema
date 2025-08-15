"""
This file aims to ingest a yaml 6.4 specification and spit out a list of relations.

A YAML file looks like this:
- object-expression  # includes a.b->c/d
- source-expression:
    left-hand-side: target-expression
# TODO: fill this out for documentation.
"""
import yaml
from pprint import pformat
from pathlib import Path
import re
import enum
from enum import Enum

def spec_from_file(file_path):
  real_path = Path(__file__).with_name(file_path)  # https://stackoverflow.com/a/65174822
  with open(real_path, "r") as file_handle:
    spec = yaml.safe_load(file_handle)
  return spec

def spec_from_string(yaml_str: str):
  assert type(yaml_str) is str
  return yaml.safe_load(yaml_str)

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

  # type
  TYPE = enum.auto()

  # This is a catchall for relations I haven't figured out what to do yet
  TBD = enum.auto()


def make_edge(interp: list, source: str, relation: rel, target: str, verbose=False):
  """
  Declares an edge in the graph by appending it to interp.
  """
  interp.append((source, relation, target))

  pretty_relation = relation.name

  assert source is not None, f'`source` cannot be None in: {source}  -{pretty_relation}->  {target}'
  assert relation is not None, f'`relation` cannot be None in: {source}  -{pretty_relation}->  {target}'
  assert target is not None, f'`target` cannot be None in: {source}  -{pretty_relation}->  {target}'
  if verbose:
    print(f'{source}  -{pretty_relation}->  {target}')

def get_edge_source(interp: list):
  return interp[0]

def get_edge_relation(interp: list):
  return interp[1]

def get_edge_target(interp: list):
  return interp[2]

def print_edge(edge: tuple):
  source = get_edge_source(edge)
  relation = get_edge_relation(edge).name
  target = get_edge_target(edge)
  print(f'{source}  -{relation}->  {target}')

def print_interp(interp: list):
  for edge in interp:
    print_edge(edge)

# --- Parse spec
def incrementally_aggregate(array: list, symbol: str):
  # Map an array to such that each term uses a combined sequence of the previous.
  # For example, here using the `/` symbol.
  # [a, b, c] => [a, a/b, a/b/c]
  aggregate = []
  for idx, term in enumerate(array):
    if idx == 0:
      aggregate.append(term)
      continue

    prev_aggregated_term = aggregate[idx-1]
    aggregated_term = prev_aggregated_term + symbol + term
    aggregate.append(aggregated_term)
  return aggregate

def strip_type(statement: str):
  return re.sub(r'\([\w\-]+\) ', '', statement)

"""
Validate that the keys in an instance declaration's dictionary are well formed.

(type) instance:
  statement: ___

statement can be of the forms:
1. relation: _
2. /attribute_map <>: _
3. /attribute_alias =: _
4. /attribute: _
"""
def validate_instance_dict(statement: str):
  # NOTE: this could be a regex, but this is probably clearer and faster.
  assert type(statement) is str, f'Type Error: `{statement}` should be a string'
  is_relation = parse_relation(statement) is not None
  is_attribute = statement[0] == '/'
  is_valid = is_relation or is_attribute
  assert is_valid, f'Key `{statement}` is an invalid key for an instance dict. \
  {is_relation=} or {is_attribute=}'
  return is_valid

def parse_compound_object(statement: str, parent: str, interp: list):
  """
  Parses compound objects like files.selected->paths/icon.

  In order of priority
   -> means mapto
   . means subset
   / means component (it's really a sort of group though)
   NOTE: `and` is parsed in the caller parse_str
  
  NOTE: This function will result in a lot of duplicate relations if a compound
  item is called multiple times. We could cache results if things get out of hand.
  NOTE: This function returns a statement with / prefixed appropriately.
  """
  assert ' and ' not in statement, "Found `and` in compound parse_compound_object. This should be dealt with in parse_str."

  # 1. Parse ->
  # First, prepend parent when the term starts with `/`
  arrow_split = []
  for phrase in statement.split('->'):
    if phrase[0] == '/':
      assert parent is not None, f'`{phrase}` starts with `/`, but its parent is None.'
      phrase = parent+phrase
    arrow_split.append(phrase)

  for arrow_idx, target in enumerate(arrow_split):
    if arrow_idx == 0:
      # Skip the first item. If there's only one item, then we'll just move on.
      continue
    source = arrow_split[arrow_idx-1]
    make_edge(interp=interp, source=source, relation=rel.MAPTO, target=target)
  
  # NOTE: we do this join instead of using the original statement because
  # we may have prepended parents to /phrases
  rebuilt_statement = '->'.join(arrow_split)

  # a->b->c -SUBSET-> c
  # NOTE: This is arguably the compiler's job, but since this is only true when
  # using inline arrow notation it makes sense to have it here. This might not be
  # worth it if it adds useless nodes.
  if len(arrow_split) > 1:
    make_edge(interp=interp, source=rebuilt_statement, relation=rel.SUBSET, target=arrow_split[-1])

  # Parse . and / together. 
  # NOTE: they don't interact with arrows at all, so we look at the phrases between arrows
  for phrase in arrow_split:
    # phrase is a combination of atoms split by . and / ie. matches [\w\-\/\.]+

    # 3. Parse /
    # The first item in the lhs chain of `.` is groups the first item
    # eg: a.b/c.d.e/f.g =>
    # a -GROUP-> a/c
    # a/c -GROUP-> a/c/f

    # Get the first term (before `.` or `/`)
    first_dot_term = re.match(r'(^\([\w\-]+\) )?[\w\-]+', phrase)
    assert first_dot_term is not None, f"The first term of this dot sequence is malformed: {phrase} in {statement}"

    # Add every term following a `/`
    leading_dot_terms = [first_dot_term.group()] + \
      list(map(lambda x: x[1:], re.findall(r'\/[\w\-]+', phrase)))

    # 3. Parse `/` relations.
    # Aggregate terms incrementally
    # [a, b, c] => [a, a/b, a/b/c]
    aggregated_leading_terms = incrementally_aggregate(leading_dot_terms, '/')
    for idx, aggregated_term in enumerate(aggregated_leading_terms):
      if idx == 0:
        continue

      prev_aggregated_term =  aggregated_leading_terms[idx-1]
      # TODO: If this is setup when the /terms are defined, then it doesn't need to be defined here?
      # In other words, this just let's you declare /terms, which might be fine but not sure.

      # TODO: I think this make_edge causes more trouble than it's worth. GROUP_EACH relations should
      # be defined through relations, rather than these compound objects. With it, it produces a ton
      # of redundant edges (eg. for views)
      make_edge(
        interp=interp, 
        source=prev_aggregated_term, relation=rel.GROUP_FOREACH, target=aggregated_term
      )
      
    # 2. Parse `.`
    # subsets nested between slashes mush be prefixed with the appropriate group
    # for namespacing purposes.
    # eg. a.b.c/d.e.f/g.h =>
    # a.b -SUB-> a   |   a.b.c -SUB-> a.b
    # a/d.e -SUB-> a/d  |   a/d.e.f -SUB-> a/d.e
    # a/d/g.h -SUB-> a/d/g
    for idx, slash_term in enumerate(phrase.split('/')):
      prefix = '' if idx == 0 else aggregated_leading_terms[idx-1]+'/'

      # a.b.c => [a, a.b, a.b.c]
      dot_aggregates = incrementally_aggregate(slash_term.split('.'), '.')

      # [a, a.b, a.b.c] => [prefix/a, prefix/a.b, prefix/a.b.c]
      dot_aggregates = list(map(lambda t: prefix+t, dot_aggregates))

      # iterate through pairs and add an edge.
      # NOTE: we flip the order because larger sequences are subsets of smaller
      # subsequences eg. a.b.c -SUBSET-> a.b
      # In other words, we could iterate through the list backquards.
      for d_idx, dot_agg in enumerate(dot_aggregates[:-1]):
        next_dot_agg = dot_aggregates[d_idx + 1]
        make_edge(interp=interp, source=next_dot_agg, relation=rel.SUBSET, target=dot_agg)

  return rebuilt_statement

def parse_str(statement: str, parent: str|None, interp: list, depth: int) -> str:
  """
  Parses the string and returns an identifier that the caller can use in a relation.
  NOTE: that this will clean up the statement eg. remove (type), =, etc.
  NOTE: `and` keyword is parsed in this function, not in parse_compound_object.
  """
  assert type(statement) is str, f'Type error, expected str got {type(statement)}'
  # TODO: a bunch of string validation eg. only valid characters, etc.
  print(f'parsed_str    : {statement=}')

  # Strip leading and trailing whitespace
  statement = statement.strip()

  # Syntax for inline aliasing
  if statement[-2:] == " =":  # TODO: do as regex to make the space optional (see other)
    statement = statement[:-2] # trim alias syntax
  
  # Syntax for attribute maps
  if statement[-3:] == " <>":
    statement = statement[:-3] # trim mapping syntax

  # Syntax for defining new types
  if str(statement[:3]) == "def":
    print(' '*depth+"definition:", statement)
    # TODO: finish
    return None
  
  # Parse `and` statement and recurse on each phrase
  if ' and ' in statement:
    and_splits = statement.split(' and ')

    # remove the (type) signatures in the parsed output
    statement_without_types = strip_type(statement)
    for and_phrase in and_splits:
      assert ' and ' not in and_phrase, 'ERROR: `and` found where it shouldn\'t be'
      # a and b => a -SUBSET-> a and b, b -SUBSET-> a and b
      make_edge(interp=interp, source=strip_type(and_phrase), relation=rel.SUBSET, target=statement_without_types)

      # Each "phrase" (as in `phrase1 and phrase2`) is parsed as its own string
      parse_str(and_phrase, parent=parent, interp=interp, depth=depth+1)  # recurse on each phrase
    return statement_without_types
      
  # Syntax for instantiation eg. (linear) alphabetical
  if type_match := re.match(r'^\((?P<type>[\w\-]+)\) (?P<instance>[\w\-\.\/>]+)', statement):
    # extract type=`type` and instance='thingy.xyz' in `(type) thingy.xyz`.
    # NOTE: ?P<instance> captures compound statements like a.b->c/d
    # NOTE: the match will fail if it doesn't get both. So if you only provide 
    # the type, it will not match, which might come across as a silent failure.
    extracted_type = type_match.group('type')
    extracted_instance = type_match.group('instance')

    # If we're declaring a typed attribute eg. (linear) /timeline, prefix the parent
    # NOTE: maybe this should use parse_compound_object, but that feels overkill.
    if extracted_instance[0] == '/':
      # TODO: handle None parent
      extracted_instance = parent + extracted_instance

    # TYPE relation only applies to the first part of a compound phrase, so we grab that with a regex.
    first_instance_word = re.match(r'^[\w\-\/]+', extracted_instance.split('->')[0]).group()
    make_edge(interp=interp, source=extracted_type, relation=rel.TYPE, target=first_instance_word)
    # statement = re.sub(r'^\([\w\-]+\) ', '', statement)  # remove type before returning
    statement = extracted_instance

  # Compound objects have these characters.
  if '.' in statement or '->' in statement or '/' in statement:
    statement = parse_compound_object(statement=statement, parent=parent, interp=interp)
  
  # Just a normal string, no bells or whistles.
  else:
    pass

  # TODO: validate the final string only contains the right characters.
  return statement

def parse_relation(statement: str) -> rel|None:
  """
  Map keywords to relations. 
  Returns None if it doesn't match, so it can be used to test for a keyword.
  """
  if statement in ('mapto', '->'):
    return rel.MAPTO
  elif statement in ('alias'):
    return rel.ALIAS
  elif statement in ('subset', '.'):
    return rel.SUBSET
  elif statement in ('affects'):
    return rel.AFFECTS
  elif statement in ('covers'):
    return rel.COVERS
  elif statement in ('groups', 'group'):
    return rel.GROUP
  elif statement in ('groups foreach', 'group foreach'):
    return rel.GROUP_FOREACH
  elif statement in ('subgroups'):
    print('TODO: How do subgroups work??')
    return rel.TBD
  elif statement in ('arguments'):
    print('TODO: How do arguments work??')
    return rel.TBD
  
  return None

def parse_list(statements: list, key_parent: str|None, val_parent: str|None, interp: list, depth: int):
  """
  Parses every item in the list and returns a list of identifiers for the parent to use.
  It passes its parent down to its items.
  """
  assert type(statements) is list, f'Statements should be a list, got `{type(statements)}` instead. {statements=}'

  results = []
  for statement in statements:
    if type(statement) is str:
      results.append(parse_str(statement, parent=val_parent, interp=interp, depth=depth+1))
    elif type(statement) is dict:
      results.append(parse_dict(statement, key_parent=key_parent, val_parent=val_parent, interp=interp, depth=depth+1))
  
  return results

def parse_dict(statement: dict, key_parent: str|None, val_parent: str|None, interp: list, depth: int):
  """
  Dictionaries are used in a few ways.

  1. If the key is a relation, then it declares: parent-relation-key.
  2. If the key starts with /, then it declares: parent/key-mapto-value.
  3. If there's a single key and its value is a list/dict,
    then its the parent to declaration involving the items in its value.
  
  In some cases, dictionaries use different parents for their keys and their values.
  This is useful when instantiating objects, since the left hand side will be attributes
  of the instance, whereas the right hand side will inherit previous val_parents.
  eg.
  (my-type) my-instance:
    (gui) /view:
      /marks: /my-attribute  # key_parent=my-instance/view    val_parent=my-instance
  
  This gets tricky when parsing keys that start with `/`.
  """
  assert type(statement) is dict
  # TODO: rename the key/value to something more semantically meaningful. That
  # might be hard because the semantics depend on their values...

  for key, value in statement.items():
    # TODO: validate key
    # TODO: validate value
    parsed_key = parse_str(key, parent=key_parent, interp=interp, depth=depth+1)

    # 1. If the key is a relation, then it declares: parent -relation-> value(s).
    relation = parse_relation(key)
    if relation is not None:
      if type(value) is str and ',' in value:
        # NOTE: this currently should only be used for YAML values. We might want
        # to support commas in the YAML keys.
        value = value.split(',')  # becomes a list

      if type(value) is str:
        # Since this is the value, we just pass val_parent as parent.
        parsed_value = parse_str(value, parent=val_parent, interp=interp, depth=depth+1)

        # but it's the key_parent that relates to the parsed value. NGL, I'm also a bit confused.
        make_edge(interp, source=key_parent, relation=relation, target=parsed_value)
      elif type(value) is list:
        # if the value is a list, then we make a relation for each item
        # NOTE: Key/val parent doesn't really matter here, parse_list will just pass it down.
        value_items = parse_list(value, key_parent=key_parent, val_parent=val_parent, interp=interp, depth=depth+1)

        for item in value_items:
          # parent (from key) relates to each item
          make_edge(interp, source=key_parent, relation=relation, target=item)
      elif type(value) is dict:
        # TODO: figure out if this is necessary.
        assert False, f"Value condition not met. That's weird. value={value}"
        # parse_dict(value, parent=parsed_key, interp=interp, depth=depth+1)
    
    # 2. If the key starts with /, then it declares: parent/key -mapto-> value.
    elif key[0] == '/':
      # TODO: this is also used to map between structures, which is... meh
      relation = None
      next_key_parent = None
      next_val_parent = None

      if key[-3:] == " <>":
        # Syntax for Instance Attribute Map eg.
        # (gui) view:
        #   /marks <>: my-cool-thing    <--- mapping attributes
        relation = rel.MAPTO
        # Right hand side (my-cool-thing) just gets the value parent
        next_key_parent = val_parent  
        next_val_parent = val_parent

      elif key[-2:] == " =": # TODO: do this properly with a regex to make the space optional (see other)
        # Syntax for alias relations eg.
        # (linear) alphabet:
        #   /first =: characters.a      <--- making alias
        relation = rel.ALIAS
        # Right hand side (characters.a) just gets the value parent
        next_key_parent = val_parent
        next_val_parent = val_parent
      
      else:
        # This is defining or using an Instance Attribute Object eg.
        # (type) instance:
        #   - /my-attribute:    <--- Instance Attribute Object 
        #       groups: stuff  (<- can have a child dictionary)
        # -- or --
        # (type) instance:
        #   - (gui) view:
        #       /marks <>:
        #         /my-attribute <--- Instance Attribute Object (not marks!)
        # -- or --
        # (tree) instance:
        #   /depth-order:       <--- Instance Attribute Object
        #     affects: something
        # NOTE: This should only be hit when declaring attributes in foreach block
        #       A simple mistake could be to forget the <> in an instance-attribute-map
        # TODO: guard against ^??
        relation = None
        # If /my-attribute maps to a dict, we want its keys to use parse_str('/my-attribute)
        # This is basically the same as a type definition eg. (linear) alphabet: ...
        next_key_parent = parsed_key
        next_val_parent = val_parent
        # NOTE: no edges added. Could *maybe* add the group foreach, but I'm a level too low I think.
        
      parsed_value = None
      if type(value) is str:
        parsed_value = parse_str(value, parent=val_parent, interp=interp, depth=depth+1)
      elif type(value) is dict:
        parsed_value = parse_dict(value, key_parent=next_key_parent, val_parent=next_val_parent, interp=interp, depth=depth+1)
      else:
        # NOTE: I don't think this is ever a list
        assert False, f"Value condition not met. That's weird. {value=}"

      print(f'/* => {relation=}     {parsed_value=}')
      if relation is not None:
        # NOTE: the value and key are intentionally flipped for `/` expressions (a quirk of the DSL)
        # This only matters for MAPTO, but ALIAS is a symmetric relation anyway.
        make_edge(interp=interp, source=parsed_value, relation=relation, target=parsed_key)

    # Syntax for alias relations
    elif key[-2:] == " =": # TODO: do this properly with a regex to make the space optional (see other)
      # TODO: repeated code with the alias check `elif key[0] == '/'`. Could abstract as a function?
      if type(value) is str:
        parsed_value = parse_str(value, parent=val_parent, interp=interp, depth=depth+1)
        make_edge(interp=interp, source=parsed_value, relation=rel.ALIAS, target=parsed_key)

      elif type(value) is list:
        # NOTE: I didn't intend for this to be listable, but it's kind of cool
        for list_parsed_value in parse_list(value, key_parent=key_parent, val_parent=val_parent, interp=interp, depth=depth+1):
          make_edge(interp=interp, source=parsed_key, relation=rel.ALIAS, target=list_parsed_value)

      else:
        # NOTE: I don't think this is ever a dict
        assert False, f"Value condition not met. That's weird. value={value}"


    # 3. If there's a single key and its value is a list/dict,
    #    then its the parent to declaration involving the items in its value.
    elif type(value) is list:
      parse_list(value, key_parent=key_parent, val_parent=val_parent, interp=interp, depth=depth+1)
    
    elif type(value) is dict:  
      # There are two scenarios in which you pass down your name as parents for children.
      # a. you have a group_foreach relation
      if rel.GROUP_FOREACH in map(lambda x: parse_relation(x), value.keys()):
        # In this case, the key is the source of the relation and one of the values is `group_foreach`
        # Therefore, the key and value parents are relation source aka parsed_key
        parse_dict(value, key_parent=parsed_key, val_parent=parsed_key, interp=interp, depth=depth+1)
      
      # b. you are an instance statement that's not an element of a parent
      # TODO: probably use proper regex...
      elif key[0] == '(':
        # key parent is the instance name, while val parent is the previous val parent
        # This is an intentional bifurcation of parents.
        parse_dict(value, key_parent=parsed_key, val_parent=val_parent, interp=interp, depth=depth+1)

      else:
        # If the key is just a variable name, then it's just an object with group/foreach relation
        # Just pass it down to the values as parents.
        parse_dict(value, key_parent=parsed_key, val_parent=parsed_key, interp=interp, depth=depth+1)
    else:
      assert False, f"Key condition not met. That's very weird. key='{key}'"
  
  # Dictionaries that need to return an identifier always have one key.
  if len(statement.keys()) == 1:
    # NOTE: interp is [] because this key's edges was already added ot interp in the `for key, val` loop
    return parse_str(list(statement.keys())[0], parent=key_parent, interp=[], depth=depth)
  return

def make_relations(spec, verbose=False):
  assert type(spec) is list, 'Top level of YAML specification must be a list.'

  interp = []
  parse_list(spec, key_parent=None, val_parent=None, interp=interp, depth=0)

  if verbose:
    print(pformat(spec))
    print('\nresult:')
    print_interp(interp)

  return interp
