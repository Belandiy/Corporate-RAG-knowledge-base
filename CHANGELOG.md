# Changelog

Все значимые архитектурные и кодовые изменения проекта RAG-базы знаний.

## [Unreleased]
### Changed
- **Архитектурный редизайн Ingestion:** Отказ от микросервиса `sync-agent` с `watchdog`. Индексация документов перенесена в `app/ingestion/` и запускается через FastAPI BackgroundTasks при загрузке файлов через API.
- **RBAC & Storage:** Добавлено использование PostgreSQL БД (в Docker контейнере) для хранения пользователей, ролей и статусов документов.
- Обновлена техническая документация и план разработки (`DEVELOPMENT_PLAN.md`) с учетом новых решений. Создан файл `AI_RULES.md`.
- **Qdrant Upgrade:** Обновлен образ Qdrant в `docker-compose.yml` с `v1.9.0` до `v1.11.3` для поддержки Universal Query API (`query_points` с Prefetch и Fusion/RRF), который отсутствовал в версии 1.9.0 и возвращал 404.
- **Архитектура Embeddings:** Замена внешнего сервиса TEI (Text Embeddings Inference) на In-process генерацию эмбеддингов с помощью библиотеки `fastembed`. Убрана зависимость от Docker образа TEI, так как он несовместим с процессорами Apple Silicon (ARM64) без AVX.
- **Оптимизация сборки Dockerfile.api:** Убран долгий и тяжелый шаг установки компиляторов `build-essential` и `libpq-dev` (зависимости ставятся из готовых binary wheels), что уменьшило вес итогового образа на ~250 МБ. Добавлен BuildKit кэш-маунт (`--mount=type=cache,target=/root/.cache/pip`) для многократного ускорения установки зависимостей без сохранения кэша внутри слоя образа.
- **Улучшение чанкинга:** В `app/ingestion/chunker.py` добавлена поддержка семантического разбиения Markdown по заголовкам (`MarkdownHeaderTextSplitter`) и точный подсчет токенов через `tiktoken` (`RecursiveCharacterTextSplitter`). Чанки теперь получают подробные метаданные (путь заголовка, индекс чанка).

### Added
- **Phase 3:** Реализован конвейер генерации ответов (LLM Generation) на основе найденного контекста. 
  - Создан клиент для интеграции с внешними OpenAI-совместимыми API (например, LM Studio) в `app/core/llm.py`. 
  - Разработан сервис генерации `app/services/generator.py` с поддержкой как обычных ответов, так и Server-Sent Events (SSE) стриминга для UI. 
  - Добавлен REST эндпоинт `POST /ask` в `app/api/endpoints.py`, который объединяет Retrieval (гибридный поиск), Reranker и Generation в единый пайплайн.
- Добавлен файл `.dockerignore` для оптимизации сборки Docker: исключены тяжелое окружение `.venv`, байт-код Python, метаданные `.git`, документация и нерелевантные модули из контекста сборки.
- **Phase 2.4:** Реализовано переранжирование через `sentence-transformers` и модель `BAAI/bge-reranker-v2-m3` в новом модуле `app/services/reranker.py`. Эндпоинт поиска обновлен для использования Reranker'а (с флагом `rerank=True` по умолчанию в схеме запроса). Теперь RRF выдает в 3 раза больше кандидатов, а Reranker оставляет самые релевантные.
- **Phase 2.1:** Реализовано ядро гибридного поиска (`app/services/retriever.py`) с использованием Qdrant Reciprocal Rank Fusion (RRF). Пайплайн загрузки обновлен: теперь он генерирует и сохраняет разреженные (sparse) эмбеддинги для BM25 наряду с dense эмбеддингами. Добавлен эндпоинт `POST /search` для тестирования гибридного поиска с поддержкой фильтрации по ролям (RBAC).
- **Phase 1.6:** Добавлен сервис `embeddings` в `docker-compose.yml`. Используется образ `ghcr.io/huggingface/text-embeddings-inference:cpu-1.5` и модель `intfloat/multilingual-e5-large`. Настроен volume `tei_cache` для кэширования модели.
- **Phase 1.5:** Разработан основной пайплайн загрузки (`app/ingestion/pipeline.py`), объединяющий парсинг, чанкинг, эмбеддинги и запись в Qdrant. Созданы Pydantic схемы (`app/models/schemas.py`) и REST эндпоинты (`app/api/endpoints.py`): `POST /upload`, `GET /documents`, `DELETE /documents/{doc_id}`. Реализована точка входа приложения `app/main.py` с автоматической инициализацией Qdrant-коллекции при старте (`lifespan`).
- **Phase 1.4:** Разработаны модули парсинга (`app/ingestion/parser.py`) для извлечения текста из файлов Markdown, PDF (`PyMuPDF`) и Docx (`python-docx`). Добавлен модуль семантического чанкинга (`app/ingestion/chunker.py`) на основе `langchain-text-splitters`.
- **Phase 1.3:** Настроен клиент Qdrant (`app/core/qdrant.py`) с асинхронной инициализацией гибридной коллекции (Dense 1024 + Sparse для BM25). Добавлены payload индексы для `allowed_roles` и `doc_id`.
- **Phase 1.2:** Создан асинхронный HTTP-клиент (`app/ingestion/embeddings.py`) для генерации эмбеддингов через TEI (Text Embeddings Inference).
- **Phase 1.1:** Реализован модуль БД (`app/db/`): настроено подключение к PostgreSQL (`database.py`), созданы SQLAlchemy-модели пользователей и документов (`models.py`), добавлен скрипт инициализации БД с созданием дефолтного администратора (`init_db.py`). Настроен парсинг `.env` через `pydantic-settings` (`app/core/config.py`).
- Добавлена техническая документация (README.md) для всех подмодулей бэкенда: `app/api`, `app/core`, `app/services`, `app/models`.
- Создана базовая структура папок и файлов микросервисов (`app`, `frontend`, `sync`).
- Написана техническая документация (LLD) для каждого микросервиса (README.md в `app`, `sync`, `frontend`) с описанием Pydantic-схем, Payload для Qdrant и структуры ролей.
- Добавлен корневой `.gitignore`.
- Добавлены рекомендации (Brainstorming) в основной архитектурный документ: разделение логики в `shared/`, хостинг LLM в отдельном инференс-сервере, уточнения по Sparse-поиску и RBAC, использование `watchdog` для мониторинга файлов.
