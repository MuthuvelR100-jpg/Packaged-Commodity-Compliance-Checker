from pathlib import Path
import io
import json

import cv2
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


DISCLAIMER = (
    "This report is an automated compliance screening result and should not be treated "
    "as a legally binding determination. Final legal verification should be performed "
    "by the competent authority/authorized professional."
)


def _safe_image_path(image_path: str | None, upload_folder: str) -> Path | None:
    if not image_path:
        return None
    upload_root = Path(upload_folder).resolve()
    candidate = (upload_root / image_path).resolve()
    if candidate.parent != upload_root or not candidate.is_file():
        return None
    return candidate


def _display(value) -> str:
    return str(value) if value not in (None, "") else "Not available"


def _draw_ocr_bounding_boxes(image_path: Path, detections: list[dict]) -> bytes | None:
    """Draw OCR bounding boxes on the image and return as PNG bytes for PDF."""
    if not detections:
        return None
    try:
        image = cv2.imread(str(image_path))
        if image is None:
            return None
        
        for det in detections:
            bbox = det.get("bbox")
            confidence = det.get("confidence")
            text = det.get("text", "")
            if not bbox:
                continue
            
            # Convert bbox to integer points
            pts = []
            for point in bbox:
                pts.append([int(point[0]), int(point[1])])
            pts = cv2.convexHull(np.array(pts, dtype=np.int32))
            
            # Color based on confidence: green for high, yellow for medium, red for low
            if confidence is None:
                color = (0, 165, 255)  # orange
            elif confidence >= 0.8:
                color = (0, 200, 0)  # green
            elif confidence >= 0.6:
                color = (0, 200, 200)  # yellow
            else:
                color = (0, 0, 200)  # red
            
            cv2.polylines(image, [pts], True, color, 2)
            
            # Add confidence label
            if confidence is not None:
                label = f"{confidence:.2f}"
                x, y = pts[0][0]
                cv2.putText(image, label, (int(x), int(y) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
        
        # Encode to PNG bytes
        _, buffer = cv2.imencode('.png', image)
        return buffer.tobytes()
    except Exception:
        return None


def generate_inspection_report(inspection, report_folder: str, upload_folder: str) -> Path:
    reports_root = Path(report_folder).resolve()
    reports_root.mkdir(parents=True, exist_ok=True)
    report_path = reports_root / f"inspection-{inspection.id}.pdf"

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    body_style = styles["BodyText"]
    body_style.fontSize = 9
    body_style.leading = 12

    document = SimpleDocTemplate(
        str(report_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Inspection Report {inspection.id}",
        author="Civic Lens",
    )
    story = [
        Paragraph("Civic Lens", title_style),
        Paragraph("Packaged Commodity Compliance Screening Report", heading_style),
        Spacer(1, 5 * mm),
    ]

    # Original uploaded image
    original_image = _safe_image_path(inspection.image_path, upload_folder)
    if original_image:
        report_image = Image(str(original_image), width=70 * mm, height=55 * mm, kind="proportional")
        story.extend([Paragraph("Original Uploaded Image", body_style), report_image, Spacer(1, 5 * mm)])

# Processed image with OCR bounding boxes (evidence)
    processed_image = _safe_image_path(inspection.processed_image_path, upload_folder)
    ocr_detections = getattr(inspection, 'ocr_detections', None) or []
    
    if processed_image and processed_image.exists():
        # Try to draw OCR bounding boxes on the processed image
        evidence_image_bytes = None
        if ocr_detections:
            evidence_image_bytes = _draw_ocr_bounding_boxes(processed_image, ocr_detections)
        
        if evidence_image_bytes:
            # Use BytesIO to keep image in memory for reportlab
            from io import BytesIO
            evidence_io = BytesIO(evidence_image_bytes)
            report_image = Image(evidence_io, width=70 * mm, height=55 * mm, kind="proportional")
            story.extend([Paragraph("Processed Image with OCR Detections (Evidence)", body_style), report_image, Spacer(1, 5 * mm)])
        else:
            # Fallback: just show the processed image
            try:
                report_image = Image(str(processed_image), width=70 * mm, height=55 * mm, kind="proportional")
                story.extend([Paragraph("Processed Image (OCR Input)", body_style), report_image, Spacer(1, 5 * mm)])
            except Exception:
                pass

    metadata = [
        ["Inspection ID", _display(inspection.id)],
        ["Date/time", _display(inspection.created_at.isoformat() if inspection.created_at else None)],
        ["Product", _display(inspection.product_name)],
        ["Category", _display(inspection.category)],
        ["Status", _display(inspection.status)],
        ["Compliance score", f"{inspection.score}%" if inspection.score is not None else "Not calculated"],
        ["Rule-set version", _display(inspection.rule_version)],
    ]
    metadata_table = Table(metadata, colWidths=[42 * mm, 125 * mm])
    metadata_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e9f3e1")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#30443b")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d7e3d7")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([metadata_table, Spacer(1, 7 * mm), Paragraph("Extracted declarations", heading_style)])

    declaration_rows = [["Field", "Extracted value", "Status", "OCR confidence", "Explanation"]]
    for declaration in inspection.declarations:
        declaration_rows.append([
            declaration.field_name.replace("_", " ").title(),
            _display(declaration.extracted_value),
            _display(declaration.status),
            f"{declaration.ocr_confidence:.2f}" if declaration.ocr_confidence is not None else "Not available",
            _display(declaration.explanation),
        ])
    if len(declaration_rows) == 1:
        declaration_rows.append(["No declarations", "Not available", "REVIEW", "Not available", "No declaration records were saved."])

    declaration_table = Table(declaration_rows, colWidths=[30 * mm, 34 * mm, 23 * mm, 25 * mm, 55 * mm], repeatRows=1)
    declaration_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#174c3b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d7e3d7")),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8f4")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([declaration_table, Spacer(1, 8 * mm), Paragraph("Important limitation", heading_style), Paragraph(DISCLAIMER, body_style)])
    document.build(story)
    return report_path
