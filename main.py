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

try:
    from models.models_init.document_init import StandardDocument, create_document as create_doc_func
except ImportError:
    print("Ошибка: Не могу найти 'models/models_init/document_init.py'.")


    class StandardDocument(BaseModel):
        id: uuid.UUID


    def create_doc_func(name: str, body: Dict[str, Any]) -> None:
        return None


class CreateRequest(BaseModel):
    name: str
    body: Dict[str, Any]


db_storage: List[StandardDocument] = []
db_lock = threading.Lock()
db_index_by_id: Dict[uuid.UUID, StandardDocument] = {}

STORAGE_FILE = "yaradb_storage.json"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом:
    - При СТАРТЕ: Загружает данные из .json в память и строит индекс.
    - При ВЫКЛЮЧЕНИИ: Сохраняет данные из памяти в .json.
    """
    global db_storage, db_index_by_id
    print("--- YaraDB: Запуск... ---")

    # --- СТАРТ: Загрузка данных ---
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

    # --- ВЫКЛЮЧЕНИЕ: Сохранение данных ---
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
    version="1.0.1",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)



@app.get("/ping")
async def root():
    return {"status": "alive"}


# --- C: Create (Улучшен) ---
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
    """Получить один документ по его ID (мгновенно, O(1))."""

    # --- Поиск по индексу O(1) (Шаг 2) ---
    with db_lock:
        doc = db_index_by_id.get(doc_id)
    # ---

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
    """
    Ищет документы, фильтруя по полям в 'body' (медленный скан, O(n)).
    """
    results: List[StandardDocument] = []
    with db_lock:
        # Копируем список, чтобы безопасно итерировать
        storage_copy = list(db_storage)

    for doc in storage_copy:
        if doc.is_archived() and not include_archived:
            continue

        matches = True
        for key, value in filter_body.items():
            if doc.get(key) != value:
                matches = False
                break

        if matches:
            results.append(doc)

    return results


# --- D: Delete (Archive) ---
@app.put("/document/archive/{doc_id}", response_model=StandardDocument)
async def archive_document(doc_id: uuid.UUID):
    """Выполняет "мягкое удаление" (архивацию) документа."""

    # --- Поиск по индексу O(1) ---
    with db_lock:
        doc = db_index_by_id.get(doc_id)

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        if doc.is_archived():
            raise HTTPException(status_code=400, detail="Document already archived")

        doc.archive()
        return doc

    raise HTTPException(status_code=404, detail="Document not found")


# --- 7. Запуск ---
if __name__ == "__main__":
    print("--- Запуск YaraDB (v1) на http://127.0.0.1:8000 ---")
    uvicorn.run(
        "main_v1:app",
        host="127.0.0.1",
        port=8000,
        workers=1,
        reload=True,
        limit_concurrency=100,
    )
