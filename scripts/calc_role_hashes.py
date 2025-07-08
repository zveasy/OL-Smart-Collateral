# scripts/calc_role_hashes.py
from eth_utils import keccak, to_hex

roles = ["ADMIN_ROLE", "MINTER_ROLE", "BURNER_ROLE"]
for r in roles:
    print(f"{r} = {to_hex(keccak(text=r))}")
