import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    chart_data = [
        {"label": "1", "height": 400, "color": "#4CAF50", "value": 1, "topic_name": "topic_1"},
        {"label": "2", "height": 160, "color": "#F44336", "value": 2, "topic_name": "topic_2"},
        {"label": "3", "height": 100, "color": "#9C27B0", "value": 3, "topic_name": "topic_3"},
        {"label": "4", "height": 100, "color": "#FF9800", "value": 4, "topic_name": "topic_4"},
    ]
    topics = ["topic_1", "topic_2", "topic_3"]
    return templates.TemplateResponse("responce.html", {
        "request": request,
        "channel_name": "Telegram_channel_name",
        "link": "@link",
        "chart_data": chart_data,
        "topics": topics
    })


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)