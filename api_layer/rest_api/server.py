from __future__ import annotations

import json
import logging
import time
import uuid

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from api_layer.config import (
    validate_env,
    get_cors_origins,
    get_log_level,
    get_log_format,
    get_docs_enabled,
)
from slowapi.middleware import SlowAPIMiddleware

from api_layer.rest_api.carbon_routes import router as carbon_router
from api_layer.rest_api.liquidity_routes import router as liquidity_router
from api_layer.rest_api.rate_limit import (
    limiter,
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

# Re-export for backwards compatibility
from fastapi import HTTPException
from api_layer.rest_api.carbon_routes import MintRequest, RetireRequest

__all__ = ["HTTPException", "MintRequest", "RetireRequest", "app"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate config at startup; fail fast if env is invalid."""
    validate_env()
    yield
    # shutdown: nothing to tear down


_docs_url = "/docs" if get_docs_enabled() else None
_redoc_url = "/redoc" if get_docs_enabled() else None

app = FastAPI(
    title="O&L Carbon Credit API",
    version="1.0",
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ───────────────────────────────
# 1. CORS
# ───────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-API-Key",
        "X-Request-ID",
        "X-Tenant-ID",
    ],
)

# ───────────────────────────────
# 2. Request ID and structured logging
# ───────────────────────────────
LOG_LEVEL = get_log_level()
LOG_FORMAT = get_log_format()
logger = logging.getLogger("uvicorn.access")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        delta_ms = (time.perf_counter() - start) * 1000
        if LOG_FORMAT == "json":
            log_obj = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(delta_ms, 2),
            }
            logger.info("%s", json.dumps(log_obj))
        else:
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
# 3. Include API routes (versioned + legacy)
# ───────────────────────────────
app.include_router(carbon_router, prefix="/v1")  # versioned: /v1/carbon/...
app.include_router(carbon_router)  # legacy: /carbon/...
app.include_router(liquidity_router, prefix="/v1")
app.include_router(liquidity_router)


# ───────────────────────────────
# 4. Health endpoints (exempt from rate limit)
# ───────────────────────────────
@app.get("/health")
@limiter.exempt
def health():
    """Liveness: process is up."""
    return {"status": "ok"}


@app.get("/health/ready")
@limiter.exempt
def health_ready():
    """Readiness: app and Kaleido gateway are reachable."""
    from fastapi.responses import JSONResponse
    from api_layer.rest_api.kaleido_client import check_connectivity

    if check_connectivity():
        return {"status": "ok", "kaleido": "up"}
    return JSONResponse(
        status_code=503,
        content={"status": "degraded", "kaleido": "down"},
    )
