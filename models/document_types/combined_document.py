import uuid
import json
import hashlib
from typing import List, Dict, Any
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone


class CombinedDocument(BaseModel):
    """
    Document that combines data from multiple StandardDocuments.

    Attributes:
        id: Unique document UUID
        name: Name of the combined document
        document_ids: List of source document UUIDs
        body: Combined data from all documents
        body_hash: SHA-256 hash of body for integrity verification
        created_at: Creation timestamp
        updated_at: Last update timestamp
        version: Document version (for OCC)
        archived_at: Archive timestamp (soft delete)
    """

    # --- Header ---
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    name: str

    # --- Document References ---
    document_ids: List[uuid.UUID] = Field(
        description="UUIDs of source documents"
    )

    # --- Body ---
    body: Dict[str, Any] = Field(
        description="Combined data from all documents"
    )

    # --- Footer (Metadata) ---
    body_hash: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = None
    version: int = 1
    archived_at: datetime | None = None

    def _update_body_hash(self) -> None:
        """Calculates and updates SHA-256 hash of body"""
        body_str = json.dumps(self.body, sort_keys=True).encode('utf-8')
        hash_obj = hashlib.sha256(body_str)
        self.body_hash = hash_obj.hexdigest()

    @model_validator(mode='after')
    def _run_hash_validator(self) -> 'CombinedDocument':
        """Automatically calculates hash after creation/update"""
        self._update_body_hash()
        return self

    def get_id_str(self) -> str:
        """Returns ID as string"""
        return str(self.id)

    def get(self, key: str, default: Any = None) -> Any:
        """Gets value from body by key"""
        return self.body.get(key, default)

    def pretty(self) -> str:
        """Returns pretty-formatted JSON"""
        return self.model_dump_json(indent=2, by_alias=True)

    def is_archived(self) -> bool:
        """Checks if document is archived"""
        return self.archived_at is not None

    def archive(self) -> None:
        """Archives document (soft delete)"""
        if not self.is_archived():
            now = datetime.now(timezone.utc)
            self.archived_at = now
            self.updated_at = now
            self.version += 1

    def get_source_documents_count(self) -> int:
        """Returns number of source documents"""
        return len(self.document_ids)

    def has_source_document(self, doc_id: uuid.UUID) -> bool:
        """Checks if document is in the source list"""
        return doc_id in self.document_ids

    def add_metadata(self, key: str, value: Any) -> None:
        """Adds metadata to body"""
        if "_metadata" not in self.body:
            self.body["_metadata"] = {}
        self.body["_metadata"][key] = value
        self._update_body_hash()