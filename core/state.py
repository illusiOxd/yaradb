import asyncio
from typing import List, Dict
import uuid
from models.document_types.document import StandardDocument
from models.document_types.combined_document import CombinedDocument

db_storage: List[StandardDocument] = []
db_index_by_id: Dict[uuid.UUID, StandardDocument] = {}
db_index_by_id_comb: Dict[uuid.UUID, CombinedDocument]

try:
    db_lock = asyncio.Lock()
    wal_lock = asyncio.Lock()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    db_lock = asyncio.Lock()
    wal_lock = asyncio.Lock()