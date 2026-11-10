from pathlib import Path
import uuid

import cv2
import numpy as np


class ImageProcessingError(ValueError):
    pass


MAX_PROCESSING_EDGE = 1200
MIN_RELIABLE_EDGE = 500
BLUR_THRESHOLD = 80.0


def _safe_source_path(filename: str, upload_folder: str) -> Path:
    if not filename or Path(filename).name != filename:
        raise ImageProcessingError("Invalid image filename.")

    upload_root = Path(upload_folder).resolve()
    source = (upload_root / filename).resolve()
    if source.parent != upload_root or not source.is_file():
        raise ImageProcessingError("Uploaded image was not found.")
    return source


def preprocess_package_image(filename: str, upload_folder: str) -> dict:
    source = _safe_source_path(filename, upload_folder)
    image = cv2.imread(str(source), cv2.IMREAD_COLOR)
    if image is None:
        raise ImageProcessingError("The stored image could not be read.")

    original_height, original_width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    shortest_edge = min(original_width, original_height)

    scale = min(1.0, MAX_PROCESSING_EDGE / max(original_width, original_height))
    if scale < 1.0:
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Fast denoising using bilateral filter instead of slow fastNlMeansDenoising
    # bilateralFilter is much faster and preserves edges well for OCR
    denoised = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
    
    # CLAHE for contrast enhancement
    enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(denoised)
    
    # Sharpen using unsharp masking (faster than GaussianBlur + addWeighted)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
    sharpened = cv2.filter2D(enhanced, -1, kernel)

    if shortest_edge < MIN_RELIABLE_EDGE or blur_score < BLUR_THRESHOLD / 2:
        quality = "poor"
        quality_message = "Image quality is insufficient for reliable OCR. Please upload a clearer image."
    elif blur_score < BLUR_THRESHOLD:
        quality = "acceptable"
        quality_message = "Image can be processed, but clearer text would improve OCR confidence."
    else:
        quality = "good"
        quality_message = "Image resolution and sharpness are suitable for OCR preprocessing."

    processed_filename = f"processed-{uuid.uuid4().hex}.png"
    processed_path = Path(upload_folder).resolve() / processed_filename
    if not cv2.imwrite(str(processed_path), sharpened):
        raise ImageProcessingError("The processed image could not be saved.")

    processed_height, processed_width = sharpened.shape[:2]
    return {
        "source_filename": source.name,
        "processed_filename": processed_filename,
        "original_dimensions": {"width": original_width, "height": original_height},
        "processed_dimensions": {"width": processed_width, "height": processed_height},
        "blur_score": round(blur_score, 2),
        "quality": quality,
        "quality_message": quality_message,
    }
