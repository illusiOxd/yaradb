from typing import Any, Dict
from pydantic import ValidationError
from models.document_types.document import StandardDocument

def create_document(name: str, body: Dict[str, Any]) -> StandardDocument | None:
    try:
        new_doc = StandardDocument(
            name=name,
            body=body
        )
        return new_doc
    except ValidationError as e:
        print(f"Pydantic validation error: {e}")
        return None