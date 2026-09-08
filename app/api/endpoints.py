import os
import shutil
import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Document as DBDocument, DocStatus
from app.models.schemas import DocumentResponse, UploadResponse, SearchRequest, SearchResponse, AskRequest, AskResponse, SearchResultItem
from app.ingestion.pipeline import process_document
from app.services.retriever import hybrid_search
from app.services.reranker import Reranker
from app.services.generator import generate_answer, generate_answer_stream
from app.core.qdrant import client as qdrant_client, COLLECTION_NAME
from qdrant_client.http import models

router = APIRouter()
reranker = Reranker()

@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Выполняет гибридный поиск по базе Qdrant с учетом ролей пользователя.
    Опционально применяет CrossEncoder reranker для улучшения релевантности.
    """
    # Запрашиваем из базы больше кандидатов, если включен реранкер
    initial_top_k = request.top_k * 3 if request.rerank else request.top_k
    
    results = await hybrid_search(
        query=request.query,
        user_roles=request.user_roles,
        top_k=initial_top_k
    )
    
    if request.rerank and results:
        results = await reranker.rerank(query=request.query, docs=results, top_k=request.top_k)
        
    return SearchResponse(results=results)

@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Отвечает на вопрос пользователя на основе документов в базе.
    Включает гибридный поиск, переранжирование и генерацию (LLM).
    """
    # 1. Поиск релевантных чанков (берем топ-8 для реранкера)
    results = await hybrid_search(
        query=request.query,
        user_roles=request.user_roles,
        top_k=8
    )
    
    if not results:
        if request.stream:
            async def empty_stream():
                yield "Я не нашел информации в доступных документах."
            return StreamingResponse(empty_stream(), media_type="text/event-stream")
        return AskResponse(answer="Я не нашел информации в доступных документах.", sources=[])
        
    # 2. Переранжирование (оставляем топ-3)
    results = await reranker.rerank(query=request.query, docs=results, top_k=3)
    
    # Форматируем источники для ответа
    sources = [SearchResultItem(**res) for res in results]
    
    # 3. Генерация ответа
    if request.stream:
        # Для стриминга мы просто отправляем текст. Источники отправить сложнее, 
        # обычно их передают в заголовках или спец. SSE-событиях. Для простоты здесь только текст.
        return StreamingResponse(
            generate_answer_stream(query=request.query, docs=results),
            media_type="text/event-stream"
        )
    
    # Без стриминга
    answer = await generate_answer(query=request.query, docs=results)
    return AskResponse(answer=answer, sources=sources)

UPLOAD_DIR = "/app/data/uploads"
# Для локальной разработки создаем папку, если нужно
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    allowed_roles: str = Form("user"),
    db: Session = Depends(get_db)
):
    """
    Загружает файл, создает запись в БД и запускает фоновую задачу по векторизации.
    `allowed_roles` передается строкой через запятую (напр. "admin,user,manager")
    """
    roles_list = [r.strip() for r in allowed_roles.split(",") if r.strip()]
    
    # Генерация уникального ID для документа
    doc_id = str(uuid.uuid4())
    
    # Сохраняем файл на диск
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Создаем запись в БД
    db_doc = DBDocument(
        doc_id=doc_id,
        filename=file.filename,
        status=DocStatus.PENDING.value,
        allowed_roles=roles_list
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    # Запуск пайплайна в фоне
    background_tasks.add_task(process_document, file_path, doc_id, roles_list)
    
    return UploadResponse(
        message="File uploaded successfully, processing started.",
        document=db_doc
    )

@router.get("/documents", response_model=List[DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    """Получает список всех документов и их статусов из БД."""
    docs = db.query(DBDocument).all()
    return docs

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, db: Session = Depends(get_db)):
    """
    Удаляет документ:
    1. Из базы данных (PostgreSQL)
    2. Файл с диска
    3. Векторы из Qdrant
    """
    doc = db.query(DBDocument).filter(DBDocument.doc_id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Удаляем из БД
    db.delete(doc)
    db.commit()
    
    # Удаляем файл с диска
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{doc.filename}")
    if os.path.exists(file_path):
        os.remove(file_path)
        
    # Удаляем из Qdrant
    try:
        await qdrant_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.Filter(
                must=[
                    models.FieldCondition(
                        key="doc_id",
                        match=models.MatchValue(value=doc_id)
                    )
                ]
            )
        )
    except Exception as e:
        print(f"Failed to delete vectors from Qdrant: {e}")
        # Не падаем, если Qdrant недоступен
        
    return {"message": f"Document {doc_id} deleted successfully"}
