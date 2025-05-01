"""
Test everything about the metaphor algorithm.
"""

import pytest
import metalgo


class TestHelpers:
  def test_listable(self):
    possible_inputs = [
      'just a string',
      ['string', 'array'],
      {'key': 'val'},
      [{'key': 'val'}, {'key': 'val'}]
    ]

    for input in possible_inputs:
      assert type(metalgo.listable(input)) is list


class TestParsing:

  def test_unit_object_registration(self):
    conditions = [
      {
        'input': 'a',
        'expect': {'a': set()}
      },
      {
        'input': 'a/x',
        'expect': {'a': set(), 'a/x': {'a'}}
      },
      {
        'input': 'a.b.c/x',
        'expect': {'a': set(), 'a.b': {'a'}, 'a.b.c': {'a.b'}, 'a.b.c/x': {'a.b.c'}}
      },
      {
        'input': 'a->b/x',
        'expect': {'a': {'b/x'}, 'b/x': {'b'}, 'b': set()}
      },
      {
        'input': 'a/x->b',
        'expect': {'a/x': {'b', 'a'}, 'a': set(), 'b': set()}
      },
    ]

    for condition in conditions:
      registry = metalgo.ObjectRegistry()
      registry.register_object(condition['input'])
      assert registry.registry == condition['expect']
  
  def test_realistic_object_registration(self):
    conditions = [
      {
        'input': 'days.selected->events',
        'expect': {'days.selected': {'events', 'days'}, 'days': set(), 'events': set()}
      },
      {
        'input': 'playhead->videos.in-editor/images',
        'expect': {'videos': set(), 'videos.in-editor': {'videos'}, 'videos.in-editor/images': {'videos.in-editor'}, 'playhead': {'videos.in-editor/images'}}
      },
    ]

    for condition in conditions:
      registry = metalgo.ObjectRegistry()
      registry.register_object(condition['input'])
      assert registry.registry == condition['expect']
  
  # TODO: test from a sample test spec (that doesn't change)

  

  
  