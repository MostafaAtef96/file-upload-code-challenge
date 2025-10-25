"""Storage abstraction: local filesystem."""
import os
import struct
from typing import Optional, List


class Storage:
    def __init__(self, base_dir: Optional[str] = None):
        self.kind = "local"
        self.base_dir = base_dir or os.path.join(os.getcwd(), "uploads")
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "indexes"), exist_ok=True)

    @classmethod
    def from_env(cls) -> "Storage":
        """Creates a Storage instance. In this version, it always uses local storage."""
        return cls()

    # ── file upload ──
    def upload_file(self, local_path: str, object_key: str):
        """Copies a file from a local path to the storage destination."""
        dest = os.path.join(self.base_dir, os.path.normpath(object_key))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(local_path, "rb") as src, open(dest, "wb") as dst:
            while True:
                b = src.read(64 * 1024)
                if not b:
                    break
                dst.write(b)

    # ── index upload ──
    def put_index(self, offsets: List[int], object_key: str):
        """Packs byte offsets into a binary index file and saves it to storage."""
        # pack as little-endian unsigned long long (8 bytes per offset)
        data = b"".join(struct.pack("<Q", off) for off in offsets)
        dest = os.path.join(self.base_dir, os.path.normpath(object_key))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
