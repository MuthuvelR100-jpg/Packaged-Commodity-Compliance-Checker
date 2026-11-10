from flask import Blueprint, current_app, jsonify, request, send_file

from extensions import db
from models.inspection import Declaration, Inspection
from services.extraction_service import extract_fields
from services.image_service import ImageProcessingError, preprocess_package_image
from services.ocr_service import OCRProcessingError, OCRUnavailableError, extract_text
from services.report_service import generate_inspection_report
from rule_engine.validator import validate_extractions
from rule_engine.scorer import score_validation
from services.upload_service import UploadValidationError, save_package_image
from services.auth_service import admin_required

inspection_bp = Blueprint("inspection", __name__)


@inspection_bp.post("/upload")
def upload_image():
    uploaded_file = request.files.get("image")
    try:
        image = save_package_image(uploaded_file, current_app.config["UPLOAD_FOLDER"])
    except UploadValidationError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({
        "message": "Image uploaded successfully.",
        "image": image,
        "processing": "pending",
    }), 201


@inspection_bp.post("/preprocess")
def preprocess_image():
    payload = request.get_json(silent=True) or {}
    try:
        result = preprocess_package_image(
            payload.get("filename"),
            current_app.config["UPLOAD_FOLDER"],
        )
    except ImageProcessingError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({
        "message": "Image preprocessing completed.",
        "processing": result,
    }), 200


@inspection_bp.post("/ocr")
def run_ocr():
    payload = request.get_json(silent=True) or {}
    try:
        result = extract_text(
            payload.get("filename"),
            current_app.config["UPLOAD_FOLDER"],
        )
    except OCRUnavailableError as error:
        return jsonify({"error": str(error), "code": "OCR_UNAVAILABLE"}), 503
    except OCRProcessingError as error:
        return jsonify({"error": str(error), "code": "OCR_FAILED"}), 422

    return jsonify({"message": "OCR completed.", "ocr": result}), 200


@inspection_bp.post("/extract")
def extract_declarations():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text")
    if not isinstance(text, str):
        return jsonify({"error": "A text string is required."}), 400

    return jsonify({
        "message": "Declaration fields extracted.",
        "extraction": extract_fields(text, payload.get("detections")),
    }), 200


@inspection_bp.post("/validate")
def validate_declarations():
    payload = request.get_json(silent=True) or {}
    category = payload.get("category")
    fields = payload.get("fields")
    if not isinstance(category, str) or not category.strip():
        return jsonify({"error": "A product category is required."}), 400
    if not isinstance(fields, dict):
        return jsonify({"error": "Extracted fields must be an object."}), 400

    return jsonify({
        "message": "Declaration validation completed.",
        "validation": validate_extractions(category, fields),
    }), 200


@inspection_bp.post("/score")
def score_declarations():
    payload = request.get_json(silent=True) or {}
    validation = payload.get("validation")
    if not isinstance(validation, dict):
        return jsonify({"error": "Validation results must be an object."}), 400

    return jsonify({
        "message": "Compliance score calculated.",
        "score": score_validation(validation),
    }), 200


@inspection_bp.get("/inspections")
def list_inspections():
    query = Inspection.query
    search = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip().upper()
    category = request.args.get("category", "").strip()
    if search:
        query = query.filter(Inspection.product_name.ilike(f"%{search}%"))
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    inspections = query.order_by(Inspection.created_at.desc()).all()
    return jsonify({
        "items": [inspection.to_dict() for inspection in inspections],
        "total": len(inspections),
    })


@inspection_bp.post("/inspection")
def create_inspection():
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON."}), 415

    payload = request.get_json(silent=True) or {}
    inspection = Inspection(
        product_name=payload.get("product_name"),
        category=payload.get("category"),
        status=payload.get("status", "NEEDS_REVIEW"),
        score=payload.get("score"),
        image_path=payload.get("image_path"),
        processed_image_path=payload.get("processed_image_path"),
        ocr_detections=payload.get("ocr_detections"),
        rule_version=payload.get("rule_version"),
    )
    db.session.add(inspection)
    db.session.flush()

    declarations = payload.get("declarations", [])
    for declaration in declarations:
        db.session.add(Declaration(
            inspection_id=inspection.id,
            field_name=declaration.get("field_name", ""),
            extracted_value=declaration.get("extracted_value"),
            status=declaration.get("status", "REVIEW"),
            ocr_confidence=declaration.get("ocr_confidence"),
            explanation=declaration.get("explanation"),
        ))

    db.session.commit()
    return jsonify(inspection.to_dict(include_declarations=True)), 201


@inspection_bp.get("/inspection/<inspection_id>")
def get_inspection(inspection_id: str):
    inspection = db.session.get(Inspection, inspection_id)
    if inspection is None:
        return jsonify({"error": "Inspection not found."}), 404
    return jsonify(inspection.to_dict(include_declarations=True))


@inspection_bp.delete("/inspection/<inspection_id>")
@admin_required
def delete_inspection(inspection_id: str):
    inspection = db.session.get(Inspection, inspection_id)
    if inspection is None:
        return jsonify({"error": "Inspection not found."}), 404
    db.session.delete(inspection)
    db.session.commit()
    return jsonify({"message": "Inspection deleted.", "inspection_id": inspection_id}), 200


@inspection_bp.get("/report/<inspection_id>")
def download_report(inspection_id: str):
    inspection = db.session.get(Inspection, inspection_id)
    if inspection is None:
        return jsonify({"error": "Inspection not found."}), 404

    report_path = generate_inspection_report(
        inspection,
        current_app.config["REPORT_FOLDER"],
        current_app.config["UPLOAD_FOLDER"],
    )
    return send_file(report_path, as_attachment=True, download_name=report_path.name, mimetype="application/pdf")
