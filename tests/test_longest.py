import io
import pytest
import xml.etree.ElementTree as ET
 
from app import app
from api.utils.db import init_db
from api.utils.storage import Storage


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A pytest fixture to create an isolated app client for each test."""
    temp_db_path = tmp_path / "test.db"
    monkeypatch.setattr("api.utils.db.DB_PATH", str(temp_db_path))
    init_db()

    def mock_storage_from_env():
        return Storage(base_dir=str(tmp_path / "uploads"))

    monkeypatch.setattr("api.utils.storage.Storage.from_env", mock_storage_from_env)

    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def setup_file(client, filename, content):
    """Helper function to upload a file."""
    return client.post("/files", data={"file": (io.BytesIO(content), filename)})


def test_get_longest_lines_all_files(client):
    """Test getting longest lines across multiple files."""
    setup_file(client, "a.txt", b"short\nvery long line a\nmedium")
    setup_file(client, "b.txt", b"another short\nlongest line of all\n")

    rv = client.get("/lines/longest?limit=2", headers={"Accept": "text/plain"})
    assert rv.status_code == 200
    assert rv.mimetype == "text/plain"
    lines = rv.data.decode().split("\n")
    assert len(lines) == 2
    assert lines[0] == "longest line of all"
    assert lines[1] == "very long line a"


def test_get_longest_lines_one_file(client):
    """Test getting longest lines from a single specified file."""
    setup_file(client, "a.txt", b"short\nlong line\nmedium")
    setup_file(client, "b.txt", b"this file should be ignored")

    rv = client.get("/lines/longest?file_name=a.txt&limit=1", headers={"Accept": "text/plain"})
    assert rv.status_code == 200
    assert rv.mimetype == "text/plain"
    assert rv.data.decode() == "long line"


def test_get_longest_lines_json_and_xml(client):
    """Test JSON and XML content negotiation for the longest lines endpoint."""
    setup_file(client, "a.txt", b"a\nbb\nccc")

    # Test JSON response
    rv_json = client.get("/lines/longest?limit=1", headers={"Accept": "application/json"})
    assert rv_json.status_code == 200
    data = rv_json.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["line"] == "ccc"

    # Test XML response
    rv_xml = client.get("/lines/longest?limit=1", headers={"Accept": "application/xml"})
    assert rv_xml.status_code == 200
    assert rv_xml.mimetype == "application/xml"
    root = ET.fromstring(rv_xml.data)
    assert root.tag == "longest_lines"
    assert root.find("line_item/line").text == "ccc"


def test_get_longest_lines_no_files(client):
    """Test that a 404 is returned when no files have been uploaded."""
    rv = client.get("/lines/longest")
    assert rv.status_code == 404
    assert "No files uploaded yet" in rv.get_json()["detail"]


def test_get_longest_lines_non_existent_file(client):
    """Test that a 404 is returned for a non-existent file_name."""
    setup_file(client, "exists.txt", b"content")
    rv = client.get("/lines/longest?file_name=nonexistent.txt")
    assert rv.status_code == 404
    assert "File not found" in rv.get_json()["detail"]


def test_get_longest_lines_limit_clamping(client):
    """Test that the limit parameter is correctly clamped."""
    setup_file(client, "a.txt", b"a\nb\nc\nd\ne")
    rv = client.get("/lines/longest?limit=2000", headers={"Accept": "application/json"})
    assert len(rv.get_json()) == 5  # The model clamps the limit to 1000, but there are only 5 lines


def test_get_longest_lines_defaults(client):
    """Test the default limit behavior."""
    # Create a file with 25 lines
    content = b"\n".join([f"line {i}".encode() for i in range(25)])
    setup_file(client, "test.txt", content)

    # 1. No file, no limit -> should default to 100, but return all 25
    rv_all = client.get("/lines/longest", headers={"Accept": "application/json"})
    assert rv_all.status_code == 200
    assert len(rv_all.get_json()) == 25

    # 2. File specified, no limit -> should default to 20
    rv_file = client.get("/lines/longest?file_name=test.txt", headers={"Accept": "application/json"})
    assert rv_file.status_code == 200
    assert len(rv_file.get_json()) == 20