import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from uuid import UUID

from core import wal
from core import state
from models.document_types.document import StandardDocument
from models.document_types.combined_document import CombinedDocument
from models.models_init.document_init import create_document as init_doc
from models.models_init.combined_document_init import create_combined_document as init_combined_doc

async def create_document(name: str, body: Dict[str, Any]) -> StandardDocument:
    new_doc = init_doc(name=name, body=body)
    if new_doc is None:
        raise ValueError("Error creating document (validation failed).")

    wal_op = {"op": "create", "doc": new_doc.model_dump(by_alias=True)}

    async with state.db_lock:
        await wal.log_to_wal(wal_op)
        state.db_storage.append(new_doc)
        state.db_index_by_id[new_doc.id] = new_doc

    return new_doc


async def get_document(doc_id: uuid.UUID) -> StandardDocument | None:
    async with state.db_lock:
        doc = state.db_index_by_id.get(doc_id)
        if doc and not doc.is_archived():
            return doc
    return None


async def find_documents(filter_body: Dict[str, Any], include_archived: bool = False) -> List[StandardDocument]:
    results: List[StandardDocument] = []
    async with state.db_lock:
        storage_copy = list(state.db_storage)

    for doc in storage_copy:
        if doc.is_archived() and not include_archived:
            continue

        matches = True
        for key, value in filter_body.items():
            if doc.get(key, default=object()) != value:
                matches = False
                break
        if matches:
            results.append(doc)

    return results


async def update_document(doc_id: uuid.UUID, version: int, body: Dict[str, Any]) -> StandardDocument:
    async with state.db_lock:
        doc = state.db_index_by_id.get(doc_id)

        if not doc:
            raise LookupError("Document not found")
        if doc.is_archived():
            raise LookupError("Document not found")
        if doc.version != version:
            raise ValueError(f"Conflict: Document version mismatch. DB is at {doc.version}, you sent {version}")

        now = datetime.now(timezone.utc)
        new_version = doc.version + 1

        wal_op = {
            "op": "update",
            "doc_id": str(doc_id),
            "version": new_version,
            "body": body,
            "updated_at": now.isoformat()
        }

        await wal.log_to_wal(wal_op)

        doc.body = body
        doc.version = new_version
        doc.updated_at = now
        doc._update_body_hash()

        return doc


async def archive_document(doc_id: uuid.UUID) -> StandardDocument:
    async with state.db_lock:
        doc = state.db_index_by_id.get(doc_id)

        if not doc:
            raise LookupError("Document not found")
        if doc.is_archived():
            raise LookupError("Document not found")

        new_version = doc.version + 1
        now = datetime.now(timezone.utc)

        wal_op = {
            "op": "archive",
            "doc_id": str(doc_id),
            "version": new_version,
            "updated_at": now.isoformat()
        }

        await wal.log_to_wal(wal_op)

        doc.archive()

        doc.version = new_version
        doc.updated_at = now
        doc.archived_at = now

        return doc

async def combine_documents(name: str, document_ids: List[uuid.UUID],
                            merge_strategy: str = "overwrite") -> CombinedDocument:
    if not document_ids:
        raise ValueError("No documents to combine")
    if len(document_ids) > 100:
        raise ValueError("Can't combine more than 100 documents at once :(")

    documents: List[StandardDocument] = []

    async with state.db_lock:
        for doc_id in document_ids:
            doc = state.db_index_by_id.get(doc_id)

            if not doc:
                raise ValueError(f"Document not found: {doc_id}")

            if doc.is_archived():
                raise ValueError(f"Can't combine archivated document: {doc_id}")

            documents.append(doc)

            if merge_strategy == "overwrite":
                combined_body = _merge_overwrite(documents)
            elif merge_strategy == "append":
                combined_body = _merge_append(documents)
            elif merge_strategy == "namespace":
                combined_body = _merge_namespace(documents)
            else:
                raise ValueError(f"Unknown merge_strategy: {merge_strategy}")

            combined_body["_metadata"] = {
                "source_documents": [
                    {
                        "id": str(doc.id),
                        "name": doc.name,
                        "version": doc.version
                    }
                    for doc in documents
                ],
                "merge_strategy": merge_strategy,
                "combined_at": datetime.now(timezone.utc).isoformat()
            }

            new_combined_doc = init_combined_doc(
                name=name,
                body=combined_body,
                document_ids=document_ids
            )

            if new_combined_doc is None:
                raise ValueError("Failed to create CombinedDocument :(")

            wal_op = {
                "op": "create_combined",
                "doc": new_combined_doc.model_dump(by_alias=True)
            }

            await wal.log_to_wal(wal_op)

            state.db.storage.append(new_combined_doc)
            state.db_index_by_id[new_combined_doc.id] = new_combined_doc
        return new_combined_doc

def _merge_overwrite(documents: List[StandardDocument]) -> Dict[str, Any]:
    result = {}
    for doc in documents:
        result.update(doc.body)
    return result


def _merge_append(documents: List[StandardDocument]) -> Dict[str, Any]:
    result = {}
    for doc in documents:
        for key, value in doc.body.items():
            if key in result:
                if isinstance(result[key], list) and isinstance(value, list):
                    result[key].extend(value)
                else:
                    result[key] = value
            else:
                result[key] = value
    return result


def _merge_namespace(documents: List[StandardDocument]) -> Dict[str, Any]:
    result = {}
    for i, doc in enumerate(documents):
        result[f"doc_{i}_{doc.name}"] = doc.body
    return result


async def get_combined_document(doc_id: uuid.UUID) -> CombinedDocument | None:
    async with state.db_lock:
        doc = state.db_index_by_id.get(doc_id)

        if doc and isinstance(doc, CombinedDocument) and not doc.is_archived():
            return doc

    return None


async def get_source_documents(combined_doc_id: uuid.UUID) -> List[StandardDocument]:
    combined_doc = await get_combined_document(combined_doc_id)

    if not combined_doc:
        raise LookupError(f"CombinedDocument not found: {combined_doc_id}")

    source_docs: List[StandardDocument] = []

    async with state.db_lock:
        for doc_id in combined_doc.document_ids:
            doc = state.db_index_by_id.get(doc_id)
            if doc and isinstance(doc, StandardDocument):
                source_docs.append(doc)

    return source_docs

