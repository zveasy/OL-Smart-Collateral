# tests/test_bond_model.py
import pytest
from pydantic import ValidationError
from decimal import Decimal
from datetime import date

from api_layer.models.bond_schema import BondMetadata, Frequency


# ─────────────────────────── 1. happy-path ────────────────────────────
def test_bond_metadata_happy():
    meta = BondMetadata(
        name="O&L Green Bond 2025-1",
        issuer="Omni & Luci LLC",
        isin="US1234567890",
        currency="USD",
        faceValue="1000000.00",
        couponRate=3.75,
        couponFrequency=Frequency.SEMI_ANNUAL,
        issueDate=date(2025, 7, 15),
        maturity="2026-07-15",
        esgScore=85,
        carbonOffsetTons="250.0000",
        metadataVersion="1.0.0",
    )
    assert meta.currency == "USD"
    assert meta.faceValue == Decimal("1000000.00")
    assert meta.couponFrequency.value == "SEMI_ANNUAL"


# ──────────────────────── 2. invalid ISO-currency ─────────────────────
def test_bond_metadata_bad_currency():
    with pytest.raises(ValidationError) as exc:
        BondMetadata(
            name="Bad Currency",
            issuer="O&L",
            currency="USDX",                    # <<< invalid
            faceValue="1000.00",
            couponRate=1.0,
            couponFrequency="ANNUAL",
            issueDate=date(2025, 1, 1),
            maturity=date(2026, 1, 1),
            esgScore=75,
            isin="US1234567890",
            carbonOffsetTons="250.0000",
            metadataVersion="1.0.0",
        )
    assert "currency" in str(exc.value)


# ─────────────── 3. maturity must be after issue date ────────────────
def test_bond_metadata_maturity_before_issue():
    with pytest.raises(ValidationError) as exc:
        BondMetadata(
            name="Bad dates",
            issuer="O&L",
            currency="USD",
            faceValue="1000.00",
            couponRate=100,
            couponFrequency="ANNUAL",
            issueDate="2026-01-01",
            maturity="2025-12-31",          # <<< before issueDate
            esgScore=80,
            isin="US1234567890",
            metadataVersion="1.0.0",
        )
    assert "maturity" in str(exc.value)


# ─────────────────────── 4. bad coupon frequency ─────────────────────
def test_bond_metadata_bad_coupon_freq():
    with pytest.raises(ValidationError) as exc:
        BondMetadata(
            name="Bad freq",
            issuer="O&L",
            currency="USD",
            faceValue="1000.00",
            couponRate=1.0,
            couponFrequency="MONTHLYY",         # <<< typo
            issueDate="2025-01-01",
            maturity="2026-01-01",
            esgScore=70,
            isin="US1234567890",
            metadataVersion="1.0.0",
        )
    assert "couponFrequency" in str(exc.value)


def test_bond_metadata_accepts_maturity_date_alias():
    meta = BondMetadata(
        name="Alias check",
        issuer="Omni & Luci LLC",
        isin="US1234567890",
        currency="USD",
        faceValue="1000.00",
        couponRate=2.5,
        couponFrequency="ANNUAL",
        issueDate="2025-01-01",
        maturityDate="2026-01-01",
        esgScore=90,
    )
    assert meta.maturity.isoformat() == "2026-01-01"


def test_bond_metadata_json_decimal_formatting():
    meta = BondMetadata(
        name="Format check",
        issuer="Omni & Luci LLC",
        isin="US1234567890",
        currency="USD",
        faceValue=Decimal("42"),
        couponRate=1.25,
        couponFrequency="MONTHLY",
        issueDate="2025-01-01",
        maturity="2026-01-01",
        esgScore=88,
        carbonOffsetTons=Decimal("2.5"),
    )
    payload = meta.model_dump(mode="json", exclude_none=True)
    assert payload["faceValue"] == "42.00"
    assert payload["carbonOffsetTons"] == "2.5000"
    assert payload["maturity"] == "2026-01-01"
