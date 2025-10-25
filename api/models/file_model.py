"""
Model layer: business logic for file uploads.
- Streams content to storage (R2 or local)
- Builds chunk index (every K lines) as compact binary
- Persists file metadata into SQLite
"""
import logging
import tempfile
from datetime import datetime
from werkzeug.datastructures import FileStorage
import os

from api.utils.storage import Storage
from api.utils.indexing import build_chunk_index
from api.utils.db import get_conn, init_db
from config import settings

logger = logging.getLogger(__name__)

# Ensure DB schema exists on first import
init_db()


def handle_upload(file_storage: FileStorage, filename: str) -> dict:
    logger.info(f"Starting upload process for file: {filename}")
    # 1) Stream to temp file while computing index
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    try:
        meta = build_chunk_index(
            infile=file_storage.stream,
            outfile_path=tmp_path,
            lines_per_chunk=settings.INDEX_LINES_PER_CHUNK,
        )
        size_bytes = meta.size_bytes
        num_lines = meta.num_lines
        offsets = meta.offsets  # list[int], offset for lines 0, K, 2K, ...

        # 2) Persist to storage backend
        logger.info(f"Persisting '{filename}' to storage.")
        storage = Storage.from_env()
        object_key = filename
        idx_key = f"indexes/{filename}.idx"

        storage.upload_file(local_path=tmp_path, object_key=object_key)
        storage.put_index(offsets=offsets, object_key=idx_key)

        logger.info(f"Upserting metadata for '{filename}' into database.")
        # 3) Upsert metadata in SQLite
        with get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO files(
                    filename, object_key, idx_key, size_bytes, uploaded_at, num_lines, lines_per_chunk
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    filename,
                    object_key,
                    idx_key,
                    size_bytes,
                    datetime.utcnow().isoformat(),
                    num_lines,
                    settings.INDEX_LINES_PER_CHUNK,
                ),
            )

        logger.info(f"Successfully processed and stored '{filename}'.")
        return {
            "filename": filename,
            "size_bytes": size_bytes,
            "num_lines": num_lines,
            "lines_per_chunk": settings.INDEX_LINES_PER_CHUNK,
            "object_key": object_key,
            "idx_key": idx_key,
            "storage": storage.kind,
        }
    finally:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
