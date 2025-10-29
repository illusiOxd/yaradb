import uuid
import json
import hashlib
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from typing import List, Any, Dict


class StandardDocument(BaseModel):
    # --- Header ---
    # (id теперь публичный, alias работает при загрузке/выгрузке)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    name: str

    # --- Body ---
    body: Dict[str, Any]

    # --- Footer ---
    # (body_hash теперь публичный)
    body_hash: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)

    @model_validator(mode='after')
    def calculate_body_hash(self) -> 'StandardDocument':
        """
        Корректно вычисляет хеш и сохраняет в 'self.body_hash'
        """
        body_str = json.dumps(self.body, sort_keys=True).encode('utf-8')
        hash_obj = hashlib.sha256(body_str)

        # Исправлено: сохраняем в 'body_hash', а не '__body_hash'
        self.body_hash = hash_obj.hexdigest()
        return self

    # --- 💡 НОВЫЕ ФУНКЦИИ (Твой запрос) ---

    def get_id_str(self) -> str:
        """
        Возвращает ID в виде удобной строки.
        (Я переименовал get_id в get_id_str для ясности)
        """
        return str(self.id)

    def get(self, key: str, default: Any = None) -> Any:
        """
        ПОЛЕЗНАЯ ФУНКЦИЯ: Позволяет легко "заглянуть"
        внутрь 'body' и достать значение по ключу.

        Пример: doc.get("username")
        """
        return self.body.get(key, default)

    def pretty(self) -> str:
        """
        ПОЛЕЗНАЯ ФУНКЦИЯ: Возвращает "красивый"
        отформатированный JSON всего документа.
        Идеально для вывода и логов.
        """
        # .model_dump_json() - встроенный метод Pydantic
        # by_alias=True - использует "_id" вместо "id"
        return self.model_dump_json(indent=2, by_alias=True)


