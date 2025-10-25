# Random Lines Web Service

A small web service that:

* **Uploads** plain text files
* Returns **one random line** (content negotiation: `text/plain`, `application/json`, `application/xml`, `application/*`)
* Returns **one random line backwards**
* Returns the **100 longest lines** across all uploads
* Returns the **20 longest lines** for a specific file

This README documents **assumptions**, **technical & non‑technical requirements**, **design decisions**, **API contracts**, and **how to run**. It’s intended to make the reviewer immediately productive when evaluating the solution.

---

## Stack Choice (and a quick correction)

> The team I’m applying to uses **Django**. For this task, an async‑friendly microframework like **FastAPI** or **Node.js (Fastify/Nest)** would be optimal for streaming and content negotiation. However, I chose **Flask** because it’s lightweight and conceptually close to Django’s request/response mental model, making the codebase familiar and easy to review for a Django team.

**Why Flask here**

* Minimal boilerplate, readable single‑file core

**If this were production**

* I would consider **FastAPI** for first‑class async I/O and automatic validation docs, or **Django/DRF** if we needed admin/auth/ORM features out of the box.

---

## Commit Message Conventions

Each commit message **must start** with one of the following symbols to indicate the nature of the change:

* `+` **Added**: new files, features, endpoints, tests, docs, or configuration.
* `-` **Removed**: deletions of files, features, flags, or dead code.
* `*` **Modified**: changes to existing code, refactors, fixes, or behavior tweaks.

---

## Assumptions

1. **File type**: input files are **UTF‑8 text** (binary files are out of scope). Non‑UTF‑8 bytes are replaced with the Unicode replacement character when decoding.
2. **Line definition**: a line is **bytes ending with `\n`**. The final line **may not** end with `\n` and is still considered a line.
3. **Large files**: files may contain **millions of lines**. We must support random access without loading the whole file into RAM.
4. **Indexing strategy**: we use **chunk‑based indexing** (offset every *K* lines, default `K=1000`) to avoid writing one DB row per line.
5. **Storage**: by default the submission can run locally with filesystem/SQLite, and optionally use **Cloudflare R2** (S3‑compatible) for object storage.
6. **Content negotiation**: the service supports `text/plain`, `application/json`, `application/xml`. If the `Accept` header includes `application/*`, metadata is returned.
7. **Security**: unauthenticated demo service.
8. **Limits**: per‑request `limit` is capped (1…1000) to prevent misuse. Upload size can be limited by web server or reverse proxy config.

---

## Technical Requirements

1. **Upload**: `POST /files` (multipart) — stream to storage, compute **chunk index** while writing, store metadata in SQLite.
2. **Random line**: `GET /lines/random` — content negotiation; if `application/*` -> include metadata:

   * `file_name`
   * `line_number`
   * `most_frequent_letter` (a–z, case‑insensitive; ties -> alphabetical)
3. **Random line (backwards)**: `GET /lines/random/backwards` — same selection, reversed string.
4. **Longest 100 lines (all files)**: `GET /lines/longest?limit=100` — min‑heap streaming scan across files.
5. **20 longest lines (one file)**: `GET /lines/longest?file_name=<name>&limit=20`.
6. **Content types**: support `text/plain`, `application/json`, `application/xml`.
7. **Scalability**: work with multi‑GB files without reading entire files into memory.

---

## Design Overview

### Storage

* **Option A (local)**: files in `./uploads/`, index in `./indexes/`, metadata in `./data.db` (SQLite).
* **Option B (Cloudflare R2)**: objects under `uploads/<filename>`, index under `indexes/<filename>.idx`, metadata still in `SQLite` (only file‑level, not per‑line).

### Chunk‑Based Indexing

* On upload, stream bytes and track **byte offsets** of line starts.
* Record the start offset every **K lines** (`K=1000` by default). The offset of line 0 is always 0.
* To fetch line *L*:

  * Compute `base = floor(L/K)*K` and `advance = L - base`.
  * Load the small index; `start_offset = index[base/K]`.
  * Range‑read from `start_offset`, **skip `advance` newlines**, then capture that line only.
  * **Example (numbers):** with `K=1000` and target line `L=3456`:

    * `base = floor(3456/1000)*1000 = 3000`
    * `advance = 3456 - 3000 = 456`
    * `start_offset = index[3000/1000] = index[3]` (byte position where line 3000 starts)
    * Range‑read from `start_offset`, skip **456** newline characters; the bytes up to the next `
      ` are the contents of line **3456**.
* **Benefits**: tiny index (~8 bytes × N/K), fast random access, no huge DB tables.

### Longest Lines

* Stream lines from storage, keep a **min‑heap** of size `limit` with entries `(length, file, line_no, text)`.
* Complexity: O(total_lines × log limit). For the default `limit=100`, log factor is tiny.

### Content Negotiation

* Inspect `Accept` header, choose response type.
* If client requests `application/*`, include metadata fields in JSON/XML bodies.
* For `text/plain`, return raw line(s) only (no metadata).