from typing import List, Union, Dict, Any
from fastembed import TextEmbedding, SparseTextEmbedding
from app.core.config import settings
import asyncio

# Глобальные переменные для кэширования моделей в памяти
_model = None
_sparse_model = None

class EmbeddingsClient:
    async def get_embeddings(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Генерирует плотные (dense) эмбеддинги.
        """
        if isinstance(texts, str):
            texts = [texts]
            
        def embed():
            global _model
            if _model is None:
                _model = TextEmbedding(model_name=settings.EMBEDDINGS_MODEL)
            return [vec.tolist() for vec in _model.embed(texts)]
            
        return await asyncio.to_thread(embed)

    async def get_sparse_embeddings(self, texts: Union[str, List[str]]) -> List[Dict[str, List[Any]]]:
        """
        Генерирует разреженные (sparse) эмбеддинги для BM25 (модель Qdrant/bm25).
        Возвращает список словарей с ключами "indices" и "values".
        """
        if isinstance(texts, str):
            texts = [texts]
            
        def embed_sparse():
            global _sparse_model
            if _sparse_model is None:
                _sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
            
            # fastembed возвращает SparseEmbedding(indices, values)
            return [{"indices": vec.indices.tolist(), "values": vec.values.tolist()} for vec in _sparse_model.embed(texts)]
            
        return await asyncio.to_thread(embed_sparse)
