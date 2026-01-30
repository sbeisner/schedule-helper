"""Scheduling rules API endpoints."""

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.tables import SchedulingRuleTable
from app.models.rules import (
    SchedulingRule,
    SchedulingRuleCreate,
    RuleCondition,
    RuleAction,
    RuleConditionType,
    RuleActionType,
    RULE_TEMPLATES,
)

router = APIRouter()


@router.get("/", response_model=list[SchedulingRule])
async def list_rules(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """List all scheduling rules."""
    query = db.query(SchedulingRuleTable)
    if active_only:
        query = query.filter(SchedulingRuleTable.is_active == True)
    rules = query.order_by(SchedulingRuleTable.priority.desc()).all()
    return [_table_to_model(r) for r in rules]


@router.get("/templates", response_model=list[dict])
async def get_rule_templates():
    """Get pre-defined rule templates."""
    return RULE_TEMPLATES


@router.get("/{rule_id}", response_model=SchedulingRule)
async def get_rule(rule_id: str, db: Session = Depends(get_db)):
    """Get a specific scheduling rule."""
    rule = db.query(SchedulingRuleTable).filter(SchedulingRuleTable.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return _table_to_model(rule)


@router.post("/", response_model=SchedulingRule, status_code=201)
async def create_rule(rule: SchedulingRuleCreate, db: Session = Depends(get_db)):
    """Create a new scheduling rule."""
    db_rule = SchedulingRuleTable(
        id=str(uuid4()),
        name=rule.name,
        description=rule.description,
        conditions=rule.conditions,
        actions=rule.actions,
        priority=rule.priority,
        is_active=True,
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return _table_to_model(db_rule)


@router.post("/from-template", response_model=SchedulingRule, status_code=201)
async def create_from_template(
    template_name: str = Query(...),
    db: Session = Depends(get_db),
):
    """Create a rule from a pre-defined template."""
    template = next((t for t in RULE_TEMPLATES if t["name"] == template_name), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    db_rule = SchedulingRuleTable(
        id=str(uuid4()),
        name=template["name"],
        description=template.get("description"),
        conditions=template.get("conditions", []),
        actions=template.get("actions", []),
        priority=template.get("priority", 0),
        is_active=True,
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return _table_to_model(db_rule)


@router.put("/{rule_id}", response_model=SchedulingRule)
async def update_rule(
    rule_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    conditions: Optional[list[dict]] = None,
    actions: Optional[list[dict]] = None,
    priority: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """Update a scheduling rule."""
    db_rule = db.query(SchedulingRuleTable).filter(SchedulingRuleTable.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if name is not None:
        db_rule.name = name
    if description is not None:
        db_rule.description = description
    if conditions is not None:
        db_rule.conditions = conditions
    if actions is not None:
        db_rule.actions = actions
    if priority is not None:
        db_rule.priority = priority
    if is_active is not None:
        db_rule.is_active = is_active

    db.commit()
    db.refresh(db_rule)
    return _table_to_model(db_rule)


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: str, db: Session = Depends(get_db)):
    """Delete a scheduling rule."""
    db_rule = db.query(SchedulingRuleTable).filter(SchedulingRuleTable.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(db_rule)
    db.commit()


def _table_to_model(table: SchedulingRuleTable) -> SchedulingRule:
    """Convert database table to Pydantic model."""
    conditions = []
    for c in table.conditions or []:
        conditions.append(
            RuleCondition(
                condition_type=RuleConditionType(c.get("condition_type")),
                value=c.get("value"),
                operator=c.get("operator", "equals"),
            )
        )

    actions = []
    for a in table.actions or []:
        actions.append(
            RuleAction(
                action_type=RuleActionType(a.get("action_type")),
                value=a.get("value"),
            )
        )

    return SchedulingRule(
        id=table.id,
        name=table.name,
        description=table.description,
        conditions=conditions,
        actions=actions,
        priority=table.priority,
        is_active=table.is_active,
        created_at=table.created_at,
        updated_at=table.updated_at,
    )
