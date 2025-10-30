from typing import Literal, Any, Dict, List
import uuid
from pydantic import BaseModel

class UpdateOperation(BaseModel):
    op: Literal["update"] = "update"
    doc_id: uuid.UUID
    version: int
    body: Dict[str, Any]

class ArchiveOperation(BaseModel):
    op: Literal["archive"] = "archive"
    doc_id: uuid.UUID
    version: int

class TransactionRequest(BaseModel):
    operations: List[UpdateOperation | ArchiveOperation] 