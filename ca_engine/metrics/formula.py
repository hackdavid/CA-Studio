"""Safe formula DSL evaluator for custom metrics."""

from __future__ import annotations

import ast
import math
import re
from typing import Any

import numpy as np

BUILTIN_IDENTIFIERS = frozenset({"density", "entropy", "entropy_nonzero"})
RESERVED_METRIC_NAMES = frozenset({"density", "entropy", "entropy_nonzero", "step"})


class FormulaError(ValueError):
    """Raised when a formula is invalid or unsafe."""


class SafeFormulaEvaluator:
    """Evaluate arithmetic expressions over whitelisted metric variables."""

    def __init__(self, allowed_names: set[str] | None = None) -> None:
        self.allowed_names = allowed_names or set(BUILTIN_IDENTIFIERS)

    def validate(self, formula: str) -> list[str]:
        """Return list of validation error messages (empty if valid)."""
        errors: list[str] = []
        formula = formula.strip()
        if not formula:
            errors.append("Formula cannot be empty")
            return errors

        try:
            tree = ast.parse(formula, mode="eval")
        except SyntaxError as e:
            errors.append(f"Syntax error: {e.msg}")
            return errors

        referenced = self._collect_names(tree)
        unknown = referenced - self.allowed_names
        if unknown:
            errors.append(f"Unknown identifiers: {', '.join(sorted(unknown))}")
        if not referenced:
            errors.append("Formula must reference at least one measurement (e.g. density, entropy)")

        try:
            self._validate_node(tree.body)
        except FormulaError as e:
            errors.append(str(e))

        return errors

    def evaluate(self, formula: str, context: dict[str, float]) -> float:
        """Evaluate formula with given variable values."""
        errors = self.validate(formula)
        if errors:
            raise FormulaError(errors[0])

        tree = ast.parse(formula.strip(), mode="eval")
        result = self._eval_node(tree.body, context)
        if not isinstance(result, (int, float)) or not math.isfinite(float(result)):
            raise FormulaError("Formula did not produce a finite number")
        return float(result)

    def _collect_names(self, tree: ast.AST) -> set[str]:
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names.add(node.id)
        return names

    def _validate_node(self, node: ast.AST) -> None:
        if isinstance(node, ast.Expression):
            self._validate_node(node.body)
        elif isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise FormulaError("Only numeric constants are allowed")
        elif isinstance(node, ast.Name):
            if node.id not in self.allowed_names:
                raise FormulaError(f"Identifier '{node.id}' is not allowed")
        elif isinstance(node, ast.BinOp):
            if not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                raise FormulaError("Only +, -, *, / operators are allowed")
            self._validate_node(node.left)
            self._validate_node(node.right)
        elif isinstance(node, ast.UnaryOp):
            if not isinstance(node.op, (ast.UAdd, ast.USub)):
                raise FormulaError("Only unary + and - are allowed")
            self._validate_node(node.operand)
        else:
            raise FormulaError(f"Unsupported expression: {type(node).__name__}")

    def _eval_node(self, node: ast.AST, context: dict[str, float]) -> float:
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id not in context:
                raise FormulaError(f"Missing value for '{node.id}'")
            return float(context[node.id])
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                if right == 0:
                    raise FormulaError("Division by zero")
                return left / right
            raise FormulaError("Unsupported operator")
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, context)
            if isinstance(node.op, ast.UAdd):
                return operand
            if isinstance(node.op, ast.USub):
                return -operand
        raise FormulaError(f"Cannot evaluate {type(node).__name__}")


METRIC_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,31}$")


def validate_metric_name(name: str) -> list[str]:
    """Validate custom metric name."""
    if not name or not METRIC_NAME_PATTERN.match(name):
        return ["Name must be 3-32 lowercase characters, start with a letter, use only a-z, 0-9, underscore"]
    if name in RESERVED_METRIC_NAMES:
        return [f"Name '{name}' is reserved for built-in metrics"]
    return []


def build_test_grid(shape: tuple[int, int] = (8, 8), num_states: int = 4) -> np.ndarray:
    """Create a small heterogeneous grid for formula dry-runs."""
    h, w = shape
    grid = np.zeros((h, w), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            grid[y, x] = (x + y) % num_states
    return grid


def compute_builtin_context(grid: np.ndarray, num_states: int) -> dict[str, float]:
    """Compute builtin metric values for a grid."""
    total = grid.size
    nonzero = int(np.count_nonzero(grid))
    density = nonzero / total if total else 0.0

    counts = np.bincount(grid.ravel(), minlength=num_states)
    probs = counts / total if total else counts.astype(float)
    nonzero_probs = probs[probs > 0]
    entropy = float(-np.sum(nonzero_probs * np.log2(nonzero_probs))) if len(nonzero_probs) else 0.0

    counts_nz = counts[1:]
    total_nz = counts_nz.sum()
    if total_nz > 0:
        probs_nz = counts_nz / total_nz
        nonzero_probs_nz = probs_nz[probs_nz > 0]
        entropy_nonzero = float(-np.sum(nonzero_probs_nz * np.log2(nonzero_probs_nz)))
    else:
        entropy_nonzero = 0.0

    return {
        "density": density,
        "entropy": entropy,
        "entropy_nonzero": entropy_nonzero,
    }
