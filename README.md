![banner 4 jpeg](https://github.com/user-attachments/assets/a9a08190-ee8f-4883-81df-713a3e36c595)


# 📦 YaraDB

> An intelligent, in-memory-first Document Database with WAL persistence

[📖 **Complete Documentation**](https://github.com/illusiOxd/yaradb/wiki) | 
[📖 **Notion Documentation**](https://www.notion.so/YaraDB-Complete-Documentation-29ed5746db8c80fca39defa67e9d8ef4) |
[🚀 Quick Start](#quick-start) | 
[🐳 Docker Hub](https://hub.docker.com/r/ashfromsky/yaradb)

---

## 🚀 Quick Start

### Option 1: Docker Run (Recommended)

**Linux / macOS:**
```bash
docker run -d -p 8000:8000 \
  -v $(pwd)/yaradb_data:/data \
  -e DATA_DIR=/data \
  --name yaradb_server \
  ashfromsky/yaradb:latest
```

**Windows (PowerShell):**
```powershell
docker run -d -p 8000:8000 -v ${PWD}/yaradb_data:/data -e DATA_DIR=/data --name yaradb_server ashfromsky/yaradb:latest
```

**Windows (CMD):**
```cmd
docker run -d -p 8000:8000 -v %cd%/yaradb_data:/data -e DATA_DIR=/data --name yaradb_server ashfromsky/yaradb:latest
```

### Option 2: Docker Compose

**Create `docker-compose.yml`:**
```yaml
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
    restart: always
```

**Start the service:**
```bash
docker-compose up -d
```

### Option 3: Local Development

**Linux / macOS:**
```bash
git clone https://github.com/illusiOxd/yaradb.git
cd yaradb
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/illusiOxd/yaradb.git
cd yaradb
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## ✅ Verify Installation

Test that the server is running:

**Linux / macOS:**
```bash
curl http://localhost:8000/ping
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/ping
```

**Or open in browser:**
```
http://localhost:8000/docs
```

Expected response: `{"status":"alive"}`

---

## 🎯 Features

- ✅ **Optimistic Concurrency Control** - Version-based conflict detection
- ✅ **WAL Persistence** - Crash-safe Write-Ahead Logging
- ✅ **Soft Deletes** - Archive documents without losing data
- ✅ **Data Integrity** - SHA-256 body hashing
- ✅ **Fast O(1) Reads** - In-memory indexing by ID
- ✅ **RESTful API** - Simple HTTP interface
- ✅ **Docker Support** - Deploy anywhere in seconds

---

## 📚 Documentation

- [Complete Guide](https://github.com/illusiOxd/yaradb/wiki)
- [API Reference](https://github.com/illusiOxd/yaradb/wiki/API-Reference)
- [Architecture Overview](https://github.com/illusiOxd/yaradb/wiki/Architecture)
- [Python Client](https://github.com/illusiOxd/yaradb-client-py)

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) before submitting PRs.

---

## 📄 License

SSPL LICENSE © 2025 Tymofii Shchur Viktorovych

---

## 🔗 Links

- [GitHub Repository](https://github.com/illusiOxd/yaradb)
- [Docker Hub](https://hub.docker.com/r/ashfromsky/yaradb)
- [Python Client](https://github.com/illusiOxd/yaradb-client-py)
- [Issue Tracker](https://github.com/illusiOxd/yaradb/issues)
