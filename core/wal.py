import os
import json
import uuid
from datetime import datetime
from fastapi import HTTPException

from core.state import db_storage, db_index_by_id, db_lock, wal_lock
from models.document import StandardDocument

STORAGE_FILE = "yaradb_storage.json"
WAL_FILE = "yaradb.wal"


def log_to_wal(operation: dict):
    log_entry = json.dumps(operation, default=str) + "\n"

    try:
        with wal_lock:
            with open(WAL_FILE, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                f.flush()
                os.fsync(f.fileno())

    except Exception as e:
        print(f"!!! CRITICAL WAL WRITE FAILED: {e} !!!")
        raise HTTPException(status_code=500, detail=f"Database WAL write error: {e}")


def _apply_op_to_memory(op: dict):
    op_type = op.get("op")
    try:
        if op_type == "create":
            doc = StandardDocument.model_validate(op["doc"])
            db_storage.append(doc)
            db_index_by_id[doc.id] = doc

        elif op_type == "update":
            doc_id = uuid.UUID(op["doc_id"])
            doc = db_index_by_id.get(doc_id)
            if doc:
                doc.body = op["body"]
                doc.version = op["version"]
                doc.updated_at = datetime.fromisoformat(op["updated_at"])
                doc.calculate_body_hash()

        elif op_type == "archive":
            doc_id = uuid.UUID(op["doc_id"])
            doc = db_index_by_id.get(doc_id)
            if doc:
                doc.archive()
                doc.version = op["version"]
                doc.updated_at = datetime.fromisoformat(op["updated_at"])

    except Exception as e:
        print(f"Failed to apply WAL op: {op_type}. Error: {e}")


def load_snapshot():
    try:
        if os.path.exists(STORAGE_FILE):
            print(f"--- Loading data from {STORAGE_FILE} ---")
            with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                for item in raw_data:
                    doc = StandardDocument.model_validate(item)
                    db_storage.append(doc)
                    db_index_by_id[doc.id] = doc
            print(f"--- Successfully loaded {len(db_storage)} documents from snapshot. ---")
        else:
            print(f"--- File {STORAGE_FILE} not found. Starting with an empty DB. ---")
    except Exception as e:
        print(f"!!! CRITICAL ERROR while loading snapshot: {e} !!!")
        raise e


def recover_from_wal():
    if os.path.exists(WAL_FILE):
        print(f"--- Replaying WAL file ({WAL_FILE})... ---")
        replayed_ops = 0
        with open(WAL_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    op = json.loads(line)
                    _apply_op_to_memory(op)
                    replayed_ops += 1
                except Exception as e:
                    print(f"!!! CRITICAL: Failed to replay WAL entry: {line}. Error: {e} !!!")
        print(f"--- WAL replay complete. {replayed_ops} operations replayed. ---")


def perform_checkpoint():
    print("\n--- YaraDB: Shutting down, saving data (Checkpointing)... ---")
    try:
        with db_lock:
            with wal_lock:
                data_to_save = [doc.model_dump(by_alias=True) for doc in db_storage]
                temp_file = f"{STORAGE_FILE}.tmp"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, default=str)

                os.replace(temp_file, STORAGE_FILE)

                with open(WAL_FILE, 'w') as f:
                    f.truncate(0)

        print("--- Data successfully checkpointed. WAL cleared. Exiting. ---")
    except Exception as e:
        print(f"!!! CRITICAL ERROR while saving DB: {e} !!!")