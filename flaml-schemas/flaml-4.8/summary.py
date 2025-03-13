import yaml
import copy
import pprint

files = [
  'calendar.yaml',
  'video-editor.yaml',
  'web-browser.yaml',
  'messages.yaml',
  'notion.yaml',
  'yt-music.yaml',
  'figma.yaml',
]

report_template = {
    'Num components': 0,
    'Num compomap': 0,
    'Num sets': 0,
    'Num mapto': 0,
    'Num structures': 0,
    'Num views': 0,
    'Num type': 0,
    'Num overrides': 0,  # ie. using `.component_item`
    'Num arrows': 0,  # ie. using `->`
    'Num single': 0,
    'Num groups': 0, # exluding covers
    'Num covers': 0,
    'Subsets': [], # [number of elements in subsets]
    'Recursions': None,
  }

def print_notes(notes, indent=''):
  if type(notes) is list:
    for note in notes:
      print_notes(note, indent=indent+'  ')
  else:
    print(indent + '- ' + str(notes))

def get_notes(data):
  notes = data.get('notes')
  if notes is None:
    return None
  
  for note in notes:
    print_notes(note)
  return notes


def process_listable_relation(func, target):
  if type(target) == list:
    for target_item in target:
      func(target_item)
  else:
    func(target)

def increment_listable(metric, relation, data, report):
  def count_structures(target):
    report[metric] += 1
  process_listable_relation(count_structures, data[relation])

def update_set_report(data, report):
  for relation, target in data.items():
    if relation == 'count':
      metric = 'Num single'
      report[metric] = 1 + (report[metric] if report[metric] is not None else 0)
    
    if relation == 'type':
      report['Num type'] += 1

    elif relation == 'contains':
      num_items = len(data[relation])
      
      if report.get('Subsets', None) is None:
        report['Subsets'] = []
      report['Subsets'].append(num_items)

    elif relation in ('mapsto', 'mapto'):
      increment_listable('Num mapto', relation, data, report)

    elif relation in ('group', 'groups'):
      if type(target) is str:
        report['Num groups'] += 1
      else:
        if target.get('along', False):
          report['Num covers'] += 1
        else:
          report['Num groups'] += 1

    elif relation == 'structures':
      increment_listable('Num structures', relation, data, report)

    elif relation == 'compomap':
      increment_listable('Num compomap', relation, data, report)

      if target in ('gui', 'screen-reader'):
        report['Num views'] += 1

    elif relation == 'mapfrom':
      increment_listable('Num mapfrom', relation, data, report)
      pass
    elif relation[0] == '.': # component override
      report['Num overrides'] += 1

    elif '->' in relation:
      report['Num arrows'] += 1
    

def make_spec_report(data):
  report = copy.deepcopy(report_template)
  
  report['Num components'] = len(data.get('components', []))
  report['Num sets'] = len(data.get('sets', []))

  for set in data.get('sets', []):
    update_set_report(set, report)

  return report

if __name__ == "__main__":
  summary = {} # file: report
  num_files = len(files)
  print(f'Looking at {num_files} specifications')

  for file in files:
    print('-- ' + file + ' ---------------------------------------------------------------------')
    summary[file] = {}
    num_lines = 0
    with open(file, 'r') as file_handle:
      data = yaml.safe_load(file_handle)
      
    with open(file, 'r') as file_handle:
      # TODO: probably a smarter way to do this than closing and reopening the file
      for _ in file_handle:
        num_lines += 1
    
    print('NOTES:')
    notes = get_notes(data)
    print()
    summary[file]['num_notes'] = (1 + len(notes)) if type(notes) is list else 0 # a bit of an approximation
    summary[file]['num_lines'] = num_lines - summary[file]['num_notes']
    
    summary[file]['report'] = make_spec_report(data)

  for metric in report_template.keys():
    print('** ' + metric)

    if report_template[metric] is None:
      print('not measured\n')

      continue
    
    for spec, content in summary.items():
      report = content['report']
      value = str(report[metric])
      print(f'{spec[:-5]}: {value}')

    print()
