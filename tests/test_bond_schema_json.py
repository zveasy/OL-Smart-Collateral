import json
from pathlib import Path

import pytest
import jsonschema

SCHEMA_PATH = Path("schemas/bond_metadata.schema.json")
GOOD_JSON   = Path("tests/fixtures/bond_ok.json")

@pytest.fixture(scope="module")
def bond_schema():
    return json.loads(SCHEMA_PATH.read_text())

def test_bond_sample_validates(bond_schema):
    sample = json.loads(GOOD_JSON.read_text())
    jsonschema.validate(instance=sample, schema=bond_schema)  # no exception

def test_bond_bad_currency(bond_schema):
    sample = json.loads(GOOD_JSON.read_text())
    sample["currency"] = "USDX"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=sample, schema=bond_schema)

def test_bond_missing_isin(bond_schema):
    sample = json.loads(GOOD_JSON.read_text())
    sample.pop("isin")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=sample, schema=bond_schema)
