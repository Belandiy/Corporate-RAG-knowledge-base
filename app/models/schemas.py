from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DocumentResponse(BaseModel):
    doc_id: str
    filename: str
    status: str
    allowed_roles: List[str]
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UploadResponse(BaseModel):
    message: str
    document: DocumentResponse
