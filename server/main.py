import os
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from loguru import logger

from models.api import (
    QueryRequest,
    QueryResponse,
    UpsertRequest,
    UpsertResponse,
    DeleteRequest,
    DeleteResponse,
    SaveURLDocumentResponse,
    SaveURLDocumentRequest
)
from datastore.factory import get_datastore

from services.data_processing import process_and_upload_documents_url, get_document_content

bearer_scheme = HTTPBearer()
BEARER_TOKEN = os.environ.get("BEARER_TOKEN")
assert BEARER_TOKEN is not None


def validate_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if credentials.scheme != "Bearer" or credentials.credentials != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return credentials


app = FastAPI(dependencies=[Depends(validate_token)])
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="static")

# Create a sub-application, in order to access just the query endpoint in an OpenAPI schema, found at http://0.0.0.0:8000/sub/openapi.json when the app is running locally
sub_app = FastAPI(
    title="Retrieval Plugin API",
    description="A retrieval API for querying and filtering documents based on natural language queries and metadata",
    version="1.0.0",
    servers=[{"url": "https://gpt.marcelomacielamaral.com"}],
    dependencies=[Depends(validate_token)],
)
app.mount("/sub", sub_app)


@app.post(
    "/upsert",
    response_model=UpsertResponse,
    description='Save chat information. Accepts an array of documents with text: ',
)
async def upsert(
    request: UpsertRequest = Body(...),
):
    try:
        response_data = await datastore.upsert(request.documents)

        # Construct the UpsertResponse with the response_data directly
        return UpsertResponse(document_id=response_data)
        
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Internal Service Error")


@app.post("/query", response_model=QueryResponse)
async def query_main(request: QueryRequest = Body(...)):
    try:
        results = await datastore.query(
            request.queries,
        )
        return QueryResponse(results=results)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Internal Service Error")



@app.delete(
    "/delete",
    response_model=DeleteResponse,
)
async def delete(
    request: DeleteRequest = Body(...),
):
    try:
        success = await datastore.delete(
            request.documents
        )
        return DeleteResponse(success=success)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Internal Service Error")


@app.post(
    "/upload_from_url", 
    response_model=SaveURLDocumentResponse
    )
async def upload_from_url(
    request: SaveURLDocumentRequest
    ):
    try:
        result = process_and_upload_documents_url(request.documents_url, request.collection, request.partition)
        return SaveURLDocumentResponse(results=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/document/{document_id}"
    )
async def get_document(
    document_id: str
    ):
    try:
        content = get_document_content(document_id)
        return content
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.on_event("startup")
async def startup():
    global datastore
    datastore = await get_datastore()


def start():
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=False)
