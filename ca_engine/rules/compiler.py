"""Rule compilation: list[RuleRow] → lookup table."""

from __future__ import annotations

import hashlib

import numpy as np

from .rule_row import COUNT_VALUES, RuleRow


class RuleTable:
    """Compiled rule table: T[state, count] → next_state.

    Attributes:
        table: np.ndarray of shape (K, COUNT_VALUES) dtype uint8.
        num_states: Number of states K.
        name: Rule name for display.
        source_hash: SHA-256 of the source text for provenance.
    """

    def __init__(self, table: np.ndarray, name: str = "", source: str = "") -> None:
        self.table = table.astype(np.uint8)
        self.num_states = table.shape[0]
        self.name = name
        self.source = source
        self.source_hash = hashlib.sha256(source.encode()).hexdigest() if source else ""

    def lookup(self, states: np.ndarray, counts: np.ndarray) -> np.ndarray:
        """Apply the rule table to a grid.

        Args:
            states: Grid of current states, shape (H, W), dtype uint8.
            counts: Grid of neighbour counts, shape (H, W), dtype uint8.

        Returns:
            Next state grid, shape (H, W), dtype uint8.
            For count >= COUNT_VALUES or state >= num_states, returns 0.
        """
        # Clip out-of-bounds to safe defaults
        safe_states = np.clip(states, 0, self.num_states - 1)
        safe_counts = np.clip(counts, 0, COUNT_VALUES - 1)

        # Advanced indexing: result[i,j] = table[states[i,j], counts[i,j]]
        next_grid = self.table[safe_states, safe_counts]

        # Explicitly zero out-of-bounds (Java behavior)
        out_of_bounds = (counts >= COUNT_VALUES) | (states >= self.num_states)
        next_grid = np.where(out_of_bounds, 0, next_grid)

        return next_grid.astype(np.uint8)

    def __repr__(self) -> str:
        return f"RuleTable({self.name!r}, K={self.num_states}, hash={self.source_hash[:16]}...)"


def compile_rule_table(rows: list[RuleRow], num_states: int = 101) -> RuleTable:
    """Compile a list of RuleRow into a lookup table.

    Rows are applied bottom-up (reverse order) so later rows override earlier.
    Default value for all entries is 0.

    Args:
        rows: List of RuleRow objects.
        num_states: Number of states (K).

    Returns:
        Compiled RuleTable.
    """
    table = np.zeros((num_states, COUNT_VALUES), dtype=np.uint8)

    for row in reversed(rows):
        for state in range(num_states):
            if not row.previous[state]:
                continue
            for count in range(COUNT_VALUES):
                if not row.count[count]:
                    continue
                if row.next_same:
                    table[state, count] = state
                else:
                    table[state, count] = row.next

    return RuleTable(table)


def rule_table_to_rows(table: np.ndarray, num_states: int = 101) -> list[RuleRow]:
    """Convert a rule table back to a list of RuleRow (round-trip).

    This is useful for editing and saving rules.
    """
    rows: list[RuleRow] = []
    for prev_state in range(num_states):
        for next_state in range(num_states):
            counts = [table[prev_state, c] == next_state for c in range(COUNT_VALUES)]
            if not any(counts):
                continue
            row = RuleRow()
            prev = [False] * num_states
            prev[prev_state] = True
            row.previous = prev
            row.count = counts
            row.next = next_state
            row.next_same = False
            rows.append(row)

    # Sort rows for canonical output
    rows.sort(key=lambda r: (r.count, r.next))

    # Merge rows with same count/next
    if not rows:
        return []

    merged: list[RuleRow] = []
    acc = rows[0]
    for row in rows[1:]:
        if row.count == acc.count and row.next == acc.next:
            # Merge previous states
            for i in range(num_states):
                if row.previous[i]:
                    acc.previous[i] = True
        else:
            merged.append(acc)
            acc = row
    merged.append(acc)

    # Encode back to strings
    from .rule_row import encode

    for row in merged:
        row.previous_code = encode(row.previous)
        row.count_code = encode(row.count)

    return merged
