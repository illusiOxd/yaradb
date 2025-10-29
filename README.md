# 📦 YaraDB

**"An intelligent, in-memory-first Document DB with JSON persistence, built on FastAPI."**

YaraDB is a lightweight, document-oriented database designed for small to medium-sized projects that require the flexibility of NoSQL but demand modern data guarantees.

It's built on Python (FastAPI & Pydantic) and runs as an in-memory-first service, persisting all data to a simple `yaradb_storage.json` file on shutdown.

Its core feature is the **"Smart Document"** architecture (`StandardDocument`), which provides data integrity and optimistic locking "out-of-the-box".

---

## ⚡️ Core Features

YaraDB isn't just a "key-value" store. Every document is wrapped in an intelligent "envelope" that provides:

- **Optimistic Concurrency Control (OCC)**: Every document has a `version` field. The `PUT /document/update` endpoint requires this version, preventing "lost update" race conditions. If the version doesn't match, the API returns a `409 Conflict`.

- **Data Integrity**: Every document's body is automatically hashed into a `body_hash` field. This allows you to verify that data hasn't been corrupted or tampered with.

- **Soft Deletes**: Deleting a document (via `PUT /document/archive`) doesn't destroy it. It just sets an `archived_at` flag, preserving your data history.

- **Built-in Indexing**: Fast O(1) reads for `GET /document/get/{id}` via an in-memory hash map.

- **JSON Persistence**: All in-memory data is safely written to `yaradb_storage.json` on graceful shutdown.

---

## 🚀 Quick Start

### 1. Run with Docker (Recommended)

*(Coming Soon - Ты можешь добавить Dockerfile позже, как мы обсуждали)*

### 2. Run Locally

**1. Clone the repo:**
```bash
git clone https://github.com/YOUR_USERNAME/YaraDB.git
cd YaraDB
```

**2. Create a virtual environment and install:**
```bash
python -m venv .venv
source .venv/bin/activate  # (or .venv\Scripts\activate on Windows)
pip install -r requirements.txt
```

**3. Run the server:**
```bash
python main.py
```

The server is now running on **http://127.0.0.1:8000**.

---

## 📖 API Reference

### `POST /document/create`

Creates a new document.

**Request Body:**
```json
{
  "name": "user_account",
  "body": {
    "username": "alice",
    "email": "alice@example.com"
  }
}
```

**Response (200 OK):**
```json
{
  "_id": "a1b2c3d4-...",
  "name": "user_account",
  "body": { ... },
  "body_hash": "a9f8b...",
  "created_at": "2025-10-29T21:00:00Z",
  "updated_at": null,
  "version": 1,
  "archived_at": null
}
```

---

### `GET /document/get/{doc_id}`

Retrieves a single document by its ID (fast, O(1) read).

**Response (200 OK):**

The `StandardDocument` object.

---

### `PUT /document/update/{doc_id}`

Updates a document only if the provided version matches.

**Request Body:**
```json
{
  "version": 1, 
  "body": {
    "username": "alice_updated",
    "email": "alice@example.com"
  }
}
```

**Response (200 OK):**

The updated `StandardDocument` with `version: 2`.

**Response (409 Conflict):**

If you try to send `version: 1` again, you will get:
```json
{
  "detail": "Conflict: Document version mismatch. DB is at 2, you sent 1"
}
```

---

### `POST /document/find`

Finds documents using a filter on the body (slow scan, O(n)).

**Request Body:**
```json
{
  "username": "alice_updated"
}
```

**Response (200 OK):**
```json
[ ...list of StandardDocument objects... ]
```

---

### `PUT /document/archive/{doc_id}`

Performs a "soft delete" on a document.

**Response (200 OK):**

The `StandardDocument` with `archived_at` set.

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **FastAPI** - Modern, fast web framework
- **Pydantic** - Data validation and settings management
- **Uvicorn** - Lightning-fast ASGI server

---

## 📝 License

Copyright (c) 2025 Tymofii Shchur Viktorovych

All Rights Reserved.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby prohibited, unless explicit prior
written permission is obtained from the copyright owner.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
