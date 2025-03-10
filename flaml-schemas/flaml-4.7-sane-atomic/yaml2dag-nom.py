# This scripts ingests a 4.7 YAML spec and produces nomnoml diagram spec.
# TODO: if I have two fields for eg. contents or groups, then the YAML parser
# will happily randomly remove one (it's a dict!). So maybe I preprocess the
# the file, or more likely make the notation more robust to that. Maybe if I
# have multiple entries I make a list, and I can make a python function that
# processes either format equivalently
import yaml
import pprint

MAKE_LEGEND = False
MAKE_DIAGRAM = True
# PATH = 'calendar-vis.yaml'
PATH = 'video-editor-vis.yaml'

with open(PATH, 'r') as file:
  data = yaml.safe_load(file)

arrows = {
  'mapto':        '->',
  'compomap':     'comp -:>',
  'subsets':      'sub ->',
  'instance':     '--:>',
  'structures':   '+->',
  'groups':       'groups o-o)',
  'groups-along': '+-o)',
  'in-component': 'in --',
}
components_registry = set()
complex_set_registry = {}

# arrows = {
#   'mapto':        'mapto ->',
#   'compomap':     'compo ->',
#   'subsets':      'subsets ->',
#   'instance':     'instance -->',
#   'structures':   'structs o->',
#   'groups':       'o-> groups',
#   'groups-along': 'o->o along',
# 'in-component': 'in --',
# }


### Make YAML diagram

# print the line formatted for nomnoml
def make_line(lhs, arrow_type, rhs):
  # Change prefix to change the nomnoml shape
  if (lhs in components_registry):
    lhs = f'<usecase> {lhs}'
  
  if (rhs in components_registry):
    rhs = f'<usecase> {rhs}'
  
  # Format appropriately
  arrow = arrows[arrow_type]
  lhs = f'[{lhs}]'
  rhs = f'[{rhs}]'

  print(' '.join([lhs, arrow, rhs]))

def process_set(set, name_prefix='', override_name=''):
  # Get the right name for the left-hand side
  name = ''
  if (override_name):
    name = override_name
  elif (name_prefix):
    name = name_prefix + '.' + set['name']
  else:
    name = set['name']

  # Process the relation and right-hand-side properly
  for relation, target in set.items():
    if (relation == 'instance'):
      # TODO: do stuff with components cache?
      components_registry.add(target)
      make_line(name, 'instance', target)

    elif (relation in ['mapto', 'mapto2']):
      make_line(name, 'mapto', target)
    
    elif relation == 'compomap':
      make_line(name, 'compomap', target)
    
    elif (relation == 'structures'):
      make_line(name, 'structures', target)
      
    elif (relation == 'groups'):
      if (type(target) == str):
        make_line(name, 'groups', target)
      else:
        group_subject = target['subject']
        make_line(name, 'groups', group_subject)
        if (group_along := target['along']):
          make_line(name, 'groups-along', group_along)
    
    elif relation in ('contents', 'contents2'): # TODO: make contents nested lists
      # TODO: do something like [<package> item1|item2]
      sub_names = []

      for subset in set[relation]:
        if (type(subset) == str):
          sub_names.append(f'{name}.{subset}')
        else:
          subset_name = subset['name']
          sub_names.append(f'{name}.{subset_name}')
          process_set(subset, name)
      lhs = '<package> ' + '|'.join(sub_names)
      make_line(lhs, 'subsets', name)

    elif (relation[0] == '.'):
      # TODO: need to think this through?
      process_set(set[relation], override_name=f'{name}{relation}')
    
    elif ('->' in relation or '.' in relation):
      # NOTE: this comes after `relation[0] == '.'`, so it matches any other
      # complex relation
      print('// TODO: ' + relation)
      print('//       ' + str(target))

      pass # TODO

    elif (relation == 'name'):
      pass # no-op, but it's accounted for

    else:
      print('// skipped relation: ' + relation)
    

# Make legend
print('#direction: right')
print('#ranker: longest-path')
# print('#ranker: network-simplex')

if MAKE_LEGEND:
  for idx, relation in enumerate(arrows):
    arrow = arrows[relation]
    print(f'[{relation}] {arrow} [{idx}]')
  print()


if MAKE_DIAGRAM:
  # TODO: what do I want to see with the interfaces?
  for interface in data['interfaces']:
    process_set(interface)

  # TODO: only show the things that are used?
  for component in data['components']:
    components_registry.add(component['name'])
    for set in component['sets']:
      make_line('.'.join([component['name'], set['name']]), 'in-component', component['name'])
      process_set(set, component['name'])

  for set in data['sets']:
    process_set(set)
