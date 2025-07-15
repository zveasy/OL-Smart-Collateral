#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────
# Smoke-mint for OL Carbon API (production/CI ready)
#
# 1. Mints 1 test credit (tokenId=999999) to TEST_ADDR
# 2. Reads ownerOf back
# 3. Retires the credit
#
# Usage:
#   ./scripts/smoke_mint.sh
#   API_BASE="https://staging.api.omniluci.com" TEST_ADDR="0xYourStagingWallet..." ./scripts/smoke_mint.sh
#
# Exit code != 0  → pipeline fails
# ────────────────────────────────────────────────────────────────

set -euo pipefail

API_BASE=${API_BASE:-"http://127.0.0.1:8000"}   # override in CI/staging
TEST_ADDR=${TEST_ADDR:-"0x2810F346088B6F9638a39B869A929E6eAFb73398"}
TOKEN_ID=${TOKEN_ID:-999999}
TOKEN_URI=${TOKEN_URI:-"ipfs://olcarbon/test.json"}

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required for this script. Please install jq." >&2
  exit 2
fi

_color() { printf "\033[1;32m%s\033[0m\n" "$*"; }

_json() { jq -r "$1"; }  # helper: extract field with jq

_color "→ Minting 1 test credit …"
mint_resp=$(\
  curl -sS -X POST "$API_BASE/carbon/mint" \
       -H "Content-Type: application/json" \
       -d '{"to_address":"'"$TEST_ADDR"'","token_id":'"$TOKEN_ID"',"amount":1,"token_uri":"'"$TOKEN_URI"'"}'
)

status=$(_json '.status' <<<"$mint_resp")
[[ "$status" == "success" ]] || { echo "Mint failed: $mint_resp"; exit 1; }
tx_hash=$(_json '.tx.transactionHash // .tx' <<<"$mint_resp")
_color "✓ Mint tx $tx_hash"

_color "→ Verifying ownerOf …"
owner_resp=$(curl -sS "$API_BASE/carbon/owner/$TOKEN_ID")
owner=$(_json '.owner // .result' <<<"$owner_resp")
[[ "${owner,,}" == "${TEST_ADDR,,}" ]] || { echo "Owner mismatch: $owner_resp"; exit 1; }
_color "✓ ownerOf ok"

_color "→ Retiring the credit …"
retire_resp=$(\
  curl -sS -X POST "$API_BASE/carbon/retire" \
       -H "Content-Type: application/json" \
       -d '{"token_id":'"$TOKEN_ID"',"amount":1}'
)
ret_status=$(_json '.status' <<<"$retire_resp")
[[ "$ret_status" == "success" ]] || { echo "Retire failed: $retire_resp"; exit 1; }
_color "✓ Retire tx succeeded"

echo "SMOKE MINT TEST PASSED ✅"
