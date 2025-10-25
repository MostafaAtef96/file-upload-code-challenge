import io
import pytest
import xml.etree.ElementTree as ET

from app import app
from api.utils.db import init_db
from api.utils.storage import Storage


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A pytest fixture to create an isolated app client for each test."""
    # 1. Use a temporary database for test isolation
    temp_db_path = tmp_path / "test.db"
    monkeypatch.setattr("api.utils.db.DB_PATH", str(temp_db_path))
    init_db()  # Ensure the schema is created in the temp DB

    # 2. Patch the Storage utility to use a temporary uploads directory
    def mock_storage_from_env():
        return Storage(base_dir=str(tmp_path / "uploads"))

    monkeypatch.setattr("api.utils.storage.Storage.from_env", mock_storage_from_env)

    # 3. Set up and yield the test client
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def setup_file(client, filename, content):
    """Helper function to upload a file."""
    return client.post("/files", data={"file": (io.BytesIO(content), filename)})


def test_get_line_no_files(client):
    """Test that a 404 is returned when no files have been uploaded."""
    rv = client.get("/lines/random")
    assert rv.status_code == 404
    assert "No files have been uploaded" in rv.get_json()["detail"]


def test_get_line_from_last_uploaded(client):
    """Test that the endpoint defaults to the last uploaded file."""
    setup_file(client, "first.txt", b"line one")
    setup_file(client, "second.txt", b"line two")  # This is the last one

    rv = client.get("/lines/random", headers={"Accept": "application/json"})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["file_name"] == "second.txt"
    assert data["line"] == "line two"


def test_get_line_from_specific_file(client):
    """Test fetching a line from a file specified by `file_name`."""
    setup_file(client, "first.txt", b"line one")
    setup_file(client, "second.txt", b"line two")

    rv = client.get("/lines/random?file_name=first.txt", headers={"Accept": "application/json"})
    assert rv.status_code == 200
    assert rv.get_json()["file_name"] == "first.txt"


def test_get_line_non_existent_file(client):
    """Test that a 404 is returned for a non-existent file_name."""
    setup_file(client, "exists.txt", b"content")
    rv = client.get("/lines/random?file_name=nonexistent.txt")
    assert rv.status_code == 404
    assert "File not found" in rv.get_json()["detail"]


def test_get_line_content_negotiation(client):
    """Test content negotiation for text/plain and application/xml."""
    setup_file(client, "test.txt", b"plain text line")

    # Test text/plain
    rv_text = client.get("/lines/random", headers={"Accept": "text/plain"})
    assert rv_text.status_code == 200
    assert rv_text.mimetype == "text/plain"
    assert rv_text.data == b"plain text line"

    # Test application/xml
    rv_xml = client.get("/lines/random", headers={"Accept": "application/xml"})
    assert rv_xml.status_code == 200
    assert rv_xml.mimetype == "application/xml"
    root = ET.fromstring(rv_xml.data)
    assert root.tag == "random_line"
    assert root.find("line").text == "plain text line"


def test_most_frequent_letter_edge_cases(client):
    """Test 'N/A' and 'Tie' cases for most_frequent_letter."""
    # Test "N/A" case
    setup_file(client, "numbers.txt", b"123-456-789")
    rv_na = client.get("/lines/random", headers={"Accept": "application/json"})
    assert rv_na.status_code == 200
    assert rv_na.get_json()["most_frequent_letter"] == "N/A"

    # Test "Tie" case
    setup_file(client, "tie.txt", b"aabbcc")
    rv_tie = client.get("/lines/random", headers={"Accept": "application/json"})
    assert rv_tie.status_code == 200
    assert rv_tie.get_json()["most_frequent_letter"] == "Tie"


def test_get_line_from_empty_file(client):
    """Test behavior when the source file is empty."""
    setup_file(client, "empty.txt", b"")
    rv = client.get("/lines/random", headers={"Accept": "application/json"})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["line"] == ""
    assert data["line_number"] == 0
    assert data["most_frequent_letter"] == "N/A"