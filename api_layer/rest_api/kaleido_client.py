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
