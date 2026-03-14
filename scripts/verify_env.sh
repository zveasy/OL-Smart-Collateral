#!/usr/bin/env bash
set -euo pipefail

echo "==> Running Python tests"
python3 -m pytest

echo "==> Running Solidity tests"
npm run test:solidity

echo "==> Environment verification complete"
