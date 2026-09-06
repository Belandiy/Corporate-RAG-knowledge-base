from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from typing import List, Dict, Any

def chunk_text(text: str, ext: str = ".md") -> List[Dict[str, Any]]:
    """
    Разбивает текст на чанки.
    Для Markdown используется семантическое разбиение по заголовкам.
    Для всех форматов контролируется длина в токенах (tiktoken) и overlap.
    Возвращает список словарей с текстом и метаданными (chunk_index, heading_hierarchy).
    """
    # 1. Семантический парсинг заголовков (только для Markdown)
    if ext.lower() == ".md":
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        docs = markdown_splitter.split_text(text)
    else:
        from langchain_core.documents import Document
        docs = [Document(page_content=text)]

    # 2. Разбиение по токенам (до 512 токенов, overlap 50)
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=512,
        chunk_overlap=50,
    )

    split_docs = text_splitter.split_documents(docs)
    import re
    has_alphanumeric = re.compile(r'[a-zA-Zа-яА-Я0-9]')
    
    final_chunks = []
    for doc in split_docs:
        content = doc.page_content.strip()
        
        # Фильтрация мусорных чанков (менее 15 символов или без букв/цифр)
        if len(content) < 15 or not has_alphanumeric.search(content):
            continue
            
        meta = doc.metadata.copy()
        # Собираем иерархию заголовков для Markdown
        hierarchy_parts = [v for k, v in meta.items() if str(k).startswith("Header")]
        hierarchy = " > ".join(hierarchy_parts) if hierarchy_parts else "Document"
        
        final_chunks.append({
            "text": content,
            "metadata": {
                "chunk_index": len(final_chunks),
                "heading_hierarchy": hierarchy,
            }
        })

    # Обновляем total_chunks после фильтрации
    total_chunks = len(final_chunks)
    for chunk in final_chunks:
        chunk["metadata"]["total_chunks"] = total_chunks

    return final_chunks
