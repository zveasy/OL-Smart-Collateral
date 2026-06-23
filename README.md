# O&L Smart Collateral Platform

This project provides deterministic collateral and liquidity intelligence for
real-world assets. It evaluates ways to access capital without treating sale as
the only liquidity path.

The platform is infrastructure-only and simulation-based. It does not connect
to brokers, banks, settlement systems, trading venues, or securities issuance
systems. Recommendations are advisory.

## Key Modules

- `tokenization_engine/` – Converts real assets into blockchain tokens (ERC-721 / ERC-1155).
- `blockchain_integration/` – Smart contracts for ownership, locking, and transfers.
- `collateral_valuation/` – Valuation models for yield, ESG impact, and carbon credits.
- `api_layer/` – REST and gRPC services to connect with frontends and banks.
- `security_compliance/` – Compliance automation and encryption.
- `liquidity_intelligence/` – Asset registry, valuation, liquidity optimization,
  fractionalization, revenue streams, dynamic collateral, private order-book
  simulation, trust adapters, and append-only audit events.

## Liquidity Intelligence

Supported assets include real estate, businesses, equipment, vehicles,
accounts receivable, inventory, energy assets, intellectual property, and
future revenue streams.

The deterministic optimizer ranks secured loans, lines of credit, revenue
financing, preferred equity, fractional ownership, securitization, investor
syndication, refinancing, and hold/defer options. Ranking balances proceeds,
ownership dilution, cost of capital, control, risk, confidence, funding time,
and caller-supplied policy constraints.

State is persisted as tenant-scoped JSONL events at
`.liquidity/events.jsonl` by default. Set `LIQUIDITY_EVENT_STORE` to use a
different durable path. Audit bundles and reconstructed state are derived from
the event log.

Trust behavior is environment-sensitive:

- Development uses a deterministic local trust stub unless an adapter is
  supplied.
- Production (`ENVIRONMENT=production`) requires verified trust evidence and
  fails closed when it is missing.

See [Liquidity Intelligence Architecture](docs/liquidity_intelligence_architecture.md).

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

Liquidity endpoints also require `X-Tenant-ID` on every request. They are
available under both the stable `/v1` prefix and the unversioned compatibility
surface:

- `POST/GET /liquidity/assets`
- `POST /liquidity/analyze`
- `GET /liquidity/recommendations/{recommendation_id}`
- `GET /liquidity/explanations/{recommendation_id}`
- `GET /liquidity/audit-bundle`
- `GET /collateral/health/{asset_id}`
- `GET /collateral/borrowing-capacity/{asset_id}`
- `POST /fractionalization/create`
- `GET /fractionalization/{fraction_id}`
- `POST /auction/bids`
- `POST /auction/asks`
- `GET /auction/book/{asset_id}`
- `POST /revenue-streams`
- `GET /revenue-streams/{stream_id}`

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
