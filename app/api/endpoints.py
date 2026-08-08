import os
import shutil
import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Document as DBDocument, DocStatus
from app.models.schemas import DocumentResponse, UploadResponse
from app.ingestion.pipeline import process_document
from app.core.qdrant import client as qdrant_client, COLLECTION_NAME
from qdrant_client.http import models

router = APIRouter()

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
