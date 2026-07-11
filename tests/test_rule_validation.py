"""Tests for rule validation service."""

import pytest

from web.services.rule_validation import validate_rule_name, validate_rule_yaml

CONWAY_YAML = """name: TestConway
version: "1.0"
states: 2
neighbourhood: moore8
transitions:
- from: [1]
  neighbors: [2, 3]
  to: 1
- from: [0]
  neighbors: [3]
  to: 1
"""


def test_validate_rule_name_valid():
    assert validate_rule_name("MyRule_01") == []


def test_validate_rule_name_invalid():
    errors = validate_rule_name("ab")
    assert errors


def test_validate_conway_yaml():
    result = validate_rule_yaml(CONWAY_YAML, "TestConway")
    assert result.is_valid


def test_validate_empty_transitions():
    yaml = """name: Bad
states: 2
neighbourhood: moore8
transitions: []
"""
    result = validate_rule_yaml(yaml, "BadRule")
    assert not result.is_valid


def test_validate_invalid_neighbourhood():
    yaml = CONWAY_YAML.replace("moore8", "invalid_hood")
    result = validate_rule_yaml(yaml, "TestConway")
    assert not result.is_valid
