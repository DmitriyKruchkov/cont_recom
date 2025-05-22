from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetHistoryRequest
from config import api_id, api_hash, session_string
from telethon.tl.types import ReactionPaid, ReactionEmoji
from emoji import emoji_translate

# 🔐 Ваши данные
channel_username = 'https://t.me/bIoodsiker'  # Можно указать юзернейм канала или ссылку

# Создание клиента
with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
    # Получение объекта канала
    channel = client.get_entity(channel_username)

    # Получение истории сообщений
    history = client(GetHistoryRequest(
        peer=channel,
        limit=10,  # Сколько постов получить
        offset_date=None,
        offset_id=0,
        max_id=0,
        min_id=0,
        add_offset=0,
        hash=0
    ))

    for message in history.messages:
        counter = 0
        for elem in message.reactions.results:
            if isinstance(elem.reaction, ReactionEmoji) and elem.reaction.emoticon in emoji_translate.keys():
                counter += emoji_translate[elem.reaction.emoticon] * elem.count
        print(counter)
