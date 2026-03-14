from datetime import date
from decimal import Decimal
from enum import Enum
import re

from pydantic import AliasChoices, BaseModel, Field, field_serializer, field_validator, model_validator

class Frequency(str, Enum):
    ANNUAL = "ANNUAL"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"


class BondMetadata(BaseModel):
    name: str = Field(min_length=1)
    isin: str
    issuer: str
    issueDate: date
    maturity: date = Field(validation_alias=AliasChoices("maturity", "maturityDate"))
    currency: str
    couponRate: float
    couponFrequency: Frequency
    faceValue: Decimal = Field(
        gt=0,
        max_digits=18,
        decimal_places=2,
        json_schema_extra={"examples": ["1000000.00"]},
    )
    esgScore: int = Field(ge=0, le=100)
    metadataVersion: str = Field(
        default="1.0.0",
        pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$",
    )
    isCallable: bool = False
    externalId: str | None = None

    carbonOffsetTons: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=18,
        decimal_places=4,
        json_schema_extra={"examples": ["250.0000"]},
    )

    @field_validator("isin")
    @classmethod
    def validate_isin(cls, value: str) -> str:
        if not re.fullmatch(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", value):
            raise ValueError("isin must be a valid ISIN code")
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        # ISO 4217 currency code: 3 uppercase letters
        if not re.fullmatch(r"^[A-Z]{3}$", value):
            raise ValueError("currency must be a valid ISO 4217 code (3 uppercase letters)")
        return value

    @field_serializer("faceValue", when_used="json")
    def serialize_face_value(self, value: Decimal) -> str:
        # Keep two decimals to match JSON schema.
        return f"{value:.2f}"

    @field_serializer("carbonOffsetTons", when_used="json")
    def serialize_carbon_offset_tons(self, value: Decimal | None) -> str | None:
        if value is None:
            return None
        return f"{value:.4f}"

    @model_validator(mode="after")
    def maturity_after_issue(self) -> "BondMetadata":
        if self.maturity <= self.issueDate:
            raise ValueError("maturity must be after issueDate")
        return self