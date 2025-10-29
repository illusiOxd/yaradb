from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel  # <-- 1. Импортируем BaseModel

import threading
import uuid

from starlette.middleware.cors import CORSMiddleware

# 2. ПЕРЕИМЕНОВЫВАЕМ импорт, чтобы не было конфликта имен
from models.models_init.document_init import create_document as create_doc_func
from models.models_init.document_init import StandardDocument

app = FastAPI(
    title="YaraDB",
    description="Document-based YaraDB API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)


class CreateRequest(BaseModel):
    name: str
    body: Dict[str, Any]



@app.get("/ping")
async def root():
    return {
        "status": "alive"
    }


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

    return new_doc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        workers=1,
        timeout_keep_alive=75,
        limit_concurrency=100,
        limit_max_requests=1000
    )