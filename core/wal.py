import os
import json
import uuid
import asyncio
from datetime import datetime
from fastapi import HTTPException

from core import state
from core.state import db_storage, db_index_by_id, wal_lock
from models.document_types.document import StandardDocument
from models.document_types.combined_document import CombinedDocument
from core.constants.main_values import WAL_FILE, STORAGE_FILE
from core.state import db_tables_by_name
from models.structure.table import Table

async def log_to_wal(operation: dict):
    log_entry = json.dumps(operation, default=str) + "\n"

    try:
        async with wal_lock:
            await asyncio.to_thread(_write_wal, log_entry)
    except Exception as e:
        print(f"!!! CRITICAL WAL WRITE FAILED: {e} !!!")
        raise HTTPException(status_code=500, detail=f"Database WAL write error: {e}")


def _write_wal(log_entry: str):
    """Synchronous helper for writing to WAL"""
    with open(WAL_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)
        f.flush()
        os.fsync(f.fileno())


def _apply_op_to_memory(op: dict):
    op_type = op.get("op")
    try:
        if op_type == "create":
            doc = StandardDocument.model_validate(op["doc"])
            db_storage.append(doc)
            db_index_by_id[doc.id] = doc

        elif op_type == "create_combined":
            doc = CombinedDocument.model_validate(op["doc"])
            db_storage.append(doc)
            db_index_by_id[doc.id] = doc

        elif op_type == "update":
            doc_id = uuid.UUID(op["doc_id"])
            doc = db_index_by_id.get(doc_id)
            if doc and isinstance(doc, StandardDocument):
                doc.body = op["body"]
                doc.version = op["version"]
                doc.updated_at = datetime.fromisoformat(op["updated_at"])
                doc._update_body_hash()

        elif op_type == "archive":
            doc_id = uuid.UUID(op["doc_id"])
            doc = db_index_by_id.get(doc_id)
            if doc:
                # 'archive()' works for both btw
                doc.archive()
                doc.version = op["version"]
                doc.updated_at = datetime.fromisoformat(op["updated_at"])
        elif op_type == "create_table":
            from models.structure.table import Table
            table = Table.model_validate(op["table"])
            db_tables_by_name[table.name] = table
            print(f"🔄 Replayed table creation: {table.name}")
        elif op_type == "drop_table":
            name = op["name"]
            if name in db_tables_by_name:
                del db_tables_by_name[name]
                print(f"🗑️ Replayed table drop: {name}")

        elif op_type == "create_index":
            table_name = op["table_name"]
            field = op["field"]
            index_type = op["index_type"]

            from core.repository import _get_or_create_index_manager
            index_manager = _get_or_create_index_manager(table_name)

            try:
                index_manager.create_index(field, index_type)
                print(f"🔄 Replayed index creation: {table_name}.{field}")
            except ValueError:
                pass

        elif op_type == "drop_index":
            table_name = op["table_name"]
            field = op["field"]

            if table_name in state.db_table_indexes:
                state.db_table_indexes[table_name].drop_index(field)
                print(f"🗑️ Replayed index drop: {table_name}.{field}")

    except Exception as e:
        print(f"Failed to apply WAL op: {op_type}. Error: {e}")


def load_snapshot():
    try:
        if os.path.exists(STORAGE_FILE):
            print(f"--- Loading data from {STORAGE_FILE} ---")
            with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

                if isinstance(raw_data, list):
                    print("⚠️ Detected legacy storage format. Migrating...")
                    for item in raw_data:
                        try:
                            doc = StandardDocument.model_validate(item)
                            db_storage.append(doc)
                            db_index_by_id[doc.id] = doc
                        except Exception as e:
                            print(f"Skipping invalid doc: {e}")

                elif isinstance(raw_data, dict):
                    tables_data = raw_data.get("tables", [])
                    for t_item in tables_data:
                        try:
                            table = Table.model_validate(t_item)
                            table.documents_count = 0
                            db_tables_by_name[table.name] = table
                        except Exception as e:
                            print(f"❌ Failed to load table: {e}")

                    docs_data = raw_data.get("documents", [])
                    for d_item in docs_data:
                        try:
                            doc = StandardDocument.model_validate(d_item)
                            db_storage.append(doc)
                            db_index_by_id[doc.id] = doc
                        except Exception as e:
                            print(f"❌ Failed to load doc: {e}")

                    print("📊 Recalculating table statistics...")
                    for doc in db_storage:
                        if doc.is_archived():
                            continue

                        t_name = None
                        if isinstance(doc.table_data, dict):
                            t_name = doc.table_data.get("name")
                        elif isinstance(doc.table_data, list) and len(doc.table_data) > 1:
                            t_name = doc.table_data[1]

                        if t_name and t_name in db_tables_by_name:
                            db_tables_by_name[t_name].documents_count += 1

                    print("--- Rebuilding indexes from snapshot... ---")
                    from core.indexes import IndexManager

                    for table_name, table in db_tables_by_name.items():
                        if table.indexes:
                            print(f"   Building indexes for table '{table_name}'...")

                            if table_name not in state.db_table_indexes:
                                state.db_table_indexes[table_name] = IndexManager()

                            index_manager = state.db_table_indexes[table_name]

                            for field, idx_type in table.indexes.items():
                                try:
                                    index_manager.create_index(field, idx_type)
                                except ValueError:
                                    pass

                            docs_in_table = []
                            for doc in db_storage:
                                if doc.is_archived():
                                    continue

                                doc_t_name = None
                                if isinstance(doc.table_data, dict):
                                    doc_t_name = doc.table_data.get("name")
                                elif isinstance(doc.table_data, list) and len(doc.table_data) > 1:
                                    doc_t_name = doc.table_data[1]

                                if doc_t_name == table_name:
                                    docs_in_table.append(doc)

                            index_manager.rebuild_all(docs_in_table)

                    print(f"--- Loaded: {len(db_tables_by_name)} tables, {len(db_storage)} documents. ---")

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
        print("--- Rebuilding indexes... ---")
        for table_name, index_manager in state.db_table_indexes.items():
            docs_in_table = [
                doc for doc in db_storage
                if doc.table_data.get("name") == table_name
            ]
            index_manager.rebuild_all(docs_in_table)
            print(f"✅ Rebuilt indexes for table: {table_name}")
        print(f"--- WAL replay complete. {replayed_ops} operations replayed. ---")


def perform_checkpoint():
    print("\n--- YaraDB: Checkpointing... ---")
    try:
        data_to_save = {
            "tables": [t.model_dump(by_alias=True) for t in db_tables_by_name.values()],
            "documents": [d.model_dump(by_alias=True) for d in db_storage]
        }

        temp_file = f"{STORAGE_FILE}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, default=str)

        os.replace(temp_file, STORAGE_FILE)

        with open(WAL_FILE, 'w') as f:
            f.truncate(0)

        print("--- Checkpoint successful. ---")
    except Exception as e:
        print(f"!!! CRITICAL ERROR while saving DB: {e} !!!")
