"""Rule CRUD API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from web.database import get_db
from web.models import RuleCreate, RuleOut, RuleUpdate, ValidationResult
from ca_engine.rules.yaml_loader import YAMLRuleLoader
from ca_engine.rules.validator import RuleValidator

router = APIRouter(prefix="/api/rules", tags=["rules"])


def _normalize_rule(row: dict[str, Any]) -> dict[str, Any]:
    """Ensure API response fields match RuleOut expectations."""
    row["description"] = row.get("description") or ""
    row["category"] = row.get("category") or "experimental"
    row["created_at"] = str(row["created_at"]) if row.get("created_at") else ""
    row["is_builtin"] = bool(row.get("is_builtin"))
    row["is_editable"] = bool(row.get("is_editable", True))
    return row


@router.get("/", response_model=list[RuleOut])
async def list_rules() -> list[dict[str, Any]]:
    """List all rules (built-in + custom)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, name, yaml_content, is_builtin, is_editable, description, category, created_at FROM rules ORDER BY name"
        )
        rows = await cursor.fetchall()
        return [_normalize_rule(dict(row)) for row in rows]
    finally:
        await db.close()


@router.get("/{rule_id}", response_model=RuleOut)
async def get_rule(rule_id: int) -> dict[str, Any]:
    """Get a single rule by ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, name, yaml_content, is_builtin, is_editable, description, category, created_at FROM rules WHERE id = ?",
            (rule_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Rule not found")
        return _normalize_rule(dict(row))
    finally:
        await db.close()


@router.post("/", response_model=RuleOut)
async def create_rule(rule: RuleCreate) -> dict[str, Any]:
    """Create a new custom rule."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO rules (name, yaml_content, is_builtin, is_editable, description, category)
               VALUES (?, ?, 0, 1, ?, ?)""",
            (rule.name, rule.yaml_content, rule.description, rule.category),
        )
        await db.commit()
        rule_id = cursor.lastrowid
        return await get_rule(rule_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await db.close()


@router.put("/{rule_id}", response_model=RuleOut)
async def update_rule(rule_id: int, rule: RuleUpdate) -> dict[str, Any]:
    """Update a custom rule. Built-in rules cannot be edited."""
    db = await get_db()
    try:
        # Check if rule exists and is editable
        cursor = await db.execute("SELECT is_editable FROM rules WHERE id = ?", (rule_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Rule not found")
        if not row["is_editable"]:
            raise HTTPException(status_code=403, detail="Built-in rules cannot be edited")

        # Build update query
        fields = []
        values = []
        if rule.name is not None:
            fields.append("name = ?")
            values.append(rule.name)
        if rule.yaml_content is not None:
            fields.append("yaml_content = ?")
            values.append(rule.yaml_content)
        if rule.description is not None:
            fields.append("description = ?")
            values.append(rule.description)
        if rule.category is not None:
            fields.append("category = ?")
            values.append(rule.category)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(rule_id)

        await db.execute(
            f"UPDATE rules SET {', '.join(fields)} WHERE id = ?",
            values,
        )
        await db.commit()
        return await get_rule(rule_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await db.close()


@router.delete("/{rule_id}")
async def delete_rule(rule_id: int) -> dict[str, str]:
    """Delete a custom rule. Built-in rules cannot be deleted."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT is_builtin FROM rules WHERE id = ?", (rule_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Rule not found")
        if row["is_builtin"]:
            raise HTTPException(status_code=403, detail="Built-in rules cannot be deleted")

        await db.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
        await db.commit()
        return {"message": "Rule deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await db.close()


@router.post("/validate")
async def validate_rule(rule: RuleCreate) -> ValidationResult:
    """Validate a rule YAML without saving."""
    try:
        loader = YAMLRuleLoader()
        table = loader._parse(rule.yaml_content)

        validator = RuleValidator(num_states=table.num_states)
        # We need to extract rows from the table for validation
        # For now, basic validation
        return ValidationResult(is_valid=True, errors=[], warnings=[])
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            errors=[{"message": str(e)}],
            warnings=[],
        )


@router.get("/categories/list")
async def list_categories() -> list[str]:
    """List all rule categories."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT DISTINCT category FROM rules ORDER BY category")
        rows = await cursor.fetchall()
        return [row["category"] for row in rows]
    finally:
        await db.close()
