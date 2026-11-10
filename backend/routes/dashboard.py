from flask import Blueprint, jsonify

from sqlalchemy import func

from extensions import db
from models.inspection import Inspection

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/dashboard")
def dashboard_summary():
    total = Inspection.query.count()
    average_score = db.session.query(func.avg(Inspection.score)).scalar()
    status_counts = {
        status: Inspection.query.filter_by(status=status).count()
        for status in ("COMPLIANT", "NEEDS_REVIEW", "NON_COMPLIANT")
    }
    return jsonify({
        "total_inspections": total,
        "compliant": status_counts["COMPLIANT"],
        "needs_review": status_counts["NEEDS_REVIEW"],
        "non_compliant": status_counts["NON_COMPLIANT"],
        "average_score": float(average_score) if average_score is not None else None,
    })
