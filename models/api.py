from typing import Any, Dict, List, Literal
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class CreateRequest(BaseModel):
    table_name: str
    name: str | None = None
    body: Dict[str, Any]

class UpdateRequest(BaseModel):
    version: int
    body: Dict[str, Any]

class CombineRequest(BaseModel):
    name: str
    document_ids: List[uuid.UUID]
    merge_strategy: str = "overwrite"

class CreateTableRequest(BaseModel):
    name: str
    mode: Literal["free", "strict"] = "free"
    schema_definition: Dict[str, Any] | None = None
    read_only: bool = False
    unique_fields: List[str] = []

class TableResponse(BaseModel):
    id: uuid.UUID
    name: str
    mode: str
    documents_count: int
    is_read_only: bool
    created_at: datetime

class SelfDestructRequest(BaseModel):
    verification_phrase: str = Field(..., description="Type 'YaraDB' backwards")
    safety_pin: int = Field(..., description="Enter (Current Year + 1)")
    confirm: bool = True

class CreateIndexRequest(BaseModel):
    field: str
    index_type: Literal["hash", "btree"] = "hash"

class IndexResponse(BaseModel):
    table_name: str
    field: str
    index_type: str
    created_at: datetime