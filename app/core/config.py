from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise RAG Knowledge Base"
    DATABASE_URL: str = "postgresql://rag_user:rag_password@localhost:5432/rag_db"
    
    # Secret key for simple auth/token if needed
    SECRET_KEY: str = "supersecretkey_change_in_production"
    
    # Default Admin
    DEFAULT_ADMIN_USER: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # Embeddings (TEI)
    EMBEDDINGS_URL: str = "http://localhost:8080"
    EMBEDDINGS_MODEL: str = "intfloat/multilingual-e5-large"

    # LLM
    LM_STUDIO_URL: str = "http://localhost:1234/v1"
    LLM_MODEL: str = "qwen3-4b"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
