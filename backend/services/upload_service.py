from pathlib import Path
import uuid

from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}


class UploadValidationError(ValueError):
    pass


def save_package_image(file: FileStorage, upload_folder: str) -> dict:
    if file is None or not file.filename:
        raise UploadValidationError("An image file is required.")

    original_name = secure_filename(file.filename)
    if not original_name:
        raise UploadValidationError("The uploaded filename is invalid.")

    extension = Path(original_name).suffix.lower().lstrip(".")
    if extension not in ALLOWED_EXTENSIONS:
        raise UploadValidationError("Unsupported image type. Use JPG, JPEG, PNG, or WEBP.")

    try:
        image = Image.open(file.stream)
        image.verify()
        image_format = image.format
    except (UnidentifiedImageError, OSError):
        raise UploadValidationError("The uploaded file is not a valid image.") from None
    finally:
        file.stream.seek(0)

    if image_format not in ALLOWED_FORMATS:
        raise UploadValidationError("The image format could not be verified.")

    verified_extension = ALLOWED_FORMATS[image_format]
    filename = f"{uuid.uuid4().hex}.{verified_extension}"
    destination_folder = Path(upload_folder)
    destination_folder.mkdir(parents=True, exist_ok=True)
    destination = destination_folder / filename
    file.save(destination)

    return {
        "filename": filename,
        "original_filename": original_name,
        "path": str(destination),
        "format": image_format,
    }
