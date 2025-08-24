import pytest
from pathlib import Path
import yaml
import pprint

import parser
import compiler
import metalgo

def get_specs():
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

class TestAnalogyComparison:
  def test_same(self):
    analogy = ({
      'conversations': 'channels',
      'conversations.active->messages': 'channels.active->messages',
      'messages': 'messages',
      'people': 'people',
      'pin': 'channel-type',
      'time': 'alphabetical'
    },
    {
      ('conversations', 'messages', 0): ('channels', 'messages', 0),
      ('conversations', 'people', 0): ('channels', 'people', 0),
      ('conversations.active->messages', 'messages', 0): ('channels.active->messages', 'messages', 0),
      ('people', 'messages', 0): ('people', 'messages', 0),
      ('pin', 'conversations', 0): ('channel-type', 'channels', 0),
      ('time', 'conversations', 0): ('alphabetical', 'channels', 0),
    })
    assert metalgo.compare_analogies(analogy, analogy, True) == []
  
  def test_ablation(self):
    analogy = ({
      'conversations': 'channels',
      'conversations.active->messages': 'channels.active->messages',
      'messages': 'messages',
      'people': 'people',
      'pin': 'channel-type',
      'time': 'alphabetical'
    },
    {
      ('conversations', 'messages', 0): ('channels', 'messages', 0),
      ('conversations', 'people', 0): ('channels', 'people', 0),
      ('conversations.active->messages', 'messages', 0): ('channels.active->messages', 'messages', 0),
      ('people', 'messages', 0): ('people', 'messages', 0),
      ('pin', 'conversations', 0): ('channel-type', 'channels', 0),
      ('time', 'conversations', 0): ('alphabetical', 'channels', 0),
    })
    
    ablated_analogy = metalgo.copy_analogy(analogy)
    ablated_analogy[0].pop('people')
    assert metalgo.compare_analogies(analogy, ablated_analogy, True) == [('deleted node', ('people', 'people'))]

    ablated_analogy = metalgo.copy_analogy(analogy)
    ablated_analogy[1].pop(('people', 'messages', 0))
    assert metalgo.compare_analogies(analogy, ablated_analogy, True) == [('deleted edge', (('people', 'messages', 0), ('people', 'messages', 0)))]

class TestIsomorphism:
  def test_slack_isomorphism(self):
    specs = get_specs()
    graph = compiler.compile_spec(specs['slack'])
    analogy, cost = metalgo.compute_analogy(graph, graph, timeout=5)

    for sinister_node, dexter_node in metalgo.get_analogy_nodes(analogy, None):
      assert sinister_node == dexter_node
  
  def test_veditor_isomorphism(self):
    specs = get_specs()
    graph = compiler.compile_spec(specs['video-editor'])
    analogy, cost = metalgo.compute_analogy(graph, graph, timeout=30)

    for sinister_node, dexter_node in metalgo.get_analogy_nodes(analogy, None):
      assert sinister_node == dexter_node

class TestSymmetry:
  def test_slack_imessage(self):
    specs = get_specs()
    slack_graph = compiler.compile_spec(specs['slack'])
    imessage_graph = compiler.compile_spec(specs['imessage'])

    forward_analogy, _ = metalgo.compute_analogy(slack_graph, imessage_graph, timeout=30)
    reverse_analogy, _ = metalgo.compute_analogy(imessage_graph, slack_graph, timeout=30)
    reverse_analogy = metalgo.flip_analogy(reverse_analogy) # so both analogies go from slack to imessage
    assert metalgo.compare_analogies(forward_analogy, reverse_analogy, True) == []


class TestDreamAnalogies:
  def test_slack_imessage(self):
    specs = get_specs()
    imessage_graph = compiler.compile_spec(specs['imessage'])
    slack_graph = compiler.compile_spec(specs['slack'])

    cv_dream = ({
      'pin': 'channel-type',
      'people': 'people',
      'messages': 'messages',
      'conversations.active->messages': 'channels.active->messages',
      'conversations': 'channels',
      'time': 'time',
      'chat-view': 'chat-view',
      'chat-view/marks': 'chat-view/marks.text',
      'chat-view/encoding.vstack': 'chat-view/encoding.vstack',
      'convo-view': 'channel-view',
      'convo-view/marks.text':'channel-view/marks',
      'convo-view/encoding.vstack': 'channel-view/encoding.vstack',
      'convo-view/encoding.cluster': 'channel-view/encoding.cluster',
    }, {})

    cv_metalgo, _ = metalgo.compute_analogy(imessage_graph, slack_graph, timeout=60)

    assert metalgo.check_analogy_match(cv_dream, cv_metalgo, allowed_edits=0, nodes_only=True, verbose=True)

  def test_slack_imessage(self):
    specs = get_specs()
    imessage_graph = compiler.compile_spec(specs['calendar'])
    slack_graph = compiler.compile_spec(specs['video-editor'])

    cv_dream = ({
      'weeks.active->events': 'editors/videos',
      'time': 'editors/timeline',
      'weeks.active->timestamps': 'editors/timestamps',
      'week-view': 'editors/view',
      'week-view/marks.hline': 'editors/view/marks.vline',
      'week-view/marks.rectangles': 'editors/view/marks.rectangles',
      'week-view/encoding.vstack': 'editors/view/encoding.hstack',
      'week-view/encoding.cluster': 'editors/view/encoding.cluster',
      'days': 'editors/tracks',
      'mini-month-view': 'media-pool',
      'mini-month-view/marks.text': 'media-pool/marks',
      'mini-month-view/encoding.hwrap': 'media-pool/encoding.hwrap',
      'months.selected->days': 'videos'
    }, {})

    cv_metalgo, _ = metalgo.compute_analogy(imessage_graph, slack_graph, timeout=60)

    assert metalgo.check_analogy_match(cv_dream, cv_metalgo, allowed_edits=0, nodes_only=True, verbose=True)





if __name__ == "__main__":
  # pprint.pprint(test_specs())
  print('waaaa')
