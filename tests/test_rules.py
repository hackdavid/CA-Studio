"""Tests for rule parsing and compilation."""

import numpy as np
import pytest

from ca_engine.rules.rule_row import RuleRow, COUNT_VALUES, decode, encode
from ca_engine.rules.compiler import compile_rule_table, RuleTable, rule_table_to_rows
from ca_engine.rules.legacy_loader import LegacyRuleLoader
from ca_engine.rules.validator import RuleValidator, ValidationResult


class TestDecode:
    def test_single(self):
        assert decode("3", 10) == [False, False, False, True, False, False, False, False, False, False]

    def test_range(self):
        result = decode("1-4", 10)
        assert result == [False, True, True, True, True, False, False, False, False, False]

    def test_comma(self):
        result = decode("0,3,5", 10)
        assert result == [True, False, False, True, False, True, False, False, False, False]

    def test_mixed(self):
        result = decode("0,3,5-8", 10)
        expected = [True, False, False, True, False, True, True, True, True, False]
        assert result == expected

    def test_empty(self):
        assert decode("", 10) == [False] * 10

    def test_roundtrip(self):
        for code in ["0", "1-4", "0,3,5-8", "0-9"]:
            decoded = decode(code, 10)
            encoded = encode(decoded)
            # decode(encode(decode(x))) should give same as decode(x)
            assert decode(encoded, 10) == decoded


class TestRuleRow:
    def test_parse_conway_survival(self):
        row = RuleRow.from_string("[;1;2,3;1]", num_colors=2)
        assert row.name == ""
        assert row.previous_code == "1"
        assert row.count_code == "2,3"
        assert row.get_next_str() == "1"
        assert row.next_same is False
        assert row.next == 1

    def test_parse_conway_birth(self):
        row = RuleRow.from_string("[;0;3;1]", num_colors=2)
        assert row.previous_code == "0"
        assert row.count_code == "3"
        assert row.get_next_str() == "1"

    def test_no_change(self):
        row = RuleRow.from_string("[;1;2,3;]", num_colors=2)
        assert row.next_same is True
        assert row.get_next_str() == "no change"

    def test_repr(self):
        row = RuleRow.from_string("[;1;2,3;1]", num_colors=2)
        assert repr(row) == "[;1;2,3;1]"


class TestCompiler:
    def test_compile_conway(self):
        """Conway's Game of Life: B3/S23."""
        rows = [
            RuleRow.from_string("[;1;2,3;1]", num_colors=2),  # Survival
            RuleRow.from_string("[;0;3;1]", num_colors=2),   # Birth
        ]
        table = compile_rule_table(rows, num_states=2)

        assert table.num_states == 2
        assert table.table.shape == (2, COUNT_VALUES)

        # State 1 with 2 or 3 neighbours → stays 1
        assert table.table[1, 2] == 1
        assert table.table[1, 3] == 1
        # State 1 with other counts → 0 (default)
        assert table.table[1, 0] == 0
        assert table.table[1, 1] == 0
        assert table.table[1, 4] == 0

        # State 0 with 3 neighbours → becomes 1
        assert table.table[0, 3] == 1
        # State 0 with other counts → 0
        assert table.table[0, 0] == 0
        assert table.table[0, 1] == 0
        assert table.table[0, 2] == 0

    def test_lookup_basic(self):
        table = RuleTable(np.array([[0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                                     [0, 0, 1, 1, 0, 0, 0, 0, 0, 0]], dtype=np.uint8))
        states = np.array([[0, 1], [1, 0]], dtype=np.uint8)
        counts = np.array([[3, 2], [2, 3]], dtype=np.uint8)
        result = table.lookup(states, counts)
        expected = np.array([[1, 1], [1, 1]], dtype=np.uint8)
        assert np.array_equal(result, expected)

    def test_lookup_out_of_bounds(self):
        table = RuleTable(np.zeros((2, COUNT_VALUES), dtype=np.uint8))
        states = np.array([[0, 1]], dtype=np.uint8)
        counts = np.array([[10, 15]], dtype=np.uint8)  # Out of bounds
        result = table.lookup(states, counts)
        assert np.array_equal(result, np.array([[0, 0]], dtype=np.uint8))

    def test_roundtrip(self):
        """Rows → table → rows should produce semantically equivalent table."""
        rows = [
            RuleRow.from_string("[;1;2,3;1]", num_colors=2),
            RuleRow.from_string("[;0;3;1]", num_colors=2),
        ]
        table1 = compile_rule_table(rows, num_states=2)
        rows2 = rule_table_to_rows(table1.table, num_states=2)
        table2 = compile_rule_table(rows2, num_states=2)
        assert np.array_equal(table1.table, table2.table)


class TestLegacyLoader:
    def test_load_conway(self):
        loader = LegacyRuleLoader()
        table = loader.load("Conway", num_states=2)
        assert table.name == "Conway"
        assert table.num_states == 2
        # Verify Conway rules
        assert table.table[1, 2] == 1  # Survival
        assert table.table[1, 3] == 1
        assert table.table[0, 3] == 1  # Birth
        assert table.table[0, 0] == 0

    def test_list_rules(self):
        loader = LegacyRuleLoader()
        rules = loader.list_rules()
        assert "Conway" in rules
        assert len(rules) >= 1


class TestValidator:
    def test_valid_conway(self):
        rows = [
            RuleRow.from_string("[;1;2,3;1]", num_colors=2),
            RuleRow.from_string("[;0;3;1]", num_colors=2),
        ]
        v = RuleValidator(num_states=2)
        result = v.validate(rows)
        assert result.is_valid

    def test_out_of_range_state(self):
        row = RuleRow.from_string("[;5;3;1]", num_colors=6)  # Parse with enough states to capture 5
        v = RuleValidator(num_states=2)
        result = v.validate([row])
        assert not result.is_valid
        assert any("out of range" in e.message for e in result.errors)

    def test_empty_row(self):
        v = RuleValidator(num_states=2)
        result = v.validate([])
        assert not result.is_valid
