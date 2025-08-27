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
        #couponFrequency="SEMI_ANNUAL",
        couponFrequency=Frequency.SEMI_ANNUAL,
        issueDate=date(2025, 7, 15),
        maturityDate=date(2026, 7, 15),
        maturity="2026-07-15", 
        esgScore=85,
        carbonOffsetTons="250.0000",
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
            maturityDate="2025-12-31",          # <<< before issueDate
            esgScore=80,
            isin="US1234567890",
        )
    assert "maturityDate" in str(exc.value)


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
            maturityDate="2026-01-01",
            esgScore=70,
        )
    assert "couponFrequency" in str(exc.value)
