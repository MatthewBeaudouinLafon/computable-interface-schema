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

SpecPath = list[int, str, tuple[str, str | int]]


def record_path(statement: str, interp: tuple[list, list], path: SpecPath):
    interp[1].append([statement, path])

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

  # actions
  CREATE = enum.auto()
  DELETE = enum.auto()
  UPDATE = enum.auto()      # if the update applies to a set
  UPDATE_SRC = enum.auto()  # if the update applies to a relation
  UPDATE_TRG = enum.auto()  # if the update applies to a relation
  DIRECTION = enum.auto()

  # type
  TYPE = enum.auto()

  # This is a catchall for relations I haven't figured out what to do yet
  TBD = enum.auto()


class dpower(Enum):
  # Definitely add the source, target, and relation to the graph.
  # eg. attribute maps, affects/covers/groups keywords
  STRONG = enum.auto()

  # Add the relation if the source and target are already in the graph
  # eg. compound term relations
  WEAK = enum.auto()

  # Compiler should check that this 
  # eg. compound term relations
  QUESTION = enum.auto()

# -- Declarations
def declare(interp: tuple[list, list], source: str, relation: rel, target: str, power: dpower, verbose=False):
  """
  Declares an edge in the graph by appending it to interp.
  """
  interp[0].append((source, relation, target, power))

  pretty_relation = relation.name

  assert source is not None, f'`source` cannot be None in: {source}  -{pretty_relation}->  {target}'
  assert relation is not None, f'`relation` cannot be None in: {source}  -{pretty_relation}->  {target}'
  assert target is not None, f'`target` cannot be None in: {source}  -{pretty_relation}->  {target}'
  if verbose:
    print(f'{source}  -{pretty_relation}->  {target}')

def get_declaration_source(edge: tuple) -> str:
  return edge[0]

def get_declaration_relation(edge: tuple) -> rel:
  return edge[1]

def get_declaration_target(edge: tuple) -> str:
  return edge[2]

def get_declaration_power(edge: tuple) -> dpower:
  return edge[3]

def update_declaration_power(edge: tuple, power: dpower):
  assert type(power) is dpower, f'Type Error: expected `dpower`, got `{type(power)}` instead.'
  return (edge[0], edge[1], edge[2], power)

"""
Substitute the instance-placeholder with the instance name. In the case of an alias, this
function treats each node of the alias independently.
"""
def sub_inst_name_in_node(node: str, instance_name: str):
  # eg. node='@/timeline', instance_name='videos.in-editor = editors/videos'
  if '@' not in node:
    return node
  
  new_names = []
  for individual_name in instance_name.split(' = '):
    new_names.append(node.replace('@', individual_name))

  return ' = '.join(new_names)

"""
Given a declaration from a type-declaration, where the instance's name is labeled `@`,
return the declaration for that instance (ie. by substituting the @ with the instance name)
"""
def substitute_instance_name_in_decl(edge: tuple, instance_name: str):
  assert type(instance_name) is str, f'Type Error: expected `str`, got `{type(instance_name)}` instead.'
  return (sub_inst_name_in_node(edge[0], instance_name), edge[1], sub_inst_name_in_node(edge[2], instance_name), edge[3])

def print_declaration(decl: tuple):
  source = get_declaration_source(decl)
  relation = get_declaration_relation(decl).name
  target = get_declaration_target(decl)
  power = get_declaration_power(decl)

  power = ''
  match get_declaration_power(decl):
    case dpower.STRONG:
      power = 'S'
    case dpower.WEAK:
      power = 'W'
    case dpower.QUESTION:
      power = '?'

  print(f'({power}) {source}  -{relation}->  {target}')

def print_interp(interp: tuple[list, list]):
  for declaration in interp:
    print_declaration(declaration)

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

def parse_compound_object(statement: str, parent: str, interp: tuple[list, list]):
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
    declare(interp=interp, source=source, relation=rel.MAPTO, target=target, power=dpower.WEAK)
  
  # NOTE: we do this join instead of using the original statement because
  # we may have prepended parents to /phrases
  rebuilt_statement = '->'.join(arrow_split)

  # a->b->c -SUBSET-> c
  # NOTE: This is arguably the compiler's job, but since this is only true when
  # using inline arrow notation it makes sense to have it here. This might not be
  # worth it if it adds useless nodes.
  if len(arrow_split) > 1:
    declare(interp=interp, source=rebuilt_statement, relation=rel.SUBSET, target=arrow_split[-1], power=dpower.WEAK)

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
    first_dot_term = re.match(r'(^\([\w\-]+\) )?[\w\-@]+', phrase)
    assert first_dot_term is not None, f"The first term of this dot sequence is malformed: {phrase} in {statement}"

    # Add every term following a `/`
    leading_dot_terms = [first_dot_term.group()] + \
      list(map(lambda x: x[1:], re.findall(r'\/[\w\-@]+', phrase)))

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
      declare(
        interp=interp, 
        source=prev_aggregated_term, relation=rel.GROUP_FOREACH, target=aggregated_term,
        power=dpower.WEAK
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
        declare(interp=interp, source=next_dot_agg, relation=rel.SUBSET, target=dot_agg, power=dpower.WEAK)

  return rebuilt_statement

def parse_str(statement: str, parent: str|None, interp: tuple[list, list], depth: int, path: list[int] = []) -> str:
  """
  Parses the string and returns an identifier that the caller can use in a relation.
  NOTE: that this will clean up the statement eg. remove (type), =, etc.
  NOTE: `and` keyword is parsed in this function, not in parse_compound_object.
  """
  assert type(statement) is str, f'Type error, expected str got {type(statement)}'
  # TODO: a bunch of string validation eg. only valid characters, etc.
  # print(f'parsed_str    : {statement=}')

  # Strip leading and trailing whitespace
  statement = statement.strip()

  # Syntax for inline aliasing
  if statement[-2:] == " =":  # TODO: do as regex to make the space optional (see other)
    statement = statement[:-2] # trim alias syntax
  
  # Syntax for attribute maps
  if statement[-3:] == " <>":
    statement = statement[:-3] # trim mapping syntax
  
  # Parse `and` statement and recurse on each phrase
  if ' and ' in statement:
    and_splits = statement.split(' and ')

    # remove the (type) signatures in the parsed output
    statement_without_types = strip_type(statement)
    for and_phrase in and_splits:
      assert ' and ' not in and_phrase, 'ERROR: `and` found where it shouldn\'t be'
      # a and b => a -SUBSET-> a and b, b -SUBSET-> a and b
      declare(interp=interp, 
                source=strip_type(and_phrase), relation=rel.SUBSET, target=statement_without_types,
                power=dpower.WEAK)

      # Each "phrase" (as in `phrase1 and phrase2`) is parsed as its own string
      parse_str(and_phrase, parent=parent, interp=interp, depth=depth+1)  # recurse on each phrase

    record_path(statement, interp, path)
    return statement_without_types
      
  # Syntax for instantiation eg. (linear) alphabetical
  if type_match := re.match(r'^\((?P<type>[\w\-]+)\) (?P<instance>[\w\-\.\/>@]+)', statement):
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
    first_instance_word = extracted_instance.split('->')[0]
    declare(interp=interp, source=extracted_type, relation=rel.TYPE, target=first_instance_word, power=dpower.STRONG)
    statement = extracted_instance
  
  # Syntax for target relation (eg. update: A.selected subset> A)
  if prepare_target_relation_statement(statement) is not None:
    # NOTE: this relies on having removed <> previously
    # HACK: this is needed for parse_list, so that it can pass the whole statement
    # back to parse_dict. We can't just parse these kinds of statement in here
    # because we need to know both the parent (for compound statements) and the
    # inflicting action for the declarations. This is not very pretty.
    record_path(statement, interp, path)
    return statement

  should_declare_parent_foreach = False
  if statement[0] == '/':
    # TODO: If this is in a instantiation, then it should be a dpower.QUESTION. If it's in a group_foreach,
    #       then it should be dpower.STRONG.
    should_declare_parent_foreach = True
  
  if statement[0] == '.':
    statement = parent + statement

  # Compound objects have these characters.
  if '.' in statement or '->' in statement or '/' in statement:
    statement = parse_compound_object(statement=statement, parent=parent, interp=interp)
  
  # Declare the parent for /statement after it's been prefixed properly.
  if should_declare_parent_foreach:
    declare(interp=interp, source=parent, relation=rel.GROUP_FOREACH, target=statement, power=dpower.STRONG)
  
  # Just a normal string, no bells or whistles.
  else:
    pass

  # TODO: validate the final string only contains the right characters.
  record_path(statement, interp, path)
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
  elif statement in ('subset', 'subsets', '.'):
    return rel.SUBSET
  elif statement in ('affects'):
    return rel.AFFECTS
  elif statement in ('covers'):
    return rel.COVERS
  elif statement in ('groups', 'group'):
    return rel.GROUP
  elif statement in ('groups foreach', 'group foreach'):
    return rel.GROUP_FOREACH
  elif statement in ('create'):
    return rel.CREATE
  elif statement in ('delete'):
    return rel.DELETE
  elif statement in ('update'):
    return rel.UPDATE
  elif statement in ('directions'):
    return rel.DIRECTION
  elif statement in ('subgroups'):
    print('TODO: How do subgroups work??')
    return rel.TBD
  elif statement in ('arguments'):
    print('TODO: How do arguments work??')
    return rel.TBD
  
  return None

def parse_list(statements: list, key_parent: str|None, val_parent: str|None, interp: tuple[list, list], depth: int, path: SpecPath = []):
  """
  Parses every item in the list and returns a list of identifiers for the parent to use.
  It passes its parent down to its items.
  """
  assert type(statements) is list, f'Statements should be a list, got `{type(statements)}` instead. {statements=}'

  results = []
  for i, statement in enumerate(statements):
    if type(statement) is str:
      results.append(parse_str(statement, parent=val_parent, interp=interp, depth=depth+1, path=[*path, i]))
    elif type(statement) is dict:
      results.append(parse_dict(statement, key_parent=key_parent, val_parent=val_parent, interp=interp, depth=depth+1, path=[*path, i]))
  
  return results

def parse_dict(statement: dict, key_parent: str|None, val_parent: str|None, interp: tuple[list, list], depth: int, path: SpecPath = []):
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
    parsed_key = parse_str(key, parent=key_parent, interp=interp, depth=depth+1, path=[*path, ("__KEY", key)],)

    # 1. If the key is a relation, then it declares: parent -relation-> value(s).
    relation = parse_relation(key)
    if relation is not None:
      if type(value) is str and ',' in value:
        # NOTE: this currently should only be used for YAML values. We might want
        # to support commas in the YAML keys.
        value = value.split(',')  # becomes a list

      if type(value) is str:
        if prepare_target_relation_statement(value) is not None:
          # parse as a target_relation (eg. update: a.sub subset> a), if that doesn't work deal with it as a string
          parse_target_relation(value, inflicting_action=key_parent, parent=val_parent, interp=interp, depth=depth, verbose=False, path=[*path, key])
        else:
          # Since this is the value, we just pass val_parent as parent.
          parsed_value = parse_str(value, parent=val_parent, interp=interp, depth=depth+1, path=[*path, key])

          # but it's the key_parent that relates to the parsed value. NGL, I'm also a bit confused.
          declare(interp=interp, source=key_parent, relation=relation, target=parsed_value, power=dpower.STRONG)
      elif type(value) is list:
        # if the value is a list, then we make a relation for each item
        # NOTE: Key/val parent doesn't really matter here, parse_list will just pass it down.
        value_items = parse_list(value, key_parent=key_parent, val_parent=val_parent, interp=interp, depth=depth+1, path=[*path, key])

        for item in value_items:
          if prepare_target_relation_statement(item) is not None:
            # parse as a target_relation (eg. update: a.sub subset> a), if that doesn't work deal with it as a string
            parse_target_relation(item, inflicting_action=key_parent, parent=val_parent, interp=interp, depth=depth, verbose=False, path=[*path, key])
          else:
            # parent (from key) relates to each item
            declare(interp=interp, source=key_parent, relation=relation, target=item, power=dpower.STRONG)
      elif type(value) is dict:
        # TODO: figure out if this is necessary.
        assert False, f"Value condition not met. That's weird. value={value}"
        # parse_dict(value, parent=parsed_key, interp=interp, depth=depth+1)

    elif key[:4] == 'def ':
      # Skip type definitions, since that's handled separately.
      # TODO: maybe this should error if it's too deep?
      continue

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
        
      parsed_value = None
      if type(value) is str:
        parsed_value = parse_str(value, parent=val_parent, interp=interp, depth=depth+1, path=[*path, key])
      elif type(value) is dict:
        parsed_value = parse_dict(value, key_parent=next_key_parent, val_parent=next_val_parent, interp=interp, depth=depth+1, path=[*path, key])
      elif type(value) is list:
        # eg. thing <>: one, two
        parsed_value = parse_list(value, key_parent=next_key_parent, val_parent=next_val_parent, interp=interp, depth=depth+1, path=[*path, key])
      else:
        assert False, f"Value condition not met. That's weird. {value=}"

      if relation is not None:
        # NOTE: the value and key are intentionally flipped for `/` expressions (a quirk of the DSL)
        # This only matters for MAPTO, but ALIAS is a symmetric relation anyway.
        if isinstance(parsed_value, str):
          declare(interp=interp, source=parsed_value, relation=relation, target=parsed_key, power=dpower.STRONG)
        elif isinstance(parsed_value, list):
          for pval in parsed_value:
            declare(interp=interp, source=pval, relation=relation, target=parsed_key, power=dpower.STRONG)


    # Syntax for alias relations
    elif key[-2:] == " =": # TODO: do this properly with a regex to make the space optional (see other)
      # TODO: repeated code with the alias check `elif key[0] == '/'`. Could abstract as a function?
      if type(value) is str:
        parsed_value = parse_str(value, parent=val_parent, interp=interp, depth=depth+1, path=[*path, key])
        declare(interp=interp, source=parsed_value, relation=rel.ALIAS, target=parsed_key, power=dpower.STRONG)

      elif type(value) is list:
        # NOTE: I didn't intend for this to be listable, but it's kind of cool
        for list_parsed_value in parse_list(value, key_parent=key_parent, val_parent=val_parent, interp=interp, depth=depth+1, path=[*path, key]):
          declare(interp=interp, source=parsed_key, relation=rel.ALIAS, target=list_parsed_value, power=dpower.STRONG)

      else:
        # NOTE: I don't think this is ever a dict
        assert False, f"Value condition not met. That's weird. value={value}"


    # 3. If there's a single key and its value is a list/dict,
    #    then its the parent to declaration involving the items in its value.
    elif type(value) is list:
      parse_list(value, key_parent=key_parent, val_parent=val_parent, interp=interp, depth=depth+1, path=[*path, key])
    
    elif type(value) is dict:  
      # There are two scenarios in which you pass down your name as parents for children.
      # a. you have a group_foreach relation
      if rel.GROUP_FOREACH in map(lambda x: parse_relation(x), value.keys()):
        # In this case, the key is the source of the relation and one of the values is `group_foreach`
        # Therefore, the key and value parents are relation source aka parsed_key
        parse_dict(value, key_parent=parsed_key, val_parent=parsed_key, interp=interp, depth=depth+1, path=[*path, key])
      
      # b. you are an instance statement that's not an element of a parent
      # TODO: probably use proper regex...
      elif key[0] == '(':
        # key parent is the instance name, while val parent is the previous val parent
        # This is an intentional bifurcation of parents.
        parse_dict(value, key_parent=parsed_key, val_parent=val_parent, interp=interp, depth=depth+1, path=[*path, key])

        # Add group_foreach edges between instance and attributes.
        for value_key in value.keys():
          # Check that keys are attributes
          assert type(value_key) is str, f'Type Error. Expected `str` or relation, and got `{type(value_key)}'

          # Skip relations
          if parse_relation(value_key) is not None:
            continue

          assert value_key[0] == '/', f'Values for instantiation should be /statements or a relation, got `{value_key}` instead.'
      else:
        # If the key is just a variable name, then it's just an object with group/foreach relation
        # Just pass it down to the values as parents.
        parse_dict(value, key_parent=parsed_key, val_parent=parsed_key, interp=interp, depth=depth+1, path=[*path, key])
    else:
      assert False, f"Key condition not met. That's very weird. key='{key}'"
  
  # Dictionaries that need to return an identifier always have one key.
  if len(statement.keys()) == 1:
    # NOTE: interp is [] because this key's edges was already added ot interp in the `for key, val` loop
    return parse_str(list(statement.keys())[0], parent=key_parent, interp=([], []), depth=depth)
  return

"""
Parse a string like `def (linear) extends (structure)`, where the extension is optional.
                           ^-type           ^-parent
Return None if it doesn't match
"""
def parse_type_def_str(statement: str, verbose=False) -> tuple[str|None, str|None]:
  # NOTE: This will intentionally not match `def (my-type) my-instance`
  assert isinstance(statement, str), f'Type Error: expected str, got {type(statement)} instead from {statement}'
  if statement[:4] != 'def ':
    return (None, None)

  re_res = re.match(r'^def \((?P<type>[\w\-]+)\) extends \((?P<parent>[\w\-]+)\)$', statement)
  parent_type_name = None
  if re_res is not None: # match succeeds
    parent_type_name = re_res.group('parent')
    type_name = re_res.group('type')
    return (type_name, parent_type_name)

  else: # match fails
    re_res = re.match(r'^def \((?P<type>[\w\-]+)\)$', statement)
    if re_res is None:  # second match fails
      return (None, None)
    
    type_name = re_res.group('type')
    return (type_name, None)

def prepare_target_relation_statement(statement: str):
  # TODO: have a verbose option for debugging
  if '>' not in statement:
    return None
  
  if '<>' in statement:
    return None
    # print(f'Expected a relation> string, got a mapping (<>) string: {statement}')

  split = statement.split(' ')
  if len(split) == 1:
    return None
  

  # At this point we know it's *supposed* to be an action term, so we switch to asserts.
  assert len(split) == 3, f'Expected relation statement two split into 3 (on space): {statement}'
  
  assert 'and' not in split, f'Expected `relation>` statement, got an `and` statement: {statement}'
  # and statements and relation statements don't mix, so if there's an and it's
  # not a relation statement
  
  relation = split[1]
  assert relation[-1] == '>', f'Expected `relation>` in the statement: {statement}'
  
  relation = relation[:-1]
  assert parse_relation(relation) is not None, f'`relation>` is not a relation in: {statement}'
  # NOTE: we don't actually use the relation, but we could do something with it (eg. tag it as an attribute somewhere)

  return (split[0], relation, split[2])

"""
Parse a string like 'items.selected subset> items'.
"""
def parse_target_relation(statement: str, inflicting_action: str, parent: str, interp: tuple[list, list], depth: int, verbose=False, path: SpecPath = []) -> str|None:
  raw_source, raw_relation, raw_target = prepare_target_relation_statement(statement)
  source = parse_str(raw_source, parent=parent, interp=interp, depth=depth+1, path=path)
  target = parse_str(raw_target, parent=parent, interp=interp, depth=depth+1, path=path)

  declare(interp=interp, source=inflicting_action, relation=rel.UPDATE_SRC, target=source, power=dpower.STRONG, verbose=verbose)
  declare(interp=interp, source=inflicting_action, relation=rel.UPDATE_TRG, target=target, power=dpower.STRONG, verbose=verbose)
  return statement

"""
Parses spec for type declaration eg. - def (linear) extends (structure): group foreach: etc...
Returns a dictionary listing the relations declared in each type declaration:
{ type_name: [ declaration_in_type_declaration ] }
And a dictionary for type parenthood:
{ type_name: parent }

Any attribute declaration is prefixed with @ as a placeholder for the instance name.
"""
def parse_type_definitions(spec, verbose=False) -> tuple:
  assert type(spec) is list, 'Top level of YAML specification must be a list.'
  instance_name = '@'  # This is used in place of the instance-name
  interp_dict = {}  # {str(type_name): [type_interp]}
  parent_dict = {}  # {str(type_name): str(parent_type_name)}

  for statement in spec:
    type_interp = []
    # Ignore anything that's not a top level definition
    # NOTE: This approach silently ignores type definitions that are inline.
    #       These aren't supported anyway, but it'd be nice to error on them.
    if type(statement) is str:
      type_name, parent_type_name = parse_type_def_str(statement, verbose)
      if type_name is None:
        continue

      interp_dict[type_name] = []
      if parent_type_name is not None:
        interp_dict[parent_type_name] = []
      
      if verbose:
        print_parent = '' if parent_type_name is None else f' with parent: ({parent_type_name})'
        print(f'Declaring type: ({type_name})' + print_parent)
      continue

    elif type(statement) is not dict:
      continue

    # statement is dict
    assert len(statement.keys()) == 1, f'Found multiple keys in a type definition dict: {list(statement.keys())}'
    assert len(statement.values()) == 1, f'Found multiple values in a type definition dict: {list(statement.values())}'
    type_def_key, type_def_content = list(statement.keys())[0], list(statement.values())[0]
    
    if type_def_key[:4] != 'def ':
      continue

    assert type(type_def_content) is dict, f'Contents of type definition should be a dict, got this instead: {type_def_content}'

    type_name, parent_type_name = parse_type_def_str(type_def_key, verbose)
    assert type_name is not None, f'Failed to find type name in supposed type definition: `{statement}`'

    if verbose:
      print_parent = '' if parent_type_name is None else f' with parent: ({parent_type_name})'
      print(f'Declaring type: ({type_name})' + print_parent)

    # At this point we know that we're in a type definition, so anything wrong
    # should assert a failure.
    
    # Assign parents
    if parent_type_name is not None:
      parent_dict[type_name] = parent_type_name

      if verbose:
        print(f'({type_name}) has parent ({parent_type_name})')

    # Construct the list of interps
    type_relations = type_def_content.keys()
    for relation in type_relations:
      assert type(relation) is str, f'Type Error: Expected str, got `{type(relation)}` instead from `{relation}`.'
      parsed_rel = parse_relation(relation)
      assert parsed_rel in (rel.GROUP_FOREACH, rel.TBD), f'Invalid relation: {relation}'
      # TODO: Process subgroups and arguments, somehow

      # Parse Group_foreach contents
      if parsed_rel == rel.GROUP_FOREACH:
        group_foreach_content = type_def_content[relation]
        if type(group_foreach_content) is str:
          parse_str(group_foreach_content, parent=instance_name, interp=(type_interp, []), depth=2)
        elif type(group_foreach_content) is list:
          parse_list(group_foreach_content, key_parent=instance_name, val_parent=instance_name, interp=(type_interp, []), depth=2, path=[])
        else:
          assert False, f'Type Error: group_foreach_content should be str or list, got `{type(group_foreach_content)}` instead.'
    
    # Make all of the relations weak so that the compiler can decide which edges are useful.
    weakened_type_interp = []
    for declaration in type_interp:
      weak_declaration = update_declaration_power(declaration, dpower.WEAK)
      weakened_type_interp.append(weak_declaration)

    # Add to result dict
    interp_dict[type_name] = weakened_type_interp
  
  return interp_dict, parent_dict


def make_relations(spec, verbose=False, ret_locations=False):
  assert type(spec) is list, 'Top level of YAML specification must be a list.'

  interp = ([], [])
  parse_list(spec, key_parent=None, val_parent=None, interp=interp, depth=0)

  if verbose:
    print(pformat(spec))
    print('\nresult:')
    print_interp(interp)

  if ret_locations:
    return interp

  return interp[0]

if __name__ == '__main__':
  spec = spec_from_file('video-editor.yaml')
  parse_type_definitions(spec, verbose=True)
  make_relations(spec, verbose=True)
