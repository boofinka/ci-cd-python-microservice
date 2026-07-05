from datetime import datetime
from typing import Optional, Tuple
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse
from pathlib import Path
import logging
import time

import requests

from app.logging_config import configure_logging

configure_logging()
logger = logging.getLogger("app")

app = FastAPI()
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML_PATH = STATIC_DIR / "index.html"


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    return None


def get_shabbat_window(request_ip: Optional[str] = None) -> Optional[Tuple[datetime, datetime]]:
    geo_loc_api_url = f"http://ip-api.com/json/{request_ip}" if request_ip else "http://ip-api.com/json/"

    try:
        geo_response = requests.get(geo_loc_api_url, timeout=5)
        geo_response.raise_for_status()
        geo_data = geo_response.json()
        lat = geo_data.get("lat")
        lon = geo_data.get("lon")

        if lat is None or lon is None:
            return None

        shabbat_times_api_url = f"https://www.hebcal.com/shabbat/?cfg=json&latitude={lat}&longitude={lon}"
        shabbat_response = requests.get(shabbat_times_api_url, timeout=5)
        shabbat_response.raise_for_status()
        items = shabbat_response.json().get("items", [])

        if not items:
            return None

        start_time = _parse_datetime(items[0].get("date"))
        end_time = _parse_datetime(items[-1].get("date"))
        if start_time is None or end_time is None:
            return None

        return start_time, end_time
    except requests.RequestException:
        return None


def is_shaas_window(now: datetime, request_ip: Optional[str] = None) -> bool:
    window = get_shabbat_window(request_ip)
    if window is None:
        return False

    start_time, end_time = window
    if now.tzinfo is None:
        now = now.replace(tzinfo=datetime.now().astimezone().tzinfo)

    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=now.tzinfo)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=now.tzinfo)

    return start_time <= now <= end_time

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
    request_ip = request.client.host if request.client is not None else None
    answer = "Yes" if is_shaas_window(now, request_ip=request_ip) else "No"
    return PlainTextResponse(answer)
