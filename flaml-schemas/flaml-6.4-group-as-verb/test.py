"""
Test metalgo.
Run with:
pytest flaml-schemas/flaml-6.4-group-as-verb/test.py -rA
"""

import pytest
import parser

class TestSpecParser:
  def test_spec_parser(self):
    spec = parser.parse_yaml('test-specs.yaml')
    parser.make_relations(spec)
    # assert False
