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