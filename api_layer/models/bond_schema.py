from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_core import ValidationInfo


class Frequency(str, Enum):
    ANNUAL = "ANNUAL"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"


class BondMetadata(BaseModel):
    isin: str
    issuer: str
    issueDate: date
    maturity: date
    currency: str
    couponRate: float
    couponFrequency: Literal["ANNUAL", "SEMI_ANNUAL", "QUARTERLY", "MONTHLY"]
    faceValue: Decimal = Field(gt=0, examples=["1000000.00"])
    carbonOffsetTons: Decimal | None = Field(default=None, ge=0, examples=["250.0000"])

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if not re.fullmatch(r"^[A-Z]{3}$", v):
            raise ValueError("currency must be a valid ISO 4217 code (3 uppercase letters)")
        return v

    @field_validator("maturity")
    @classmethod
    def maturity_after_issue(cls, v: date, info: ValidationInfo) -> date:
        issue_date = info.data.get("issueDate")
        if issue_date and v <= issue_date:
            raise ValueError("maturity must be after issueDate")
        return v

    @field_validator("couponFrequency")
    @classmethod
    def validate_coupon_frequency(cls, v: str) -> str:
        allowed = {"ANNUAL", "SEMI_ANNUAL", "QUARTERLY", "MONTHLY"}
        if v not in allowed:
            raise ValueError(f"couponFrequency must be one of {allowed}")
        return v