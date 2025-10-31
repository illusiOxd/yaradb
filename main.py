from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
import uvicorn
import uuid

from core import repository
from core.lifespan import lifespan
from models.document import StandardDocument
from starlette.middleware.cors import CORSMiddleware
from models.api import CreateRequest, UpdateRequest

app = FastAPI(
    title="YaraDB",
    description="Document-based YaraDB API (v2 with WAL Persistence)",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)



@app.get("/ping")
async def root():
    return {"status": "alive"}


@app.post("/document/create", response_model=StandardDocument)
async def create_document_endpoint(request_data: CreateRequest):
    try:
        new_doc = repository.create_document(
            name=request_data.name,
            body=request_data.body
        )
        return new_doc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@app.get("/document/get/{doc_id}", response_model=StandardDocument)
async def get_document_by_id(doc_id: uuid.UUID):
    doc = repository.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.post("/document/find", response_model=List[StandardDocument])
async def find_documents(
        filter_body: Dict[str, Any],
        include_archived: bool = False
):
    results = repository.find_documents(filter_body, include_archived)
    return results


@app.put("/document/update/{doc_id}", response_model=StandardDocument)
async def update_document_endpoint(doc_id: uuid.UUID, update_data: UpdateRequest):
    try:
        updated_doc = repository.update_document(
            doc_id=doc_id,
            version=update_data.version,
            body=update_data.body
        )
        return updated_doc
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        if "Conflict" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@app.put("/document/archive/{doc_id}", response_model=StandardDocument)
async def archive_document_endpoint(doc_id: uuid.UUID):
    try:
        archived_doc = repository.archive_document(doc_id)
        return archived_doc
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")



if __name__ == "__main__":
    print("--- Starting YaraDB (v2.0 with WAL) on http://0.0.0.0:8000 ---")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        reload=False,
        limit_concurrency=100,
    )