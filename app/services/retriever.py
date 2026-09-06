import logging
from typing import List, Dict, Any
from qdrant_client.http import models
from app.core.qdrant import client as qdrant_client, COLLECTION_NAME
from app.ingestion.embeddings import EmbeddingsClient

logger = logging.getLogger(__name__)

async def hybrid_search(query: str, user_roles: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Выполняет гибридный поиск (Dense + Sparse) по базе Qdrant с использованием
    Reciprocal Rank Fusion (RRF) и фильтрацией по ролям (RBAC).
    """
    embeddings_client = EmbeddingsClient()
    
    # 1. Генерируем оба вектора для запроса
    logger.info(f"Generating vectors for query: '{query}'")
    dense_emb = await embeddings_client.get_embeddings(query)
    sparse_emb = await embeddings_client.get_sparse_embeddings(query)
    
    dense_vector = dense_emb[0]
    sparse_vector = sparse_emb[0]
    
    # 2. Формируем RBAC фильтр (юзер должен иметь хотя бы одну из ролей документа)
    rbac_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="allowed_roles",
                match=models.MatchAny(any=user_roles)
            )
        ]
    )
    
    # 3. Делаем гибридный запрос (Qdrant Query API с Prefetch и Fusion)
    logger.info("Executing Qdrant hybrid search with RRF fusion")
    results = await qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            models.Prefetch(
                query=dense_vector,
                using="", # Default dense vector
                filter=rbac_filter,
                limit=top_k * 2, # берем больше кандидатов для RRF
            ),
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse_vector["indices"],
                    values=sparse_vector["values"]
                ),
                using="text_sparse",
                filter=rbac_filter,
                limit=top_k * 2,
            )
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=top_k,
    )
    
    # 4. Форматируем результат
    formatted_results = []
    for point in results.points:
        formatted_results.append({
            "id": point.id,
            "score": point.score,
            "text": point.payload.get("text", ""),
            "doc_id": point.payload.get("doc_id", ""),
            "chunk_index": point.payload.get("chunk_index", 0),
            "heading_hierarchy": point.payload.get("heading_hierarchy", ""),
        })
        
    return formatted_results
