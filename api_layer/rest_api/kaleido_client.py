from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import Any

import requests
from dotenv import load_dotenv

from api_layer.utils import to_checksum

load_dotenv()

REQUIRED_ENV_VARS = (
    "KALEIDO_API_URL",
    "KALEIDO_API_KEY",
    "CARBON_CONTRACT_ADDRESS",
    "ADMIN_ADDRESS",
)


class UpstreamUnavailableError(RuntimeError):
    """Raised when the circuit breaker is open for Kaleido calls."""


@dataclass(frozen=True)
class RuntimeConfig:
    api_url: str
    api_key: str
    contract_addr: str
    admin_addr: str


_cb_lock = threading.Lock()
_cb_failures = 0
_cb_open_until = 0.0


def runtime_config_health() -> dict[str, Any]:
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    return {"ready": not missing, "missing": missing}


def _get_runtime_config() -> RuntimeConfig:
    health = runtime_config_health()
    if not health["ready"]:
        missing = ", ".join(health["missing"])
        raise RuntimeError(f"Missing environment variables: {missing}")
    return RuntimeConfig(
        api_url=os.environ["KALEIDO_API_URL"].rstrip("/"),
        api_key=os.environ["KALEIDO_API_KEY"],
        contract_addr=to_checksum(os.environ["CARBON_CONTRACT_ADDRESS"]),
        admin_addr=to_checksum(os.environ["ADMIN_ADDRESS"]),
    )


def _base_headers(cfg: RuntimeConfig) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }


def _circuit_is_open() -> bool:
    with _cb_lock:
        return time.time() < _cb_open_until


def _record_success() -> None:
    global _cb_failures, _cb_open_until
    with _cb_lock:
        _cb_failures = 0
        _cb_open_until = 0.0


def _record_failure() -> None:
    global _cb_failures, _cb_open_until
    threshold = int(os.getenv("KALEIDO_CB_FAILURE_THRESHOLD", "5"))
    cooldown_seconds = float(os.getenv("KALEIDO_CB_COOLDOWN_SECONDS", "30"))
    with _cb_lock:
        _cb_failures += 1
        if _cb_failures >= threshold:
            _cb_open_until = time.time() + cooldown_seconds


def _request_json(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json_payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    if _circuit_is_open():
        raise UpstreamUnavailableError("Kaleido circuit breaker is open")

    attempts = int(os.getenv("KALEIDO_RETRY_ATTEMPTS", "3"))
    backoff_base = float(os.getenv("KALEIDO_RETRY_BACKOFF_SECONDS", "0.5"))
    last_exc: Exception | None = None

    for attempt in range(attempts):
        try:
            resp = requests.request(
                method,
                url,
                params=params,
                json=json_payload,
                headers=headers,
                timeout=timeout,
            )
            resp.raise_for_status()
            _record_success()
            return resp.json()
        except requests.HTTPError as exc:
            last_exc = exc
            status = exc.response.status_code if exc.response is not None else None
            retryable = status is None or status == 429 or status >= 500
            if not retryable or attempt == attempts - 1:
                _record_failure()
                raise
        except requests.RequestException as exc:
            last_exc = exc
            if attempt == attempts - 1:
                _record_failure()
                raise
        time.sleep(backoff_base * (2**attempt))

    _record_failure()
    if last_exc:
        raise last_exc
    raise RuntimeError("Kaleido request failed unexpectedly")


def _gw(path: str) -> str:
    cfg = _get_runtime_config()
    return f"{cfg.api_url}{path}"


def _post_sync(
    path: str,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = _get_runtime_config()
    return _request_json(
        "POST",
        _gw(path),
        params=params,
        json_payload=json,
        headers=_base_headers(cfg)
        | {
            "x-kaleido-from": cfg.admin_addr,
            "x-kaleido-sync": "true",
        },
        timeout=30,
    )


def _call(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = _get_runtime_config()
    url = _gw(path)
    try:
        return _request_json(
            "GET",
            url,
            params=params,
            headers=_base_headers(cfg),
            timeout=15,
        )
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code not in (404, 405, 501):
            raise
        return _request_json(
            "POST",
            url,
            params=params,
            headers=_base_headers(cfg) | {"x-kaleido-call": "true"},
            timeout=15,
        )
    except requests.exceptions.InvalidSchema:
        return _request_json(
            "POST",
            url,
            params=params,
            headers=_base_headers(cfg) | {"x-kaleido-call": "true"},
            timeout=15,
        )


def grant_role(role_hash: str, addr: str) -> dict[str, Any]:
    return _post_sync(
        f"/contracts/{_get_runtime_config().contract_addr}/grantRole",
        params={
            "role": role_hash,
            "address": to_checksum(addr),
        },
    )


def mint_nft(
    to_address: str,
    token_id: int,
    amount: int,
    token_uri: str,
) -> dict[str, Any]:
    return _post_sync(
        f"/contracts/{_get_runtime_config().contract_addr}/mint",
        params={
            "to": to_checksum(to_address),
            "id": token_id,
            "amount": amount,
            "data": "0x",
        },
        json={"uri": token_uri},
    )


def retire_nft(token_id: int, amount: int) -> dict[str, Any]:
    cfg = _get_runtime_config()
    return _post_sync(
        f"/contracts/{cfg.contract_addr}/burn",
        params={
            "from": cfg.admin_addr,
            "id": token_id,
            "amount": amount,
        },
    )


def owner_of(token_id: int) -> dict[str, Any]:
    return _call(
        f"/contracts/{_get_runtime_config().contract_addr}/ownerOf",
        params={"tokenId": token_id},
    )


def token_uri(token_id: int) -> dict[str, Any]:
    return _call(
        f"/contracts/{_get_runtime_config().contract_addr}/tokenURI",
        params={"tokenId": token_id},
    )


def balance_of(owner: str, token_id: int) -> dict[str, Any]:
    return _call(
        f"/contracts/{_get_runtime_config().contract_addr}/balanceOf",
        params={
            "account": to_checksum(owner),
            "id": token_id,
        },
    )


def tokens_by_owner(owner: str) -> dict[str, Any]:
    return _call(
        f"/contracts/{_get_runtime_config().contract_addr}/tokensOfOwner",
        params={"owner": to_checksum(owner)},
    )


def transfer_from(fr: str, to: str, token_id: int, amount: int) -> dict[str, Any]:
    return _post_sync(
        f"/contracts/{_get_runtime_config().contract_addr}/transferFrom",
        params={
            "from": to_checksum(fr),
            "to": to_checksum(to),
            "id": token_id,
            "amount": amount,
            "data": "0x",
        },
    )
