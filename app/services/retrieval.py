import time
from typing import Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.core.config import settings
from app.core.llm import embed_model, llm
from app.models.schemas import QueryRequest, QueryResponse, SourceDocument, QueryMetrics
from llama_index.core.prompts import PromptTemplate

# Initialize Qdrant Client
import os
qdrant_host = os.getenv("QDRANT_HOST", settings.QDRANT_HOST)
if qdrant_host == "local":
    qdrant_client = QdrantClient(path=os.getenv("QDRANT_PATH", "qdrant_db"))
else:
    qdrant_client = QdrantClient(host=qdrant_host, port=settings.QDRANT_PORT)

QA_PROMPT_TMPL = (
    "Контекстная информация приведена ниже.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Учитывая контекстную информацию и не используя предварительные знания, "
    "ответьте на запрос.\n"
    "Запрос: {query_str}\n"
    "Ответ: "
)
qa_prompt = PromptTemplate(QA_PROMPT_TMPL)

def query_knowledge_base(request: QueryRequest) -> QueryResponse:
    start_time = time.time()

    # 1. Generate embedding for query
    query_embedding = embed_model.get_text_embedding(request.query)

    # 2. Prepare filters
    filter_conditions = []
    if request.filters:
        for key, value in request.filters.items():
            filter_conditions.append(
                models.FieldCondition(
                    key=f"metadata.{key}",
                    match=models.MatchValue(value=value)
                )
            )

    query_filter = models.Filter(must=filter_conditions) if filter_conditions else None

    # 3. Search Qdrant (Dense Retrieval)
    try:
        # Some versions of Qdrant use search, newer versions might prefer query_points
        # Using query_points for newer clients.
        search_results = qdrant_client.query_points(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query=query_embedding,
            query_filter=query_filter,
            limit=request.top_k,
            with_payload=True
        ).points
    except Exception as e:
        print(f"Error searching Qdrant: {e}")
        search_results = []

    sources = []
    context_chunks = []

    for hit in search_results:
        payload = hit.payload or {}
        chunk_text = payload.get("text_content", "")
        context_chunks.append(chunk_text)

        sources.append(
            SourceDocument(
                document_id=payload.get("doc_id", "unknown"),
                title=payload.get("filename", "unknown"),
                chunk_text=chunk_text[:200] + "...", # Snippet
                score=hit.score
            )
        )

    # 4. Generate Answer using LLM
    context_str = "\n\n".join(context_chunks)
    formatted_prompt = qa_prompt.format(context_str=context_str, query_str=request.query)

    try:
        # Simplistic token counting approximation
        tokens_used_prompt = len(formatted_prompt) // 4

        response = llm.complete(formatted_prompt)
        answer = response.text

        tokens_used_completion = len(answer) // 4
        tokens_used = tokens_used_prompt + tokens_used_completion
    except Exception as e:
        print(f"Error generating LLM response: {e}")
        answer = "Извините, произошла ошибка при генерации ответа."
        tokens_used = 0

    end_time = time.time()
    latency_ms = int((end_time - start_time) * 1000)

    metrics = QueryMetrics(
        latency_ms=latency_ms,
        tokens_used=tokens_used
    )

    return QueryResponse(
        answer=answer,
        sources=sources,
        metrics=metrics
    )
