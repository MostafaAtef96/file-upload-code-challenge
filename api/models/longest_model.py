from typing import Optional, List, Dict, Tuple
import heapq
import logging
from api.utils.db import get_conn
from api.utils.storage import Storage
from api.utils.reader import iter_lines

logger = logging.getLogger(__name__)

def _files_to_scan(file_name: Optional[str]) -> List[Tuple[str, str]]:
    """
    Returns a list of (filename, object_key).
    If file_name is provided, validate and return just that file.
    Otherwise return all uploaded files.
    """
    with get_conn() as conn:
        if file_name:
            logger.info(f"Querying database for specified file: {file_name}")
            row = conn.execute(
                "SELECT filename, object_key FROM files WHERE filename=?",
                (file_name,),
            ).fetchone()
            if not row:
                raise ValueError("File not found")
            return [(row["filename"], row["object_key"])]
        logger.info("Querying database for all uploaded files.")
        rows = conn.execute("SELECT filename, object_key FROM files").fetchall()
        if not rows:
            raise ValueError("No files uploaded yet")
        return [(r["filename"], r["object_key"]) for r in rows]

def get_longest_lines(limit: int = 100, file_name: Optional[str] = None) -> List[Dict]:
    """
    Returns up to `limit` longest lines either across all files or for one file.
    Each item: { length, file_name, line_number, line }.
    """
    logger.info(f"Searching for up to {limit} longest lines. File filter: {file_name or 'All'}")

    storage = Storage.from_env()

    # Min-heap of (length, file_name, line_no, text)
    heap: List[Tuple[int, str, int, str]] = []

    def push(item: Tuple[int, str, int, str]):
        if len(heap) < limit:
            heapq.heappush(heap, item)
        else:
            if item[0] > heap[0][0]:
                heapq.heapreplace(heap, item)

    files_to_scan = _files_to_scan(file_name)
    logger.info(f"Scanning {len(files_to_scan)} file(s).")
    for fname, object_key in files_to_scan:
        for i, line in enumerate(iter_lines(storage, object_key)):
            L = len(line)
            push((L, fname, i, line))

    # largest first
    heap.sort(key=lambda x: x[0], reverse=True)
    logger.info(f"Found {len(heap)} lines matching criteria.")
    return [
        {"length": L, "file_name": fn, "line_number": ln + 1, "line": txt} # Added one to be indexed from 1 instead of 0
        for (L, fn, ln, txt) in heap
    ]
