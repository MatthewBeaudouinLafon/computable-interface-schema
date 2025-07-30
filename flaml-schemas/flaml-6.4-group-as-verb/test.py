"""
Test metalgo.
"""

import pytest
import parser

class TestSpecParser:
  def test_spec_parser(self):
    spec = parser.parse_yaml('test-specs.yaml')
    print(parser.make_relations(spec))
    # assert False
