# api_layer/rest_api/server.py

from fastapi import FastAPI, Body
from .kaleido_client import mint_nft

app = FastAPI(
    title="O&L Smart Collateral API",
    description="API for tokenizing and managing infrastructure assets via Kaleido ERC-721",
    version="0.1.0"
)

@app.post("/mint")
def mint_asset(
    to_address: str = Body(..., embed=True, description="Ethereum address to receive the NFT"),
    token_id: str = Body(..., embed=True, description="Unique token ID"),
    token_uri: str = Body(..., embed=True, description="Metadata URI for the NFT")
):
    """
    Mint a new ERC-721 NFT on the Kaleido blockchain.

    - **to_address**: Recipient Ethereum address
    - **token_id**: Unique token/NFT ID
    - **token_uri**: URI with metadata JSON
    """
    result = mint_nft(to_address, token_id, token_uri)
    return result
