"""Rule validation: check user-defined rules for correctness."""

from __future__ import annotations

from dataclasses import dataclass, field

from .rule_row import COUNT_VALUES, RuleRow


@dataclass
class ValidationError:
    line: int | None
    message: str
    got: str = ""
    expected: str = ""


@dataclass
class ValidationWarning:
    line: int | None
    message: str


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationWarning] = field(default_factory=list)

    def add_error(self, line: int | None, message: str, got: str = "", expected: str = "") -> None:
        self.errors.append(ValidationError(line, message, got, expected))
        self.is_valid = False

    def add_warning(self, line: int | None, message: str) -> None:
        self.warnings.append(ValidationWarning(line, message))


class RuleValidator:
    """Validate rule rows before compilation."""

    def __init__(self, num_states: int = 101) -> None:
        self.num_states = num_states

    def validate(self, rows: list[RuleRow]) -> ValidationResult:
        """Validate a list of RuleRow objects."""
        result = ValidationResult()

        if not rows:
            result.add_error(None, "Rule has no rows")
            return result

        for i, row in enumerate(rows):
            line = i + 1
            self._validate_row(row, line, result)

        # Check for overlapping rows
        self._check_overlaps(rows, result)

        # Check for unhandled states
        self._check_coverage(rows, result)

        return result

    def _validate_row(self, row: RuleRow, line: int, result: ValidationResult) -> None:
        # Check previous states
        if not any(row.previous):
            result.add_warning(line, "Row has no previous states (will never match)")

        # Check for out-of-range states in the raw code
        max_prev = self._max_in_code(row.previous_code)
        if max_prev is not None and max_prev >= self.num_states:
            result.add_error(
                line,
                f"Previous state {max_prev} out of range",
                got=str(max_prev),
                expected=f"0..{self.num_states - 1}",
            )

        for state in range(self.num_states):
            if state < len(row.previous) and row.previous[state] and state >= self.num_states:
                result.add_error(
                    line,
                    f"Previous state {state} out of range",
                    got=str(state),
                    expected=f"0..{self.num_states - 1}",
                )

        # Check neighbour counts
        if not any(row.count):
            result.add_warning(line, "Row has no neighbour counts (will never match)")

        max_count = self._max_in_code(row.count_code)
        if max_count is not None and max_count >= COUNT_VALUES:
            result.add_error(
                line,
                f"Neighbour count {max_count} out of range",
                got=str(max_count),
                expected=f"0..{COUNT_VALUES - 1}",
            )

        for count in range(COUNT_VALUES):
            if count < len(row.count) and row.count[count] and count >= COUNT_VALUES:
                result.add_error(
                    line,
                    f"Neighbour count {count} out of range",
                    got=str(count),
                    expected=f"0..{COUNT_VALUES - 1}",
                )

        # Check next state
        if not row.next_same:
            if row.next < 0 or row.next >= self.num_states:
                result.add_error(
                    line,
                    f"Next state {row.next} out of range",
                    got=str(row.next),
                    expected=f"0..{self.num_states - 1}",
                )

    @staticmethod
    def _max_in_code(code: str) -> int | None:
        """Extract the maximum integer from a code string like '1-4' or '0,3,5'."""
        if not code.strip():
            return None
        import re
        numbers = [int(m) for m in re.findall(r"\d+", code)]
        return max(numbers) if numbers else None

    def _check_overlaps(self, rows: list[RuleRow], result: ValidationResult) -> None:
        """Warn about overlapping rows (later rows override earlier)."""
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                row_a = rows[i]
                row_b = rows[j]
                overlap_prev = [a and b for a, b in zip(row_a.previous, row_b.previous)]
                overlap_count = [a and b for a, b in zip(row_a.count, row_b.count)]
                if any(overlap_prev) and any(overlap_count):
                    if row_a.next != row_b.next or row_a.next_same != row_b.next_same:
                        result.add_warning(
                            j + 1,
                            f"Row {j + 1} overlaps with row {i + 1} and will override it",
                        )

    def _check_coverage(self, rows: list[RuleRow], result: ValidationResult) -> None:
        """Warn about states not covered by any row."""
        covered = [False] * self.num_states
        for row in rows:
            for state in range(self.num_states):
                if row.previous[state]:
                    covered[state] = True

        for state in range(self.num_states):
            if not covered[state]:
                result.add_warning(None, f"State {state} is not handled by any rule row")
