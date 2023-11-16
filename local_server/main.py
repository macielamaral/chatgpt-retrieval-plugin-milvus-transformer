# This is a version of the main.py file found in ../../../server/main.py for testing the plugin locally.
# Use the command `poetry run dev` to run this.
import uvicorn
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

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

from starlette.responses import FileResponse

from services.data_processing import process_and_upload_documents_url, get_document_content


app = FastAPI()

PORT = 3333

origins = [
    f"http://localhost:{PORT}",
    "https://chat.openai.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.route("/")
async def get_manifest(request):
    file_path = "./local_server/ai-plugin.json"
    simple_headers = {}
    simple_headers["Access-Control-Allow-Private-Network"] = "true"
    return FileResponse(file_path, media_type="text/json", headers=simple_headers)



@app.route("/.well-known/ai-plugin.json")
async def get_manifest(request):
    file_path = "./local_server/ai-plugin.json"
    simple_headers = {}
    simple_headers["Access-Control-Allow-Private-Network"] = "true"
    return FileResponse(file_path, media_type="text/json", headers=simple_headers)


@app.route("/.well-known/logo.png")
async def get_logo(request):
    file_path = "./local_server/logo.png"
    return FileResponse(file_path, media_type="image/png")


@app.route("/.well-known/openapi.yaml")
async def get_openapi(request):
    file_path = "./local_server/openapi.yaml"
    return FileResponse(file_path, media_type="text/json")

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
    uvicorn.run("local_server.main:app", host="0.0.0.0", port=PORT, reload=True)
