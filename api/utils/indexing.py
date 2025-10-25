"""Chunk-based index builder.
Records byte offsets for lines 0, K, 2K, ... while streaming input → output file.
"""
from dataclasses import dataclass
from typing import List
from dataclasses import dataclass

CHUNK_BYTES = 64 * 1024

@dataclass
class IndexMeta:
    size_bytes: int
    num_lines: int
    offsets: List[int]


def build_chunk_index(infile, outfile_path: str, lines_per_chunk: int) -> IndexMeta:
    line = 0
    byte_offset = 0
    offsets = [0]  # line 0 starts at byte 0

    with open(outfile_path, "wb") as out:
        while True:
            chunk = infile.read(CHUNK_BYTES)
            if not chunk:
                break
            start = 0
            while True:
                idx = chunk.find(b"\n", start)
                if idx == -1:
                    out.write(chunk[start:])
                    byte_offset += len(chunk) - start
                    break
                # write through the newline, next line begins at byte_offset + idx + 1
                out.write(chunk[start: idx + 1])
                line += 1
                if line % lines_per_chunk == 0:
                    offsets.append(byte_offset + idx + 1)
                byte_offset += (idx + 1 - start)
                start = idx + 1

    # Determine size & total lines (handle final line without trailing \n)
    size_bytes = byte_offset
    if size_bytes == 0:
        num_lines = 0
    else:
        # we can infer final byte from out file without reopening the stream
        with open(outfile_path, "rb") as fc:
            fc.seek(max(0, size_bytes - 1))
            tail = fc.read(1)
        num_lines = line if tail == b"\n" else line + 1

    return IndexMeta(size_bytes=size_bytes, num_lines=num_lines, offsets=offsets)