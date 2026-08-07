from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class QueryRequest(BaseModel):
    query: str = Field(..., description="Текст запроса пользователя")
    top_k: int = Field(default=3, description="Количество возвращаемых чанков-кандидатов")
    filters: Optional[Dict[str, str]] = Field(default=None, description="Фильтры по метаданным (например, roles, department)")
    stream: bool = Field(default=False, description="Флаг для стриминга ответа")

class SourceDocument(BaseModel):
    document_id: str
    title: str
    chunk_text: str
    score: float

class QueryMetrics(BaseModel):
    latency_ms: int
    tokens_used: int

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    metrics: QueryMetrics
