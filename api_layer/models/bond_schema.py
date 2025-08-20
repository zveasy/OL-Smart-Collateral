from pydantic import BaseModel, validator, Field
from typing import Literal
from datetime import date
import re
from decimal import Decimal
from enum import Enum

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
    couponFrequency: Literal['ANNUAL', 'SEMI_ANNUAL', 'QUARTERLY', 'MONTHLY']
    faceValue: Decimal = Field(
        gt=0,
        max_digits=18,        # ← new line
        decimal_places=2,
        examples=["1000000.00"],
    )

    carbonOffsetTons: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=18,        # ← new line
        decimal_places=4,
        examples=["250.0000"],
    )

    @validator('currency')
    def validate_currency(cls, v):
        # ISO 4217 currency code: 3 uppercase letters
        if not re.fullmatch(r'^[A-Z]{3}$', v):
            raise ValueError('currency must be a valid ISO 4217 code (3 uppercase letters)')
        return v

    @validator('maturity')
    def maturity_after_issue(cls, v, values):
        issue_date = values.get('issueDate')
        if issue_date and v <= issue_date:
            raise ValueError('maturity must be after issueDate')
        return v

    @validator('couponFrequency')
    def validate_coupon_frequency(cls, v):
        allowed = {'ANNUAL', 'SEMI_ANNUAL', 'QUARTERLY', 'MONTHLY'}
        if v not in allowed:
            raise ValueError(f'couponFrequency must be one of {allowed}')