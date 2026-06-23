# ─────────────────────────────────────────────────────────────────────────────
# FastAPI route surface for OL Carbon-Credit Platform
# ─────────────────────────────────────────────────────────────────────────────
# Every handler:
#   1) validates inputs via utils.py
#   2) calls the matching kaleido_client helper
#   3) converts lower-case eth addresses to checksum (to_checksum)
#   4) maps requests.HTTPError → HTTPException(502)
#
# NOTE: Kaleido helpers you already have / will add:
#   • mint_nft(to, id, amount, uri)
#   • retire_nft(id, amount)
#   • owner_of(id)
#   • token_uri(id)
#   • balance_of(owner, id)
#   • tokens_by_owner(owner)
#   • transfer_from(from_, to, id, amount)
# ─────────────────────────────────────────────────────────────────────────────

import logging
import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api_layer.utils import (
    is_valid_eth_address,
    to_checksum,
    is_valid_token_id,
    is_valid_uri,
)
from .auth import verify_api_key
from .kaleido_client import (
    mint_nft,
    retire_nft,
    owner_of,
    token_uri,
    balance_of,
    tokens_by_owner,
    transfer_from,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/carbon", tags=["Carbon Credits"])


# ─────────── Pydantic models ───────────
class MintRequest(BaseModel):
    to_address: str = Field(..., json_schema_extra={"example": "0x2810F346088B..."})
    token_id: int = Field(..., ge=0)
    amount: int = Field(1, ge=1)
    token_uri: str = Field(..., json_schema_extra={"example": "ipfs://olcarbon/1.json"})


class RetireRequest(BaseModel):
    token_id: int = Field(..., ge=0)
    amount: int = Field(1, ge=1)


class TransferRequest(BaseModel):
    from_address: str
    to_address: str
    token_id: int = Field(..., ge=0)
    amount: int = Field(1, ge=1)


# ─────────── Helper for consistent error mapping (no upstream leak in response) ───────────
def _wrap_kaleido(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except requests.HTTPError as exc:
        logger.warning(
            "Kaleido upstream error: status=%s body=%s",
            getattr(exc.response, "status_code", None),
            (exc.response.text if exc.response else str(exc))[:500],
        )
        raise HTTPException(502, "Upstream service temporarily unavailable")


# ─────────── Routes ───────────


@router.post("/mint", dependencies=[Depends(verify_api_key)])
def mint(req: MintRequest):
    """Mint new carbon credits (requires MINTER_ROLE on caller wallet)."""
    if not is_valid_eth_address(req.to_address):
        raise HTTPException(422, "Invalid to_address")
    if not is_valid_uri(req.token_uri):
        raise HTTPException(422, "Invalid token_uri")
    return _wrap_kaleido(
        mint_nft, to_checksum(req.to_address), req.token_id, req.amount, req.token_uri
    )


@router.post("/retire", dependencies=[Depends(verify_api_key)])
def retire(req: RetireRequest):
    """Burn (retire) existing carbon credits."""
    if not is_valid_token_id(req.token_id):
        raise HTTPException(422, "Invalid token_id")
    return _wrap_kaleido(retire_nft, req.token_id, req.amount)


@router.get("/owner/{token_id}", dependencies=[Depends(verify_api_key)])
def get_owner(token_id: int):
    """Return current owner for a given tokenId."""
    if not is_valid_token_id(token_id):
        raise HTTPException(422, "Invalid token_id")
    return _wrap_kaleido(owner_of, token_id)


@router.get("/uri/{token_id}", dependencies=[Depends(verify_api_key)])
def get_uri(token_id: int):
    """Return metadata URI for a tokenId."""
    if not is_valid_token_id(token_id):
        raise HTTPException(422, "Invalid token_id")
    return _wrap_kaleido(token_uri, token_id)


@router.get("/balance/{owner}/{token_id}", dependencies=[Depends(verify_api_key)])
def get_balance(owner: str, token_id: int):
    """ERC-1155 balanceOf wrapper."""
    if not is_valid_eth_address(owner):
        raise HTTPException(422, "Invalid owner address")
    return _wrap_kaleido(balance_of, to_checksum(owner), token_id)


@router.get("/tokens/{owner}", dependencies=[Depends(verify_api_key)])
def list_tokens(owner: str):
    """List all token IDs held by an address."""
    if not is_valid_eth_address(owner):
        raise HTTPException(422, "Invalid owner address")
    return _wrap_kaleido(tokens_by_owner, to_checksum(owner))


@router.post("/transfer", dependencies=[Depends(verify_api_key)])
def transfer(req: TransferRequest):
    """Secondary-market transfer (requires approval or operator)."""
    for addr in (req.from_address, req.to_address):
        if not is_valid_eth_address(addr):
            raise HTTPException(422, "Invalid address supplied")
    return _wrap_kaleido(
        transfer_from,
        to_checksum(req.from_address),
        to_checksum(req.to_address),
        req.token_id,
        req.amount,
    )
