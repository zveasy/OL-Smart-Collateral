import os
import requests
from dotenv import load_dotenv

load_dotenv()

KALEIDO_API_URL = os.environ["KALEIDO_API_URL"]
KALEIDO_API_KEY = os.environ["KALEIDO_API_KEY"]

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
