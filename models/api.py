from models.models import (
    Document,
    DocumentMetadataFilter,
    Query,
    QueryResult,
    DocumentDelete
)
from pydantic import BaseModel
from typing import List, Dict, Any


class UpsertRequest(BaseModel):
    documents: List[Document]

class UpsertResponse(BaseModel):
    document_id: Dict[str, Dict[str, str]]

class QueryRequest(BaseModel):
    queries: List[Query]

class QueryResponse(BaseModel):
    results: List[QueryResult]

class DeleteRequest(BaseModel):
    documents: List[DocumentDelete]

class DeleteResponse(BaseModel):
    success: bool
    