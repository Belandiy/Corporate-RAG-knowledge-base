import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "knowledge_base"

    EMBEDDING_MODEL_ID: str = "intfloat/multilingual-e5-large"

    # LLM settings (configured for local LM Studio by default or similar OpenAI compatible endpoint)
    OPENAI_API_KEY: str = "dummy"
    LLM_BASE_URL: str = "http://localhost:1234/v1"
    LLM_MODEL: str = "qwen3-4b-thinking"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
