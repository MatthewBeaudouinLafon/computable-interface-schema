"""
Test metalgo.
Run with:
pytest flaml-schemas/flaml-6.4-group-as-verb/test.py -rA
"""

import pytest
import parser
from parser import rel

def interp_as_tuple(interp):
  res = []
  for relation in interp:
    res.append((relation['source'], relation['relation'], relation['target']))
  return res

def compare_interp(test, expected: list[tuple]):
  assert type(test) == list, f'Expected list, got `{type(test)}` instead.'

  # NOTE: We could check the the lenghts are the same, but then we couldn't get
  # an error telling us where the mismatch is.
  
  expected_dict = dict(list(map(lambda x: (x, 0), expected)))

  for t in interp_as_tuple(test):
    if t not in expected_dict:
      assert False, f'Could not find `{t}` in expected interp.'
    expected_dict[t] += 1
  
  unfound_relations = [relation for relation, count in expected_dict.items() if count == 0]
  assert len(unfound_relations) == 0, f'The following relations were expected: {unfound_relations}'
   
  return True

class TestCompoundObjectParser:
  def test_subsets(self):
    interp = []
    parser.parse_compound_object('a.b.c', interp)
    assert compare_interp(interp, 
                          [
                            ('a.b.c', rel.SUBSET, 'a.b'),
                            ('a.b', rel.SUBSET, 'a'),
                          ])
    
    interp = []
    parser.parse_compound_object('a-b.c-d', interp)
    assert compare_interp(interp, 
                          [
                            ('a-b.c-d', rel.SUBSET, 'a-b'),
                          ])
  
  def test_arrows(self):
    interp = []
    parser.parse_compound_object('a->b->c', interp)
    assert compare_interp(interp, 
                          [
                            ('a', rel.MAPTO, 'b'),
                            ('b', rel.MAPTO, 'c'),
                          ])
    
    interp = []
    parser.parse_compound_object('a-b->c-d', interp)
    assert compare_interp(interp, 
                          [
                            ('a-b', rel.MAPTO, 'c-d'),
                          ])
    
  def test_slash(self):
    interp = []
    parser.parse_compound_object('a-1/b-2/c-3', interp)
    assert compare_interp(interp, 
                          [
                            ('a-1', rel.GROUP, 'a-1/b-2'),
                            ('a-1/b-2', rel.GROUP, 'a-1/b-2/c-3'),
                          ])
    
  def test_and(self):
    interp = []
    parser.parse_compound_object('a-1 and b-2', interp)
    assert compare_interp(interp, 
                          [
                            ('a-1', rel.SUBSET, 'a-1 and b-2'),
                            ('b-2', rel.SUBSET, 'a-1 and b-2'),
                          ])
    
    interp = []
    parser.parse_compound_object('a and b and c', interp)
    assert compare_interp(interp, 
                          [
                            ('a', rel.SUBSET, 'a and b and c'),
                            ('b', rel.SUBSET, 'a and b and c'),
                            ('c', rel.SUBSET, 'a and b and c'),
                          ])
    
  def test_imagined_compound_terms(self):
    interp = []
    parser.parse_compound_object('a.b/c.d.e/f.g', interp)
    assert compare_interp(interp, 
                          [
                            ('a', rel.GROUP, 'a/c'),
                            ('a/c', rel.GROUP, 'a/c/f'),
                            ('a.b', rel.SUBSET, 'a'),
                            ('a/c.d', rel.SUBSET, 'a/c'),
                            ('a/c.d.e', rel.SUBSET, 'a/c.d'),
                            ('a/c/f.g', rel.SUBSET, 'a/c/f'),
                          ])
    
    interp = []
    parser.parse_compound_object('a/b->c.d/e->f/g.h', interp)
    assert compare_interp(interp, 
                          [
                            ('a/b', rel.MAPTO, 'c.d/e'),
                            ('c.d/e', rel.MAPTO, 'f/g.h'),
                            ('a', rel.GROUP, 'a/b'),
                            ('c', rel.GROUP, 'c/e'),
                            ('c.d', rel.SUBSET, 'c'),
                            ('f', rel.GROUP, 'f/g'),
                            ('f/g.h', rel.SUBSET, 'f/g'),
                          ])
    
    interp = []
    parser.parse_compound_object('a.b.c->d.e.f->g.h', interp)
    assert compare_interp(interp, 
                          [
                            ('a.b.c', rel.MAPTO, 'd.e.f'),
                            ('d.e.f', rel.MAPTO, 'g.h'),
                            ('a.b.c', rel.SUBSET, 'a.b'),
                            ('a.b', rel.SUBSET, 'a'),
                            ('d.e.f', rel.SUBSET, 'd.e'),
                            ('d.e', rel.SUBSET, 'd'),
                            ('g.h', rel.SUBSET, 'g'),
                          ])

    interp = []
    parser.parse_compound_object('a.b and c->d and e/f', interp)
    assert compare_interp(interp, 
                          [
                            ('a.b', rel.SUBSET, 'a.b and c->d and e/f'),
                            ('a.b', rel.SUBSET, 'a'),
                            ('c->d', rel.SUBSET, 'a.b and c->d and e/f'),
                            ('c', rel.MAPTO, 'd'),
                            ('e/f', rel.SUBSET, 'a.b and c->d and e/f'),
                            ('e', rel.GROUP, 'e/f'),
                          ])
  
  def test_realistic_compound_objects(self):
    interp = []
    parser.parse_compound_object('playhead->video/timestamps', interp)
    assert compare_interp(interp, 
                          [
                            ('playhead', rel.MAPTO, 'video/timestamps'),
                            ('video', rel.GROUP, 'video/timestamps'),
                          ])
    
    interp = []
    parser.parse_compound_object('editors.current/timestamps.playhead', interp)
    assert compare_interp(interp, 
                          [
                            ('editors', rel.GROUP, 'editors/timestamps'),
                            ('editors.current', rel.SUBSET, 'editors'),
                            ('editors/timestamps.playhead', rel.SUBSET, 'editors/timestamps'),
                          ])
    
    interp = []
    parser.parse_compound_object('folders.in-selected-path->items', interp)
    assert compare_interp(interp, 
                          [
                            ('folders.in-selected-path', rel.MAPTO, 'items'),
                            ('folders.in-selected-path', rel.SUBSET, 'folders'),
                          ])
    
    interp = []
    parser.parse_compound_object('channels.!dm', interp)
    assert compare_interp(interp, 
                          [
                            ('channels.!dm', rel.SUBSET, 'channels'),
                          ])
    
    interp = []
    parser.parse_compound_object('folders and files', interp)
    assert compare_interp(interp, 
                          [
                            ('folders', rel.SUBSET, 'folders and files'),
                            ('files', rel.SUBSET, 'folders and files'),
                          ])
    
    interp = []
    parser.parse_compound_object('chart-summary and numerical->dimension-info and numerical->interval-info', interp)
    assert compare_interp(interp, 
                          [
                            ('chart-summary', rel.SUBSET, 'chart-summary and numerical->dimension-info and numerical->interval-info'),
                            ('numerical->dimension-info', rel.SUBSET, 'chart-summary and numerical->dimension-info and numerical->interval-info'),
                            ('numerical', rel.MAPTO, 'dimension-info'),
                            ('numerical->interval-info', rel.SUBSET, 'chart-summary and numerical->dimension-info and numerical->interval-info'),
                            ('numerical', rel.MAPTO, 'interval-info'),
                          ])

class TestSpecParser:
  def test_spec_parser(self):
    spec = parser.parse_yaml('test-specs.yaml')
    parser.make_relations(spec)
    # assert False
