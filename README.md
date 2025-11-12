![banner 4 jpeg](https://github.com/user-attachments/assets/a9a08190-ee8f-4883-81df-713a3e36c595)

<div align="center">

# 📦 YaraDB

### An intelligent, in-memory-first Document Database with WAL persistence

[![Docker Hub](https://img.shields.io/badge/Docker-Hub-blue?logo=docker)](https://hub.docker.com/r/ashfromsky/yaradb)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-SSPL-green)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688?logo=fastapi)](https://fastapi.tiangolo.com/)

[📖 Documentation](https://github.com/illusiOxd/yaradb/wiki) • 
[🚀 Quick Start](#-quick-start) • 
[🎯 Features](#-features) • 
[🐳 Docker Hub](https://hub.docker.com/r/ashfromsky/yaradb) • 
[📚 API Reference](https://github.com/illusiOxd/yaradb/wiki/API-Reference)

</div>

---

## 📋 Overview

**YaraDB** is a lightweight, high-performance document database built for modern applications. Designed with simplicity and speed in mind, it combines in-memory operations with durable Write-Ahead Logging (WAL) to deliver both performance and reliability.

Perfect for:
- 🚀 **Rapid prototyping** - Get started in seconds
- 📊 **Real-time applications** - Ultra-fast O(1) reads
- 🔄 **Microservices** - Lightweight and containerized
- 🧪 **Testing environments** - Easy setup and teardown

---

## 🎯 Key Features

| Feature | Description |
|---------|-------------|
| ⚡ **In-Memory Performance** | Lightning-fast O(1) document retrieval by ID |
| 💾 **WAL Persistence** | Crash-safe Write-Ahead Logging ensures data durability |
| 🔐 **Optimistic Concurrency** | Version-based conflict detection prevents data races |
| 🗑️ **Soft Deletes** | Archive documents without permanent data loss |
| 🔒 **Data Integrity** | SHA-256 body hashing validates document consistency |
| 🌐 **RESTful API** | Clean HTTP interface with automatic OpenAPI docs |
| 🐳 **Docker Ready** | Deploy anywhere with official Docker images |
| 📦 **Zero Dependencies** | Minimal external requirements for easy integration |

---

## 🚀 Quick Start

### Prerequisites
- Docker (recommended) **OR**
- Python 3.8+

### 🐳 Option 1: Docker (Recommended)

**Using Docker Run:**

```bash
# Linux / macOS
docker run -d -p 8000:8000 \
  -v $(pwd)/yaradb_data:/data \
  -e DATA_DIR=/data \
  --name yaradb_server \
  ashfromsky/yaradb:latest

# Windows (PowerShell)
docker run -d -p 8000:8000 -v ${PWD}/yaradb_data:/data -e DATA_DIR=/data --name yaradb_server ashfromsky/yaradb:latest
```

**Using Docker Compose:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  yaradb:
    image: ashfromsky/yaradb:latest
    container_name: yaradb_server
    ports:
      - "8000:8000"
    volumes:
      - ./yaradb_data:/data
    environment:
      - DATA_DIR=/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/ping"]
      interval: 30s
      timeout: 10s
      retries: 3
```

```bash
docker-compose up -d
```

### 🐍 Option 2: Local Development

```bash
# Clone repository
git clone https://github.com/illusiOxd/yaradb.git
cd yaradb

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

### ✅ Verify Installation

**Test the server:**
```bash
curl http://localhost:8000/ping
# Expected: {"status":"alive"}
```

**Access interactive API documentation:**
```
http://localhost:8000/docs
```

---

## 💡 Usage Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Create a document
response = requests.post(f"{BASE_URL}/db/users", json={
    "name": "Alice",
    "email": "alice@example.com",
    "role": "admin"
})
doc = response.json()
print(f"Created document with ID: {doc['id']}")

# Read a document
response = requests.get(f"{BASE_URL}/db/users/{doc['id']}")
print(response.json())

# Update a document
response = requests.put(f"{BASE_URL}/db/users/{doc['id']}", json={
    "name": "Alice Smith",
    "email": "alice@example.com",
    "role": "admin"
})

# Delete a document (soft delete)
response = requests.delete(f"{BASE_URL}/db/users/{doc['id']}")
```

**For a full-featured Python client, check out [yaradb-client-py](https://github.com/illusiOxd/yaradb-client-py)**

---

## 📊 Architecture

YaraDB follows a simple but powerful architecture:

```
┌─────────────────┐
│   REST API      │ ← FastAPI (port 8000)
│   (FastAPI)     │
└────────┬────────┘
         │
┌────────▼────────┐
│  In-Memory      │ ← O(1) lookups
│  Document Store │
└────────┬────────┘
         │
┌────────▼────────┐
│  WAL Engine     │ ← Crash-safe persistence
│  (Write-Ahead)  │
└────────┬────────┘
         │
┌────────▼────────┐
│  JSON Files     │ ← Durable storage
└─────────────────┘
```

For detailed architecture documentation, see the [Architecture Overview](https://github.com/illusiOxd/yaradb/wiki/Architecture).

---

## 📚 Documentation

| Resource | Description |
|----------|-------------|
| [📖 Complete Guide](https://github.com/illusiOxd/yaradb/wiki) | Full documentation and tutorials |
| [📖 Notion Docs](https://www.notion.so/YaraDB-Complete-Documentation-29ed5746db8c80fca39defa67e9d8ef4) | Alternative documentation format |
| [🔌 API Reference](https://github.com/illusiOxd/yaradb/wiki/API-Reference) | Detailed API endpoint documentation |
| [🏗️ Architecture](https://github.com/illusiOxd/yaradb/wiki/Architecture) | System design and internals |
| [🐍 Python Client](https://github.com/illusiOxd/yaradb-client-py) | Official Python client library |

---

## 🛣️ Roadmap

- [ ] Query language support (filters, sorting)
- [ ] Secondary indexes for non-ID lookups
- [ ] Full-text search capabilities
- [ ] Replication and clustering
- [ ] Client libraries (Go, JavaScript, Rust)
- [ ] Backup and restore utilities
- [ ] Performance monitoring and metrics

---

## 🤝 Contributing

We welcome contributions from the community! Whether it's bug reports, feature requests, or code contributions, please feel free to get involved.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read our [Contributing Guide](CONTRIBUTING.md) for more details.

---

## 📄 License

This project is licensed under the **Server Side Public License (SSPL)**.

© 2025 Tymofii Shchur Viktorovych

---

## 🔗 Links & Resources

- [GitHub Repository](https://github.com/illusiOxd/yaradb)
- [Docker Hub](https://hub.docker.com/r/ashfromsky/yaradb)
- [Python Client Library](https://github.com/illusiOxd/yaradb-client-py)
- [Issue Tracker](https://github.com/illusiOxd/yaradb/issues)
- [Discussions](https://github.com/illusiOxd/yaradb/discussions)

---

<div align="center">

**⭐ If you find YaraDB useful, please consider giving it a star!**

Made with ❤️ by [illusiOxd](https://github.com/illusiOxd)

</div>
