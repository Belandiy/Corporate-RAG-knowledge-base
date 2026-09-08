from openai import AsyncOpenAI
from app.core.config import settings

# Инициализируем клиент OpenAI, настроенный на локальный LM Studio
llm_client = AsyncOpenAI(
    base_url=settings.LM_STUDIO_URL,
    api_key="lm-studio" # Для локального сервера ключ может быть любым
)
