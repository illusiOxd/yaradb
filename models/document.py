import uuid
import json
import hashlib
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from typing import List, Any, Dict
from interfaces.strategy_interface import IValueProcessor
from models.types.processors.document_processor import DefaultProcessor, EmailProcessor, AgeProcessor

class StandardDocument(BaseModel):
    # --- Header ---
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    name: str

    # --- Body ---
    body: Dict[str, Any]

    # --- Footer ---
    body_hash: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)

    updated_at: datetime | None = None
    version: int = 1
    archived_at: datetime | None = None


    @model_validator(mode='after')
    def calculate_body_hash(self) -> 'StandardDocument':
        """
        Корректно вычисляет хеш и сохраняет в 'self.body_hash'
        """
        body_str = json.dumps(self.body, sort_keys=True).encode('utf-8')
        hash_obj = hashlib.sha256(body_str)
        self.body_hash = hash_obj.hexdigest()
        return self

    _processors: Dict[str, IValueProcessor] = {
        "email": EmailProcessor(),
        "age": AgeProcessor()
    }
    _default_processor: IValueProcessor = DefaultProcessor()

    # --- Удобные методы ---

    def get_id_str(self) -> str:
        """
        Возвращает ID в виде удобной строки.
        """
        return str(self.id)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Позволяет легко "заглянуть" внутрь 'body'.
        """
        return self.body.get(key, default)

    def pretty(self) -> str:
        """
        Возвращает "красивый" отформатированный JSON.
        """
        return self.model_dump_json(indent=2, by_alias=True)


    def is_archived(self) -> bool:
        """Проверяет, "удален" ли (архивирован) документ."""
        return self.archived_at is not None

    def archive(self) -> None:
        """
        "Мягко" удаляет (архивирует) документ.
        Этот метод нужно вызывать из твоего эндпоинта /document/archive/{doc_id}
        """
        if not self.is_archived():
            now = datetime.now()
            self.archived_at = now
            self.updated_at = now
            self.version += 1

    def update_one_value(self, value_name: str, new_value: Any):
        """
        Обновляет одно значение, используя 'позднее связывание'
        для выбора правильного обработчика (Стратегии).
        """

        processor = self._processors.get(value_name, self._default_processor)

        try:
            processed_value = processor.process(new_value)

        except ValueError as e:
            print(f"Ошибка валидации для '{value_name}': {e}")
            return

        self.body[value_name] = processed_value

        now = datetime.now()
        self.updated_at = now
        self.version += 1
        self.calculate_body_hash()

        print(f"Updated '{value_name}' successfully.")



