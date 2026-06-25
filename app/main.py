from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import time
import logging

from app.logging_config import configure_logging

configure_logging()
logger = logging.getLogger("app")

app = FastAPI()

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
    return {"message": "Hello from CI/CD Python Microservice!"}
