# O&L Smart Collateral Platform!

This project powers the digital collateral engine for Omni & Luci, enabling tokenization and valuation of infrastructure-backed, ESG-aligned assets including:

- Carbon credits
- Renewable infrastructure
- Green bonds

## Key Modules

- `tokenization_engine/` – Converts real assets into blockchain tokens (ERC-721 / ERC-1155).
- `blockchain_integration/` – Smart contracts for ownership, locking, and transfers.
- `collateral_valuation/` – Valuation models for yield, ESG impact, and carbon credits.
- `api_layer/` – REST and gRPC services to connect with frontends and banks.
- `security_compliance/` – Compliance automation and encryption.

## Stack (proposed)

- **Backend**: Node.js or Python (FastAPI)
- **Smart Contracts**: Solidity (Ethereum / Polygon)
- **DevOps**: Docker, GitHub Actions, AWS

## Getting Started

1. Clone the repo
2. Install dependencies
3. Start building 🚀

---

## Run the API Locally

1. Copy environment template and set values:
   ```bash
   cp .env.example .env
   # Edit .env with your Kaleido URL, API key, contract address, and admin address.
   ```
2. Activate your virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the server:
   ```bash
   uvicorn api_layer.rest_api.server:app --reload
   ```

The API will be available at http://127.0.0.1:8000/

- **Health:** `GET /health` (liveness), `GET /health/ready` (readiness, checks Kaleido).
- **Docs:** http://127.0.0.1:8000/docs (disabled when `ENVIRONMENT=production` or `DOCS_ENABLED=false`).
- **Versioned API:** Use `/v1/carbon/...` for the stable versioned API; `/carbon/...` is supported for backward compatibility.

### Optional: REST API key

If you set `API_KEY` in `.env`, all carbon routes (`/v1/carbon/*` and `/carbon/*`) require authentication via:

- Header: `X-API-Key: <your-api-key>`, or
- Header: `Authorization: Bearer <your-api-key>`

If `API_KEY` is not set, routes are open (suitable for local dev only).

## 🧪 Example Requests

### Mint a New Asset

```http
POST /carbon/mint
Content-Type: application/json
X-API-Key: your-api-key

{
  "to_address": "0x1234567890abcdef1234567890abcdef12345678",
  "token_id": 1,
  "amount": 1,
  "token_uri": "https://your-metadata-uri.com/asset1.json"
}
```

## License

MIT
