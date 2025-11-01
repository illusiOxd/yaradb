# Quick Start

Get YaraDB up and running in 5 minutes.

---

## 1. Start the Server

=== "Docker Compose"

    Create `docker-compose.yml`:
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

    Start the service:
```bash
    docker-compose up -d
```

=== "Docker Run"
```bash
    docker run -d -p 8000:8000 \
      -v $(pwd)/yaradb_data:/data \
      -e DATA_DIR=/data \
      --name yaradb_server \
      ashfromsky/yaradb:latest
```

=== "Local Development"
```bash
    git clone https://github.com/illusiOxd/yaradb.git
    cd yaradb
    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    python main.py
```

---

## 2. Verify Server is Running
```bash
curl http://localhost:8000/ping
# Response: {"status":"alive"}
```

---

## 3. Install Python Client
```bash
pip install yaradb-client
```

---

## 4. Create Your First Document
```python
from yaradb_client import YaraClient

client = YaraClient("http://localhost:8000")

# Check connection
if not client.ping():
    print("Server is offline!")
    exit()

# Create a document
doc = client.create(
    name="user_account",
    body={
        "username": "alice",
        "email": "alice@example.com",
        "level": 1
    }
)

print(f"Created document with ID: {doc['_id']}")
print(f"Version: {doc['version']}")
```

---

## 5. Read, Update, and Archive
```python
# Get document by ID
doc = client.get(doc["_id"])
print(f"Username: {doc['body']['username']}")

# Update document (with version check)
updated = client.update(
    doc_id=doc["_id"],
    version=doc["version"],
    body={
        "username": "alice",
        "email": "alice@example.com",
        "level": 2  # Level up!
    }
)
print(f"New version: {updated['version']}")

# Archive (soft delete)
archived = client.archive(doc["_id"])
print(f"Archived at: {archived['archived_at']}")
```

---

## 6. Search Documents
```python
# Find all level 2 users
results = client.find({"level": 2})
print(f"Found {len(results)} documents")

# Find including archived
all_results = client.find({"username": "alice"}, include_archived=True)
```

---

## Next Steps

- [API Reference](api.md) - Full API documentation
- [Client Guide](client.md) - Advanced client usage
- [Architecture](architecture/wal.md) - How YaraDB works internally