from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DocumentResponse(BaseModel):
    doc_id: str
    filename: str
    status: str
    allowed_roles: List[str]
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UploadResponse(BaseModel):
    message: str
    document: DocumentResponse

class SearchRequest(BaseModel):
    query: str
    user_roles: List[str]
    top_k: int = 5
    rerank: bool = True

class SearchResultItem(BaseModel):
    id: str
    score: float
    text: str
    doc_id: str
    chunk_index: int
    heading_hierarchy: str

class SearchResponse(BaseModel):
    results: List[SearchResultItem]

class AskRequest(BaseModel):
    query: str
    user_roles: List[str]
    stream: bool = False

class AskResponse(BaseModel):
    answer: str
    sources: List[SearchResultItem]
