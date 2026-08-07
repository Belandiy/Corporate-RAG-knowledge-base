from typing import List
from llama_index.core.node_parser import SentenceSplitter

def get_chunks(text: str, chunk_size: int = 512, chunk_overlap: int = 50) -> List[str]:
    """
    Splits text into chunks using LlamaIndex's SentenceSplitter.
    Overlap is approximately 10-15% of chunk_size.
    """
    if not text.strip():
        return []

    parser = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = parser.split_text(text)
    return chunks
