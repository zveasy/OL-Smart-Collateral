# Blockchain Architecture

## O&L Smart Collateral Platform

---

### 1. Blockchain Platform & Node

- **Provider:** Kaleido.io
- **Network:** OL Smart Collateral (AWS us-east-2)
- **Node Name:** ol-collateral-node1
- **Consensus Engine:** Ethereum Geth v1.11.6 (Signer)
- **Node Status:** Started

---

### 2. Smart Contract Details

- **Type:** ERC-721 (Mintable, Kaleido template)
- **Template Version:** KaleidoERC721Mintable
- **Contract Factory App Name:** kaleidoerc721m
- **Deployment Date:** 2025-06-19 1:09:28 PM
- **Contract ID:** u0rvu4hepj

---

### 3. Gateway API Information

- **Base URL:**  
  `https://u0g44pplce-u0u8e12l02-connect.us0-aws.kaleido.io/gateways/kaleidoerc721m`
- **API Docs:**  
  Exposed as OpenAPI/Swagger UI at the base URL above.
- **Authentication:**  
  All API calls require Bearer token authentication via the `Authorization` header with your Kaleido app credentials.

---

### 4. Key API Endpoints & Usage

#### a. **Deploy Contract (Constructor)**
- **POST /**  
  Deploys a new ERC-721 contract instance.

  **Request Body:**
  ```json
  {
    "name": "OL Collateral Token",
    "symbol": "OLC"
  }
