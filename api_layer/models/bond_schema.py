from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import AliasChoices, BaseModel, Field, ValidationInfo, field_validator


class Frequency(str, Enum):
    ANNUAL = "ANNUAL"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"


class BondMetadata(BaseModel):
    name: str | None = None
    isin: str | None = None
    issuer: str
    issueDate: date
    maturityDate: date = Field(
        validation_alias=AliasChoices("maturityDate", "maturity"),
        serialization_alias="maturityDate",
    )
    currency: str
    couponRate: float
    couponFrequency: Frequency
    faceValue: Decimal = Field(gt=0, json_schema_extra={"examples": ["1000000.00"]})
    carbonOffsetTons: Decimal | None = Field(
        default=None, ge=0, json_schema_extra={"examples": ["250.0000"]}
    )
    esgScore: int | None = Field(default=None, ge=0, le=100)
    metadataVersion: str | None = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if not re.fullmatch(r"^[A-Z]{3}$", v):
            raise ValueError(
                "currency must be a valid ISO 4217 code (3 uppercase letters)"
            )
        return v

    @field_validator("maturityDate")
    @classmethod
    def maturity_after_issue(cls, v: date, info: ValidationInfo) -> date:
        issue_date = info.data.get("issueDate")
        if issue_date and v <= issue_date:
            raise ValueError("maturity must be after issueDate")
        return v

    @field_validator("couponFrequency")
    @classmethod
    def validate_coupon_frequency(cls, v: Frequency) -> Frequency:
        return v
