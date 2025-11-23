import uuid
import json

from datetime import datetime, timezone
from typing import List, Dict, Any
from uuid import UUID

from core import wal
from core import state
from models.document_types.document import StandardDocument
from models.document_types.combined_document import CombinedDocument
from models.models_init.document_init import create_document as init_doc
from models.models_init.combined_document_init import create_combined_document as init_combined_doc
from models.structure.table import Table
from models.api import CreateTableRequest, TableResponse
from core.constants.main_values import STORAGE_FILE, WAL_FILE


async def create_document(name: str, body: Dict[str, Any], table_name: str) -> StandardDocument:
    async with state.db_lock:
        table = state.db_tables_by_name.get(table_name)

        if not table:
            table = Table(name=table_name)
            state.db_tables_by_name[table_name] = table

        if table.settings.get("read_only", False):
            raise ValueError(f"Table '{table_name}' is READ-ONLY. Cannot create documents.")

        unique_fields = table.settings.get("unique_fields", [])
        for field in unique_fields:
            value = body.get(field)
            if value is not None:
                if _check_duplicate(table_name, field, value):
                    raise ValueError(f"Conflict: Value '{value}' for unique field '{field}' already exists.")

    if "schema" in table.settings:
        try:
            from jsonschema import validate
            validate(instance=body, schema=table.settings["schema"])
        except Exception as e:
            raise ValueError(f"Schema validation failed: {e}")

    tabledata = {
        "id": str(table.id),
        "name": table.name
    }

    new_doc = init_doc(name=name, body=body,
                       tabledata=tabledata)

    if new_doc is None:
        raise ValueError("Error creating document (pydantic validation failed).")

    wal_op = {"op": "create", "doc": new_doc.model_dump(by_alias=True)}

    async with state.db_lock:
        await wal.log_to_wal(wal_op)
        state.db_storage.append(new_doc)
        state.db_index_by_id[new_doc.id] = new_doc
        table.documents_count += 1

    return new_doc


async def get_document(doc_id: uuid.UUID) -> StandardDocument | CombinedDocument | None:
    async with state.db_lock:
        doc = state.db_index_by_id.get(doc_id)

        if not doc or doc.is_archived():
            return None

        if isinstance(doc, CombinedDocument):
            return await get_combined_document(doc_id)


        return doc


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

        table_name = None
        if isinstance(doc.table_data, dict):
            table_name = doc.table_data.get("name")
        elif isinstance(doc.table_data, list) and len(doc.table_data) > 1:
            table_name = doc.table_data[1]

        if table_name:
            table = state.db_tables_by_name.get(table_name)
            if table:
                if table.settings.get("read_only", False):
                    raise ValueError(f"Table '{table_name}' is READ-ONLY. Cannot update documents.")

                unique_fields = table.settings.get("unique_fields", [])
                for field in unique_fields:
                    if field in body:
                        new_value = body[field]
                        if _check_duplicate(table_name, field, new_value, exclude_doc_id=doc_id):
                            raise ValueError(
                                f"Conflict: Value '{new_value}' for unique field '{field}' is already taken.")

                if "schema" in table.settings:
                    try:
                        from jsonschema import validate
                        validate(instance=body, schema=table.settings["schema"])
                    except Exception as e:
                        raise ValueError(f"Schema validation failed for update: {e}")

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

            state.db_storage.append(new_combined_doc)
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


async def create_new_table(request: CreateTableRequest) -> Table:
    async with state.db_lock:
        if request.name in state.db_tables_by_name:
            raise ValueError(f"Table '{request.name}' already exists.")

        settings = {}

        if request.mode == "strict":
            if not request.schema_definition:
                raise ValueError("Strict mode requires a 'schema_definition'!")

            schema = request.schema_definition.copy()
            schema["additionalProperties"] = False
            settings["schema"] = schema

        if request.read_only:
            settings["read_only"] = True

        if hasattr(request, "unique_fields") and request.unique_fields:
            settings["unique_fields"] = request.unique_fields

        new_table = Table(
            name=request.name,
            settings=settings
        )

        wal_op = {"op": "create_table", "table": new_table.model_dump(by_alias=True)}
        await wal.log_to_wal(wal_op)

        state.db_tables_by_name[new_table.name] = new_table

        return new_table


async def list_tables() -> List[TableResponse]:
    tables_list = []

    for table in state.db_tables_by_name.values():

        mode = "free"
        if "schema" in table.settings and table.settings["schema"].get("additionalProperties") is False:
            mode = "strict"

        is_read_only = table.settings.get("read_only", False)

        tables_list.append(TableResponse(
            id=table.id,
            name=table.name,
            mode=mode,
            documents_count=table.documents_count,
            is_read_only=is_read_only,
            created_at=table.created_at
        ))

    return tables_list


async def get_table_details(name: str) -> Table | None:
    return state.db_tables_by_name.get(name)


async def delete_table(name: str):
    async with state.db_lock:
        if name not in state.db_tables_by_name:
            raise LookupError(f"Table '{name}' not found")

        del state.db_tables_by_name[name]

        wal_op = {"op": "drop_table", "name": name}
        await wal.log_to_wal(wal_op)

        return True


async def get_documents_in_table(table_name: str) -> List[StandardDocument]:
    results = []

    if table_name not in state.db_tables_by_name:
        raise LookupError(f"Table '{table_name}' not found")

    async with state.db_lock:
        for doc in state.db_storage:
            if doc.is_archived():
                continue

            doc_table_name = doc.table_data.get("name")

            if doc_table_name == table_name:
                results.append(doc)

    return results


async def wipe_all_data():
    async with state.db_lock:
        state.db_storage.clear()
        state.db_index_by_id.clear()
        state.db_tables_by_name.clear()

        with open(WAL_FILE, 'w') as f:
            f.truncate(0)

        empty_state = {"tables": [], "documents": []}
        with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(empty_state, f)

    return True


def _check_duplicate(table_name: str, field: str, value: Any, exclude_doc_id: uuid.UUID = None) -> bool:
    if table_name not in state.db_tables_by_name:
        return False

    for doc in state.db_storage:
        if doc.is_archived() or doc.id == exclude_doc_id:
            continue

        doc_table_data = getattr(doc, "table_data", {})
        if isinstance(doc_table_data, dict):
            current_table_name = doc_table_data.get("name")
        else:
            current_table_name = doc_table_data[1] if isinstance(doc_table_data, list) and len(
                doc_table_data) > 1 else None

        if current_table_name != table_name:
            continue

        if doc.body.get(field) == value:
            return True

    return False