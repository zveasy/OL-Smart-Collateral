# api_layer/crypto/meta_hash.py
from __future__ import annotations
import json
from typing import Any, Mapping
from pydantic import BaseModel

try:
    from eth_utils import keccak, to_hex
except ImportError:
    from Crypto.Hash import keccak as crypto_keccak

    def keccak(*, text: str) -> bytes:
        digest = crypto_keccak.new(digest_bits=256)
        digest.update(text.encode("utf-8"))
        return digest.digest()

    def to_hex(value: bytes) -> str:
        return "0x" + value.hex()


def _canonicalize(obj: Any) -> Any:
    """
    Sort dict keys recursively and leave scalar values as-is.
    Lists keep order. This ensures stable JSON before hashing.
    """
    if isinstance(obj, Mapping):
        # sort keys for deterministic output
        return {k: _canonicalize(obj[k]) for k in sorted(obj)}
    if isinstance(obj, list):
        return [_canonicalize(x) for x in obj]
    return obj


def bond_meta_hash(meta: BaseModel | dict) -> str:
    """
    Returns 0x-prefixed keccak256(meta_json) as hex.
    IMPORTANT: The JSON you upload to IPFS/HTTP must be byte-for-byte
    identical to what we hash here (same ordering & decimals).
    """
    if isinstance(meta, BaseModel):
        # mode="json" applies your Pydantic field_serializers (e.g., Decimals→str)
        data = meta.model_dump(mode="json", exclude_none=True)
    else:
        data = meta

    canon = _canonicalize(data)
    # No spaces, stable separators, Unicode preserved
    json_str = json.dumps(canon, separators=(",", ":"), ensure_ascii=False)
    return to_hex(keccak(text=json_str))


def bond_meta_json(meta: BaseModel | dict) -> str:
    """
    Canonical JSON string (the exact bytes you should upload to IPFS/HTTP).
    """
    if isinstance(meta, BaseModel):
        data = meta.model_dump(mode="json", exclude_none=True)
    else:
        data = meta
    canon = _canonicalize(data)
    return json.dumps(canon, separators=(",", ":"), ensure_ascii=False)
