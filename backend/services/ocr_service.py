from pathlib import Path
from threading import Lock
from typing import Any


class OCRUnavailableError(RuntimeError):
    pass


class OCRProcessingError(RuntimeError):
    pass


_engine = None
_engine_lock = Lock()


def _load_paddle_engine():
    global _engine
    if _engine is not None:
        return _engine

    with _engine_lock:
        if _engine is None:
            try:
                from paddleocr import PaddleOCR
            except ImportError as error:
                raise OCRUnavailableError(
                    "PaddleOCR is not installed. Install paddleocr and a compatible PaddlePaddle runtime."
                ) from error

            try:
                _engine = PaddleOCR(
                    lang="en",
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                    enable_mkldnn=False,
                    det_limit_side_len=960,
                    det_limit_type="max",
                )
            except Exception as error:
                raise OCRUnavailableError(f"PaddleOCR could not be initialized: {error}") from error
    return _engine


def _result_value(result: Any, key: str):
    if isinstance(result, dict):
        return result.get(key, [])
    try:
        return result[key]
    except (KeyError, IndexError, TypeError):
        return getattr(result, key, [])


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        value = value.tolist()
    return list(value)


def _normalise_box(box: Any) -> list[list[float]]:
    points = _as_list(box)
    return [[float(point[0]), float(point[1])] for point in points]


def _normalise_prediction(result: Any) -> list[dict]:
    texts = _as_list(_result_value(result, "rec_texts"))
    scores = _as_list(_result_value(result, "rec_scores"))
    boxes = _as_list(_result_value(result, "dt_polys"))
    detections = []
    for index, text in enumerate(texts):
        value = str(text).strip()
        if not value:
            continue
        confidence = float(scores[index]) if index < len(scores) else None
        box = _normalise_box(boxes[index]) if index < len(boxes) else []
        detections.append({
            "text": value,
            "confidence": round(confidence, 4) if confidence is not None else None,
            "bbox": box,
        })
    return detections


def extract_text(filename: str, image_folder: str) -> dict:
    if not filename or Path(filename).name != filename:
        raise OCRProcessingError("Invalid processed image filename.")

    image_root = Path(image_folder).resolve()
    image_path = (image_root / filename).resolve()
    if image_path.parent != image_root or not image_path.is_file():
        raise OCRProcessingError("Processed image was not found.")

    engine = _load_paddle_engine()
    try:
        predictions = engine.predict(str(image_path))
        detections = []
        for prediction in predictions:
            detections.extend(_normalise_prediction(prediction))
    except OCRUnavailableError:
        raise
    except Exception as error:
        raise OCRProcessingError(f"OCR processing failed: {error}") from error

    confidences = [item["confidence"] for item in detections if item["confidence"] is not None]
    return {
        "engine": "PaddleOCR",
        "filename": filename,
        "text": "\n".join(item["text"] for item in detections),
        "detections": detections,
        "detection_count": len(detections),
        "average_confidence": round(sum(confidences) / len(confidences), 4) if confidences else None,
        "message": "No text was detected." if not detections else "Text extracted successfully.",
    }
