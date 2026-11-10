from datetime import datetime, timezone
import uuid

from extensions import db


class Inspection(db.Model):
    __tablename__ = "inspections"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_name = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(30), nullable=False, default="NEEDS_REVIEW")
    score = db.Column(db.Float, nullable=True)
    image_path = db.Column(db.String(500), nullable=True)
    processed_image_path = db.Column(db.String(500), nullable=True)
    ocr_detections = db.Column(db.JSON, nullable=True)
    rule_version = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    declarations = db.relationship("Declaration", back_populates="inspection", cascade="all, delete-orphan")

    def to_dict(self, include_declarations: bool = False) -> dict:
        data = {
            "id": self.id,
            "product_name": self.product_name,
            "category": self.category,
            "status": self.status,
            "score": self.score,
            "rule_version": self.rule_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_declarations:
            data["declarations"] = [declaration.to_dict() for declaration in self.declarations]
        return data


class Declaration(db.Model):
    __tablename__ = "declarations"

    id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.String(36), db.ForeignKey("inspections.id"), nullable=False, index=True)
    field_name = db.Column(db.String(100), nullable=False)
    extracted_value = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="REVIEW")
    ocr_confidence = db.Column(db.Float, nullable=True)
    explanation = db.Column(db.Text, nullable=True)

    inspection = db.relationship("Inspection", back_populates="declarations")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "field_name": self.field_name,
            "extracted_value": self.extracted_value,
            "status": self.status,
            "ocr_confidence": self.ocr_confidence,
            "explanation": self.explanation,
        }
