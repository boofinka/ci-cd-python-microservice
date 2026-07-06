from datetime import datetime, time as dt_time, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse
import logging
import time

from app.logging_config import configure_logging

configure_logging()
logger = logging.getLogger("app")

app = FastAPI()
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML_PATH = STATIC_DIR / "index.html"


def is_shaas_window(now: datetime) -> bool:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    if now.weekday() == 4:  # Friday
        start_time = datetime.combine(now.date(), dt_time(15, 30), tzinfo=timezone.utc)
        end_time = datetime.combine(now.date() + timedelta(days=1), dt_time(16, 0), tzinfo=timezone.utc)
        return start_time <= now <= end_time

    if now.weekday() == 5:  # Saturday
        start_time = datetime.combine(now.date(), dt_time(0, 0), tzinfo=timezone.utc)
        end_time = datetime.combine(now.date(), dt_time(16, 0), tzinfo=timezone.utc)
        return start_time <= now <= end_time

    return False

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()

    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    client_ip = request.client.host if request.client is not None else None

    logger.info(
        "request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration,
            "client_ip": client_ip,
        },
    )

    return response

@app.get("/favicon.ico")
def favicon():
    return FileResponse("app/static/favicon.ico")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return FileResponse(INDEX_HTML_PATH)


@app.get("/shaas")
def shaas(request: Request):
    now = datetime.now().astimezone()
    answer = "Yes" if is_shaas_window(now) else "No"
    return PlainTextResponse(answer)
