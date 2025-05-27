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


app = FastAPI()
client = TelegramClient(StringSession(session_string), api_id, api_hash)

class Item(BaseModel):
    query: str


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
            history = await client(GetHistoryRequest(
                peer=channel,
                limit=10,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))
            # добавить добавление поста в бд и колво реакций на посте
            # добавить отправку постов на обработку llm для топиков и реализовать через kafka
            for message in history.messages:
                counter = 0
                for elem in message.reactions.results:
                    if isinstance(elem.reaction, ReactionEmoji) and elem.reaction.emoticon in emoji_translate.keys():
                        counter += emoji_translate[elem.reaction.emoticon] * elem.count
                print(counter)
        else:
            raise HTTPException(status_code=404, detail="Channel not found")



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)