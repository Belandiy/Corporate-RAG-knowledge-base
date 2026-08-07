import os
import re
import pdfplumber
import docx

def parse_markdown(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    # Basic cleanup
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL) # Optional: remove code blocks
    return text

def parse_pdf(filepath: str) -> str:
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        print(f"Error parsing PDF {filepath}: {e}")
    return text

def parse_docx(filepath: str) -> str:
    try:
        doc = docx.Document(filepath)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error parsing DOCX {filepath}: {e}")
        return ""

def parse_file(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".md":
        return parse_markdown(filepath)
    elif ext == ".pdf":
        return parse_pdf(filepath)
    elif ext in [".doc", ".docx"]:
        return parse_docx(filepath)
    else:
        # Fallback to plain text
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            print(f"Unsupported or unreadable file format: {filepath}")
            return ""
