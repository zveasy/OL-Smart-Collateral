# O&L Smart Collateral Platform

O&L Smart Collateral powers tokenization and lifecycle operations for ESG-aligned assets such as:

- Carbon credits
- Renewable infrastructure assets
- Green bonds

## Repository Overview

- `api_layer/` - FastAPI service and REST route handlers
- `contracts/` - Solidity smart contracts
- `schemas/` - JSON schemas for off-chain metadata
- `tests/` - Python tests (API, metadata models, hashing, utilities)
- `test/` - Hardhat Solidity tests
- `.github/workflows/` - CI pipelines

## Prerequisites

- Python 3.12+
- Node.js 20+
- npm 10+

## Local Setup

### 1) Python API and tests

```bash
python3 -m pip install -r requirements.txt -r requirements-dev.txt
```

Run API locally:

```bash
uvicorn api_layer.rest_api.server:app --reload
```

Run Python tests:

```bash
python3 -m pytest
```

### 2) Solidity toolchain and tests

```bash
npm ci
```

Compile contracts:

```bash
npm run compile:solidity
```

Run Solidity tests:

```bash
npm run test:solidity
```

## REST API Quick Reference

Base URL: `http://127.0.0.1:8000`

All carbon endpoints are under the `/carbon` prefix:

- `POST /carbon/mint`
- `POST /carbon/retire`
- `GET /carbon/owner/{token_id}`
- `GET /carbon/uri/{token_id}`
- `GET /carbon/balance/{owner}/{token_id}`
- `GET /carbon/tokens/{owner}`
- `POST /carbon/transfer`
- `GET /health`

See `docs/api_reference.md` for request/response details.

### Example: mint carbon credits

```http
POST /carbon/mint
Content-Type: application/json

{
  "to_address": "0x1234567890abcdef1234567890abcdef12345678",
  "token_id": 1,
  "amount": 1,
  "token_uri": "https://your-metadata-uri.com/asset1.json"
}
```

## License

MIT
