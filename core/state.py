import asyncio
from typing import List, Dict
import uuid
from models.document import StandardDocument

db_storage: List[StandardDocument] = []
db_index_by_id: Dict[uuid.UUID, StandardDocument] = {}

db_lock = asyncio.Lock()
wal_lock = asyncio.Lock()