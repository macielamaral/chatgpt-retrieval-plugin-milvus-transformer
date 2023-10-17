from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from pydantic import validator


class Partition(str, Enum):
    chats = "chats"
    ourpapers = "ourpapers"
    papers = "papers"
    notes = "notes"
    books = "books"
    others = "others"
    
class SearchPrecision(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class DocumentMetadata(BaseModel):
    created_at: Optional[str] = None
    authors: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    keywords: Optional[str] = None
    category: Optional[str] = None

class DocumentChunkMetadata(DocumentMetadata):
    document_id: Optional[str] = None

class DocumentChunk(BaseModel):
    id: Optional[str] = None
    text: str
    partition: Optional[Partition] = None
    metadata: Optional[DocumentChunkMetadata] = None
    embedding: Optional[List[float]] = None

class DocumentChunkWithScore(DocumentChunk):
    score: float

class Document(BaseModel):
    text: str
    partition: Optional[Partition] = None
    metadata: Optional[DocumentMetadata] = None

class DocumentWithChunks(Document):
    chunks: List[DocumentChunk]

class DocumentMetadataFilter(BaseModel):
    document_id: Optional[str] = None
    authors: Optional[str] = None

class Query(BaseModel):
    query: str
    filter: Optional[DocumentMetadataFilter] = None
    top_k: Optional[int] = 5
    searchprecision: Optional[SearchPrecision] = None
    partition: Optional[Partition] = None

class QueryWithEmbedding(Query):
    embedding: List[float]

class QueryResult(BaseModel):
    query: str
    results: List[DocumentChunkWithScore]
