import os

DATA_DIR = os.getenv("DATA_DIR", ".")

STORAGE_FILE = os.path.join(DATA_DIR, "yaradb_storage.json")
WAL_FILE = os.path.join(DATA_DIR, "yaradb_wal")