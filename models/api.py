from models.models import (
    Document,
    DocumentMetadataFilter,
    Query,
    QueryResult,
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
    document_ids: List[str]

class DeleteResponse(BaseModel):
    success: bool
    