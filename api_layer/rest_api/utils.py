import re

def is_valid_eth_address(address: str) -> bool:
    return bool(re.fullmatch(r"0x[a-fA-F0-9]{40}", address))

def is_valid_token_id(token_id) -> bool:
    if isinstance(token_id, int):
        return token_id >= 0
    elif isinstance(token_id, str):
        return len(token_id.strip()) > 0
    return False

def is_valid_uri(uri: str) -> bool:
    return uri.startswith("http://") or uri.startswith("https://")

def to_checksum(addr: str) -> str:
    """
    Convert to EIP-55 checksum, raising ValueError if invalid.
    """
    if not is_valid_eth_address(addr):
        raise ValueError(f"Invalid ethereum address: {addr}")
    return Web3.to_checksum_address(addr)
