import os
import requests
import json
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

KALEIDO_API_URL = os.environ["KALEIDO_API_URL"]
KALEIDO_API_KEY = os.environ["KALEIDO_API_KEY"]
CONTRACT = Web3.to_checksum_address(os.getenv("CARBON_CONTRACT_ADDRESS"))

w3 = Web3(Web3.HTTPProvider(KALEIDO_API_URL))  

with open(os.path.join(os.path.dirname(__file__), "..", "carbon_abi.json")) as f:
    CARBON_ABI = json.load(f)

carbon = w3.eth.contract(address=CONTRACT, abi=CARBON_ABI)

HEADERS = {
    "Authorization": f"Bearer {KALEIDO_API_KEY}",
    "x-kaleido-from": os.getenv("ADMIN_ADDRESS"),   # the address that holds DEFAULT_ADMIN_ROLE
    "Content-Type": "application/json"
}

def _gw(path):            # helper to build full URL
    return f"{KALEIDO_API_URL}{path}"

def grant_role(role_hash: str, addr: str):
    resp = requests.post(
        _gw(f"/contracts/{CONTRACT}/grantRole"),
        params={"role": role_hash, "address": addr},
        headers=HEADERS | {"x-kaleido-sync": "true"},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()

# fast wrappers for mint / retire, etc…

def mint_nft(to_address, token_id, token_uri):
    payload = {
        "to": to_address,
        "tokenId": token_id,
        "tokenURI": token_uri
    }
    headers = {
        "Authorization": f"Bearer {KALEIDO_API_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.post(f"{KALEIDO_API_URL}/mint", json=payload, headers=headers)
    return resp.json()

def owner_of(token_id):
    url = f"{KALEIDO_API_URL}/ownerOf"
    payload = {"tokenId": token_id}
    headers = {"Authorization": f"Bearer {KALEIDO_API_KEY}"}
    resp = requests.post(url, json=payload, headers=headers)
    return resp.json()

def token_uri(token_id):
    url = f"{KALEIDO_API_URL}/tokenURI"
    payload = {"tokenId": token_id}
    headers = {
        "Authorization": f"Bearer {KALEIDO_API_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.post(url, json=payload, headers=headers)
    return resp.json()

def tokens_by_owner(owner_address):
    url = f"{KALEIDO_API_URL}/tokensOfOwner"
    payload = {"owner": owner_address}
    headers = {
        "Authorization": f"Bearer {KALEIDO_API_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.post(url, json=payload, headers=headers)
    return resp.json()

def transfer_from(from_address, to_address, token_id):
    url = f"{KALEIDO_API_URL}/transferFrom"
    payload = {
        "from": from_address,
        "to": to_address,
        "tokenId": token_id
    }
    headers = {
        "Authorization": f"Bearer {KALEIDO_API_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.post(url, json=payload, headers=headers)
    return resp.json()
