import uuid
from typing import Any, Dict, List, Set, Optional
from collections import defaultdict
from datetime import datetime
import bisect


class BaseIndex:
    def __init__(self, field_name: str):
        self.field_name = field_name
        self.index_type = "base"

    def add(self, doc_id: uuid.UUID, value: Any) -> None:
        """add document to index"""
        raise NotImplementedError

    def remove(self, doc_id: uuid.UUID, value: Any) -> None:
        """delete document from index"""
        raise NotImplementedError

    def lookup(self, value: Any) -> Set[uuid.UUID]:
        """search documents by exact value"""
        raise NotImplementedError

    def range_lookup(self, min_val: Any = None, max_val: Any = None) -> Set[uuid.UUID]:
        """search documents by range"""
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class HashIndex(BaseIndex):
    """
    Hash Index - O(1) lookup for exact matches only
    """

    def __init__(self, field_name: str):
        super().__init__(field_name)
        self.index_type = "hash"
        # value -> set of doc_ids
        self._data: Dict[Any, Set[uuid.UUID]] = defaultdict(set)

    def add(self, doc_id: uuid.UUID, value: Any) -> None:
        """O(1) - insertion"""
        if value is None:
            return

        if isinstance(value, list):
            for item in value:
                self._data[item].add(doc_id)
        else:
            self._data[value].add(doc_id)

    def remove(self, doc_id: uuid.UUID, value: Any) -> None:
        """O(1) - deletion"""
        if value is None:
            return

        if isinstance(value, list):
            for item in value:
                self._data[item].discard(doc_id)
                if not self._data[item]:
                    del self._data[item]
        else:
            self._data[value].discard(doc_id)
            if not self._data[value]:
                del self._data[value]

    def lookup(self, value: Any) -> Set[uuid.UUID]:
        """O(1) - search by exact value"""
        return self._data.get(value, set()).copy()

    def range_lookup(self, min_val: Any = None, max_val: Any = None) -> Set[uuid.UUID]:
        """Hash index doesn't support range queries"""
        raise NotImplementedError("Hash index doesn't support range queries. Use BTreeIndex instead.")

    def clear(self) -> None:
        self._data.clear()

    def stats(self) -> Dict[str, Any]:
        """Index statistics"""
        total_docs = sum(len(docs) for docs in self._data.values())
        return {
            "type": self.index_type,
            "field": self.field_name,
            "unique_values": len(self._data),
            "total_entries": total_docs,
            "avg_docs_per_value": total_docs / len(self._data) if self._data else 0
        }


class BTreeIndex(BaseIndex):
    """
    B-Tree Index - O(log n) lookup, supports range queries
    """

    def __init__(self, field_name: str):
        super().__init__(field_name)
        self.index_type = "btree"
        self._sorted_keys: List[Any] = []
        self._data: Dict[Any, Set[uuid.UUID]] = defaultdict(set)

    def add(self, doc_id: uuid.UUID, value: Any) -> None:
        """O(log n) - insertion"""
        if value is None:
            return

        if value not in self._data:
            bisect.insort(self._sorted_keys, value)

        self._data[value].add(doc_id)

    def remove(self, doc_id: uuid.UUID, value: Any) -> None:
        """O(log n) - deletion"""
        if value is None or value not in self._data:
            return

        self._data[value].discard(doc_id)

        if not self._data[value]:
            del self._data[value]
            self._sorted_keys.remove(value)

    def lookup(self, value: Any) -> Set[uuid.UUID]:
        """O(log n) - search by exact value"""
        return self._data.get(value, set()).copy()

    def range_lookup(self, min_val: Any = None, max_val: Any = None) -> Set[uuid.UUID]:
        """
        O(log n + k) - range query
        k = quantity of matched keys
        """
        result = set()

        start_idx = 0 if min_val is None else bisect.bisect_left(self._sorted_keys, min_val)
        end_idx = len(self._sorted_keys) if max_val is None else bisect.bisect_right(self._sorted_keys, max_val)

        for i in range(start_idx, end_idx):
            key = self._sorted_keys[i]
            result.update(self._data[key])

        return result

    def clear(self) -> None:
        self._sorted_keys.clear()
        self._data.clear()

    def stats(self) -> Dict[str, Any]:
        total_docs = sum(len(docs) for docs in self._data.values())
        return {
            "type": self.index_type,
            "field": self.field_name,
            "unique_values": len(self._data),
            "total_entries": total_docs,
            "min_value": self._sorted_keys[0] if self._sorted_keys else None,
            "max_value": self._sorted_keys[-1] if self._sorted_keys else None
        }


class IndexManager:
    def __init__(self):
        self.indexes: Dict[str, BaseIndex] = {}

    def create_index(self, field_name: str, index_type: str = "hash") -> BaseIndex:
        if field_name in self.indexes:
            raise ValueError(f"Index for field '{field_name}' already exists")

        if index_type == "hash":
            index = HashIndex(field_name)
        elif index_type == "btree":
            index = BTreeIndex(field_name)
        else:
            raise ValueError(f"Unknown index type: {index_type}")

        self.indexes[field_name] = index
        return index

    def drop_index(self, field_name: str) -> bool:
        if field_name in self.indexes:
            del self.indexes[field_name]
            return True
        return False

    def has_index(self, field_name: str) -> bool:
        return field_name in self.indexes

    def get_index(self, field_name: str) -> Optional[BaseIndex]:
        return self.indexes.get(field_name)

    def add_document(self, doc_id: uuid.UUID, body: Dict[str, Any]) -> None:
        for field_name, index in self.indexes.items():
            value = self._get_nested_value(body, field_name)
            if value is not None:
                index.add(doc_id, value)

    def remove_document(self, doc_id: uuid.UUID, body: Dict[str, Any]) -> None:
        for field_name, index in self.indexes.items():
            value = self._get_nested_value(body, field_name)
            if value is not None:
                index.remove(doc_id, value)

    def update_document(self, doc_id: uuid.UUID, old_body: Dict[str, Any],
                        new_body: Dict[str, Any]) -> None:
        for field_name, index in self.indexes.items():
            old_value = self._get_nested_value(old_body, field_name)
            new_value = self._get_nested_value(new_body, field_name)

            if old_value != new_value:
                if old_value is not None:
                    index.remove(doc_id, old_value)
                if new_value is not None:
                    index.add(doc_id, new_value)

    def query(self, field_name: str, value: Any = None,
              min_val: Any = None, max_val: Any = None) -> Set[uuid.UUID]:
        index = self.indexes.get(field_name)
        if not index:
            raise ValueError(f"No index for field '{field_name}'")

        if value is not None:
            return index.lookup(value)

        if min_val is not None or max_val is not None:
            return index.range_lookup(min_val, max_val)

        raise ValueError("Either 'value' or 'min_val/max_val' must be provided")

    def rebuild_all(self, documents: List[Any]) -> None:
        for index in self.indexes.values():
            index.clear()

        for doc in documents:
            if hasattr(doc, 'id') and hasattr(doc, 'body'):
                self.add_document(doc.id, doc.body)

    def list_indexes(self) -> List[Dict[str, Any]]:
        return [index.stats() for index in self.indexes.values()]

    def clear_all(self) -> None:
        for index in self.indexes.values():
            index.clear()

    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        keys = field_path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value