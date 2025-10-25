#!/usr/bin/env python3
"""
make_big_files.py — generate large UTF-8 text files for testing.

Usage:
  python make_big_files.py
  python make_big_files.py --sizes 50MB,80MB,120MB --names big1.txt,big2.txt,big3.txt
  python make_big_files.py --sizes 200MB,200MB,200MB --seed 123 --long-line-every 500 --very-long-len 8000
"""

import argparse
import os
import random
import string
from typing import List, Tuple

DEFAULT_SIZES = ["50MB", "80MB", "120MB"]
DEFAULT_NAMES = ["big1.txt", "big2.txt", "big3.txt"]

ALPHABET = string.ascii_letters + "     "  # spaces to create word-like text


def parse_size(s: str) -> int:
    s = s.strip().upper()
    mult = 1
    if s.endswith("KB"):
        mult, s = 1024, s[:-2]
    elif s.endswith("MB"):
        mult, s = 1024 ** 2, s[:-2]
    elif s.endswith("GB"):
        mult, s = 1024 ** 3, s[:-2]
    elif s.endswith("B"):
        mult, s = 1, s[:-1]
    # else assume raw bytes if no suffix
    return int(float(s) * mult)


def parse_sizes_csv(csv: str) -> List[int]:
    return [parse_size(x) for x in csv.split(",") if x.strip()]


def parse_names_csv(csv: str) -> List[str]:
    return [x.strip() for x in csv.split(",") if x.strip()]


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.2f}{unit}"
        n /= 1024
    return f"{n:.2f}B"


def random_line(rng: random.Random, min_len: int, max_len: int) -> str:
    L = rng.randint(min_len, max_len)
    # Make it word-ish: chunks separated by spaces
    return "".join(rng.choice(ALPHABET) for _ in range(L))


def write_one_file(
    path: str,
    target_bytes: int,
    rng: random.Random,
    min_len: int = 40,
    max_len: int = 200,
    long_line_every: int = 400,
    very_long_len: int = 6000,
) -> None:
    """
    Stream lines until we reach (or slightly exceed) target_bytes.
    Every `long_line_every` lines, write a very long line to help test longest-lines.
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    bytes_written = 0
    line_no = 0

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        while bytes_written < target_bytes:
            line_no += 1

            if long_line_every > 0 and (line_no % long_line_every == 0):
                # Deterministic very long line pattern, with some variation
                prefix = f"LONG{line_no:08d}: "
                filler_len = max(very_long_len - len(prefix), 0)
                line = prefix + ("X" * filler_len)
            else:
                line = random_line(rng, min_len, max_len)

            # Always end with \n so your parser sees clean line boundaries
            data = line + "\n"
            f.write(data)
            bytes_written += len(data.encode("utf-8"))

    print(f"✔ Wrote {path}  (~{human(bytes_written)}) lines={line_no}")


def main():
    ap = argparse.ArgumentParser(description="Generate large text files for testing.")
    ap.add_argument(
        "--sizes",
        default=",".join(DEFAULT_SIZES),
        help=f"Comma-separated sizes (e.g., 50MB,80MB,120MB). Default: {','.join(DEFAULT_SIZES)}",
    )
    ap.add_argument(
        "--names",
        default=",".join(DEFAULT_NAMES),
        help=f"Comma-separated file names. Default: {','.join(DEFAULT_NAMES)}",
    )
    ap.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)"
    )
    ap.add_argument(
        "--min-len", type=int, default=40, help="Minimum line length (default: 40)"
    )
    ap.add_argument(
        "--max-len", type=int, default=200, help="Maximum line length (default: 200)"
    )
    ap.add_argument(
        "--long-line-every",
        type=int,
        default=400,
        help="Insert a very long line every N lines (0 to disable). Default: 400",
    )
    ap.add_argument(
        "--very-long-len",
        type=int,
        default=6000,
        help="Length of the very long line (default: 6000 characters)",
    )

    args = ap.parse_args()
    sizes = parse_sizes_csv(args.sizes)
    names = parse_names_csv(args.names)
    if len(sizes) != len(names):
        raise SystemExit("sizes and names must have the same number of items")

    rng = random.Random(args.seed)

    for name, sz in zip(names, sizes):
        print(f"→ Generating {name}  target={human(sz)}  seed={args.seed}")
        write_one_file(
            name,
            sz,
            rng,
            min_len=args.min_len,
            max_len=args.max_len,
            long_line_every=args.long_line_every,
            very_long_len=args.very_long_len,
        )


# if __name__ == "__main__":
#     main()