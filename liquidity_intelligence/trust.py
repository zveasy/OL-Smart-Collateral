from __future__ import annotations

import os
from typing import Any, Protocol

from pydantic import BaseModel, Field


class TrustEvidence(BaseModel):
    provider: str
    verified: bool
    confidence: float = Field(ge=0, le=1)
    references: list[str] = Field(default_factory=list)


class TrustAdapter(Protocol):
    def resolve(
        self, tenant_id: str, asset_id: str, references: list[str]
    ) -> TrustEvidence | None: ...


class LocalDeterministicTrustAdapter:
    def resolve(
        self, tenant_id: str, asset_id: str, references: list[str]
    ) -> TrustEvidence:
        confidence = min(0.99, 0.70 + (0.03 * len(references)))
        return TrustEvidence(
            provider="local-deterministic-stub",
            verified=True,
            confidence=confidence,
            references=sorted(references),
        )


class VeilTrustAdapter:
    """Adapter boundary for VEIL. A resolver can be injected without coupling."""

    def __init__(self, resolver: Any) -> None:
        self.resolver = resolver

    def resolve(
        self, tenant_id: str, asset_id: str, references: list[str]
    ) -> TrustEvidence | None:
        result = self.resolver(tenant_id, asset_id, references)
        return TrustEvidence.model_validate(result) if result else None


class TrustPolicy:
    def __init__(
        self,
        adapter: TrustAdapter | None = None,
        environment: str | None = None,
    ) -> None:
        self.environment = (
            environment or os.getenv("ENVIRONMENT", "development")
        ).lower()
        self.adapter = adapter
        if self.adapter is None and self.environment != "production":
            self.adapter = LocalDeterministicTrustAdapter()

    def evidence_for(
        self, tenant_id: str, asset_id: str, references: list[str]
    ) -> TrustEvidence:
        evidence = (
            self.adapter.resolve(tenant_id, asset_id, references)
            if self.adapter
            else None
        )
        if evidence is None or not evidence.verified:
            raise PermissionError("Verified trust evidence is required")
        return evidence
