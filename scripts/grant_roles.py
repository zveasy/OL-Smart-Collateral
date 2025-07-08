# scripts/grant_roles.py
from api_layer.rest_api.kaleido_client import grant_role

BANK_NODE = "0x2810f346088b6f9638a39b869a929e6eafb73398"          # wallet that will mint/retire credits
MINTER    = "0x9f2df0fed2c77648de5860a4cc508cd0818c85b8b8a1ab4ceeef8d981c8956a6"
BURNER    = "0x3c11d16cbaffd01df69ce1c404f6340ee057498f5f00246190ea54220576a848"

grant_role(MINTER, BANK_NODE)
grant_role(BURNER, BANK_NODE)

print("Roles granted ✓")
