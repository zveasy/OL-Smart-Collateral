# API Reference

Base URL: `http://127.0.0.1:8000`

## Authentication and authorization

All `/carbon/*` routes require bearer authentication.

Header:

```http
Authorization: Bearer <token>
```

Role model:

- `reader`: read-only operations
- `admin`: write operations (`mint`, `retire`, `transfer`)

## Health

### `GET /health`

Returns service health status.

Response:

```json
{
  "status": "ok"
}
```

### `GET /health/live`

Liveness endpoint for runtime/process health.

### `GET /health/ready`

Readiness endpoint for dependency/config readiness.

### `GET /metrics`

Prometheus-style metrics output.

## Carbon Credit Routes

All routes are prefixed with `/carbon`.

### `POST /carbon/mint`

Mint new carbon credits.

Requires `admin` token and `Idempotency-Key` header.

Request body:

```json
{
  "to_address": "0x2810f346088b6f9638a39b869a929e6eafb73398",
  "token_id": 1,
  "amount": 1,
  "token_uri": "ipfs://olcarbon/1.json"
}
```

### `POST /carbon/retire`

Retire existing carbon credits.

Requires `admin` token and `Idempotency-Key` header.

Request body:

```json
{
  "token_id": 1,
  "amount": 1
}
```

### `GET /carbon/owner/{token_id}`

Return current owner for a token ID.

### `GET /carbon/uri/{token_id}`

Return metadata URI for a token ID.

### `GET /carbon/balance/{owner}/{token_id}`

Return ERC-1155 balance for an owner/token pair.

### `GET /carbon/tokens/{owner}`

List token IDs held by an address.

### `POST /carbon/transfer`

Transfer token units between addresses.

Requires `admin` token and `Idempotency-Key` header.

Request body:

```json
{
  "from_address": "0x2810f346088b6f9638a39b869a929e6eafb73398",
  "to_address": "0x1234567890abcdef1234567890abcdef12345678",
  "token_id": 1,
  "amount": 1
}
```
