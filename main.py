from fastapi import FastAPI, HTTPException, Request
from typing import List, Dict, Any, Union
import uvicorn
import uuid
import logging

from slowapi.errors import RateLimitExceeded
from core import repository
from core.lifespan import lifespan
from models.document_types.document import StandardDocument
from models.document_types.combined_document import CombinedDocument
from starlette.middleware.cors import CORSMiddleware
from models.api import CreateRequest, UpdateRequest, CombineRequest
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address


app = FastAPI(
    title="YaraDB",
    description="Document-based YaraDB API (v3 with WAL Persistence)",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)

Instrumentator().instrument(app).expose(app)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("yaradb.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("yaradb")


@app.get("/ping")
async def root():
    return {"status": "alive"}


@app.post("/document/create", response_model=StandardDocument)
@limiter.limit("10/minute")
async def create_document_endpoint(request: Request, request_data: CreateRequest):
    try:
        new_doc = await repository.create_document(
            name=request_data.name,
            body=request_data.body
        )
        logger.info(f"Document created: {new_doc.id}")
        return new_doc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@app.get("/document/get/{doc_id}", response_model=Union[StandardDocument, CombinedDocument])
@limiter.limit("10/minute")
async def get_document_by_id(request: Request, doc_id: uuid.UUID):
    doc = await repository.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.post("/document/find", response_model=List[StandardDocument])
@limiter.limit("10/minute")
async def find_documents(
        request: Request,
        filter_body: Dict[str, Any],
        include_archived: bool = False
):
    results = await repository.find_documents(filter_body, include_archived)
    return results


@app.put("/document/update/{doc_id}", response_model=StandardDocument)
@limiter.limit("10/minute")
async def update_document_endpoint(request: Request, doc_id: uuid.UUID, update_data: UpdateRequest):
    try:
        updated_doc = await repository.update_document(
            doc_id=doc_id,
            version=update_data.version,
            body=update_data.body
        )
        logger.info(f"Document updated: {updated_doc.id}")
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
@limiter.limit("10/minute")
async def archive_document_endpoint(request: Request, doc_id: uuid.UUID):
    try:
        archived_doc = await repository.archive_document(doc_id)
        logger.info(f"Document archived: {archived_doc.id}")
        return archived_doc
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.post("/document/batch/create")
@limiter.limit("10/minute")
async def batch_create(request: Request, docs: List[CreateRequest]):
    results = []
    for req in docs:
        doc = await repository.create_document(req.name, req.body)
        results.append(doc)
    logger.info(f"Batch created: {len(results)} documents")
    return results

@app.post("/document/combine", response_model=CombinedDocument)
@limiter.limit("10/minute")
async def combine_docs(request: Request, payload: CombineRequest):
    try:
        combined_doc = await repository.combine_documents(
            name=payload.name,
            document_ids=payload.document_ids,
            merge_strategy=payload.merge_strategy
        )
        logger.info(f"Combined document: {combined_doc.id}")
        return combined_doc
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error combining documents: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# this endpoint temporarily commented bc it's not working rn
# @app.get("/document/combined/{doc_id}/sources", response_model=List[StandardDocument])
# @limiter.limit("10/minute")
# async def get_source_documents_endpoint(request: Request, doc_id: uuid.UUID):
#     try:
#         source_docs = await repository.get_source_documents(doc_id)
#         return source_docs
#     except LookupError as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


if __name__ == "__main__":
    print("--- Starting YaraDB (v3.0) on http://0.0.0.0:8000 ---")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        reload=False,
        limit_concurrency=100,
    )