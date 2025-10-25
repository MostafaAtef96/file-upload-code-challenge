# api/views/line_views.py
from flask import Blueprint, request, Response, jsonify
from typing import Optional
from api.models.line_model import fetch_line
from api.utils.response import negotiate_content_type, to_xml
from api.utils.textutils import most_frequent_letter

lines_bp = Blueprint("lines", __name__)

@lines_bp.get("/lines/random")
def get_line():
    ctype = negotiate_content_type(request)
    file_name = request.args.get("file_name")

    try:
        result = fetch_line(file_name=file_name)
    except ValueError as ve:
        return jsonify({"detail": str(ve)}), 404
    except Exception:
        return jsonify({"detail": "Internal server error"}), 500

    # Plain text → return just the line
    if ctype == "text/plain":
        return Response(result["line"], mimetype="text/plain")

    # application/json or application/xml → include metadata
    # Strip whitespace/newlines from the line for cleaner structured output
    line_content = result["line"].strip()
    payload = {
        "file_name": result["file_name"],
        "line_number": result["line_number"],
        "line": line_content,
        "most_frequent_letter": most_frequent_letter(line_content),
    }
    if ctype == "application/xml":
        return Response(to_xml(payload, root="random_line"), mimetype="application/xml")
    return jsonify(payload)


@lines_bp.get("/lines/random/backwards")
def get_line_backwards():
    """Returns a random line from a file, with the line content reversed."""
    ctype = negotiate_content_type(request)
    file_name = request.args.get("file_name")

    try:
        result = fetch_line(file_name=file_name)
    except ValueError as ve:
        return jsonify({"detail": str(ve)}), 404
    except Exception:
        return jsonify({"detail": "Internal server error"}), 500

    line_content = result["line"].strip()
    reversed_line = line_content[::-1]

    if ctype == "text/plain":
        return Response(reversed_line, mimetype="text/plain")

    payload = {
        "file_name": result["file_name"],
        "line_number": result["line_number"],
        "line_reversed": reversed_line,
        "most_frequent_letter": most_frequent_letter(line_content),
    }
    if ctype == "application/xml":
        return Response(to_xml(payload, root="random_line_backwards"), mimetype="application/xml")
    return jsonify(payload)
