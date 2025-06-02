from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetHistoryRequest
from config import api_id, api_hash, session_string
from telethon.tl.types import ReactionPaid, ReactionEmoji, Channel
from emoji import emoji_translate
from fastapi import FastAPI, Request
import uvicorn
from pydantic import BaseModel
from telethon.errors.rpcerrorlist import UsernameInvalidError
from os import getenv
import psycopg2
import logging
import json
from confluent_kafka import Consumer, Producer
import asyncio
import uuid
import boto3
import io



POSTS_COUNT = 5

dsn = {
    "dbname": getenv("POSTGRES_DB"),
    "user": getenv("POSTGRES_USER"),
    "password": getenv("POSTGRES_PASSWORD"),
    "host": getenv("POSTGRES_HOST", "postgres"),
    "port": getenv("POSTGRES_PORT", "5432"),
}

kafka_conf_producer = {'bootstrap.servers': 'kafka:9092'}
kafka_conf_consumer = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'ml_responces_group',
    'auto.offset.reset': 'earliest'
}
BUCKET_NAME = "picture-bucket"
MINIO_ENDPOINT = getenv("MINIO_ENDPOINT")

s3 = boto3.client(
    's3',
    endpoint_url='http://minio:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin',
    region_name='us-east-1'
)
policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": "*",
        "Action": ["s3:GetObject"],
        "Resource": [f"arn:aws:s3:::{BUCKET_NAME}/*"]
    }]
}

s3.put_bucket_policy(
    Bucket=BUCKET_NAME,
    Policy=json.dumps(policy)
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

producer = Producer(kafka_conf_producer)

app = FastAPI()
client = TelegramClient(StringSession(session_string), api_id, api_hash)

class Item(BaseModel):
    query: str


@app.on_event("startup")
def start_kafka_consumer():
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, consume_kafka)

def send_to_s3(buffer):
    s3_key = f"avatars/{uuid.uuid4().hex}.jpg"
    s3.upload_fileobj(buffer, BUCKET_NAME, s3_key, ExtraArgs={'ContentType': 'image/jpeg'})
    return f"http://{MINIO_ENDPOINT}/{BUCKET_NAME}/{s3_key}"
    

@app.post("/add_in_queue")
async def send_to_queue(item: Item):

    channel_username = item.query
    async with client:
        try:
            channel = await client.get_entity(channel_username)
        except UsernameInvalidError:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        if isinstance(channel, Channel) and channel.megagroup is False:
            # добавить добавление канала в БД и в редис и возврат uuid для дальнейшей обработки
            with psycopg2.connect(**dsn) as conn:
                with conn.cursor() as cur:

                    buffer = io.BytesIO()
                    await client.download_profile_photo(channel, file=buffer)
                    buffer.seek(0)

                    cur.execute("""INSERT INTO channels_status (
                                    telegram_link, channel_name, picture_link, processing_status
                                    ) 
                                    VALUES (%s, %s, %s, %s)
                                    RETURNING id""", (
                    channel_username,
                    channel.title,
                    # добавить отправку на S3
                    send_to_s3(buffer),
                    False
                    ))
                    channel_uuid = cur.fetchone()[0]
                    history = await client(GetHistoryRequest(
                        peer=channel,
                        limit=POSTS_COUNT,
                        offset_date=None,
                        offset_id=0,
                        max_id=0,
                        min_id=0,
                        add_offset=0,
                        hash=0
                    ))
                    logger.info(history.messages)
                    # добавить добавление поста в бд и колво реакций на посте
                    # добавить отправку постов на обработку llm для топиков и реализовать через kafka
                    for message in history.messages:
                        counter = 0
                        emoji_counter = 0
                        if not message.reactions:
                            continue
                        for elem in message.reactions.results:
                            if isinstance(elem.reaction, ReactionEmoji) and elem.reaction.emoticon in emoji_translate.keys():
                                emoji_counter += emoji_translate[elem.reaction.emoticon] * elem.count

                        cur.execute("""INSERT INTO posts (
                                    channel_id, reaction, message_link, processing_status
                                    ) 
                                    VALUES (%s, %s, %s, %s)
                                    RETURNING id""", (
                                    channel_uuid,
                                    emoji_counter,
                                    channel_username,
                                    False
                                    ))
                        post_id = cur.fetchone()[0]
                        data = {
                            "channel_uuid": channel_uuid,
                            "post_id": post_id,
                            "text": message.message,
                            "emoji": emoji_counter,
                            "is_last": counter == len(history.messages) - 1
                            }
                        producer.produce(
                            topic="ml_requests",
                            value=json.dumps(data),
                            callback=delivery_report
                        )
                        counter += 1
                    conn.commit()
                    producer.flush()

                    return {"channel_uuid": channel_uuid}
        else:
            raise HTTPException(status_code=404, detail="Channel not found")
def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

@app.get("/channel/{channel_uuid}")
def get_channel_topics(channel_uuid):

    if not is_valid_uuid(channel_uuid):
        return {"status": False}

    with psycopg2.connect(**dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT processing_status FROM channels_status WHERE id = %s", (channel_uuid,))
            status = cur.fetchone()

            if not status or not status[0]:
                return {"status": False}
            else:
                cur.execute("""
                                SELECT 
                                    cs.channel_name,
                                    cs.telegram_link,
                                    cs.picture_link,
                                    pt.topic,
                                    SUM(p.reaction) AS total_reactions
                                FROM channels_status cs
                                JOIN posts p ON cs.id = p.channel_id
                                JOIN post_topics pt ON p.id = pt.post_id
                                WHERE cs.id = %s AND cs.processing_status = TRUE
                                GROUP BY cs.channel_name, cs.telegram_link, cs.picture_link, pt.topic
                                ORDER BY total_reactions DESC;
                """, (channel_uuid,))
                rows = cur.fetchall()

                channel_name = rows[0][0] if rows else None
                telegram_link = rows[0][1] if rows else None
                picture_link = rows[0][2] if rows else None
                chart_data = [
                    {"label": topic, "value": reactions}
                    for _, _, _, topic, reactions in rows
                ]
                topics = [row[2] for row in rows]
                return {
                    "status": True,
                    "channel_name": channel_name,
                    "link": telegram_link,
                    "picture_link": picture_link,
                    "chart_data": chart_data,
                    "topics": topics
                    }

def delivery_report(err, msg):
    if err is not None:
        logger.error(f"Delivery failed: {err}")
    else:
        logger.info(
            f"Message delivered to {msg.topic()} [partition {msg.partition()}] at offset {msg.offset()}"
        )

def consume_kafka():
    consumer = Consumer(kafka_conf_consumer)
    consumer.subscribe(['ml_responces'])

    conn = psycopg2.connect(**dsn)
    cur = conn.cursor()

    logger.info("Kafka consumer started")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None or msg.error():
                continue

            try:
                data = json.loads(msg.value())
                channel_uuid = data["channel_uuid"]
                post_id = data["post_id"]
                topics = data["topics"]
                is_last = data["is_last"]

                for topic in topics:
                    cur.execute(
                        "INSERT INTO post_topics (post_id, topic) VALUES (%s, %s)",
                        (post_id, topic)
                    )

                if is_last:
                    cur.execute(
                        "UPDATE channels_status SET processing_status = %s WHERE id = %s",
                        (True, channel_uuid)
                    )
                    cur.execute(
                        "UPDATE posts SET processing_status = %s WHERE id = %s",
                        (True, post_id)
                    )
                    conn.commit()

            except Exception as e:
                logger.info("Error handling message:", e)
                conn.rollback()

    except Exception as e:
        logger.info("Kafka loop error:", e)
    finally:
        cur.close()
        conn.close()
        consumer.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)