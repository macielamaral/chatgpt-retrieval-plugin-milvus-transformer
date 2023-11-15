from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from pydantic import validator

class Collection(str, Enum):
    collection1 = "collection1"
    collection2 = "collection2"

class Partition(str, Enum):
    chats = "chats"
    researches = "researches"
    papers = "papers"
    notes = "notes"
    books = "books"
    others = "others"
    emails = "emails"
    codes = "codes"
    
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
    collection: Optional[Collection] = None
    partition: Optional[Partition] = None
    metadata: Optional[DocumentChunkMetadata] = None
    embedding: Optional[List[float]] = None

class DocumentChunkWithScore(DocumentChunk):
    score: float

class Document(BaseModel):
    text: str
    collection: Optional[Collection] = None
    partition: Optional[Partition] = None
    metadata: Optional[DocumentMetadata] = None

class DocumentWithChunks(Document):
    chunks: List[DocumentChunk]

class DocumentMetadataFilter(BaseModel):
    document_id: Optional[str] = None
    authors: Optional[str] = None

class DocumentGroupWithScores(BaseModel):
    texts: List[str]  
    collection: Optional[str] = None
    partition: Optional[str] = None
    metadata: Optional[DocumentMetadata] = None
    embedding: Optional[List[float]] = None
    scores: List[float]  
    
class Query(BaseModel):
    query: str
    collection: Optional[Collection] = None
    partition: Optional[Partition] = None
    filter: Optional[DocumentMetadataFilter] = None
    top_k: Optional[int] = 5
    searchprecision: Optional[SearchPrecision] = None
    
class QueryWithEmbedding(Query):
    embedding: List[float]

class QueryResult(BaseModel):
    query: str
    results: List[DocumentChunkWithScore]

class DocumentDelete(BaseModel):
    document_id: str
    collection: Optional[Collection] = None

class DocumentGroupWithScores(BaseModel):
    texts: List[str]  
    collection: Optional[str] = None
    partition: Optional[str] = None
    metadata: Optional[DocumentMetadata] = None
    embedding: Optional[List[float]] = None
    scores: List[float]  
    
class QueryGroupResult(BaseModel):
    query: str
    results: List[DocumentGroupWithScores]

    