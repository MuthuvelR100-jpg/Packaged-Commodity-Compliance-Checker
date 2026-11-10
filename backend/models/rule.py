from datetime import date

from extensions import db


class Rule(db.Model):
    __tablename__ = "rules"

    id = db.Column(db.Integer, primary_key=True)
    rule_code = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(100), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    requirement_description = db.Column(db.Text, nullable=False)
    mandatory = db.Column(db.Boolean, nullable=False, default=True)
    validation_type = db.Column(db.String(50), nullable=False, default="presence")
    validation_expression = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(30), nullable=False, default="standard")
    effective_from = db.Column(db.Date, nullable=True, default=date.today)
    effective_to = db.Column(db.Date, nullable=True)
    source_reference = db.Column(db.Text, nullable=True)
    rule_version = db.Column(db.String(50), nullable=False, default="0.1")
    active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "rule_code": self.rule_code,
            "category": self.category,
            "field_name": self.field_name,
            "requirement_description": self.requirement_description,
            "mandatory": self.mandatory,
            "validation_type": self.validation_type,
            "validation_expression": self.validation_expression,
            "severity": self.severity,
            "effective_from": self.effective_from.isoformat() if self.effective_from else None,
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "source_reference": self.source_reference,
            "rule_version": self.rule_version,
            "active": self.active,
        }
