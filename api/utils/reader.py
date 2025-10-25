from typing import List, Optional
import struct, os

from api.utils.storage import Storage

CHUNK_BYTES = 64 * 1024

def load_index(storage: Storage, idx_key: str) -> List[int]:
    """Load binary .idx (8-byte little-endian offsets)."""
    if storage.kind == "r2":
        obj = storage.client.get_object(Bucket=storage.bucket, Key=idx_key)
        data = obj["Body"].read()
    else:
        path = os.path.join(storage.base_dir, idx_key)
        with open(path, "rb") as f:
            data = f.read()
    out = []
    for i in range(0, len(data), 8):
        (off,) = struct.unpack("<Q", data[i:i+8])
        out.append(off)
    return out

def _stream_from_offset(storage: Storage, object_key: str, start: int):
    if storage.kind == "r2":
        resp = storage.client.get_object(Bucket=storage.bucket, Key=object_key, Range=f"bytes={start}-")
        body = resp["Body"]
        while True:
            chunk = body.read(CHUNK_BYTES)
            if not chunk:
                break
            yield chunk
    else:
        path = os.path.join(storage.base_dir, object_key)
        with open(path, "rb") as f:
            f.seek(start)
            while True:
                chunk = f.read(CHUNK_BYTES)
                if not chunk:
                    break
                yield chunk

def extract_line_from_offset(storage: Storage, object_key: str, start_offset: int, advance_newlines: int) -> str:
    """Skip `advance_newlines` line breaks from start_offset, then return that line (without trailing \\n)."""
    buf = bytearray()
    pending = advance_newlines
    for chunk in _stream_from_offset(storage, object_key, start_offset):
        i = 0
        while i < len(chunk):
            if pending > 0:
                j = chunk.find(b"\n", i)
                if j == -1:
                    # need more bytes to finish skipping
                    i = len(chunk)
                    continue
                pending -= 1
                i = j + 1
                continue
            # at start of desired line
            j = chunk.find(b"\n", i)
            if j == -1:
                buf += chunk[i:]
                i = len(chunk)
            else:
                buf += chunk[i:j]
                return buf.decode("utf-8", "replace")
    # reached EOF without newline
    return buf.decode("utf-8", "replace")
