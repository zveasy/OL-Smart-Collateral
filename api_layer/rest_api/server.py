import logging
import os
import time
import uuid
from collections import defaultdict
from threading import Lock

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api_layer.rest_api.carbon_routes import MintRequest, RetireRequest  # re-export compatibility
from api_layer.rest_api.carbon_routes import router as carbon_router
from api_layer.rest_api.kaleido_client import runtime_config_health

app = FastAPI(
    title="O&L Carbon Credit API",
    version="1.0",
)


def _parse_cors_origins() -> list[str]:
    raw = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


ALLOW_ORIGINS = _parse_cors_origins()
ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
ALLOW_HEADERS = ["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_methods=ALLOW_METHODS,
    allow_headers=ALLOW_HEADERS,
)

logger = logging.getLogger("uvicorn.access")
logger.setLevel(logging.INFO)

_metrics_lock = Lock()
_request_counts: dict[tuple[str, str, int], int] = defaultdict(int)
_request_latency_ms_sum: dict[tuple[str, str], float] = defaultdict(float)
_idempotency_lock = Lock()
_idempotent_cache: dict[str, tuple[float, int, bytes, str | None]] = {}
_IDEMPOTENT_PATHS = {"/carbon/mint", "/carbon/retire", "/carbon/transfer"}


def _observe_request(method: str, path: str, status: int, latency_ms: float) -> None:
    with _metrics_lock:
        _request_counts[(method, path, status)] += 1
        _request_latency_ms_sum[(method, path)] += latency_ms


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        _observe_request(request.method, request.url.path, response.status_code, elapsed_ms)
        logger.info(
            "request_id=%s method=%s path=%s status=%d latency_ms=%.1f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method != "POST" or request.url.path not in _IDEMPOTENT_PATHS:
            return await call_next(request)

        key = request.headers.get("Idempotency-Key")
        if not key:
            return JSONResponse(
                status_code=400,
                content={"detail": "Idempotency-Key header required"},
            )

        ttl_seconds = int(os.getenv("IDEMPOTENCY_TTL_SECONDS", "600"))
        cache_key = f"{request.url.path}:{key}"
        now = time.time()

        with _idempotency_lock:
            cached = _idempotent_cache.get(cache_key)
            if cached and cached[0] > now:
                _, status_code, body, media_type = cached
                response = Response(
                    content=body,
                    status_code=status_code,
                    media_type=media_type,
                )
                response.headers["X-Idempotent-Replay"] = "true"
                return response

        response = await call_next(request)
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        replayable = response.status_code < 500
        if replayable:
            with _idempotency_lock:
                _idempotent_cache[cache_key] = (
                    now + ttl_seconds,
                    response.status_code,
                    response_body,
                    response.media_type,
                )

        final_response = Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
        return final_response


app.add_middleware(RequestContextMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.include_router(carbon_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/live")
def health_live():
    return {"status": "alive"}


@app.get("/health/ready")
def health_ready():
    state = runtime_config_health()
    if not state["ready"]:
        raise HTTPException(status_code=503, detail={"status": "not_ready", **state})
    return {"status": "ready"}


@app.get("/metrics")
def metrics() -> Response:
    lines = [
        "# HELP api_requests_total Total API requests by method/path/status",
        "# TYPE api_requests_total counter",
    ]
    with _metrics_lock:
        for (method, path, status), count in sorted(_request_counts.items()):
            lines.append(
                f'api_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}'
            )
        lines.append("# HELP api_request_latency_ms_sum Sum of request latency in milliseconds")
        lines.append("# TYPE api_request_latency_ms_sum counter")
        for (method, path), total in sorted(_request_latency_ms_sum.items()):
            lines.append(
                f'api_request_latency_ms_sum{{method="{method}",path="{path}"}} {total:.3f}'
            )
    return Response("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")
