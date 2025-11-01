from typing import Any, Dict, List
from pydantic import BaseModel, Field

import uuid
from datetime import datetime, timezone

class CreateRequest(BaseModel):
    name: str
    body: Dict[str, Any]


class UpdateRequest(BaseModel):
    version: int
    body: Dict[str, Any]

class CombineRequest(BaseModel):
    name: str
    document_ids: List[uuid.UUID]
    merge_strategy: str = "overwrite"

