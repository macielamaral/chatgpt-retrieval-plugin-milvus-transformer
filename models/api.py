from models.models import (
    Document,
    DocumentMetadataFilter,
    Query,
    QueryGroupResult,
    DocumentDelete,
    Partition,
    Collection
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
    results: List[QueryGroupResult]

class DeleteRequest(BaseModel):
    documents: List[DocumentDelete]

class DeleteResponse(BaseModel):
    success: bool

class SaveURLDocumentRequest(BaseModel):
    documents_url: List[str]
    collection: Collection
    partition: Partition

class SaveURLDocumentResponse(BaseModel):
    results: str