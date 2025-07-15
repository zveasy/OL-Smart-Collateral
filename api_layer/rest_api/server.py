
import os
import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from api_layer.rest_api.carbon_routes import router as carbon_router
# server.py  (bottom)
from fastapi import HTTPException as HTTPException        # re-export
from api_layer.rest_api.carbon_routes import MintRequest, RetireRequest


app = FastAPI(
    title="O&L Carbon Credit API",
    version="1.0",
)

# ───────────────────────────────
# 1.  CORS  (allow everything in dev; restrict in prod)
# ───────────────────────────────
ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
ALLOW_HEADERS = ["Authorization", "Content-Type"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_methods=ALLOW_METHODS,
    allow_headers=ALLOW_HEADERS,
)

# ───────────────────────────────
# 2.  Structured request-logging
# ───────────────────────────────
logger = logging.getLogger("uvicorn.access")  # reuse Uvicorn’s handler
logger.setLevel(logging.INFO)

class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        delta_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s → %d (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            delta_ms,
        )
        return response

app.add_middleware(RequestLogMiddleware)

# ───────────────────────────────
# 3.  Include API routes
# ───────────────────────────────
app.include_router(carbon_router)

# ───────────────────────────────
# 4.  Health check endpoint
# ───────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}
