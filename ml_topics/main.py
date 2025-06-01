from ollama import Client
from topics import TOPICS
import os
import logging
import json
from confluent_kafka import Consumer, Producer

client = Client(host=os.getenv("OLLAMA_HOST"))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'ml_requests_group',
    'auto.offset.reset': 'earliest'
})
consumer.subscribe(['ml_requests'])
kafka_conf_producer = {'bootstrap.servers': 'kafka:9092'}
producer = Producer(kafka_conf_producer)

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
    last_line = raw.strip().splitlines()[-1]

    return json.loads(last_line)["topics"]


def main():
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None or msg.error():
                continue

            try:
                data = json.loads(msg.value())
                text = data["text"]
                if not text:
                    logger.info("No text in message")
                    continue

                logger.info("Post received. Running LLM topic classification...")
                topics_json = get_topics(text)
                logger.info(f"Topics: {topics_json}")

                data = {
                    "channel_uuid": data["channel_uuid"],
                    "post_id": data["post_id"],
                    "topics": topics_json,
                    "is_last": data["is_last"]
                    }
                producer.produce(
                    topic="ml_responces",
                    value=json.dumps(data)
                )
                producer.flush()

            except Exception as e:
                logger.info(f"Error processing message: {e}")

    except KeyboardInterrupt:
        logger.info("Shutting down...")

    finally:
        consumer.close()

if __name__ == "__main__":
    main()