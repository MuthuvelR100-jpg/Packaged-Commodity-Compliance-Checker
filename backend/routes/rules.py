from flask import Blueprint, jsonify, request

from extensions import db
from models.category import Category
from models.user import AuditLog
from models.rule import Rule
from services.auth_service import admin_required, current_user

rules_bp = Blueprint("rules", __name__)


@rules_bp.get("/categories")
def list_categories():
    categories = Category.query.filter_by(active=True).order_by(Category.name).all()
    return jsonify({
        "items": [category.to_dict() for category in categories],
        "total": len(categories),
    })


@rules_bp.get("/rules")
def list_rules():
    category = request.args.get("category")
    query = Rule.query
    if category:
        query = query.filter_by(category=category)
    rules = query.order_by(Rule.category, Rule.field_name).all()
    return jsonify({
        "items": [rule.to_dict() for rule in rules],
        "total": len(rules),
    })


@rules_bp.post("/rules")
@admin_required
def create_rule():
    payload = request.get_json(silent=True) or {}
    required_fields = ["rule_code", "category", "field_name", "requirement_description"]
    missing_fields = [field for field in required_fields if not payload.get(field)]
    if missing_fields:
        return jsonify({"error": "Missing required fields.", "fields": missing_fields}), 400

    if Rule.query.filter_by(rule_code=payload["rule_code"]).first():
        return jsonify({"error": "rule_code must be unique."}), 409

    if not payload.get("source_reference") or not payload.get("rule_version"):
        return jsonify({"error": "source_reference and rule_version are required for traceability."}), 400

    if not Category.query.filter_by(code=payload["category"], active=True).first():
        return jsonify({"error": "Unknown or inactive category."}), 400

    rule = Rule(
        rule_code=payload["rule_code"],
        category=payload["category"],
        field_name=payload["field_name"],
        requirement_description=payload["requirement_description"],
        mandatory=payload.get("mandatory", True),
        validation_type=payload.get("validation_type", "presence"),
        validation_expression=payload.get("validation_expression"),
        severity=payload.get("severity", "standard"),
        source_reference=payload.get("source_reference"),
        rule_version=payload.get("rule_version", "0.1"),
        active=payload.get("active", True),
    )
    db.session.add(rule)
    db.session.flush()
    db.session.add(AuditLog(
        user_id=current_user().id,
        action="create",
        entity_type="rule",
        entity_id=str(rule.id),
        new_value=rule.to_dict(),
        reason=payload.get("reason"),
    ))
    db.session.commit()
    return jsonify(rule.to_dict()), 201


@rules_bp.put("/rules/<int:rule_id>")
@admin_required
def update_rule(rule_id: int):
    rule = db.session.get(Rule, rule_id)
    if rule is None:
        return jsonify({"error": "Rule not found."}), 404
    payload = request.get_json(silent=True) or {}
    previous = rule.to_dict()
    editable_fields = ["requirement_description", "mandatory", "validation_type", "validation_expression", "severity", "source_reference", "rule_version", "active"]
    for field in editable_fields:
        if field in payload:
            setattr(rule, field, payload[field])
    if "category" in payload:
        if not Category.query.filter_by(code=payload["category"], active=True).first():
            return jsonify({"error": "Unknown or inactive category."}), 400
        rule.category = payload["category"]
    db.session.flush()
    db.session.add(AuditLog(user_id=current_user().id, action="update", entity_type="rule", entity_id=str(rule.id), previous_value=previous, new_value=rule.to_dict(), reason=payload.get("reason")))
    db.session.commit()
    return jsonify(rule.to_dict())


@rules_bp.delete("/rules/<int:rule_id>")
@admin_required
def disable_rule(rule_id: int):
    rule = db.session.get(Rule, rule_id)
    if rule is None:
        return jsonify({"error": "Rule not found."}), 404
    previous = rule.to_dict()
    rule.active = False
    db.session.flush()
    db.session.add(AuditLog(user_id=current_user().id, action="disable", entity_type="rule", entity_id=str(rule.id), previous_value=previous, new_value=rule.to_dict(), reason=request.args.get("reason")))
    db.session.commit()
    return jsonify(rule.to_dict())
