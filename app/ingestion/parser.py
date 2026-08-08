import os
import pymupdf # type: ignore
import docx # type: ignore

def parse_markdown(file_path: str) -> str:
    """Парсит Markdown файл."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_pdf(file_path: str) -> str:
    """Извлекает текст из PDF файла."""
    text = ""
    doc = pymupdf.open(file_path)
    for page in doc:
        text += page.get_text() + "\n"
    return text

def parse_docx(file_path: str) -> str:
    """Извлекает текст из Word документа."""
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def parse_file(file_path: str) -> str:
    """
    Определяет тип файла по расширению и вызывает соответствующий парсер.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.md':
        return parse_markdown(file_path)
    elif ext == '.pdf':
        return parse_pdf(file_path)
    elif ext == '.docx':
        return parse_docx(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
