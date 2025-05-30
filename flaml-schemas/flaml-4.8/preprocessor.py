import yaml
import pprint

# This does two things:
# 1. Counts how many terms are used stored as term_count {term: int}
#    This counts how often a complex term is used in the LHS, and how often
#    a type(target) == str:
# 2. TODO: Create a dupe of the YAML that is mapto only and places complex terms
#    in the right place

def mprint(value):
  if __name__ == '__main__':
    print(value)

def increment_count(term_count, prefix, term):
  # NOTE: If it's always zero then it's probably not changing by ref
  assert(type(prefix) == str)
  assert(type(term) == str)
  if prefix != '':
    term = prefix + '.' + term
  mprint('  incrementing: ' + term)
  term_count[term] = 1 + term_count.get(term, 0)

def process_listable_relation(func, target):
  if type(target) == list:
    for target_item in target:
      func(target_item)
  else:
    func(target)

  
def preprocess_set(in_set, components_data, term_count, name_prefix='', term_prefix='', compo_name=''):
  # NOTE: Use this if you want a set's existence to be counted
  # set_name = ''
  # if set_name:= set.get('name', False):
  #   increment_count(term_count, name_prefix, set_name)
  set_name = in_set.get('name', '')

  for relation, target in in_set.items():
    if relation == 'type':
      # Find the right component
      component = {}
      for candidate in components_data:
        if candidate.get('name') == target:
          component = candidate
          break
      
      # Process it
      for composet in component.get('sets', []):
        # NOTE: ngl I kind of hacked this until it worked to have nested instances. 
        # so that works now, but I can't say I have a robust sense of how it should work.
        # Or if it will play nicely eg. with contents.
        new_compo_name = set_name
        if compo_name != '':
          # Don't overwrite compo_name if you're nesting instances (I think?)
          new_compo_name = compo_name + '.' + set_name
        preprocess_set(composet, components_data, term_count, name_prefix=new_compo_name, term_prefix=new_compo_name, compo_name=new_compo_name)

    elif relation == 'compomap':
      assert(type(target) == str)
      increment_count(term_count, term_prefix, target)

    elif relation == 'mapto':
      def process_mapto(target):
        assert(type(target) == str)
        increment_count(term_count, term_prefix, target)
      
      process_listable_relation(process_mapto, target)

    elif relation == 'structures':
      def process_structures(target):
        assert(type(target) == str)
        increment_count(term_count, term_prefix, target)
      
      process_listable_relation(process_structures, target)

    elif relation in ['group', 'groups']:
      def process_group(target):
        if type(target) == str:
          increment_count(term_count, term_prefix, target)
        else:
          assert(target.get('subject'))
          increment_count(term_count, term_prefix, target['subject'])
          assert(target.get('along'))
          increment_count(term_count, term_prefix, target['along'])
      
      process_listable_relation(process_group, target)
    
    elif relation == 'contains':
      assert(type(target) == list)
      for subset in target:
        if type(subset) == str:
          pass  # doesn't relate to anything (and probably won't be in the next version)
        else:
          preprocess_set(subset, components_data, term_count, 
                         name_prefix=set_name, term_prefix=compo_name, compo_name=compo_name)

    elif relation[0] == '.':
      # Record that the complex RHS has been used. Note that the prefix is not
      # applies to everything inside.
      increment_count(term_count, compo_name, set_name + relation)
      preprocess_set(target, components_data, term_count, term_prefix=term_prefix, compo_name=compo_name)
      

    elif relation in ['name', 'count']:
      # We ignore these
      pass
    
    else:
      mprint(f'Failed to process `{relation}`')


def preprocess(data):
  term_count = {}
  compo_data = data.get('components', [])

  for interface in data.get('interfaces'):
    preprocess_set(interface, compo_data, term_count)
  
  # NOTE: this doesn't work because it's not looking for sets, but also I don't
  # want it so it's fine
  # for component in compo_data:
  #   name = component.get('name')
  #   assert(name)

  #   mprint('processing component: ' + name)
  #   # NOTE: prefix only applies to components,
  #   preprocess_set(component, compo_data, term_count, name_prefix=name, term_prefix=name)

  for set in data.get('sets'):
    name = set.get('name')
    assert(name)

    mprint('processing set: ' + name)
    # NOTE: prefix only applies to components,
    preprocess_set(set, compo_data, term_count)

  return term_count


if __name__ == "__main__":
  PATH = 'calendar.yaml'
  # PATH = 'video-editor.yaml'

  with open(PATH, 'r') as file:
    data = yaml.safe_load(file)
  
  term_count = preprocess(data)
  pprint.pprint(term_count)
  if failure_count := term_count.get(None, False):
    print(f'OH NO! Something went wrong and there are {failure_count} values for key `None`')
  else:
    print(term_count.get(None, "No accidental `None`. That's good."))
