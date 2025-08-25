from pathlib import Path
import yaml

import networkx as nx
import compiler

def get_test_specs():
  real_path = Path(__file__).with_name('test-specs.yaml')  # https://stackoverflow.com/a/65174822
  with open(real_path, "r") as file_handle:
    raw_specs = yaml.safe_load_all(file_handle)
  
    specs = {}
    for raw_spec in raw_specs:
      assert isinstance(raw_spec[0], dict), f'First line of spec should be `$name`.'
      spec_name = raw_spec[0].get('$name')
      assert spec_name is not None, f'First line of spec should be `$name`.'

      specs[spec_name] = raw_spec[1:]

  return specs

def is_graph_empty(graph: nx.MultiGraph):
  return len(graph.nodes()) == 0

class TestCompilationSmoke:
  def test_test_specs(self):
    specs = get_test_specs()
    for spec_name, spec in specs.items():
      print('Compiling', spec_name)
      graph = compiler.compile_spec(spec)
      assert not is_graph_empty(graph)


  def test_specs(self):
    specs = ['imessage.yaml',
      'slack.yaml',
      'calendar.yaml',
      'video-editor.yaml',
      # 'figma.yaml',
      # 'finder.yaml',
      ]
    for spec_file_name in specs:
      print('Compiling', spec_file_name)
      graph = compiler.compile(spec_file_name)
      assert not is_graph_empty(graph)
