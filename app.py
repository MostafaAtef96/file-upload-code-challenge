from flask import Flask
from api.views.upload_views import upload_bp

app = Flask(__name__)
app.register_blueprint(upload_bp)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)