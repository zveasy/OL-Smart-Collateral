

from __future__ import annotations

import os
import requests
from typing import Any, Dict

from dotenv import load_dotenv
##from web3 import Web3
from api_layer.utils import to_checksum

load_dotenv()

# ────────────────────────────────────────────────────────────────────
#  Environment
# ────────────────────────────────────────────────────────────────────
KALEIDO_API_URL: str = os.environ["KALEIDO_API_URL"].rstrip("/")
KALEIDO_API_KEY: str = os.environ["KALEIDO_API_KEY"]

CONTRACT_ADDR: str = to_checksum(os.environ["CARBON_CONTRACT_ADDRESS"])
ADMIN_ADDR: str = to_checksum(os.environ["ADMIN_ADDRESS"])

# ────────────────────────────────────────────────────────────────────
#  Common headers + helpers
# ────────────────────────────────────────────────────────────────────
HEADERS_BASE = {
    "Authorization": f"Bearer {KALEIDO_API_KEY}",
    "Content-Type": "application/json",
}

def _gw(path: str) -> str:
    """Build full Gateway URL for a given path (already starts with '/')."""
    return f"{KALEIDO_API_URL}{path}"

def _post_sync(path: str,
               params: Dict[str, Any] | None = None,
               json: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    POST that writes state (sync = true).
    Raises HTTPError on non-2xx; returns parsed JSON.
    """
    resp = requests.post(
        _gw(path),
        params=params,
        json=json,
        headers=HEADERS_BASE | {
            "x-kaleido-from": ADMIN_ADDR,
            "x-kaleido-sync": "true",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()

def _call(path: str,
          params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Read-only view call. Tries GET first; if Kaleido only exposes POST,
    send POST with x-kaleido-call:true.
    """
    url = _gw(path)
    try:
        resp = requests.get(url, params=params, headers=HEADERS_BASE, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except (requests.HTTPError, requests.exceptions.InvalidSchema):
        # fallback to POST read-only call
        resp = requests.post(
            url,
            params=params,
            headers=HEADERS_BASE | {"x-kaleido-call": "true"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

# ────────────────────────────────────────────────────────────────────
#  Role management
# ────────────────────────────────────────────────────────────────────
def grant_role(role_hash: str, addr: str) -> Dict[str, Any]:
    """
    Assign MINTER/BURNER/ADMIN role to an address (checksum inside).
    """
    return _post_sync(
        f"/contracts/{CONTRACT_ADDR}/grantRole",
        params={
            "role": role_hash,
            "address": to_checksum(addr),
        },
    )

# ────────────────────────────────────────────────────────────────────
#  ERC-1155 helpers
# ────────────────────────────────────────────────────────────────────
def mint_nft(to_address: str,
             token_id: int,
             amount: int,
             token_uri: str) -> Dict[str, Any]:
    """
    Mint `amount` of token_id to `to_address`.
    """
    return _post_sync(
        f"/contracts/{CONTRACT_ADDR}/mint",
        params={
            "to": to_checksum(to_address),
            "id": token_id,
            "amount": amount,
            "data": "0x",
        },
        json={"uri": token_uri},
    )

def retire_nft(token_id: int,
               amount: int) -> Dict[str, Any]:
    """
    Burn (retire) credits from msg.sender (ADMIN_ADDR).
    """
    return _post_sync(
        f"/contracts/{CONTRACT_ADDR}/burn",
        params={
            "from": ADMIN_ADDR,
            "id": token_id,
            "amount": amount,
        },
    )

def owner_of(token_id: int) -> Dict[str, Any]:
    """
    For ERC-721 style; Kaleido exposes ownerOf on wrapped 1155-721.
    """
    return _call(
        f"/contracts/{CONTRACT_ADDR}/ownerOf",
        params={"tokenId": token_id},
    )

def token_uri(token_id: int) -> Dict[str, Any]:
    return _call(
        f"/contracts/{CONTRACT_ADDR}/tokenURI",
        params={"tokenId": token_id},
    )

def balance_of(owner: str,
               token_id: int) -> Dict[str, Any]:
    return _call(
        f"/contracts/{CONTRACT_ADDR}/balanceOf",
        params={
            "account": to_checksum(owner),
            "id": token_id,
        },
    )

def tokens_by_owner(owner: str) -> Dict[str, Any]:
    """
    Convenience wrapper for tokensOfOwner (if Kaleido generated it).
    """
    return _call(
        f"/contracts/{CONTRACT_ADDR}/tokensOfOwner",
        params={"owner": to_checksum(owner)},
    )

def transfer_from(fr: str,
                  to: str,
                  token_id: int,
                  amount: int) -> Dict[str, Any]:
    """
    Secondary-market transfer (operator must have approval).
    """
    return _post_sync(
        f"/contracts/{CONTRACT_ADDR}/transferFrom",
        params={
            "from": to_checksum(fr),
            "to":   to_checksum(to),
            "id": token_id,
            "amount": amount,
            "data": "0x",
        },
    )
