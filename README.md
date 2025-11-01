# 📦 YaraDB

> An intelligent, in-memory-first Document Database with WAL persistence

[📖 **Complete Documentation**](https://github.com/illusiOxd/yaradb/wiki) | 
[📖 **Notion complete Documentation**](https://www.notion.so/YaraDB-Complete-Documentation-29ed5746db8c80fca39defa67e9d8ef4?source=copy_link) |
[🚀 Quick Start](https://github.com/illusiOxd/yaradb/wiki/Quick-Start) | 
[🐳 Docker Hub](https://hub.docker.com/r/ashfromsky/yaradb)

## Quick Start

\`\`\`bash
docker run -d -p 8000:8000 \
  -v $(pwd)/yaradb_data:/data \
  -e DATA_DIR=/data \
  --name yaradb_server \
  ashfromsky/yaradb:latest
\`\`\`

## Features

- ✅ Optimistic Concurrency Control
- ✅ WAL Persistence
- ✅ Soft Deletes
- ✅ Data Integrity Hashing
- ✅ Fast O(1) Reads

## Documentation

- [Complete Guide](https://github.com/illusiOxd/yaradb/wiki)
- [API Reference](https://github.com/illusiOxd/yaradb/wiki/API-Reference)
- [Architecture](https://github.com/illusiOxd/yaradb/wiki/Architecture)

## License

MIT © 2025 Tymofii Shchur Viktorovych
