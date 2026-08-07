from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
from app.core.config import settings

def setup_llm_and_embeddings():
    # Setup Embeddings
    embed_model = HuggingFaceEmbedding(model_name=settings.EMBEDDING_MODEL_ID)
    Settings.embed_model = embed_model

    # Setup LLM (OpenAI Compatible like LM Studio)
    from llama_index.llms.openai import OpenAI
    # Use generic OpenAI constructor kwargs for custom model
    llm = OpenAI(
        model="gpt-3.5-turbo", # fallback or just pass anything since API will override
        api_base=settings.LLM_BASE_URL,
        api_key=settings.OPENAI_API_KEY,
        additional_kwargs={"model": settings.LLM_MODEL}
    )
    Settings.llm = llm

    return llm, embed_model

llm, embed_model = setup_llm_and_embeddings()
