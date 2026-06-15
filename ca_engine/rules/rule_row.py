"""Rule row parser for the legacy [;previous;counts;next] format."""

from __future__ import annotations

COUNT_VALUES = 10  # Neighbour count buckets 0..9


class RuleRow:
    """A single row in a rule file.

    Format: [;previousStates;neighbourCounts;nextState]
    - previousStates: comma-separated indices and ranges (e.g., "1-4", "0,3,5-8")
    - neighbourCounts: same encoding, 0-9 buckets
    - nextState: integer digit, or empty/non-digit for "no change"
    """

    def __init__(self, name: str = "") -> None:
        self.name = name
        self.previous: list[bool] = []
        self.count: list[bool] = []
        self.previous_code = ""
        self.count_code = ""
        self.next_same = True
        self.next = 0

    def set_previous(self, code: str, num_colors: int = 101) -> None:
        self.previous_code = code
        self.previous = decode(code, num_colors)

    def set_count(self, code: str) -> None:
        self.count_code = code
        self.count = decode(code, COUNT_VALUES)

    def set_next(self, code: str) -> None:
        """Set next state from string. Empty or non-digit = 'no change'."""
        digits = [c for c in code if c.isdigit()]
        if not digits:
            self.next_same = True
            self.next = 0
        else:
            self.next_same = False
            self.next = int("".join(digits))

    def get_next_str(self) -> str:
        if self.next_same:
            return "no change"
        return str(self.next)

    @classmethod
    def from_string(cls, row: str, num_colors: int = 101) -> RuleRow:
        """Parse a row string like '[;1;2,3;1]' or '[;0;3;1]'."""
        r = cls()
        # Strip brackets
        row = row.strip()
        if row.startswith("["):
            row = row[1:]
        if row.endswith("]"):
            row = row[:-1]

        parts = row.split(";")
        # Expected: [;previous;counts;next] → 4 parts, first is empty
        if len(parts) < 4:
            # Try without leading semicolon
            parts = row.split(";")

        if len(parts) >= 4:
            r.name = parts[0]
            r.set_previous(parts[1], num_colors)
            r.set_count(parts[2])
            r.set_next(parts[3])
        elif len(parts) == 3:
            r.set_previous(parts[0], num_colors)
            r.set_count(parts[1])
            r.set_next(parts[2])
        else:
            raise ValueError(f"Invalid rule row format: {row!r}")

        return r

    def __repr__(self) -> str:
        return f"[{self.name};{self.previous_code};{self.count_code};{self.get_next_str()}]"


def decode(code: str, length: int) -> list[bool]:
    """Decode a comma-separated/range string into a boolean list.

    Examples:
        "0"     → [True, False, ...]
        "1-4"   → [False, True, True, True, True, ...]
        "0,3,5-8" → [True, False, False, True, False, True, True, True, True, ...]
    """
    result = [False] * length
    if not code.strip():
        return result

    current = 0
    in_range = False
    buffer = ""

    for i, char in enumerate(code):
        if char.isdigit():
            buffer += char
        else:
            if buffer:
                value = int(buffer)
                buffer = ""
                if not in_range:
                    current = value
                start = min(current, value)
                end = max(current, value)
                start = max(0, start)
                end = min(length - 1, end)
                for j in range(start, end + 1):
                    result[j] = True
                current = value
                in_range = False
            if char == "-":
                in_range = True

    # Handle trailing buffer
    if buffer:
        value = int(buffer)
        if not in_range:
            current = value
        start = min(current, value)
        end = max(current, value)
        start = max(0, start)
        end = min(length - 1, end)
        for j in range(start, end + 1):
            result[j] = True

    return result


def encode(data: list[bool]) -> str:
    """Encode a boolean list into a comma-separated/range string.

    This is the inverse of decode().
    """
    if not any(data):
        return ""

    parts: list[str] = []
    run_length = 0
    first_index = True

    for i, active in enumerate(data):
        if active:
            if run_length == 0:
                if not first_index:
                    parts.append(",")
                parts.append(str(i))
            first_index = False
            run_length += 1
        else:
            if run_length == 2:
                parts.append(",")
                parts.append(str(i - 1))
            elif run_length > 2:
                parts.append("-")
                parts.append(str(i - 1))
            run_length = 0

    # Handle trailing run
    n = len(data)
    if run_length == 2:
        parts.append(",")
        parts.append(str(n - 1))
    elif run_length > 2:
        parts.append("-")
        parts.append(str(n - 1))

    return "".join(parts)
