from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Синглтон-клиент Qdrant
client = AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

COLLECTION_NAME = "rag_collection"
VECTOR_SIZE = 1024 # для intfloat/multilingual-e5-large размерность 1024

async def init_qdrant():
    """
    Проверяет существование коллекции и создает её при необходимости.
    Настраивает гибридный поиск: dense vectors + sparse vectors (BM25).
    """
    try:
        collections = await client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if COLLECTION_NAME not in collection_names:
            logger.info(f"Creating Qdrant collection: {COLLECTION_NAME}")
            
            await client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE
                ),
                # Настройка sparse векторов для BM25-поиска
                sparse_vectors_config={
                    "text_sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(
                            on_disk=False,
                        )
                    )
                }
            )
            
            # Индекс по allowed_roles (pre-filtering RBAC)
            await client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="allowed_roles",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            
            # Индекс по doc_id (для быстрого удаления документа)
            await client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="doc_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            
            logger.info("Collection and indexes created successfully.")
        else:
            logger.info(f"Collection {COLLECTION_NAME} already exists.")
            
    except Exception as e:
        logger.error(f"Error initializing Qdrant: {e}")
        raise
