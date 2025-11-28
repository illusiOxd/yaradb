import asyncio
from typing import List, Dict
import uuid
from models.document_types.document import StandardDocument
from models.document_types.combined_document import CombinedDocument
from models.structure.table import Table
from core.indexes import IndexManager

db_storage: List[StandardDocument] = []
db_index_by_id: Dict[uuid.UUID, StandardDocument] = {}
db_tables_by_name: Dict[str, Table] = {}

db_table_indexes: Dict[str, IndexManager] = {}

try:
    db_lock = asyncio.Lock()
    wal_lock = asyncio.Lock()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    db_lock = asyncio.Lock()
    wal_lock = asyncio.Lock()