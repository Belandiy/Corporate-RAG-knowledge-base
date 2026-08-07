# App Module (FastAPI Backend)

## Назначение
Основной API-сервер приложения, обеспечивающий логику поиска и генерации ответов (RAG). 

## Внутренняя структура
* `api/` — роуты FastAPI (в том числе `/api/v1/query`).
* `core/` — зависимости (DI), настройки LlamaIndex (LLM, Embeddings), промпты.
* `services/` — бизнес-логика Retrieval (Hybrid Search, RRF) и Reranking.
* `models/` — Pydantic-схемы контрактов.

## Схемы данных (Pydantic Models)

### Request Schema (`QueryRequest`)
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict

class QueryRequest(BaseModel):
    query: str = Field(..., description="Текст запроса пользователя")
    top_k: int = Field(default=3, description="Количество возвращаемых чанков-кандидатов")
    filters: Optional[Dict[str, str]] = Field(default=None, description="Фильтры по метаданным (например, roles, department)")
    stream: bool = Field(default=False, description="Флаг для стриминга ответа")
```

### Response Schema (`QueryResponse`)
```python
from pydantic import BaseModel
from typing import List

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
```
