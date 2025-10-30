from typing import Any, Dict
from pydantic import BaseModel

class CreateRequest(BaseModel):
    name: str
    body: Dict[str, Any]


class UpdateRequest(BaseModel):
    version: int
    body: Dict[str, Any]

