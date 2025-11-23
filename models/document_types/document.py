import uuid
import json
import hashlib
from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator
from typing import List, Any, Dict

from models.interfaces.strategy_interface import IValueProcessor
from models.processors.document_processor import DefaultProcessor, EmailProcessor, AgeProcessor


class StandardDocument(BaseModel):
    # --- Header ---
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    name: str
    table_data: Dict[str, Any] = Field(default_factory=dict)

    # --- Body ---
    body: Dict[str, Any]

    # --- Footer ---
    body_hash: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    updated_at: datetime | None = None
    version: int = 1
    archived_at: datetime | None = None

    def _update_body_hash(self) -> None:
        body_str = json.dumps(self.body, sort_keys=True).encode('utf-8')
        hash_obj = hashlib.sha256(body_str)
        self.body_hash = hash_obj.hexdigest()

    @model_validator(mode='after')
    def _run_hash_validator(self) -> 'StandardDocument':
        self._update_body_hash()
        return self

    _processors: Dict[str, IValueProcessor] = {
        "email": EmailProcessor(),
        "age": AgeProcessor()
    }
    _default_processor: IValueProcessor = DefaultProcessor()

    def get_id_str(self) -> str:
        return str(self.id)

    def get(self, key: str, default: Any = None) -> Any:
        return self.body.get(key, default)

    def pretty(self) -> str:
        return self.model_dump_json(indent=2, by_alias=True)

    def is_archived(self) -> bool:
        return self.archived_at is not None

    def archive(self) -> None:
        if not self.is_archived():
            now = datetime.now(timezone.utc)

            self.archived_at = now
            self.updated_at = now
            self.version += 1

    def update_one_value(self, value_name: str, new_value: Any):
        processor = self._processors.get(value_name, self._default_processor)

        try:
            processed_value = processor.process(new_value)
        except ValueError as e:
            print(f"Validation error for '{value_name}': {e}")
            return

        self.body[value_name] = processed_value

        now = datetime.now(timezone.utc)
        self.updated_at = now
        self.version += 1
        self._update_body_hash()

        print(f"Updated '{value_name}' successfully.")