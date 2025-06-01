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
    return RedirectResponse(f"/channel/{channel_uuid}", status_code=302)

@app.exception_handler(404)
async def handle_404(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


@app.get("/channel/{channel_uuid}", response_class=HTMLResponse)
async def read_root(channel_uuid: str, request: Request):
    channel = (httpx.get(f"http://tg_preparator:8000/channel/{channel_uuid}")).json()

    if channel.get('status'):
        chart_data = channel["chart_data"]
        
        # Нормализация значений
        max_val = max(abs(item["value"]) for item in chart_data) or 1
        for item in chart_data:
            item["normalized"] = abs(item["value"]) / max_val

        print(chart_data)
        return templates.TemplateResponse("graph.html", {
            "request": request,
            "channel_name": channel["channel_name"],
            "link": channel["link"],
            "chart_data": chart_data,
            "topics": channel["topics"],
        })
    else:
        raise HTTPException(status_code=404, detail="Item not found")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)