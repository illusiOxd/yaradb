import uuid
from datetime import datetime
from typing import List, Dict, Any

from core import wal
from core import state
from models.document import StandardDocument
from models.models_init.document_init import create_document

def create_document(name: str, body: Dict[str, Any]) -> StandardDocument:
    new_doc = create_document(name=name, body=body)
    if new_doc is None:
        raise ValueError("Error creating document (validation failed).")  #

    wal_op = {"op": "create", "doc": new_doc.model_dump(by_alias=True)}

    with state.db_lock:
        wal.log_to_wal(wal_op)
        state.db_storage.append(new_doc)
        state.db_index_by_id[new_doc.id] = new_doc

    return new_doc


def get_document(doc_id: uuid.UUID) -> StandardDocument | None:
    with state.db_lock:
        doc = state.db_index_by_id.get(doc_id)
        if doc and not doc.is_archived():  #
            return doc
    return None


def find_documents(filter_body: Dict[str, Any], include_archived: bool = False) -> List[StandardDocument]:
    results: List[StandardDocument] = []
    with state.db_lock:
        storage_copy = list(state.db_storage)

    for doc in storage_copy:
        if doc.is_archived() and not include_archived:
            continue

        matches = True
        for key, value in filter_body.items():
            if doc.body.get(key, default=object()) != value:
                matches = False
                break
        if matches:
            results.append(doc)

    return results


def update_document(doc_id: uuid.UUID, version: int, body: Dict[str, Any]) -> StandardDocument:
    with state.db_lock:
        doc = state.db_index_by_id.get(doc_id)

        if not doc:
            raise LookupError("Document not found")
        if doc.is_archived():
            raise ValueError("Cannot update an archived document")
        if doc.version != version:
            raise ValueError(f"Conflict: Document version mismatch. DB is at {doc.version}, you sent {version}")

        now = datetime.now(datetime.UTC)
        new_version = doc.version + 1

        wal_op = {
            "op": "update",
            "doc_id": str(doc_id),
            "version": new_version,
            "body": body,
            "updated_at": now.isoformat()
        }

        wal.log_to_wal(wal_op)

        doc.body = body
        doc.version = new_version
        doc.updated_at = now
        doc.calculate_body_hash()

        return doc


def archive_document(doc_id: uuid.UUID) -> StandardDocument:
    with state.db_lock:
        doc = state.db_index_by_id.get(doc_id)

        if not doc:
            raise LookupError("Document not found")
        if doc.is_archived():
            raise ValueError("Document already archived")

        new_version = doc.version + 1
        now = datetime.now(datetime.UTC)

        wal_op = {
            "op": "archive",
            "doc_id": str(doc_id),
            "version": new_version,
            "updated_at": now.isoformat()
        }

        wal.log_to_wal(wal_op)

        doc.archive()

        doc.version = new_version
        doc.updated_at = now
        doc.archived_at = now

        return doc