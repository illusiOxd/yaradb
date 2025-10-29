from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import threading
import uuid
from starlette.middleware.cors import CORSMiddleware
import uvicorn

try:
    from models.models_init.document_init import StandardDocument, create_document as create_doc_func
except ImportError:
    print("Ошибка: Не могу найти 'models/models_init/document_init.py'.")
    print("Пожалуйста, убедись, что файл существует и содержит 'StandardDocument' и 'create_document'.")
    StandardDocument = BaseModel


    def create_doc_func(name: str, body: Dict[str, Any]) -> None:
        return None


class CreateRequest(BaseModel):
    name: str
    body: Dict[str, Any]


db_storage: List[StandardDocument] = []
db_lock = threading.Lock()

app = FastAPI(
    title="YaraDB",
    description="Document-based YaraDB API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)



@app.get("/ping")
async def root():
    return {
        "status": "alive"
    }


# --- C: Create ---
@app.post("/document/create", response_model=StandardDocument)
async def create_document_endpoint(request_data: CreateRequest):
    new_doc = create_doc_func(
        name=request_data.name,
        body=request_data.body
    )

    if new_doc is None:
        raise HTTPException(
            status_code=400,
            detail="Ошибка создания документа. Проверьте данные."
        )

    with db_lock:
        db_storage.append(new_doc)

    return new_doc


# --- R: Read (Get by ID) ---
@app.get("/document/get/{doc_id}", response_model=StandardDocument)
async def get_document_by_id(doc_id: uuid.UUID):
    with db_lock:
        for doc in db_storage:
            if doc.id == doc_id and not doc.is_archived():
                return doc

    raise HTTPException(status_code=404, detail="Document not found")


# --- R: Read (Find by filter) ---
@app.post("/document/find", response_model=List[StandardDocument])
async def find_documents(
        filter_body: Dict[str, Any],
        include_archived: bool = False
):
    results: List[StandardDocument] = []
    with db_lock:
        for doc in db_storage:
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
    with db_lock:
        for doc in db_storage:
            if doc.id == doc_id:
                if doc.is_archived():
                    raise HTTPException(status_code=400, detail="Document already archived")

                doc.archive()
                return doc

    raise HTTPException(status_code=404, detail="Document not found")


if __name__ == "__main__":
    print("--- Запуск YaraDB на http://127.0.0.1:8000 ---")
    print("--- Документация API доступна на http://127.0.0.1:8000/docs ---")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        workers=1,
        timeout_keep_alive=75,
        limit_concurrency=100,
        limit_max_requests=1000
    )
