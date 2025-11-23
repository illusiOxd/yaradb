<div align="center">

<img src="https://github.com/user-attachments/assets/a9a08190-ee8f-4883-81df-713a3e36c595" alt="YaraDB Banner" width="100%">

<h1>
  <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Card%20File%20Box.png" alt="📦" width="35" height="35" />
  YaraDB
</h1>

<h3>🚀 Lightning-fast • 🛡️ Crash-safe • 🎯 Developer-friendly</h3>

<p align="center">
  <a href="https://hub.docker.com/r/ashfromsky/yaradb">
    <img src="https://img.shields.io/docker/pulls/ashfromsky/yaradb?style=for-the-badge&logo=docker&logoColor=white&color=0db7ed" alt="Docker Pulls">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/python-3.8+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-SSPL-00ADD8?style=for-the-badge" alt="License">
  </a>
  <a href="https://github.com/illusiOxd/yaradb/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/illusiOxd/yaradb/ci.yml?style=for-the-badge&logo=github" alt="CI/CD">
  </a>
</p>

<p align="center">
  <a href="#-quick-start"><b>Quick Start</b></a> •
  <a href="https://github.com/illusiOxd/yaradb/wiki"><b>Documentation</b></a> •
  <a href="https://hub.docker.com/r/ashfromsky/yaradb"><b>Docker Hub</b></a> •
  <a href="https://github.com/illusiOxd/yaradb-client-py"><b>Python Client</b></a>
</p>

</div>

<br>

---

<div align="center">

## 💎 What Makes YaraDB Special?

</div>

<table>
<tr>
<td width="50%" valign="top">

### ⚡ **Blazing Performance**

```python
# O(1) lookups - Always fast
doc = client.get(doc_id)
# Sub-millisecond response time
```

✨ **In-memory operations**  
✨ **Hash-based indexing**  
✨ **Zero query overhead**

</td>
<td width="50%" valign="top">

### 🛡️ **Enterprise Reliability**

```python
# Crash? No problem.
# WAL recovery restores everything
```

✨ **Write-Ahead Logging (WAL)**  
✨ **Automatic crash recovery**  
✨ **SHA-256 integrity checks**

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🎯 **Developer Experience**

```python
# One line to start
docker run -p 8000:8000 ashfromsky/yaradb
```

✨ **RESTful API + OpenAPI docs**  
✨ **Zero configuration**  
✨ **Native Python client**

</td>
<td width="50%" valign="top">

### 🔧 **Smart Flexibility**

```python
# Free mode or strict schemas
# Your choice, your rules
```

✨ **Schema-free OR JSON Schema**  
✨ **Optimistic locking (OCC)**  
✨ **Soft deletes built-in**

</td>
</tr>
</table>

<br>

---

<div align="center">

## 🚀 Get Started in 30 Seconds

</div>

<table>
<tr>
<td width="33%" align="center">

### 🐳 Docker

**Linux / macOS:**
```bash
docker pull ashfromsky/yaradb:latest
docker run -d \
  --name yaradb_server \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  ashfromsky/yaradb:latest
```

**Windows (PowerShell):**
```powershell
docker pull ashfromsky/yaradb:latest
docker run -d `
  --name yaradb_server `
  -p 8000:8000 `
  -v ${PWD}/data:/data `
  ashfromsky/yaradb:latest
```

**Windows (CMD):**
```cmd
docker pull ashfromsky/yaradb:latest
docker run -d ^
  --name yaradb_server ^
  -p 8000:8000 ^
  -v %cd%/data:/data ^
  ashfromsky/yaradb:latest
```

<sub>**Recommended** • Production-ready</sub>

</td>
<td width="33%" align="center">

### 📦 Docker Compose

```yaml
services:
  yaradb:
    image: ashfromsky/yaradb
    ports: ["8000:8000"]
    volumes: ["./data:/data"]
```

<sub>**Easy** • One command deploy</sub>

</td>
<td width="33%" align="center">

### 🐍 From Source

```bash
git clone https://github.com/illusiOxd/yaradb
cd yaradb
pip install -r requirements.txt
python main.py
```

<sub>**Development** • Full control</sub>

</td>
</tr>
</table>

<div align="center">

**Verify it's running:**

```bash
curl http://localhost:8000/ping
# {"status":"alive"} ✅
```

**Explore the API:**  
👉 **http://localhost:8000/docs** 👈

</div>

<br>

---

<div align="center">

## 💻 Usage Examples

</div>

<table>
<tr>
<td width="50%">

### 🌐 REST API

```bash
# Create a document
curl -X POST http://localhost:8000/document/create \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "users",
    "body": {
      "name": "Alice",
      "email": "alice@example.com",
      "role": "admin"
    }
  }'
```

```bash
# Get by ID
curl http://localhost:8000/document/get/{doc_id}
```

```bash
# Update with version control
curl -X PUT http://localhost:8000/document/update/{doc_id} \
  -d '{"version": 1, "body": {"name": "Alice Smith"}}'
```

```bash
# Soft delete
curl -X PUT http://localhost:8000/document/archive/{doc_id}
```

</td>
<td width="50%">

### 🐍 Python Client

**Install:**
```bash
pip install yaradb-client
```

**Use:**
```python
from yaradb_client import YaraClient

client = YaraClient("http://localhost:8000")

# Create
doc = client.create(
    table_name="users",
    body={
        "name": "Alice",
        "email": "alice@example.com",
        "level": 5
    }
)

# Read
user = client.get(doc["_id"])

# Update (with optimistic locking)
updated = client.update(
    doc_id=doc["_id"],
    version=doc["version"],
    body={"name": "Alice", "level": 6}
)

# Search
results = client.find({"level": 6})

# Archive (soft delete)
client.archive(doc["_id"])
```

</td>
</tr>
</table>

<br>

---

<div align="center">

## 🏗️ How It Works

</div>

```
╔══════════════════════════════════════════════════════════════╗
║                      🌐 FastAPI REST API                     ║
║                   (OpenAPI • JSON • HTTP/2)                  ║
╚═════════════════════════════╤════════════════════════════════╝
                              │
                              ▼
╔══════════════════════════════════════════════════════════════╗
║                  💾 In-Memory Hash Index                     ║
║              { UUID → Document } - O(1) Lookup               ║
╚═════════════════════════════╤════════════════════════════════╝
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
        ╔═══════════════════╗  ╔═══════════════════╗
        ║   📝 WAL Engine   ║  ║ 🔐 OCC Locking    ║
        ║  Append-Only Log  ║  ║ Version Control   ║
        ╚═════════╤═════════╝  ╚═══════════════════╝
                  │
                  ▼
        ╔═══════════════════╗
        ║ 💿 JSON Storage   ║
        ║ Periodic Snapshot ║
        ╚═══════════════════╝
```

<table>
<tr>
<td align="center" width="25%">

### 🎯 **Write Path**

1. Validate request
2. Append to WAL
3. Update memory
4. Return success

<sub>~2ms latency</sub>

</td>
<td align="center" width="25%">

### 📖 **Read Path**

1. Hash lookup
2. Return from RAM
3. Done!

<sub><1ms latency</sub>

</td>
<td align="center" width="25%">

### 🔄 **Crash Recovery**

1. Load snapshot
2. Replay WAL
3. Rebuild index
4. Ready!

<sub>Automatic on startup</sub>

</td>
<td align="center" width="25%">

### 💾 **Checkpoints**

1. Serialize state
2. Write snapshot
3. Truncate WAL
4. Continue

<sub>Background process</sub>

</td>
</tr>
</table>

<br>

---

<div align="center">

## 🎯 Perfect For

</div>

<table>
<tr>
<td align="center" width="20%">

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Hammer%20and%20Wrench.png" width="50" height="50" alt="🛠️">

### Prototyping

Spin up a database in seconds. No complex setup, no configuration files.

</td>
<td align="center" width="20%">

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/High%20Voltage.png" width="50" height="50" alt="⚡">

### Real-Time Apps

WebSockets, live dashboards, gaming leaderboards - anywhere speed matters.

</td>
<td align="center" width="20%">

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Package.png" width="50" height="50" alt="📦">

### Microservices

Lightweight data layer for containerized architectures.

</td>
<td align="center" width="20%">

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Test%20Tube.png" width="50" height="50" alt="🧪">

### Testing

Fast, ephemeral test databases. Create, test, destroy.

</td>
<td align="center" width="20%">

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/Globe%20Showing%20Europe-Africa.png" width="50" height="50" alt="🌍">

### Edge Computing

Low footprint, works anywhere Docker runs.

</td>
</tr>
</table>

<br>

---

<div align="center">

## 📚 Learn More

</div>

<table>
<tr>
<td align="center" width="33%">

### 📖 [Complete Documentation](https://github.com/illusiOxd/yaradb/wiki)

Full guides, tutorials, and best practices

</td>
<td align="center" width="33%">

### 🔌 [API Reference](https://github.com/illusiOxd/yaradb/wiki/API-Reference)

REST endpoints, schemas, and examples

</td>
<td align="center" width="33%">

### 🏗️ [Architecture Deep Dive](https://github.com/illusiOxd/yaradb/wiki/Architecture)

WAL internals, OCC, and design decisions

</td>
</tr>
</table>

<div align="center">

### 🌟 Alternative Resources

[![Notion Docs](https://img.shields.io/badge/Notion-Docs-000000?style=for-the-badge&logo=notion&logoColor=white)](https://www.notion.so/YaraDB-Complete-Documentation-29ed5746db8c80fca39defa67e9d8ef4)
[![Python Client Repo](https://img.shields.io/badge/GitHub-Python_Client-181717?style=for-the-badge&logo=github)](https://github.com/illusiOxd/yaradb-client-py)
[![Discussions](https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github)](https://github.com/illusiOxd/yaradb/discussions)

</div>

<br>

---

<div align="center">

## 🤝 Contributing

**We ❤️ contributions from the community!**

Whether you're fixing bugs, adding features, improving docs, or sharing ideas — you're welcome here.

</div>

<table>
<tr>
<td align="center" width="25%">

### 🐛 Report Bugs

Found an issue?  
[Open an Issue →](https://github.com/illusiOxd/yaradb/issues/new?template=bug_report.md)

</td>
<td align="center" width="25%">

### 💡 Request Features

Have an idea?  
[Share It →](https://github.com/illusiOxd/yaradb/issues/new?template=feature_request.md)

</td>
<td align="center" width="25%">

### 📝 Improve Docs

Make it clearer  
[Edit on GitHub →](https://github.com/illusiOxd/yaradb/wiki)

</td>
<td align="center" width="25%">

### 🔧 Submit Code

Fork • Code • PR  
[Guidelines →](.github/CONTRIBUTING.md)

</td>
</tr>
</table>

<div align="center">

**Read our** [Code of Conduct](.github/CODE_OF_CONDUCT.md) • [Contributing Guide](.github/CONTRIBUTING.md)

</div>

<br>

---

<div align="center">

## 📜 License & Legal

**Server Side Public License (SSPL)**  
© 2025 Tymofii Shchur Viktorovych

[Read Full License →](LICENSE)

<sub>Free for development and internal use • Contact for commercial SaaS deployment</sub>

</div>

---

<div align="center">

## 🔗 Connect With Us

<a href="https://github.com/illusiOxd/yaradb">
  <img src="https://img.shields.io/badge/GitHub-YaraDB-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
</a>
<a href="https://hub.docker.com/r/ashfromsky/yaradb">
  <img src="https://img.shields.io/badge/Docker_Hub-YaraDB-0db7ed?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Hub">
</a>
<a href="https://github.com/illusiOxd/yaradb-client-py">
  <img src="https://img.shields.io/badge/PyPI-Client-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="PyPI">
</a>
<a href="https://github.com/illusiOxd/yaradb/discussions">
  <img src="https://img.shields.io/badge/Discussions-Join-7057ff?style=for-the-badge&logo=github&logoColor=white" alt="Discussions">
</a>

<br><br>

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Hand%20gestures/Red%20Heart.png" width="25" height="25" alt="❤️"> **Built with passion by** [**illusiOxd**](https://github.com/illusiOxd)

<br>

<sub>⭐ **Star us on GitHub if YaraDB powers your project!** ⭐</sub>

<br><br>

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/Star.png" width="20" height="20" alt="✨">
<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/Star.png" width="20" height="20" alt="✨">
<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/Star.png" width="20" height="20" alt="✨">

</div>
