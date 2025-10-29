from abc import ABC, abstractmethod
from typing import Any

class IValueProcessor(ABC):
    @abstractmethod
    def process(self, value: Any) -> Any:
        pass