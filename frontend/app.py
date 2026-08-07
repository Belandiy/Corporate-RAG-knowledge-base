import os
import requests
import chainlit as cl

API_URL = os.environ.get("API_URL", "http://localhost:8000")

@cl.on_chat_start
async def start():
    await cl.Message(content="Добро пожаловать в Корпоративную RAG-базу знаний! Задайте ваш вопрос.").send()

@cl.on_message
async def main(message: cl.Message):
    # Send request to FastAPI backend
    payload = {
        "query": message.content,
        "top_k": 3,
        "stream": False
    }

    try:
        response = requests.post(f"{API_URL}/api/v1/query", json=payload)
        response.raise_for_status()
        data = response.json()

        answer = data.get("answer", "Нет ответа")
        sources = data.get("sources", [])
        metrics = data.get("metrics", {})

        # Build text elements for sources
        elements = []
        source_names = []
        for i, src in enumerate(sources):
            source_name = f"Источник {i+1} ({src['title']})"
            source_names.append(source_name)

            # Chainlit Text element to display source content
            text_el = cl.Text(name=source_name, content=src['chunk_text'], display="side")
            elements.append(text_el)

        # Add metrics info to the answer
        metrics_info = f"\n\n*Latency: {metrics.get('latency_ms', 0)} ms | Tokens: {metrics.get('tokens_used', 0)}*"

        final_answer = answer + metrics_info
        if source_names:
            final_answer += f"\n\n**Источники:** {', '.join(source_names)}"

        await cl.Message(content=final_answer, elements=elements).send()

    except Exception as e:
        await cl.Message(content=f"Произошла ошибка при обращении к API: {e}").send()
