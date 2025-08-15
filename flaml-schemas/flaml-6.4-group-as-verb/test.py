"""
Test metalgo.
Run with:
pytest flaml-schemas/flaml-6.4-group-as-verb/test.py -rA
"""

import pytest
import parser
from parser import rel

def parse_str(statement: str, interp: list):
  return parser.parse_str(statement=statement, parent=None, interp=interp, depth=0)

def compare_interp(test, expected: list[tuple], verbose=False):
  assert type(test) == list, f'Expected list, got `{type(test)}` instead.'

  # NOTE: We could check the the lenghts are the same, but then we couldn't get
  # an error telling us where the mismatch is.
  expected_dict = dict(list(map(lambda x: (x, 0), expected)))

  for edge in test:
    if verbose:
      parser.print_edge(edge)
    if edge not in expected_dict:
      # TODO: instead of asserting, collect and print all of the issues.
      assert False, f'Test includes `{edge}`, which is not part of the expected interp.'
    expected_dict[edge] += 1
  
  unfound_relations = [relation for relation, count in expected_dict.items() if count == 0]
  assert len(unfound_relations) == 0, f'The following relations were expected edges, but not found in the test:{unfound_relations}'
   
  return True

class TestCompoundObjectParser:
  def test_subsets(self):
    interp = []
    parser.parse_compound_object('a.b.c', '', interp)
    assert compare_interp(interp, 
                          [
                            ('a.b.c', rel.SUBSET, 'a.b'),
                            ('a.b', rel.SUBSET, 'a'),
                          ])
    
    interp = []
    parser.parse_compound_object('a-b.c-d', '', interp)
    assert compare_interp(interp, 
                          [
                            ('a-b.c-d', rel.SUBSET, 'a-b'),
                          ])
  
  def test_arrows(self):
    interp = []
    parser.parse_compound_object('a->b->c', '', interp)
    assert compare_interp(interp, 
                          [
                            ('a', rel.MAPTO, 'b'),
                            ('b', rel.MAPTO, 'c'),
                            ('a->b->c', rel.SUBSET, 'c'),
                          ])
    
    interp = []
    parser.parse_compound_object('a-b->c-d', '', interp)
    assert compare_interp(interp, 
                          [
                            ('a-b', rel.MAPTO, 'c-d'),
                            ('a-b->c-d', rel.SUBSET, 'c-d'),
                          ])
    
  def test_slash(self):
    interp = []
    parser.parse_compound_object('a-1/b-2/c-3', '', interp)
    assert compare_interp(interp, 
                          [
                            ('a-1', rel.GROUP_FOREACH, 'a-1/b-2'),
                            ('a-1/b-2', rel.GROUP_FOREACH, 'a-1/b-2/c-3'),
                          ])
    
  def test_and(self):
    interp = []
    parse_str('a-1 and b-2', interp)
    assert compare_interp(interp, 
                          [
                            ('a-1', rel.SUBSET, 'a-1 and b-2'),
                            ('b-2', rel.SUBSET, 'a-1 and b-2'),
                          ])
    
    interp = []
    parse_str('a and b and c and d', interp=interp)
    assert compare_interp(interp, 
                          [
                            ('a', rel.SUBSET, 'a and b and c and d'),
                            ('b', rel.SUBSET, 'a and b and c and d'),
                            ('c', rel.SUBSET, 'a and b and c and d'),
                            ('d', rel.SUBSET, 'a and b and c and d'),
                          ])
    
  def test_type(self):
    interp = []
    parse_str('(a-1) b-2', interp=interp, )
    assert compare_interp(interp, 
                          [
                            ('a-1', rel.TYPE, 'b-2'),
                          ])
  
  def test_validate_instance_dict(self):
    key = 'affects'
    assert parser.validate_instance_dict(key), f'`{key}` failed'

    key = '/attribute-map <>'
    assert parser.validate_instance_dict(key), f'`{key}` failed'

    key = '/attribute-alias ='
    assert parser.validate_instance_dict(key), f'`{key}` failed'

    key = '/plain-attribute'
    assert parser.validate_instance_dict(key), f'`{key}` failed'

    with pytest.raises(AssertionError):
      key = 'plain-word'
      parser.validate_instance_dict(key), f'`{key}` failed'
    
  def test_imagined_compound_terms(self):
    interp = []
    parser.parse_compound_object('a.b/c.d.e/f.g', '', interp)
    assert compare_interp(interp, 
                          [
                            ('a', rel.GROUP_FOREACH, 'a/c'),
                            ('a/c', rel.GROUP_FOREACH, 'a/c/f'),
                            ('a.b', rel.SUBSET, 'a'),
                            ('a/c.d', rel.SUBSET, 'a/c'),
                            ('a/c.d.e', rel.SUBSET, 'a/c.d'),
                            ('a/c/f.g', rel.SUBSET, 'a/c/f'),
                          ])
    
    interp = []
    parser.parse_compound_object('a/b->c.d/e->f/g.h', '', interp)
    assert compare_interp(interp, 
                          [
                            ('a/b', rel.MAPTO, 'c.d/e'),
                            ('c.d/e', rel.MAPTO, 'f/g.h'),
                            ('a', rel.GROUP_FOREACH, 'a/b'),
                            ('c', rel.GROUP_FOREACH, 'c/e'),
                            ('c.d', rel.SUBSET, 'c'),
                            ('f', rel.GROUP_FOREACH, 'f/g'),
                            ('f/g.h', rel.SUBSET, 'f/g'),
                            ('a/b->c.d/e->f/g.h', rel.SUBSET, 'f/g.h'),
                          ])
    
    interp = []
    parser.parse_compound_object('a.b.c->d.e.f->g.h', '', interp)
    assert compare_interp(interp, 
                          [
                            ('a.b.c', rel.MAPTO, 'd.e.f'),
                            ('d.e.f', rel.MAPTO, 'g.h'),
                            ('a.b.c', rel.SUBSET, 'a.b'),
                            ('a.b', rel.SUBSET, 'a'),
                            ('d.e.f', rel.SUBSET, 'd.e'),
                            ('d.e', rel.SUBSET, 'd'),
                            ('g.h', rel.SUBSET, 'g'),
                            ('a.b.c->d.e.f->g.h', rel.SUBSET, 'g.h'),
                          ])

    interp = []
    parse_str('a.b and c->d and e/f', interp=interp)
    assert compare_interp(interp, 
                          [
                            ('a.b', rel.SUBSET, 'a.b and c->d and e/f'),
                            ('a.b', rel.SUBSET, 'a'),
                            ('c->d', rel.SUBSET, 'a.b and c->d and e/f'),
                            ('c->d', rel.SUBSET, 'd'),
                            ('c', rel.MAPTO, 'd'),
                            ('e/f', rel.SUBSET, 'a.b and c->d and e/f'),
                            ('e', rel.GROUP_FOREACH, 'e/f'),
                          ])
    

    interp = []
    parse_str('b.c/d and y.z', interp=interp)
    assert compare_interp(interp, 
                          [
                            ('b.c/d', rel.SUBSET, 'b.c/d and y.z'),
                            ('b.c', rel.SUBSET, 'b'),
                            ('b', rel.GROUP_FOREACH, 'b/d'),
                            ('y.z', rel.SUBSET, 'b.c/d and y.z'),
                            ('y.z', rel.SUBSET, 'y'),
                          ])

    interp = []
    parse_str('(a) b.c/d and (x) y.z', interp=interp)
    assert compare_interp(interp, 
                          [
                            ('b.c/d', rel.SUBSET, 'b.c/d and y.z'),
                            ('a', rel.TYPE, 'b'),
                            ('b.c', rel.SUBSET, 'b'),
                            ('b', rel.GROUP_FOREACH, 'b/d'),
                            ('y.z', rel.SUBSET, 'b.c/d and y.z'),
                            ('x', rel.TYPE, 'y'),
                            ('y.z', rel.SUBSET, 'y'),
                          ])
  
  def test_realistic_compound_objects(self):
    interp = []
    parser.parse_compound_object('playhead->video/timestamps', '', interp)
    assert compare_interp(interp, 
                          [
                            ('playhead', rel.MAPTO, 'video/timestamps'),
                            ('video', rel.GROUP_FOREACH, 'video/timestamps'),
                            ('playhead->video/timestamps', rel.SUBSET, 'video/timestamps'),
                          ])
    
    interp = []
    parser.parse_compound_object('editors.current/timestamps.playhead', '', interp)
    assert compare_interp(interp, 
                          [
                            ('editors', rel.GROUP_FOREACH, 'editors/timestamps'),
                            ('editors.current', rel.SUBSET, 'editors'),
                            ('editors/timestamps.playhead', rel.SUBSET, 'editors/timestamps'),
                          ])
    
    interp = []
    parser.parse_compound_object('folders.in-selected-path->items', '', interp)
    assert compare_interp(interp, 
                          [
                            ('folders.in-selected-path', rel.MAPTO, 'items'),
                            ('folders.in-selected-path', rel.SUBSET, 'folders'),
                            ('folders.in-selected-path->items', rel.SUBSET, 'items'),
                          ])
    
    interp = []
    parser.parse_compound_object('channels.!dm', '', interp)
    assert compare_interp(interp, 
                          [
                            ('channels.!dm', rel.SUBSET, 'channels'),
                          ])
    
    interp = []
    parse_str('folders and files', interp=interp)
    assert compare_interp(interp, 
                          [
                            ('folders', rel.SUBSET, 'folders and files'),
                            ('files', rel.SUBSET, 'folders and files'),
                          ])
    
    interp = []
    parse_str('chart-summary and numerical->dimension-info and numerical->interval-info', interp=interp)
    assert compare_interp(interp, 
                          [
                            ('chart-summary', rel.SUBSET, 'chart-summary and numerical->dimension-info and numerical->interval-info'),
                            ('numerical->dimension-info', rel.SUBSET, 'dimension-info'),
                            ('numerical->dimension-info', rel.SUBSET, 'chart-summary and numerical->dimension-info and numerical->interval-info'),
                            ('numerical', rel.MAPTO, 'dimension-info'),
                            ('numerical->interval-info', rel.SUBSET, 'interval-info'),
                            ('numerical->interval-info', rel.SUBSET, 'chart-summary and numerical->dimension-info and numerical->interval-info'),
                            ('numerical', rel.MAPTO, 'interval-info'),
                          ])


class TestRecursiveDescent:
  # --- Testing base cases
  def test_group(self):
    interp = parser.make_relations(parser.spec_from_string("""
- thing:
    groups: other-thing
"""))
    assert compare_interp(interp, 
                  [
                    ('thing', rel.GROUP, 'other-thing')
                  ])
    
  def test_type_relation(self):
    interp = parser.make_relations(parser.spec_from_string("""
- (linear) alphabetical
"""))
    assert compare_interp(interp, 
                  [
                    ('linear', rel.TYPE, 'alphabetical')
                  ])
    
  def test_compound_relation(self):
    # Check that putting something in the list is the same as using the compound_object function
    compound_expression = 'a.b and c->d and e/f'
    file_interp = parser.make_relations(parser.spec_from_string(f"""
- {compound_expression}
"""))

    string_interp = []
    parser.parse_str(compound_expression, parent=None, interp=string_interp, depth=0)
    assert compare_interp(file_interp,string_interp)

  # --- Testing recursive features
  def test_structure(self):
    interp = parser.make_relations(parser.spec_from_string("""
- (linear) alphabetical:
    affects: people
    covers: words
"""))
    assert compare_interp(interp, 
                  [
                    ('linear', rel.TYPE, 'alphabetical'),
                    ('alphabetical', rel.AFFECTS, 'people'),
                    ('alphabetical', rel.COVERS, 'words'),
                  ])
    
  def test_structure_attribute_alias(self):
    interp = parser.make_relations(parser.spec_from_string("""
- (linear) alphabetical:
    /first =: a
"""))
    assert compare_interp(interp, 
                  [
                    ('linear', rel.TYPE, 'alphabetical'),
                    ('alphabetical', rel.GROUP_FOREACH, 'alphabetical/first'),
                    ('a', rel.ALIAS, 'alphabetical/first'),
                  ])
    
  def test_structure_attribute_mapping(self):
    interp = parser.make_relations(parser.spec_from_string("""
- (gui) chat-view:
    /marks <>: messages
    /encoding <>: time
"""))
    assert compare_interp(interp, 
                  [
                    ('gui', rel.TYPE, 'chat-view'),
                    ('chat-view', rel.GROUP_FOREACH, 'chat-view/marks'),
                    ('messages', rel.MAPTO, 'chat-view/marks'),
                    ('chat-view', rel.GROUP_FOREACH, 'chat-view/encoding'),
                    ('time', rel.MAPTO, 'chat-view/encoding'),
                  ])

  def test_group_attributes(self):
    interp = parser.make_relations(parser.spec_from_string("""
- editors:
    group foreach:
      - /videos
"""))
    assert compare_interp(interp, 
                  [
                    ('editors', rel.GROUP_FOREACH, 'editors/videos')
                  ])
    
  def test_group_attribute_alias(self):
    interp = parser.make_relations(parser.spec_from_string("""
- editors:
    group foreach:
      - /videos =: videos-in-editor
"""))
    assert compare_interp(interp, 
                  [
                    ('editors', rel.GROUP_FOREACH, 'editors/videos'),
                    ('videos.in-editor', rel.ALIAS, 'editors/videos'),
                  ])

    
  def test_group_attribute_alias(self):
    interp = parser.make_relations(parser.spec_from_string("""
- editors:
    group foreach:
      - /videos <>: videos-in-editor
"""))
    assert compare_interp(interp, 
                  [
                    ('editors', rel.GROUP_FOREACH, 'editors/videos'),
                    ('videos-in-editor', rel.MAPTO, 'editors/videos'),
                  ])
  
  def test_inline_structure_definition(self):
    interp = parser.make_relations(parser.spec_from_string("""
- (gui) chat-view:
    /marks <>: messages
    /encoding <>:
        (linear) time:
            affects: messages
"""))
    assert compare_interp(interp, 
                  [
                    ('gui', rel.TYPE, 'chat-view'),
                    ('chat-view', rel.GROUP_FOREACH, 'chat-view/marks'),
                    ('messages', rel.MAPTO, 'chat-view/marks'),
                    ('chat-view', rel.GROUP_FOREACH, 'chat-view/encoding'),
                    ('time', rel.MAPTO, 'chat-view/encoding'),
                    ('linear', rel.TYPE, 'time'),
                    ('time', rel.AFFECTS, 'messages'),
                  ])
  
  def test_attribute_structure(self):
    interp = parser.make_relations(parser.spec_from_string("""
- editors:
    group foreach:
      - (linear) /timeline:
          affects: /timestamps
"""))
    assert compare_interp(interp, 
                  [
                    ('editors', rel.GROUP_FOREACH, 'editors/timeline'),
                    ('editors', rel.GROUP_FOREACH, 'editors/timestamps'),
                    ('linear', rel.TYPE, 'editors/timeline'),
                    ('editors/timeline', rel.AFFECTS, 'editors/timestamps'),
                  ])
    
  def test_group_of_structure_with_attributes(self):
    # The turbo nest
    interp = parser.make_relations(parser.spec_from_string("""
- editors:
    group foreach: # feels redundant if there's just one (but there could be more!!)
      - (gui) /view:
          /encoding.cluster <>:
            /tracks:
              groups: /videos
"""))
    parser.print_interp(interp)
    assert compare_interp(interp, 
                  [
                    ('editors', rel.GROUP_FOREACH, 'editors/view'),
                    ('gui', rel.TYPE, 'editors/view'),
                    ('editors/view', rel.GROUP_FOREACH, 'editors/view/encoding'),
                    ('editors/view/encoding.cluster', rel.SUBSET, 'editors/view/encoding'),
                    ('editors/tracks', rel.MAPTO, 'editors/view/encoding.cluster'),
                    ('editors', rel.GROUP_FOREACH, 'editors/tracks'),
                    ('editors', rel.GROUP_FOREACH, 'editors/videos'),
                    ('editors/tracks', rel.GROUP, 'editors/videos'),
                  ])


class TestSpecParser:
  def test_spec_parser(self):
    spec = parser.spec_from_file('test-specs.yaml')
    parser.make_relations(spec)
    # assert False
