from typing import Any, Dict, List
from pydantic import ValidationError
from models.document_types.combined_document import CombinedDocument
import uuid


def create_combined_document(
        name: str,
        body: Dict[str, Any],
        document_ids: List[uuid.UUID]
) -> CombinedDocument | None:
    try:
        new_combined_doc = CombinedDocument(
            name=name,
            body=body,
            document_ids=document_ids
        )
        return new_combined_doc
    except ValidationError as e:
        print(f"❌ Validation error creating CombinedDocument: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error creating CombinedDocument: {e}")
        return None