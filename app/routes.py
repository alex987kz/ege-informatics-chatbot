from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.knowledge import COMPANY
from app.nlp import analyze, get_answer
from app.schemas import ChatRequest, ChatResponse

templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Страница чата с приветствием бота."""
    context = {"company": COMPANY, "greeting": get_answer("greeting")}
    return templates.TemplateResponse(request=request, name="index.html", context=context)


@router.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest):
    """Принимает сообщение и возвращает ответ, тему и шаги распознавания."""
    message = data.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Введите сообщение.")

    topic, steps = analyze(message)
    return ChatResponse(answer=get_answer(topic), topic=topic, steps=steps)
