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

This is the easiest and most reliable way to run YaraDB as a service.

**1. Run the container (with data persistence):**
```bash
# This command automatically downloads the image from Docker Hub
# and starts the server.
#
# It creates a 'yaradb_data' folder in your current directory 
# to save your database files (WAL + snapshot).

docker run -d -p 8000:8000 -v $(pwd)/yaradb_data:/app --name yaradb_server ashfromsky/yaradb:latest
```

**Flags explanation:**
- `-d`: Detached mode (runs in background)
- `-p 8000:8000`: Maps your local port 8000 to the container's port 8000
- `-v $(pwd)/yaradb_data:/app`: **(IMPORTANT)** Saves your `yaradb_storage.json` file into a `yaradb_data` folder on your host machine, so your data persists even if the container is removed
- `--name yaradb_server`: A friendly name to make it easy to stop

The server is now running on **http://127.0.0.1:8000**.

**To stop the server:**
```bash
docker stop yaradb_server
```

**To restart:**
```bash
docker start yaradb_server
```

**To remove:**
```bash
docker rm yaradb_server
```

---

### 2. Run Locally (Alternative)

**1. Clone the repo:**
```bash
git clone https://github.com/illusiOxd/yaradb.git
cd yaradb
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
  "body": { "username": "alice", "email": "alice@example.com" },
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
[
  { ...StandardDocument objects... }
]
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

**MIT License**

Copyright (c) 2025 Tymofii Shchur Viktorovych

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 🤝 Contributing

Contributions are welcome! Please read our [CONTRIBUTING.md](.github/CONTRIBUTING.md) to understand our contribution process and CLA.

Feel free to open issues or submit pull requests.

---

## 🔗 Links

- **Documentation**: Coming soon
- **Issues**: [GitHub Issues](https://github.com/illusiOxd/yaradb/issues)
- **Discussions**: [GitHub Discussions](https://github.com/illusiOxd/yaradb/discussions)
