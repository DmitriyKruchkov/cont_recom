from ollama import Client
from topics import TOPICS
import os

client = Client(host=os.getenv("OLLAMA_HOST"))


def get_topics(text: str) -> list[str]:
    format_string = '{"topics": ["topic1", ...]}'

    system_prompt = f"""
        Ты — аналитик, определяющий тематику Telegram-постов.

        Назови 1–5 подходящих тем из следующего списка:
        {", ".join(TOPICS)}

        Ответ строго в формате JSON:
        {format_string}
    """

    prompt = f"""Текст: {text}"""
    response = client.chat(model='qwen3:4b',
        messages=[
            {"role": "system", "content": system_prompt},
            {'role': 'user', 'content': prompt}
            ],
        options={
            "temperature": 0.0
            })

    raw = response['message']['content']
    return raw

# 🔬 Пример поста из Telegram
post = """"""
print(get_topics(post))

