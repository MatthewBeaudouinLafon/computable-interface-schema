"""
Test metalgo.
Run with:
pytest flaml-schemas/flaml-6.4-group-as-verb/test.py -rA
"""

import pytest
import parser
from parser import rel, dpower

def parse_str(statement: str, interp: list):
  return parser.parse_str(statement=statement, parent=None, interp=interp, depth=0)

def compare_interp(test, expected: list[tuple], verbose=False):
  assert type(test) == list, f'Expected list, got `{type(test)}` instead.'

  # NOTE: We could check the the lenghts are the same, but then we couldn't get
  # an error telling us where the mismatch is.
  expected_dict = dict(list(map(lambda x: (x, 0), expected)))

  for edge in test:
    # Is the test written correctly?
    assert type(parser.get_declaration_source(edge)) is str, f'Declaration must be a string, got {parser.get_declaration_source(edge)} instead.'
    assert type(parser.get_declaration_relation(edge)) is rel, f'Declaration must be a string, got {parser.get_declaration_relation(edge)} instead.'
    assert type(parser.get_declaration_target(edge)) is str, f'Declaration must be a string, got {parser.get_declaration_target(edge)} instead.'
    assert type(parser.get_declaration_power(edge)) is dpower, f'Declaration must be a string, got {parser.get_declaration_power(edge)} instead.'

    if verbose:
      parser.print_declaration(edge)
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
                            ('a.b.c', rel.SUBSET, 'a.b', dpower.WEAK),
                            ('a.b', rel.SUBSET, 'a', dpower.WEAK),
                          ])
    
    interp = []
    parser.parse_compound_object('a-b.c-d', '', interp)
    assert compare_interp(interp, 
                          [
                            ('a-b.c-d', rel.SUBSET, 'a-b', dpower.WEAK),
                          ])
  
  def test_arrows(self):
    interp = []
    parser.parse_compound_object('a->b->c', '', interp)
    assert compare_interp(interp, 
                          [
                            ('a', rel.MAPTO, 'b', dpower.WEAK),
                            ('b', rel.MAPTO, 'c', dpower.WEAK),
                            ('a->b->c', rel.SUBSET, 'c', dpower.WEAK),
                          ])
    
    interp = []
    parser.parse_compound_object('a-b->c-d', '', interp)
    assert compare_interp(interp, 
                          [
                            ('a-b', rel.MAPTO, 'c-d', dpower.WEAK),
                            ('a-b->c-d', rel.SUBSET, 'c-d', dpower.WEAK),
                          ])
    
  def test_slash(self):
    interp = []
    parser.parse_compound_object('a-1/b-2/c-3', '', interp)
    assert compare_interp(interp, 
                          [
                            ('a-1', rel.GROUP_FOREACH, 'a-1/b-2', dpower.WEAK),
                            ('a-1/b-2', rel.GROUP_FOREACH, 'a-1/b-2/c-3', dpower.WEAK),
                          ])
    
  def test_and(self):
    interp = []
    parse_str('a-1 and b-2', interp)
    assert compare_interp(interp, 
                          [
                            ('a-1', rel.SUBSET, 'a-1 and b-2', dpower.WEAK),
                            ('b-2', rel.SUBSET, 'a-1 and b-2', dpower.WEAK),
                          ])
    
    interp = []
    parse_str('a and b and c and d', interp=interp)
    assert compare_interp(interp, 
                          [
                            ('a', rel.SUBSET, 'a and b and c and d', dpower.WEAK),
                            ('b', rel.SUBSET, 'a and b and c and d', dpower.WEAK),
                            ('c', rel.SUBSET, 'a and b and c and d', dpower.WEAK),
                            ('d', rel.SUBSET, 'a and b and c and d', dpower.WEAK),
                          ])
    
  def test_type(self):
    interp = []
    parse_str('(a-1) b-2', interp=interp, )
    assert compare_interp(interp, 
                          [
                            ('a-1', rel.TYPE, 'b-2', dpower.STRONG),
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
                            ('a', rel.GROUP_FOREACH, 'a/c', dpower.WEAK),
                            ('a/c', rel.GROUP_FOREACH, 'a/c/f', dpower.WEAK),
                            ('a.b', rel.SUBSET, 'a', dpower.WEAK),
                            ('a/c.d', rel.SUBSET, 'a/c', dpower.WEAK),
                            ('a/c.d.e', rel.SUBSET, 'a/c.d', dpower.WEAK),
                            ('a/c/f.g', rel.SUBSET, 'a/c/f', dpower.WEAK),
                          ])
    
    interp = []
    parser.parse_compound_object('a/b->c.d/e->f/g.h', '', interp)
    assert compare_interp(interp, 
                          [
                            ('a/b', rel.MAPTO, 'c.d/e', dpower.WEAK),
                            ('c.d/e', rel.MAPTO, 'f/g.h', dpower.WEAK),
                            ('a', rel.GROUP_FOREACH, 'a/b', dpower.WEAK),
                            ('c', rel.GROUP_FOREACH, 'c/e', dpower.WEAK),
                            ('c.d', rel.SUBSET, 'c', dpower.WEAK),
                            ('f', rel.GROUP_FOREACH, 'f/g', dpower.WEAK),
                            ('f/g.h', rel.SUBSET, 'f/g', dpower.WEAK),
                            ('a/b->c.d/e->f/g.h', rel.SUBSET, 'f/g.h', dpower.WEAK),
                          ])
    
    interp = []
    parser.parse_compound_object('a.b.c->d.e.f->g.h', '', interp)
    assert compare_interp(interp, 
                          [
                            ('a.b.c', rel.MAPTO, 'd.e.f', dpower.WEAK),
                            ('d.e.f', rel.MAPTO, 'g.h', dpower.WEAK),
                            ('a.b.c', rel.SUBSET, 'a.b', dpower.WEAK),
                            ('a.b', rel.SUBSET, 'a', dpower.WEAK),
                            ('d.e.f', rel.SUBSET, 'd.e', dpower.WEAK),
                            ('d.e', rel.SUBSET, 'd', dpower.WEAK),
                            ('g.h', rel.SUBSET, 'g', dpower.WEAK),
                            ('a.b.c->d.e.f->g.h', rel.SUBSET, 'g.h', dpower.WEAK),
                          ])

    interp = []
    parse_str('a.b and c->d and e/f', interp=interp)
    assert compare_interp(interp, 
                          [
                            ('a.b', rel.SUBSET, 'a.b and c->d and e/f', dpower.WEAK),
                            ('a.b', rel.SUBSET, 'a', dpower.WEAK),
                            ('c->d', rel.SUBSET, 'a.b and c->d and e/f', dpower.WEAK),
                            ('c->d', rel.SUBSET, 'd', dpower.WEAK),
                            ('c', rel.MAPTO, 'd', dpower.WEAK),
                            ('e/f', rel.SUBSET, 'a.b and c->d and e/f', dpower.WEAK),
                            ('e', rel.GROUP_FOREACH, 'e/f', dpower.WEAK),
                          ])
    

    interp = []
    parse_str('b.c/d and y.z', interp=interp)
    assert compare_interp(interp, 
                          [
                            ('b.c/d', rel.SUBSET, 'b.c/d and y.z', dpower.WEAK),
                            ('b.c', rel.SUBSET, 'b', dpower.WEAK),
                            ('b', rel.GROUP_FOREACH, 'b/d', dpower.WEAK),
                            ('y.z', rel.SUBSET, 'b.c/d and y.z', dpower.WEAK),
                            ('y.z', rel.SUBSET, 'y', dpower.WEAK),
                          ])

    interp = []
    parse_str('(a) b.c/d and (x) y.z->w', interp=interp)
    assert compare_interp(interp, 
                          [
                            ('b.c/d', rel.SUBSET, 'b.c/d and y.z->w', dpower.WEAK),
                            ('a', rel.TYPE, 'b.c/d', dpower.STRONG),
                            ('b.c', rel.SUBSET, 'b', dpower.WEAK),
                            ('b', rel.GROUP_FOREACH, 'b/d', dpower.WEAK),
                            ('y.z->w', rel.SUBSET, 'b.c/d and y.z->w', dpower.WEAK),
                            ('x', rel.TYPE, 'y.z', dpower.STRONG),
                            ('y.z', rel.SUBSET, 'y', dpower.WEAK),
                            ('y.z', rel.MAPTO, 'w', dpower.WEAK),
                            ('y.z->w', rel.SUBSET, 'w', dpower.WEAK),
                          ])
  
  def test_realistic_compound_objects(self):
    interp = []
    parser.parse_compound_object('playhead->video/timestamps', '', interp)
    assert compare_interp(interp, 
                          [
                            ('playhead', rel.MAPTO, 'video/timestamps', dpower.WEAK),
                            ('video', rel.GROUP_FOREACH, 'video/timestamps', dpower.WEAK),
                            ('playhead->video/timestamps', rel.SUBSET, 'video/timestamps', dpower.WEAK),
                          ])
    
    interp = []
    parser.parse_compound_object('editors.current/timestamps.playhead', '', interp)
    assert compare_interp(interp, 
                          [
                            ('editors', rel.GROUP_FOREACH, 'editors/timestamps', dpower.WEAK),
                            ('editors.current', rel.SUBSET, 'editors', dpower.WEAK),
                            ('editors/timestamps.playhead', rel.SUBSET, 'editors/timestamps', dpower.WEAK),
                          ])
    
    interp = []
    parser.parse_compound_object('folders.in-selected-path->items', '', interp)
    assert compare_interp(interp, 
                          [
                            ('folders.in-selected-path', rel.MAPTO, 'items', dpower.WEAK),
                            ('folders.in-selected-path', rel.SUBSET, 'folders', dpower.WEAK),
                            ('folders.in-selected-path->items', rel.SUBSET, 'items', dpower.WEAK),
                          ])
    
    interp = []
    parser.parse_compound_object('channels.!dm', '', interp)
    assert compare_interp(interp, 
                          [
                            ('channels.!dm', rel.SUBSET, 'channels', dpower.WEAK),
                          ])
    
    interp = []
    parse_str('folders and files', interp=interp)
    assert compare_interp(interp, 
                          [
                            ('folders', rel.SUBSET, 'folders and files', dpower.WEAK),
                            ('files', rel.SUBSET, 'folders and files', dpower.WEAK),
                          ])
    
    interp = []
    parse_str('chart-summary and numerical->dimension-info and numerical->interval-info', interp=interp)
    assert compare_interp(interp, 
                          [
                            ('chart-summary', rel.SUBSET, 'chart-summary and numerical->dimension-info and numerical->interval-info', dpower.WEAK),
                            ('numerical->dimension-info', rel.SUBSET, 'dimension-info', dpower.WEAK),
                            ('numerical->dimension-info', rel.SUBSET, 'chart-summary and numerical->dimension-info and numerical->interval-info', dpower.WEAK),
                            ('numerical', rel.MAPTO, 'dimension-info', dpower.WEAK),
                            ('numerical->interval-info', rel.SUBSET, 'interval-info', dpower.WEAK),
                            ('numerical->interval-info', rel.SUBSET, 'chart-summary and numerical->dimension-info and numerical->interval-info', dpower.WEAK),
                            ('numerical', rel.MAPTO, 'interval-info', dpower.WEAK),
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
                    ('thing', rel.GROUP, 'other-thing', dpower.STRONG)
                  ])
    
  def test_type_relation(self):
    interp = parser.make_relations(parser.spec_from_string("""
- (linear) alphabetical
"""))
    assert compare_interp(interp, 
                  [
                    ('linear', rel.TYPE, 'alphabetical', dpower.STRONG)
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
                    ('linear', rel.TYPE, 'alphabetical', dpower.STRONG),
                    ('alphabetical', rel.AFFECTS, 'people', dpower.STRONG),
                    ('alphabetical', rel.COVERS, 'words', dpower.STRONG),
                  ])
    
  def test_structure_attribute_alias(self):
    interp = parser.make_relations(parser.spec_from_string("""
- (linear) alphabetical:
    /first =: a
"""))
    assert compare_interp(interp, 
                  [
                    ('linear', rel.TYPE, 'alphabetical', dpower.STRONG),
                    ('alphabetical', rel.GROUP_FOREACH, 'alphabetical/first', dpower.WEAK),
                    ('alphabetical', rel.GROUP_FOREACH, 'alphabetical/first', dpower.STRONG),
                    ('a', rel.ALIAS, 'alphabetical/first', dpower.STRONG),
                  ])
    
  def test_structure_attribute_mapping(self):
    interp = parser.make_relations(parser.spec_from_string("""
- (gui) chat-view:
    /marks <>: messages
    /encoding <>: time
"""))
    assert compare_interp(interp, 
                  [
                    ('gui', rel.TYPE, 'chat-view', dpower.STRONG),
                    ('chat-view', rel.GROUP_FOREACH, 'chat-view/marks', dpower.STRONG),
                    ('chat-view', rel.GROUP_FOREACH, 'chat-view/marks', dpower.WEAK),
                    ('messages', rel.MAPTO, 'chat-view/marks', dpower.STRONG),
                    ('chat-view', rel.GROUP_FOREACH, 'chat-view/encoding', dpower.STRONG),
                    ('chat-view', rel.GROUP_FOREACH, 'chat-view/encoding', dpower.WEAK),
                    ('time', rel.MAPTO, 'chat-view/encoding', dpower.STRONG),
                  ])

  def test_group_attributes(self):
    interp = parser.make_relations(parser.spec_from_string("""
- editors:
    group foreach:
      - /videos
"""))
    parser.print_interp(interp)
    assert compare_interp(interp, 
                  [
                    ('editors', rel.GROUP_FOREACH, 'editors/videos', dpower.STRONG),  # from group_foreach
                    ('editors', rel.GROUP_FOREACH, 'editors/videos', dpower.WEAK)    # from compound term editors/videos
                  ])
    
  def test_group_attribute_alias(self):
    interp = parser.make_relations(parser.spec_from_string("""
- editors:
    group foreach:
      - /videos =: videos-in-editor
"""))
    assert compare_interp(interp, 
                  [
                    ('editors', rel.GROUP_FOREACH, 'editors/videos', dpower.WEAK),
                    ('editors', rel.GROUP_FOREACH, 'editors/videos', dpower.STRONG),
                    ('videos-in-editor', rel.ALIAS, 'editors/videos', dpower.STRONG),
                  ])

    
  def test_group_attribute_map(self):
    interp = parser.make_relations(parser.spec_from_string("""
- editors:
    group foreach:
      - /videos <>: videos-in-editor
"""))
    assert compare_interp(interp, 
                  [
                    ('editors', rel.GROUP_FOREACH, 'editors/videos', dpower.WEAK),
                    ('editors', rel.GROUP_FOREACH, 'editors/videos', dpower.STRONG),
                    ('videos-in-editor', rel.MAPTO, 'editors/videos', dpower.STRONG),
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
                    ('gui', rel.TYPE, 'chat-view', dpower.STRONG),
                    ('chat-view', rel.GROUP_FOREACH, 'chat-view/marks', dpower.WEAK),
                    ('chat-view', rel.GROUP_FOREACH, 'chat-view/marks', dpower.STRONG),
                    ('messages', rel.MAPTO, 'chat-view/marks', dpower.STRONG),
                    ('chat-view', rel.GROUP_FOREACH, 'chat-view/encoding', dpower.WEAK),
                    ('chat-view', rel.GROUP_FOREACH, 'chat-view/encoding', dpower.STRONG),
                    ('time', rel.MAPTO, 'chat-view/encoding', dpower.STRONG),
                    ('linear', rel.TYPE, 'time', dpower.STRONG),
                    ('time', rel.AFFECTS, 'messages', dpower.STRONG),
                  ])
  
  def test_attribute_structure(self):
    interp = parser.make_relations(parser.spec_from_string("""
- editors:
    group foreach:
      - (linear) /timeline:
          affects: /timestamps
"""), verbose=True)
    assert compare_interp(interp, 
                  [
                    ('editors', rel.GROUP_FOREACH, 'editors/timeline', dpower.WEAK),
                    ('editors', rel.GROUP_FOREACH, 'editors/timeline', dpower.STRONG),
                    ('editors', rel.GROUP_FOREACH, 'editors/timestamps', dpower.WEAK),
                    ('editors', rel.GROUP_FOREACH, 'editors/timestamps', dpower.STRONG),
                    ('linear', rel.TYPE, 'editors/timeline', dpower.STRONG),
                    ('editors/timeline', rel.AFFECTS, 'editors/timestamps', dpower.STRONG),
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
                    ('editors', rel.GROUP_FOREACH, 'editors/view', dpower.WEAK),
                    ('editors', rel.GROUP_FOREACH, 'editors/view', dpower.STRONG),
                    ('gui', rel.TYPE, 'editors/view', dpower.STRONG),
                    ('editors/view', rel.GROUP_FOREACH, 'editors/view/encoding', dpower.WEAK),
                    ('editors/view', rel.GROUP_FOREACH, 'editors/view/encoding.cluster', dpower.STRONG),
                    ('editors/view/encoding.cluster', rel.SUBSET, 'editors/view/encoding', dpower.WEAK),
                    ('editors/tracks', rel.MAPTO, 'editors/view/encoding.cluster', dpower.STRONG),
                    ('editors', rel.GROUP_FOREACH, 'editors/tracks', dpower.WEAK),
                    ('editors', rel.GROUP_FOREACH, 'editors/tracks', dpower.STRONG),
                    ('editors', rel.GROUP_FOREACH, 'editors/videos', dpower.WEAK),
                    ('editors', rel.GROUP_FOREACH, 'editors/videos', dpower.STRONG),
                    ('editors/tracks', rel.GROUP, 'editors/videos', dpower.STRONG),
                  ])


class TestTypeDeclarations:
  def test_basic(self):
    type_interps = parser.parse_type_definitions(parser.spec_from_string("""
- def (video):
    group foreach:
      - /timestamps
"""))
    
    interp = type_interps.get('video', None)
    assert interp is not None

    assert compare_interp(interp, 
                  [
                    ('@', rel.GROUP_FOREACH, '@/timestamps', dpower.WEAK),
                  ])
  
  def test_multiple(self):
    type_interps = parser.parse_type_definitions(parser.spec_from_string("""
- def (linear):
    group foreach:
      - /first

- def (tree):
    group foreach:
      - /root
"""))
    
    linear_interp = type_interps.get('linear', None)
    assert linear_interp is not None
    assert compare_interp(linear_interp, 
                  [
                    ('@', rel.GROUP_FOREACH, '@/first', dpower.WEAK),                    
                  ])

    tree_interp = type_interps.get('tree', None)
    assert tree_interp is not None
    assert compare_interp(tree_interp, 
                  [
                    ('@', rel.GROUP_FOREACH, '@/root', dpower.WEAK),                    
                  ])

  def test_depth(self):
    type_interps = parser.parse_type_definitions(parser.spec_from_string("""
- def (video):
    group foreach:
      - (linear) /timeline:
          affects: /images
"""))
    
    interp = type_interps.get('video', None)
    assert interp is not None

    assert compare_interp(interp, 
                  [
                    ('@', rel.GROUP_FOREACH, '@/timeline', dpower.WEAK),
                    ('@', rel.GROUP_FOREACH, '@/images', dpower.WEAK),
                    ('linear', rel.TYPE, '@/timeline', dpower.WEAK),
                    ('@/timeline', rel.AFFECTS, '@/images', dpower.WEAK),
                  ])
  
  def test_no_interp_definition(self):
    type_interps = parser.parse_type_definitions(parser.spec_from_string("""
- def (action)
"""))
    
    res_interp = type_interps.get('action', None)
    assert type_interps.get('action', None) is not None
    assert type(res_interp) is list and len(res_interp) == 0


class TestSpecParser:
  def test_spec_parser(self):
    spec = parser.spec_from_file('test-specs.yaml')
    parser.make_relations(spec)
    # assert False
