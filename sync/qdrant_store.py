import os
import uuid
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from dotenv import load_dotenv

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = "knowledge_base"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL_ID", "intfloat/multilingual-e5-large")

# Initialize Embedding Model
# This downloads the model on first run if not present.
embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)
VECTOR_SIZE = 1024 # specific to intfloat/multilingual-e5-large

class QdrantStore:
    def __init__(self):
        if QDRANT_HOST == "local":
            self.client = QdrantClient(path=os.getenv("QDRANT_PATH", "qdrant_db"))
        else:
            self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self._init_collection()

    def _init_collection(self):
        if not self.client.collection_exists(COLLECTION_NAME):
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE
                )
            )
            # Create payload indexes as specified in documentation
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="doc_id",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="department",
                field_schema=models.PayloadSchemaType.KEYWORD
            )

    def delete_document(self, filepath: str):
        """
        Deletes all chunks associated with a specific file.
        We filter by path because doc_id might not be known if we just have the filepath from watchdog.
        """
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="path",
                            match=models.MatchValue(value=filepath)
                        )
                    ]
                )
            )
        )
        print(f"Deleted points for {filepath} from Qdrant.")

    def upsert_document(self, filepath: str, filename: str, chunks: List[str]):
        """
        Embeds chunks and stores them in Qdrant.
        """
        # Delete existing entries for this file to avoid duplication on modification
        self.delete_document(filepath)

        if not chunks:
            return

        doc_id = str(uuid.uuid4())

        # Determine some basic metadata
        # In a real app, this might come from tags, folders, or file properties.
        department = "general"
        document_type = "unknown"
        if "policy" in filename.lower():
            document_type = "policy"
            department = "HR"

        points = []
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = embed_model.get_text_embedding(chunk)

            point = models.PointStruct(
                id=str(uuid.uuid4()), # Unique point ID
                vector=embedding,
                payload={
                    "doc_id": doc_id,
                    "filename": filename,
                    "path": filepath,
                    "chunk_index": i,
                    "text_content": chunk,
                    "metadata": {
                        "department": department,
                        "created_at": int(os.path.getmtime(filepath)),
                        "document_type": document_type,
                        "tags": []
                    }
                }
            )
            points.append(point)

        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print(f"Upserted {len(points)} chunks for {filename} into Qdrant.")

# Singleton instance
store = QdrantStore()
