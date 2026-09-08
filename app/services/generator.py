import logging
from typing import List, Dict, Any, AsyncGenerator
from app.core.llm import llm_client
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful and precise assistant for an Enterprise Knowledge Base.
Your task is to answer the user's question ONLY based on the provided context. 
If the context does not contain the answer, say exactly: "Информация не найдена в базе знаний." (or translate this phrase to the language of the user's query).
Do NOT use outside knowledge.
Use citations in the format [1], [2], etc., corresponding to the document index provided in the context.
IMPORTANT: Always answer in the same language as the user's query."""

def format_context(docs: List[Dict[str, Any]]) -> str:
    """Формирует контекст из списка документов с нумерацией."""
    context_parts = []
    for i, doc in enumerate(docs):
        # Нумерация начинается с 1
        part = f"Document [{i+1}]:\nSource: {doc.get('doc_id')}\nHeading: {doc.get('heading_hierarchy')}\nContent:\n{doc.get('text')}\n"
        context_parts.append(part)
    return "\n".join(context_parts)

async def generate_answer(query: str, docs: List[Dict[str, Any]]) -> str:
    """
    Генерирует ответ без стриминга.
    """
    context = format_context(docs)
    prompt = f"Context information is below.\n---------------------\n{context}\n---------------------\nGiven the context information and not prior knowledge, answer the query.\nQuery: {query}\nAnswer:"
    
    logger.info(f"Generating answer using {settings.LLM_MODEL}")
    
    response = await llm_client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=1024,
    )
    
    return response.choices[0].message.content

async def generate_answer_stream(query: str, docs: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
    """
    Генерирует ответ со стримингом (Server-Sent Events).
    """
    context = format_context(docs)
    prompt = f"Context information is below.\n---------------------\n{context}\n---------------------\nGiven the context information and not prior knowledge, answer the query.\nQuery: {query}\nAnswer:"
    
    logger.info(f"Streaming answer using {settings.LLM_MODEL}")
    
    stream = await llm_client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=1024,
        stream=True,
    )
    
    async for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content
