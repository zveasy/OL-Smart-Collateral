from __future__ import annotations

import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


MONEY_QUANTUM = Decimal("0.01")
SCORE_QUANTUM = Decimal("0.0001")


def decimal(value: Any) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def money(value: Any) -> Decimal:
    return decimal(value).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def score(value: Any) -> Decimal:
    return decimal(value).quantize(SCORE_QUANTUM, rounding=ROUND_HALF_UP)


def clamp(value: Any, minimum: Any = 0, maximum: Any = 1) -> Decimal:
    return max(decimal(minimum), min(decimal(maximum), decimal(value)))


def canonical_data(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if hasattr(value, "model_dump"):
        return canonical_data(value.model_dump(mode="python"))
    if isinstance(value, dict):
        return {str(key): canonical_data(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [canonical_data(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(canonical_data(value), sort_keys=True, separators=(",", ":"))


def deterministic_id(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()[:24]
    return f"{prefix}_{digest}"
