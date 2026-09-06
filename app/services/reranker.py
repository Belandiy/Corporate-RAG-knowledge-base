import logging
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
import asyncio

logger = logging.getLogger(__name__)

# Глобальная переменная для ленивой загрузки модели в памяти
_cross_encoder = None

class Reranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        self.model_name = model_name

    async def rerank(self, query: str, docs: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Переранжирует список документов относительно запроса с помощью CrossEncoder.
        Выполняется в пуле потоков (asyncio.to_thread).
        """
        if not docs:
            return []

        def _do_rerank():
            global _cross_encoder
            if _cross_encoder is None:
                logger.info(f"Loading CrossEncoder model: {self.model_name}...")
                _cross_encoder = CrossEncoder(self.model_name)
            
            # Подготавливаем пары (запрос, текст документа)
            pairs = [[query, doc["text"]] for doc in docs]
            
            # Вычисляем скоры
            scores = _cross_encoder.predict(pairs)
            
            # Добавляем скоры в документы и обновляем общий score (чтобы было видно в API)
            for doc, score in zip(docs, scores):
                doc["rerank_score"] = float(score)
                doc["score"] = float(score) # Перезаписываем score из Qdrant на более точный
            
            # Сортируем по убыванию rerank_score
            docs.sort(key=lambda x: x["rerank_score"], reverse=True)
            
            # Возвращаем top_k
            return docs[:top_k]

        return await asyncio.to_thread(_do_rerank)
