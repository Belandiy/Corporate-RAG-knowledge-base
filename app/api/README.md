# API Layer (`app/api`)

## Назначение
Слой маршрутизации (Routing) для FastAPI. Отвечает исключительно за прием HTTP-запросов, их базовую валидацию и возврат ответов. Вся бизнес-логика делегируется в `app/services`.

## Ожидаемая структура
* `__init__.py`
* `routes.py` (или `query.py`) — Определение маршрутов (например, `POST /api/v1/query`).
* `dependencies.py` — FastAPI Depends-инъекции (например, получение экземпляра LlamaIndex или клиента Qdrant).

## Правила написания кода
- **Zero Business Logic:** Роуты не должны содержать логику поиска (Retrieval) или вызова LLM.
- **Strict Typing:** Обязательное использование Pydantic-моделей из `app/models` для валидации Request и формирования Response.
- **Exception Handling:** Все внутренние ошибки сервисов должны перехватываться и возвращаться в виде стандартизированных HTTP-ошибок (например, 400 Bad Request или 500 Internal Server Error) с понятными сообщениями.
