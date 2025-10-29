from typing import Any
from models.interfaces.strategy_interface import IValueProcessor


class DefaultProcessor(IValueProcessor):
    def process(self, value: Any) -> Any:
        return value


class EmailProcessor(IValueProcessor):
    def process(self, value: Any) -> Any:
        value_str = str(value).lower()
        if "@" not in value_str:
            raise ValueError("Invalid email format")
        return value_str


class AgeProcessor(IValueProcessor):
    def process(self, value: Any) -> Any:
        value_int = int(value)
        if value_int < 0:
            raise ValueError("Age cannot be negative")
        return value_int