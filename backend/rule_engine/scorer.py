from typing import Any


APPLICABLE_STATUSES = {"PASS", "FAIL", "REVIEW"}


def score_validation(validation: dict[str, Any]) -> dict[str, Any]:
    results = validation.get("results", [])
    applicable = [result for result in results if result.get("status") in APPLICABLE_STATUSES]
    passed = [result for result in applicable if result.get("status") == "PASS"]
    failed = [result for result in applicable if result.get("status") == "FAIL"]
    review = [result for result in applicable if result.get("status") == "REVIEW"]
    critical_failures = [
        result for result in failed
        if result.get("mandatory") and str(result.get("severity", "")).lower() == "critical"
    ]

    score = round((len(passed) / len(applicable)) * 100, 2) if applicable else None
    if not applicable:
        status = "REVIEW"
        message = "No applicable validation results are available; manual verification is required."
    elif failed:
        status = "NON_COMPLIANT"
        message = "One or more mandatory declarations failed validation."
    elif review:
        status = "NEEDS_REVIEW"
        message = "All detected failures are unresolved review items."
    else:
        status = "COMPLIANT"
        message = "All applicable configured rules passed validation."

    return {
        "category": validation.get("category"),
        "score": score,
        "status": status,
        "message": message,
        "rule_count": len(results),
        "applicable_count": len(applicable),
        "passed_count": len(passed),
        "failed_count": len(failed),
        "review_count": len(review),
        "not_applicable_count": len(results) - len(applicable),
        "critical_failures": critical_failures,
        "failed_fields": [result.get("field_name") for result in failed],
        "review_fields": [result.get("field_name") for result in review],
        "rule_versions": validation.get("rule_versions", []),
    }
