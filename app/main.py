import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse
import logging
import time

import requests

from app.logging_config import configure_logging

configure_logging()
logger = logging.getLogger("app")

app = FastAPI()
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML_PATH = STATIC_DIR / "index.html"
CACHE_FILE = Path(__file__).resolve().parent / "shabbat_cache.json"
_SHABBAT_WINDOW_CACHE: Dict[Tuple[str, int, int], Tuple[datetime, datetime]] = {}


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    return None


def _get_cache_key(location: Optional[str], now: datetime) -> Tuple[str, int, int]:
    location_key = location or "default"
    return location_key, now.year, now.isocalendar().week


def _load_cache() -> None:
    global _SHABBAT_WINDOW_CACHE
    if not CACHE_FILE.exists():
        _SHABBAT_WINDOW_CACHE = {}
        return

    try:
        with CACHE_FILE.open("r", encoding="utf-8") as handle:
            raw_cache = json.load(handle)
    except (OSError, json.JSONDecodeError):
        _SHABBAT_WINDOW_CACHE = {}
        return

    parsed_cache: Dict[Tuple[str, int, int], Tuple[datetime, datetime]] = {}
    for (location_key, year, week), (start_text, end_text) in raw_cache.items():
        start_time = _parse_datetime(start_text)
        end_time = _parse_datetime(end_text)
        if start_time is not None and end_time is not None:
            parsed_cache[(location_key, int(year), int(week))] = (start_time, end_time)

    _SHABBAT_WINDOW_CACHE = parsed_cache


def _save_cache() -> None:
    serializable_cache = {
        str(key): [start_time.isoformat(), end_time.isoformat()]
        for key, (start_time, end_time) in _SHABBAT_WINDOW_CACHE.items()
    }
    with CACHE_FILE.open("w", encoding="utf-8") as handle:
        json.dump(serializable_cache, handle, indent=2)


_load_cache()


def get_shabbat_window(request_ip: Optional[str] = None, now: Optional[datetime] = None) -> Optional[Tuple[datetime, datetime]]:
    current_time = now or datetime.now().astimezone()
    cache_key = _get_cache_key(request_ip, current_time)

    if cache_key in _SHABBAT_WINDOW_CACHE:
        return _SHABBAT_WINDOW_CACHE[cache_key]

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

        _SHABBAT_WINDOW_CACHE[cache_key] = (start_time, end_time)
        _save_cache()
        return _SHABBAT_WINDOW_CACHE[cache_key]
    except requests.RequestException:
        return None


def is_shaas_window(now: datetime, request_ip: Optional[str] = None) -> bool:
    window = get_shabbat_window(request_ip=request_ip, now=now)
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
