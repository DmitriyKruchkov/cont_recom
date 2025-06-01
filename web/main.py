import uvicorn
from fastapi import FastAPI, Request, Query, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import httpx

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
@app.get("/search", response_class=HTMLResponse)
async def home(request: Request, query: str = None):
    return templates.TemplateResponse("search.html", {"request": request})

@app.post("/search", response_class=RedirectResponse)
async def post_form(request: Request, query: str = Form(...)):
    body = {
        "query": query
    }
    send_channel = httpx.post("http://tg_preparator:8000/add_in_queue", json=body)
    if send_channel.status_code == 404:
        raise HTTPException(status_code=404, detail="Item not found")
    channel_uuid = send_channel.json().get("channel_uuid")
    return RedirectResponse(f"/channel/{channel_uuid}")

@app.exception_handler(404)
async def handle_404(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


@app.get("/channel/{channel_uuid}", response_class=HTMLResponse)
async def read_root(channel_uuid, request):
    chart_data = [
        {"label": "1", "height": 400, "color": "#4CAF50", "value": 1, "topic_name": "topic_1"},
        {"label": "2", "height": 160, "color": "#F44336", "value": 2, "topic_name": "topic_2"},
        {"label": "3", "height": 100, "color": "#9C27B0", "value": 3, "topic_name": "topic_3"},
        {"label": "4", "height": 100, "color": "#FF9800", "value": 4, "topic_name": "topic_4"},
    ]
    topics = ["topic_1", "topic_2", "topic_3"]
    return templates.TemplateResponse("graph.html", {
        "request": request,
        "channel_name": "Telegram_channel_name",
        "link": "@link",
        "chart_data": chart_data,
        "topics": topics
    })


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)