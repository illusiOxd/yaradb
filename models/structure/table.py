import uuid
from typing import Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class Table(BaseModel):
    # --- Header ---
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    name: str

    # --- Body ---
    settings: Dict[str, Any] = Field(default_factory=dict)

    # --- Footer ---
    config_hash: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    documents_count: int = 0