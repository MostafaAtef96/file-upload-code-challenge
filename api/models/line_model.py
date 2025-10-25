import random
from typing import Optional, Dict

from api.utils.db import get_conn
from api.utils.storage import Storage
from api.utils.reader import load_index, extract_line_from_offset


def fetch_line(file_name: Optional[str] = None) -> Dict:
    """
    Retrieves a random line from a specified file, or from the last uploaded
    file if no file name is provided.

    Args:
        file_name: The name of the file to retrieve a line from. If None,
                   the most recently uploaded file is used.

    Returns:
        A dictionary containing the file name, line number, and line content.

    Raises:
        ValueError: If the specified file is not found, or if no files have
                    been uploaded when no file_name is provided.
    """
    conn = get_conn()

    if file_name:
        file_meta = conn.execute("SELECT * FROM files WHERE filename = ?", (file_name,)).fetchone()
        if not file_meta:
            raise ValueError(f"File not found: {file_name}")
    else:
        # Fetch the most recently uploaded file.
        file_meta = conn.execute("SELECT * FROM files ORDER BY id DESC LIMIT 1").fetchone()
        if not file_meta:
            raise ValueError("No files have been uploaded yet.")

    num_lines = file_meta["num_lines"]
    if num_lines == 0:
        return {"file_name": file_meta["filename"], "line_number": 0, "line": ""}

    # Pick a random line number (0-indexed).
    line_num = random.randint(0, num_lines - 1)

    # Use the index to find the correct chunk and offset.
    lines_per_chunk = file_meta["lines_per_chunk"]
    chunk_idx = line_num // lines_per_chunk
    line_in_chunk = line_num % lines_per_chunk

    storage = Storage.from_env()
    offsets = load_index(storage, file_meta["idx_key"])
    start_offset = offsets[chunk_idx]

    line_content = extract_line_from_offset(
        storage=storage, object_key=file_meta["object_key"], start_offset=start_offset, advance_newlines=line_in_chunk
    )

    return {"file_name": file_meta["filename"], "line_number": line_num + 1, "line": line_content}