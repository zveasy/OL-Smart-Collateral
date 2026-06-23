from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Iterable

from .models import canonical_data, canonical_json, deterministic_id


class EventStore:
    """Tenant-scoped append-only event store with deterministic logical ordering."""

    def __init__(self, path: str | Path | None = None) -> None:
        configured = path or os.getenv(
            "LIQUIDITY_EVENT_STORE", ".liquidity/events.jsonl"
        )
        self.path = Path(configured)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)
        self._lock = threading.RLock()

    def read(self, tenant_id: str | None = None) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        with self._lock:
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                event = json.loads(line)
                if tenant_id is None or event["tenant_id"] == tenant_id:
                    events.append(event)
        return events

    def append(
        self, tenant_id: str, event_type: str, aggregate_id: str, payload: Any
    ) -> dict[str, Any]:
        with self._lock:
            sequence = len(self.read()) + 1
            normalized = canonical_data(payload)
            event = {
                "sequence": sequence,
                "event_id": deterministic_id(
                    "evt",
                    {
                        "sequence": sequence,
                        "tenant_id": tenant_id,
                        "event_type": event_type,
                        "aggregate_id": aggregate_id,
                        "payload": normalized,
                    },
                ),
                "tenant_id": tenant_id,
                "event_type": event_type,
                "aggregate_id": aggregate_id,
                "logical_time": sequence,
                "payload": normalized,
            }
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(canonical_json(event) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            return event

    def export_bundle(self, tenant_id: str) -> dict[str, Any]:
        events = self.read(tenant_id)
        return {
            "tenant_id": tenant_id,
            "event_count": len(events),
            "events": events,
            "bundle_id": deterministic_id("audit", events),
        }

    @staticmethod
    def select(
        events: Iterable[dict[str, Any]], event_type: str
    ) -> list[dict[str, Any]]:
        return [event for event in events if event["event_type"] == event_type]
