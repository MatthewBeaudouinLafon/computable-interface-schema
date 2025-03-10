# This scripts ingests a 4.7 YAML spec and produces nomnoml diagram spec.
# TODO: if I have two fields for eg. contents or groups, then the YAML parser
# will happily randomly remove one (it's a dict!). So maybe I preprocess the
# the file, or more likely make the notation more robust to that. Maybe if I
# have multiple entries I make a list, and I can make a python function that
# processes either format equivalently
import yaml
import pprint
from preprocessor import preprocess

MAKE_LEGEND = False
MAKE_DIAGRAM = True
INCLUDE_UNUSED = False
# PATH = 'calendar-vis.yaml'
# PATH = 'video-editor-vis.yaml'
PATH = 'messages-vis.yaml'

with open(PATH, 'r') as file:
  data = yaml.safe_load(file)

term_count = preprocess(data)
last_id = 0

arrows = {
  'mapto':        '-- mapto -->',
  'compomap':     '== compo ==>',
  'subsets':      '-- sub -->',
  'instance':     '-- inst -->',
  'structures':   '-- structs -->',
  'groups':       '-- groups -->',
  'groups-along': '-- along -->',
  'in-component': '-- in -->',
}


def new_id():
  last_id += 1
  return last_id

### Make YAML diagram
# format either side of a line
def format_side(side):
  # TODO: change shape of component node
  if '->' in side:
    # mermaid doesn't like -> in ids, so replace them and label the box instead
    side = side.replace('->', '__') + '['+side+']'

  return side

# print the line formatted for nomnoml
def make_line(lhs, arrow_type, rhs):
  if '->' in lhs or '->' in rhs:
    print(f'%% aborting due to ->: {lhs}, {arrow_type}, {rhs}')
    return
  
  # Format appropriately
  arrow = arrows[arrow_type]
  lhs = format_side(lhs)
  rhs = format_side(rhs)

  print(' '.join([lhs, arrow, rhs]))

def process_set(set, name_prefix='', term_prefix='', compo_name='', override_name=''):
  # Get the right name for the left-hand side
  print('%% Processing: ' + str(set))
  name = ''
  if (override_name):
    name = override_name
  elif (name_prefix):
    name = name_prefix + '.' + set['name']
  else:
    name = set['name']
  
  # Prepare to prepend to strings
  if term_prefix != '' and term_prefix[-1] != '.': # HACK: avoid double dots
    term_prefix = term_prefix + '.'


  # Process the relation and right-hand-side properly
  # TODO: ...why am I looping through keys again? I guess I can catch things I'm
  # missing.
  for relation, target in set.items():
    if (relation == 'name'):
      if name in term_count.keys() or INCLUDE_UNUSED:
        print(name)
  
    elif (relation == 'instance'):
      component = None

      # Find the component in the original data
      for compo in data['components']:  # TODO: a bit sketch to refer to data in global scope
        if compo['name'] == target:
          component = compo
          break

      if component is None:
        print("%% Err: couldn't find component", target)
      else:
        print('\nsubgraph', name)
        print('direction LR')
        print('%% component instance')
        for compo_set in component['sets']:
          process_set(compo_set, name_prefix=name, term_prefix=name, compo_name=name)
        print('end\n')

    elif (relation in ['mapto', 'mapto2']):
      make_line(name, 'mapto', term_prefix + target)
    
    elif relation == 'compomap':
      make_line(name, 'compomap', target)
    
    elif (relation in ['structures', 'structures2']):
      make_line(name, 'structures', term_prefix + target)
      
    elif (relation in ['group', 'groups']):
      if (type(target) == str):
        make_line(name, 'groups', term_prefix + target)
      else:
        group_subject = target['subject']
        make_line(name, 'groups', term_prefix + group_subject)
        if (group_along := target['along']):
          make_line(name, 'groups-along', term_prefix + group_along)
    
    elif relation in ('contents', 'contents2'): # TODO: make contents nested lists
      print('\nsubgraph ' + name)
      print('direction TB')
      print('%% subset')
      for subset in set[relation]:
        if (type(subset) == str):
          # if it's just a string, print it if gets used
          if f'{name}.{subset}' in term_count.keys() or INCLUDE_UNUSED:
            print(f'{name}.{subset}')
        else:
          # do the subset name if it's a new set
          subset_name = subset['name']
          if f'{name}.{subset_name}' in term_count.keys() or INCLUDE_UNUSED:
            print(f'{name}.{subset_name}')
          process_set(subset, name_prefix=name, term_prefix=compo_name, compo_name=compo_name) # TODO: what is the correct prefix here?
      print('end')
      print(f'class {name} SubsetClass')
      print()

    elif (relation[0] == '.'):
      # TODO: need to think this through?
      print('%% DEBUG: override name: ' + f'{name}{relation}')
      process_set(set[relation], override_name=f'{name}{relation}', term_prefix=term_prefix, compo_name=compo_name)
    
    elif ('->' in relation or '.' in relation):
      # NOTE: this comes after `relation[0] == '.'`, so it matches any other
      # complex relation
      print('%% TODO: ' + relation)
      print('%%       ' + str(target))

      pass # TODO

    elif (relation == 'count'):
      pass # no-op, but it's accounted for
    

    else:
      print('%% skipped relation: ' + relation)
    

# Make legend


# if MAKE_LEGEND:
#   for idx, relation in enumerate(arrows):
#     arrow = arrows[relation]
#     make_line(relation, arrow, idx)
#   print()


if MAKE_DIAGRAM:
  print('flowchart LR')
  print('classDef SubsetClass fill:#ffdfdf')
  # TODO: what do I want to see with the interfaces?
  print('subgraph interfaces')
  for interface in data['interfaces']:
    print('%% '+ str(interface))
    process_set(interface)
  print('end')
  print('class interfaces SubsetClass')
  print

  # NOTE: No need for this, we only care how the components are instantiated
  # for component in data['components']:
  #   print('\nsubgraph '+ component['name'])
  #   print('direction TB')
  #   for set in component['sets']:
  #     process_set(set, component['name'])
  #   print('end\n')

  for set in data['sets']:
    process_set(set)

  
