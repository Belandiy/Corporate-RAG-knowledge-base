# Sync Agent Module

## Назначение
Фоновый микросервис для автоматического отслеживания директории с документами (`docs/`), их парсинга, чанкинга, векторизации и обновления в векторной базе Qdrant.

## Внутренняя структура
* `main.py` — Точка входа. Запускает `watchdog` для слежения за файловой системой (реакция на события `IN_CREATE`, `IN_MODIFY`, `IN_DELETE`).
* `parser.py` — Извлечение чистого текста из исходных форматов (Markdown, PDF, Docx) с сохранением иерархии заголовков.
* `chunker.py` — Разбиение текста на фрагменты (Semantic / Recursive Character Text Splitting) с заданным параметром overlap.
* `qdrant_store.py` — Логика взаимодействия с базой Qdrant (вызов `upsert` при обновлении/добавлении, `delete` при удалении исходного файла).

## Схема Метаданных (Payload Schema в Qdrant)

Каждый вектор (Point), сохраняемый в Qdrant, содержит следующую структуру Payload для обеспечения пред-фильтрации (Pre-filtering) в процессе поиска:

```json
{
  "doc_id": "uuid4 (уникальный ID документа)",
  "filename": "string (имя исходного файла)",
  "path": "string (относительный путь)",
  "chunk_index": "integer (номер чанка)",
  "text_content": "string (содержимое чанка)",
  "metadata": {
    "department": "string",
    "created_at": "timestamp",
    "document_type": "string",
    "allowed_roles": ["list", "of", "strings"]
  }
}
```
