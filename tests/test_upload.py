import io
from app import app

def client():
    app.testing = True
    return app.test_client()

def test_upload_ok(tmp_path, monkeypatch):
    c = client()
    data = {"file": (io.BytesIO(b"hello\nworld\n"), "ok.txt")}
    rv = c.post("/files", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["filename"] == "ok.txt"
    assert body["num_lines"] == 2

def test_missing_file():
    c = client()
    rv = c.post("/files", data={}, content_type="multipart/form-data")
    assert rv.status_code == 400

def test_disallowed_ext(monkeypatch):
    monkeypatch.setattr("config.settings.ALLOWED_EXTENSIONS", {".txt"})
    c = client()
    data = {"file": (io.BytesIO(b"a\n"), "bad.log")}
    rv = c.post("/files", data=data, content_type="multipart/form-data")
    assert rv.status_code == 400

def test_too_large(monkeypatch):
    monkeypatch.setattr("config.settings.MAX_UPLOAD_MB", 1)
    c = client()
    big = b"a" * (2 * 1024 * 1024)  # 2MB
    data = {"file": (io.BytesIO(big), "big.txt")}
    rv = c.post("/files", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200

def test_upload_empty_file(monkeypatch):
    """Tests uploading a 0-byte file."""
    monkeypatch.setattr("config.settings.ALLOWED_EXTENSIONS", {".txt"})
    c = client()
    data = {"file": (io.BytesIO(b""), "empty.txt")}
    rv = c.post("/files", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["filename"] == "empty.txt"
    assert body["size_bytes"] == 0
    assert body["num_lines"] == 0

def test_upload_with_path_traversal_filename():
    """Tests that directory traversal in filenames is sanitized."""
    c = client()
    data = {"file": (io.BytesIO(b"secret"), "../../secret.txt")}
    rv = c.post("/files", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["filename"] == "secret.txt"

def test_reupload_replaces_metadata(monkeypatch):
    """Tests that re-uploading a file updates its metadata."""
    monkeypatch.setattr("config.settings.ALLOWED_EXTENSIONS", {".txt"})
    c = client()
    c.post("/files", data={"file": (io.BytesIO(b"v1"), "overwrite.txt")})
    rv = c.post("/files", data={"file": (io.BytesIO(b"version2"), "overwrite.txt")})
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["size_bytes"] == 8