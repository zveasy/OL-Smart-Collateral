# api_layer/rest_api/server.py

from fastapi import FastAPI, Body, HTTPException, status
from .kaleido_client import mint_nft
from .utils import is_valid_eth_address

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
        # Basic input validation
    if not to_address.startswith("0x") or len(to_address) != 42:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid Ethereum address format."
        )
    if not token_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Token ID cannot be empty."
        )
    if not token_uri.startswith("http"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Token URI must start with 'http'."
        )
    # Call Kaleido and handle errors
    resp = mint_nft(to_address, token_id, token_uri)
    if resp.get("error"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Kaleido error: {resp['error']}"
        )
    return resp

    """
    Mint a new ERC-721 NFT on the Kaleido blockchain.

    - **to_address**: Recipient Ethereum address
    - **token_id**: Unique token/NFT ID
    - **token_uri**: URI with metadata JSON
    """
    result = mint_nft(to_address, token_id, token_uri)

@app.get("/ownerOf/{token_id}")
def get_owner(token_id: str):
    """
    Query the owner of a specific tokenId.
    """
    if not token_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Token ID cannot be empty."
        )
    resp = owner_of(token_id)
    if resp.get("error"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kaleido error: {resp['error']}"
        )
    return resp

@app.get("/tokenURI/{token_id}")
def get_token_uri(token_id: str):
    """Get the metadata URI for a specific tokenId."""
    if not token_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Token ID is required."
        )
    resp = token_uri(token_id)
    if resp.get("error"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kaleido error: {resp['error']}"
        )
    return resp

@app.get("/tokensByOwner/{owner_address}")
def get_tokens_by_owner(owner_address: str):
    """
    List all tokens owned by a specific address.
    """
    if not owner_address or not owner_address.startswith("0x") or len(owner_address) != 42:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid Ethereum address format."
        )
    resp = tokens_by_owner(owner_address)
    if resp.get("error"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kaleido error: {resp['error']}"
        )
    return resp

@app.post("/transferFrom")
def transfer_asset(
    from_address: str = Body(..., embed=True),
    to_address: str = Body(..., embed=True),
    token_id: str = Body(..., embed=True)
):
    """
    Transfer an NFT from one address to another.
    """
    return transfer_from(from_address, to_address, token_id)


   ## return result
