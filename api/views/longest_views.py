# api/views/longest_views.py
import logging
from flask import Blueprint, request, Response, jsonify
from typing import Optional
from api.models.longest_model import get_longest_lines
from api.utils.response import negotiate_content_type, to_xml

longest_bp = Blueprint("longest", __name__)
logger = logging.getLogger(__name__)

@longest_bp.get("/lines/longest")
def longest_lines():
    ctype = negotiate_content_type(request)
    file_name = request.args.get("file_name")

    # Determine the default limit based on whether a file_name is provided
    default_limit = 20 if file_name else 100

    try:
        # Use the provided limit, or fall back to the calculated default
        limit = int(request.args.get("limit", default_limit))
    except (ValueError, TypeError):
        # If parsing fails (e.g., limit="abc"), use the default
        limit = default_limit

    try:
        # Clamp the final limit to the allowed range
        limit = max(1, min(1000, limit))
        items = get_longest_lines(limit=limit, file_name=file_name)
    except ValueError as ve:
        # Not found / no files -> 404 style response
        logger.warning(f"Could not get longest lines: {ve}")
        return jsonify({"detail": str(ve)}), 404
    except Exception:
        logger.exception("An unhandled error occurred while getting longest lines.")
        return jsonify({"detail": "Internal server error"}), 500

    # text/plain: return just the lines joined by '\n'
    if ctype == "text/plain":
        body = "\n".join(item["line"] for item in items)
        return Response(body, mimetype="text/plain")

    # application/xml or application/json: include metadata
    if ctype == "application/xml":
        return Response(to_xml(items, root="longest_lines", item_name="line_item"), mimetype="application/xml")

    # default JSON
    return jsonify(items)