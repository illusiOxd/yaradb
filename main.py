from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import threading
import uuid
import json
import os
from contextlib import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime

try:
    from models.document import StandardDocument
    from models.models_init.document_init import create_document as create_doc_func
except ImportError:
    print("!!! КРИТИЧЕСКАЯ ОШИБКА: Не могу найти 'models/...' !!!")


    class StandardDocument(BaseModel):
        id: uuid.UUID
        version: int = 1

        def is_archived(self) -> bool: return False

        def archive(self): pass

        def get(self, key: str) -> Any: return None

        def calculate_body_hash(self): pass


    def create_doc_func(name: str, body: Dict[str, Any]) -> None:
        return None


class CreateRequest(BaseModel):
    name: str
    body: Dict[str, Any]


class UpdateRequest(BaseModel):
    version: int
    body: Dict[str, Any]



db_storage: List[StandardDocument] = []
db_lock = threading.Lock()
db_index_by_id: Dict[uuid.UUID, StandardDocument] = {}

STORAGE_FILE = "yaradb_storage.json"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_storage, db_index_by_id
    print("--- YaraDB: Запуск... ---")

    try:
        if os.path.exists(STORAGE_FILE):
            print(f"--- Загрузка данных из {STORAGE_FILE} ---")
            with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

                for item in raw_data:
                    doc = StandardDocument.model_validate(item)
                    db_storage.append(doc)
                    db_index_by_id[doc.id] = doc
            print(f"--- Успешно загружено {len(db_storage)} документов. ---")
        else:
            print(f"--- Файл {STORAGE_FILE} не найден. Запуск с пустой БД. ---")
    except Exception as e:
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА при загрузке БД: {e} !!!")

    yield

    print("\n--- YaraDB: Сохранение данных... ---")
    try:
        with db_lock:
            data_to_save = [doc.model_dump() for doc in db_storage]

        with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, default=str)
        print("--- Данные успешно сохранены. Выход. ---")
    except Exception as e:
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА при сохранении БД: {e} !!!")


app = FastAPI(
    title="YaraDB",
    description="Document-based YaraDB API (with JSON Persistence)",
    version="1.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)


@app.get("/ping")
async def root():
    return {"status": "alive"}


# --- C: Create ---
@app.post("/document/create", response_model=StandardDocument)
async def create_document_endpoint(request_data: CreateRequest):
    new_doc = create_doc_func(
        name=request_data.name,
        body=request_data.body
    )
    if new_doc is None:
        raise HTTPException(status_code=400, detail="Ошибка создания документа.")

    with db_lock:
        db_storage.append(new_doc)
        db_index_by_id[new_doc.id] = new_doc

    return new_doc


# --- R: Read (Get by ID) ---
@app.get("/document/get/{doc_id}", response_model=StandardDocument)
async def get_document_by_id(doc_id: uuid.UUID):
    with db_lock:
        doc = db_index_by_id.get(doc_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.is_archived():
        raise HTTPException(status_code=404, detail="Document not found (archived)")

    return doc


# --- R: Read (Find by filter) ---
@app.post("/document/find", response_model=List[StandardDocument])
async def find_documents(
        filter_body: Dict[str, Any],
        include_archived: bool = False
):
    results: List[StandardDocument] = []
    with db_lock:
        storage_copy = list(db_storage)

    for doc in storage_copy:
        if doc.is_archived() and not include_archived:
            continue

        matches = True
        for key, value in filter_body.items():
            if doc.get(key, default=object()) != value:
                matches = False
                break

        if matches:
            results.append(doc)

    return results


# --- 💡 U: Update (Шаг 3) 💡 ---
@app.put("/document/update/{doc_id}", response_model=StandardDocument)
async def update_document(doc_id: uuid.UUID, update_data: UpdateRequest):
    with db_lock:
        doc = db_index_by_id.get(doc_id)

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        if doc.is_archived():
            raise HTTPException(status_code=400, detail="Cannot update an archived document")

        if doc.version != update_data.version:
            raise HTTPException(
                status_code=409,  # 409 Conflict
                detail=f"Conflict: Document version mismatch. DB is at {doc.version}, you sent {update_data.version}"
            )

        now = datetime.now()
        doc.body = update_data.body
        doc.version += 1
        doc.updated_at = now

        doc.calculate_body_hash()

        return doc


# --- D: Delete (Archive) ---
@app.put("/document/archive/{doc_id}", response_model=StandardDocument)
async def archive_document(doc_id: uuid.UUID):
    with db_lock:
        doc = db_index_by_id.get(doc_id)

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        if doc.is_archived():
            raise HTTPException(status_code=400, detail="Document already archived")

        doc.archive()
        return doc

    raise HTTPException(status_code=404, detail="Document not found")


if __name__ == "__main__":
    print("--- Запуск YaraDB (v1.1) на http://120.0.0.1:8000 ---")
    uvicorn.run(
        "main:app",
        host="120.0.0.1",
        port=8000,
        workers=1,
        reload=True,
        limit_concurrency=100,
    )