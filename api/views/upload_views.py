import os
import logging
from flask import Blueprint, request, jsonify
from api.models.file_model import handle_upload
from config import settings

upload_bp = Blueprint("upload", __name__)
logger = logging.getLogger(__name__)

@upload_bp.post("/files")
def upload_file():
    """API View: receives multipart, parses, validates, then delegates to model."""
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"detail": "No file provided"}), 400

    # Sanitize filename to prevent path traversal attacks
    filename = os.path.basename(f.filename)
    if not filename:
        return jsonify({"detail": "Invalid filename provided"}), 400

    # Validate file extension
    if settings.ALLOWED_EXTENSIONS:
        _, ext = os.path.splitext(filename)
        if ext not in settings.ALLOWED_EXTENSIONS:
            return jsonify({"detail": f"File extension '{ext}' is not allowed."}), 400

    try:
        result = handle_upload(file_storage=f, filename=filename)
        return jsonify(result), 200
    except ValueError as ve:
        logger.warning(f"Validation error during upload: {ve}")
        return jsonify({"detail": str(ve)}), 400
    except Exception:
        logger.exception("An unhandled error occurred during file upload.")
        return jsonify({"detail": "Internal server error"}), 500
