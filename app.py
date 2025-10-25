import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, request

from api.views.upload_views import upload_bp
from api.views.line_views import lines_bp
from api.views.longest_views import longest_bp

# --- Logging Setup ---
# Ensure log directory exists
if not os.path.exists("logs"):
    os.mkdir("logs")

# Set up a file handler with rotation
file_handler = RotatingFileHandler("logs/app.log", maxBytes=10240, backupCount=10)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
)
file_handler.setLevel(logging.INFO)

# --- App Creation ---
app = Flask(__name__)

# Add the handler to the app's logger and werkzeug's logger
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
logging.getLogger("werkzeug").addHandler(file_handler)

app.register_blueprint(upload_bp)
app.register_blueprint(lines_bp)
app.register_blueprint(longest_bp)

if __name__ == "__main__":
    app.logger.info("Application starting up...")
    app.run(host="127.0.0.1", port=8000, debug=True)