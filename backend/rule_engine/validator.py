from datetime import date
import re
from typing import Any

from models.rule import Rule


LOW_CONFIDENCE_THRESHOLD = 0.75


def _active_rules(category: str) -> list[Rule]:
    today = date.today()
    return Rule.query.filter(
        Rule.category == category,
        Rule.active.is_(True),
        (Rule.effective_from.is_(None) | (Rule.effective_from <= today)),
        (Rule.effective_to.is_(None) | (Rule.effective_to >= today)),
    ).order_by(Rule.field_name).all()


def _validate_rule(rule: Rule, extracted_field: dict[str, Any] | None) -> dict[str, Any]:
    value = (extracted_field or {}).get("value")
    extraction_status = (extracted_field or {}).get("status", "missing")
    confidence = (extracted_field or {}).get("confidence")
    base = {
        "rule_id": rule.id,
        "rule_code": rule.rule_code,
        "field_name": rule.field_name,
        "requirement_description": rule.requirement_description,
        "mandatory": rule.mandatory,
        "severity": rule.severity,
        "source_reference": rule.source_reference,
        "rule_version": rule.rule_version,
        "confidence": confidence,
    }

    if not rule.mandatory and extraction_status == "missing":
        return {**base, "status": "NOT_APPLICABLE", "message": "Optional declaration was not detected."}
    if extraction_status in {"missing", "ambiguous"} or not value:
        status = "FAIL" if rule.mandatory and extraction_status == "missing" else "REVIEW"
        message = "Required declaration was not detected." if status == "FAIL" else "Multiple or uncertain values require manual verification."
        return {**base, "status": status, "message": message}
    if confidence is None or confidence < LOW_CONFIDENCE_THRESHOLD:
        return {**base, "status": "REVIEW", "message": "Declaration detected, but OCR confidence is low."}

    if rule.validation_type == "regex":
        if not rule.validation_expression:
            return {**base, "status": "REVIEW", "message": "Rule has no validation expression; manual verification is required."}
        try:
            valid = re.fullmatch(rule.validation_expression, str(value), flags=re.IGNORECASE) is not None
        except re.error:
            return {**base, "status": "REVIEW", "message": "Rule validation expression is invalid; manual verification is required."}
        if not valid:
            return {**base, "status": "FAIL", "message": "Detected value does not match the configured rule expression."}

    return {**base, "status": "PASS", "message": "Declaration detected and passed the configured validation."}


def validate_extractions(category: str, fields: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rules = _active_rules(category)
    if not rules:
        return {
            "category": category,
            "rule_count": 0,
            "results": [],
            "status": "REVIEW",
            "message": "No active rules are configured for this category; manual verification is required.",
            "rule_versions": [],
        }

    results = [_validate_rule(rule, fields.get(rule.field_name)) for rule in rules]
    statuses = {result["status"] for result in results}
    if "FAIL" in statuses:
        overall_status = "NON_COMPLIANT"
    elif "REVIEW" in statuses:
        overall_status = "NEEDS_REVIEW"
    else:
        overall_status = "COMPLIANT"

    return {
        "category": category,
        "rule_count": len(results),
        "results": results,
        "status": overall_status,
        "message": "Validation completed against active, versioned rules.",
        "rule_versions": sorted({result["rule_version"] for result in results}),
    }
