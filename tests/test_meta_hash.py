from api_layer.crypto.meta_hash import bond_meta_hash, bond_meta_json
from api_layer.models.bond_schema import BondMetadata, Frequency

def _sample():
    return BondMetadata(
        name="O&L Green Bond 2025-1",
        issuer="Omni & Luci LLC",
        isin="US1234567890",
        currency="USD",
        faceValue="1000000.00",
        couponRate=3.75,
        couponFrequency=Frequency.SEMI_ANNUAL,
        issueDate="2025-07-15",
        maturity="2026-07-15",
        esgScore=85,
        carbonOffsetTons="250.0000",
        metadataVersion="1.0.0",
    )

def test_hash_is_stable_against_key_order():
    m = _sample()
    h1 = bond_meta_hash(m)

    # Same data, different python dict order
    d = m.model_dump(mode="json", exclude_none=True)
    re_ordered = {k: d[k] for k in reversed(list(d.keys()))}
    h2 = bond_meta_hash(re_ordered)
    assert h1 == h2

def test_canonical_json_roundtrip():
    m = _sample()
    js = bond_meta_json(m)
    assert js.count(" ") == 0  # no spaces
    assert bond_meta_hash(m).startswith("0x")
