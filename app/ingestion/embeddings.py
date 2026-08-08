from typing import List, Union
from fastembed import TextEmbedding
from app.core.config import settings
import asyncio

# Глобальная переменная для кэширования модели в памяти
_model = None

class EmbeddingsClient:
    async def get_embeddings(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Генерирует эмбеддинги локально через FastEmbed.
        Инициализация модели и генерация выполняются в пуле потоков 
        для неблокирующей работы основного event loop FastAPI.
        """
        if isinstance(texts, str):
            texts = [texts]
            
        def embed():
            global _model
            if _model is None:
                # Загружаем модель лениво при первом обращении
                _model = TextEmbedding(model_name=settings.EMBEDDINGS_MODEL)
            # fastembed возвращает генератор numpy arrays, преобразуем в списки float
            return [vec.tolist() for vec in _model.embed(texts)]
            
        # Запускаем синхронный код fastembed в асинхронном потоке
        embeddings = await asyncio.to_thread(embed)
        return embeddings
