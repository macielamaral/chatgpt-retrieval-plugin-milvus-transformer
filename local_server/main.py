# This is a version of the main.py file found in ../../../server/main.py for testing the plugin locally.
# Use the command `poetry run dev` to run this.
from typing import Optional
import uvicorn
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware

from loguru import logger

from models.api import (
    QueryRequest,
    QueryResponse,
    UpsertRequest,
    UpsertResponse,
    DeleteRequest,
    DeleteResponse
)
from datastore.factory import get_datastore

from starlette.responses import FileResponse

from models.models import DocumentMetadata

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


@app.on_event("startup")
async def startup():
    global datastore
    datastore = await get_datastore()

def start():
    uvicorn.run("local_server.main:app", host="0.0.0.0", port=PORT, reload=True)
