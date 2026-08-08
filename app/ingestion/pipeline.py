import os
import uuid
import logging
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Document, DocStatus
from app.ingestion.parser import parse_file
from app.ingestion.chunker import chunk_text
from app.ingestion.embeddings import EmbeddingsClient
from app.core.qdrant import client as qdrant_client, COLLECTION_NAME
from qdrant_client.http import models

logger = logging.getLogger(__name__)

async def process_document(file_path: str, doc_id: str, allowed_roles: list[str]):
    """
    Основной пайплайн обработки документа:
    1. Парсинг
    2. Разбиение на чанки
    3. Генерация эмбеддингов
    4. Сохранение в Qdrant
    """
    db: Session = SessionLocal()
    try:
        # Устанавливаем статус PROCESSING
        doc = db.query(Document).filter(Document.doc_id == doc_id).first()
        if not doc:
            logger.error(f"Document {doc_id} not found in DB")
            return
        
        doc.status = DocStatus.PROCESSING.value
        db.commit()

        # 1. Парсинг файла
        logger.info(f"Parsing file {file_path}")
        text = parse_file(file_path)
        
        # 2. Чанкинг
        logger.info("Chunking text")
        ext = os.path.splitext(file_path)[1].lower()
        chunks = chunk_text(text, ext=ext)
        if not chunks:
            raise ValueError("No text extracted from document")
        
        # 3. Генерация эмбеддингов
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        texts_to_embed = [chunk["text"] for chunk in chunks]
        embeddings_client = EmbeddingsClient()
        embeddings = await embeddings_client.get_embeddings(texts_to_embed)
        
        # 4. Сохранение в Qdrant
        logger.info("Upserting vectors to Qdrant")
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            
            payload = {
                "doc_id": doc_id,
                "text": chunk["text"],
                "allowed_roles": allowed_roles,
            }
            payload.update(chunk["metadata"])
            
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector={
                        "": embedding, # Основной dense vector
                    },
                    payload=payload
                )
            )
        
        # Загружаем батчами по 100 чанков
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            await qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch
            )
        
        # Завершение
        doc.status = DocStatus.COMPLETED.value
        db.commit()
        logger.info(f"Successfully processed document {doc_id}")

    except Exception as e:
        logger.error(f"Error processing document {doc_id}: {e}")
        doc = db.query(Document).filter(Document.doc_id == doc_id).first()
        if doc:
            doc.status = DocStatus.ERROR.value
            doc.error_message = str(e)
            db.commit()
    finally:
        db.close()
