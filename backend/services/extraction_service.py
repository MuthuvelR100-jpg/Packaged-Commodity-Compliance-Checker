import re
from typing import Any


FIELD_ORDER = (
    "product_name",
    "manufacturer_name",
    "manufacturer_address",
    "packer_name",
    "packer_address",
    "importer_name",
    "importer_address",
    "net_quantity",
    "mrp",
    "manufacturing_date",
    "packing_date",
    "import_date",
    "consumer_care_name",
    "consumer_care_phone",
    "consumer_care_email",
    "country_of_origin",
)

FIELD_PATTERNS = {
    "net_quantity": re.compile(r"(?:net\s*(?:qty|quantity|wt|weight)|qty|n\.?\s*qty)\s*[:\-]?\s*([\w.\s]+(?:g|kg|ml|l|lb|oz))", re.I),
    "mrp": re.compile(r"(?:m\.?\s*r\.?\s*p\.?|maximum\s*retail\s*price)\s*(?:rs\.?|₹|inr)?\s*[:\-]?\s*([₹]?\s*\d+(?:[.,]\d{1,2})?)", re.I),
    "manufacturing_date": re.compile(r"(?:mfd|mfg|manufactur(?:ed|ing))\s*(?:date)?\s*[:\-]?\s*([\d./-]{4,10}|[A-Za-z]{3,9}\s+\d{4})", re.I),
    "packing_date": re.compile(r"(?:pkd|packed|packing)\s*(?:date)?\s*[:\-]?\s*([\d./-]{4,10}|[A-Za-z]{3,9}\s+\d{4})", re.I),
    "import_date": re.compile(r"(?:imported|import)\s*(?:date)?\s*[:\-]?\s*([\d./-]{4,10}|[A-Za-z]{3,9}\s+\d{4})", re.I),
    "consumer_care_phone": re.compile(r"(?:customer|consumer)\s*care[^\n]*?(?:ph(?:one)?|tel|call)\s*[:\-]?\s*(\+?\d[\d\s().-]{7,})", re.I),
    "consumer_care_email": re.compile(r"(?:customer|consumer)\s*care[^\n]*?([\w.+-]+@[\w.-]+\.[A-Za-z]{2,})", re.I),
    "country_of_origin": re.compile(r"(?:country\s*of\s*origin|made\s*in)\s*[:\-]?\s*([^\n]+)", re.I),
    "manufacturer_name": re.compile(r"(?:mfd\.?\s*by|manufactured\s*by|manufacturer|mfr)\s*[:\-]?\s*([^\n]+)", re.I),
    "manufacturer_address": re.compile(r"(?:mfd\.?\s*by|manufactured\s*by|manufacturer|mfr)[^\n]*\n\s*(?:address\s*[:\-]?\s*)?([^\n]+)", re.I),
}

LABEL_PATTERNS = {
    "packer_name": re.compile(r"(?:packed|packers?)\s*by\s*[:\-]?\s*([^\n]+)", re.I),
    "packer_address": re.compile(r"(?:packed|packers?)\s*by[^\n]*\n\s*(?:address\s*[:\-]?\s*)?([^\n]+)", re.I),
    "importer_name": re.compile(r"(?:imported|importers?)\s*by\s*[:\-]?\s*([^\n]+)", re.I),
    "importer_address": re.compile(r"(?:imported|importers?)\s*by[^\n]*\n\s*(?:address\s*[:\-]?\s*)?([^\n]+)", re.I),
    "consumer_care_name": re.compile(r"(?:customer|consumer)\s*care\s*[:\-]?\s*([^\n@]+)", re.I),
}

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"(?:(?:\+?91|0)?[\s-]?)?(?:\d{2,5}[\s-]?){2,}\d{3,4}")


def normalize_ocr_text(text: str) -> str:
    normalized = text or ""
    normalized = normalized.replace("M.R.P", "MRP").replace("M R P", "MRP")
    normalized = normalized.replace("Rs.", "Rs").replace("R.s", "Rs")
    normalized = re.sub(r"\bN[e3]t\s+(?:0ty|Qtv|Wt)\b", "Net Qty", normalized, flags=re.I)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    return normalized.strip()


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip(" :;-\t"))


def _confidence_for(value: str, detections: list[dict[str, Any]]) -> float | None:
    if value is None:
        return None
    value_lower = value.lower()
    matches = [item.get("confidence") for item in detections if value_lower in str(item.get("text", "")).lower() and item.get("confidence") is not None]
    return round(max(matches), 4) if matches else None


def _confidence_for_words(value: str, detections: list[dict[str, Any]]) -> float | None:
    """Find confidence by matching individual words from value to detection text."""
    if value is None:
        return None
    value_words = [w.lower() for w in value.split() if len(w) > 2]
    if not value_words:
        return None
    best = 0.0
    found = False
    for item in detections:
        det_text = str(item.get("text", "")).lower()
        det_conf = item.get("confidence")
        if det_conf is None:
            continue
        matched_words = sum(1 for w in value_words if w in det_text)
        if matched_words > 0:
            ratio = matched_words / len(value_words)
            if ratio > 0.3:
                best = max(best, det_conf * ratio)
                found = True
    return round(best, 4) if found else None


def _field_result(field_name: str, value: str | None, confidence: float | None, candidates: list[str] | None = None) -> dict:
    if candidates and len(candidates) > 1:
        return {"field_name": field_name, "value": None, "status": "ambiguous", "confidence": confidence, "candidates": candidates, "message": "Multiple possible values were detected; manual verification is required."}
    if value:
        return {"field_name": field_name, "value": value, "status": "detected", "confidence": confidence, "candidates": [], "message": "Value detected by OCR text extraction."}
    return {"field_name": field_name, "value": None, "status": "missing", "confidence": None, "candidates": [], "message": "No matching declaration was detected in the OCR text."}


def extract_fields(text: str, detections: list[dict[str, Any]] | None = None) -> dict:
    normalized = normalize_ocr_text(text)
    available_detections = detections or []
    extracted = {}

    for field_name in FIELD_ORDER:
        pattern = FIELD_PATTERNS.get(field_name) or LABEL_PATTERNS.get(field_name)
        matches = [_clean(match.group(1)) for match in pattern.finditer(normalized)] if pattern else []
        unique_matches = list(dict.fromkeys(item for item in matches if item))
        value = unique_matches[0] if len(unique_matches) == 1 else None
        confidence = _confidence_for(value, available_detections) if value else None
        extracted[field_name] = _field_result(field_name, value, confidence, unique_matches if len(unique_matches) > 1 else None)

    if not extracted["consumer_care_email"]["value"]:
        email = EMAIL_PATTERN.search(normalized)
        if email:
            extracted["consumer_care_email"] = _field_result("consumer_care_email", email.group(0), _confidence_for(email.group(0), available_detections))
    if not extracted["consumer_care_phone"]["value"]:
        phone = PHONE_PATTERN.search(normalized)
        if phone:
            extracted["consumer_care_phone"] = _field_result("consumer_care_phone", _clean(phone.group(0)), _confidence_for(phone.group(0), available_detections))

    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    labelled_values = {item["value"] for item in extracted.values() if item["value"]}
    
    # Extract product name - try to find a clean product name from the first few lines
    if lines and not extracted["product_name"]["value"]:
        declaration_keywords = {'net', 'qty', 'quantity', 'mrp', 'mfd', 'mfg', 'manufact', 'exp', 'expiry', 'customer', 'consumer', 'care', 'address', 'manufactured', 'packed', 'imported', 'email', 'phone', 'tel', 'call', 'made in', 'country', 'origin', 'ingredients', 'energy', 'protein', 'fat', 'carbohydrate', 'sodium', 'sugar', 'nutritional', 'information', 'approx', 'per100g', 'per', '100g', 'kcal', 'mg', 'of', 'which', 'sugars', 'saturated', 'trans'}
        likely_name = None
        for line in lines[:8]:
            if len(line) > 120:
                continue
            if line in labelled_values:
                continue
            words = line.lower().split()
            if any(kw in words for kw in declaration_keywords):
                continue
            # Skip lines that are just numbers or very short
            if len(line) < 3:
                continue
            likely_name = line
            break
        
        if likely_name is None and lines:
            likely_name = next((line for line in lines[:5] if line not in labelled_values and len(line) <= 120 and len(line) >= 3), None)
        
        if likely_name:
            conf = _confidence_for(likely_name, available_detections)
            if conf is None:
                conf = _confidence_for_words(likely_name, available_detections)
            extracted["product_name"] = _field_result("product_name", likely_name, conf)

    # Post-process manufacturer_name to avoid overly long values
    mfr = extracted.get("manufacturer_name")
    if mfr and mfr.get("value") and len(mfr["value"]) > 200:
        short_match = re.search(r"(?:PEPSICO|HINDUSTAN|UNILEVER|NESTLE|ITC|BRITANNIA|PARLE|DABUR|MARICO|EMAMI|GODREJ|TATA|BAJAJ|HERO|MAHINDRA|ASHOK LEYLAND|FORCE MOTORS|EICHER|TVS|ROYAL ENFIELD|BAJAJ AUTO|HERO MOTOCORP)[^\n]{0,50}", mfr["value"], re.I)
        if short_match:
            extracted["manufacturer_name"] = _field_result("manufacturer_name", short_match.group(0).strip(), mfr.get("confidence"))

# Post-process consumer_care_phone to prefer actual phone numbers over license numbers
    phone_field = extracted.get("consumer_care_phone")
    if phone_field and phone_field.get("value"):
        val = phone_field["value"]
        # If the detected value is a long pure digit string (likely license/barcode), try to find a real phone number
        # License numbers are typically 13-14 digits without spaces; phone numbers have spaces/dashes or are shorter
        val_clean = val.replace(" ", "").replace("-", "")
        if re.match(r"^\d{13,}$", val_clean):
            # Search for phone-like patterns in the text
            phone_matches = list(re.finditer(r"(?:(?:\+?91|0)?[\s-]?)?(?:\d{2,5}[\s-]?){2,}\d{3,4}", normalized))
            for match in phone_matches:
                candidate = _clean(match.group(0))
                cand_clean = candidate.replace(" ", "").replace("-", "")
                # Prefer candidates that have spaces/dashes (not pure digit strings) and are not 13+ digits
                if len(candidate) >= 8 and (not re.match(r"^\d{13,}$", cand_clean) or " " in candidate or "-" in candidate):
                    extracted["consumer_care_phone"] = _field_result("consumer_care_phone", candidate, _confidence_for(candidate, available_detections))
                    break

    return {
        "normalized_text": normalized,
        "fields": extracted,
        "field_count": len(extracted),
        "detected_count": sum(item["status"] == "detected" for item in extracted.values()),
        "ambiguous_count": sum(item["status"] == "ambiguous" for item in extracted.values()),
        "message": "Structured fields extracted from OCR text.",
    }