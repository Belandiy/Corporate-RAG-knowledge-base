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
    total_chunks = len(split_docs)
    
    final_chunks = []
    for i, doc in enumerate(split_docs):
        meta = doc.metadata.copy()
        # Собираем иерархию заголовков для Markdown
        hierarchy_parts = [v for k, v in meta.items() if str(k).startswith("Header")]
        hierarchy = " > ".join(hierarchy_parts) if hierarchy_parts else "Document"
        
        final_chunks.append({
            "text": doc.page_content,
            "metadata": {
                "chunk_index": i,
                "total_chunks": total_chunks,
                "heading_hierarchy": hierarchy,
            }
        })

    return final_chunks
