# Business Rules: Vending Machine API

## Payment Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| PAY-001 | A purchase request without X-PAYMENT header MUST return HTTP 402 | Route handler checks header presence |
| PAY-002 | A purchase request with empty X-PAYMENT header MUST return HTTP 400 | Validation after header extraction |
| PAY-003 | A purchase request with any non-empty X-PAYMENT header MUST be accepted as valid payment (MVP) | `validate_payment()` returns True for any non-empty string |
| PAY-004 | The 402 response MUST include payment terms specific to the requested product | `get_payment_terms(product)` generates terms from product data |
| PAY-005 | The 402 response MUST include `X-PAYMENT-REQUIRED: true` response header | Set in JSONResponse headers |

## Catalog Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| CAT-001 | Product catalog is static and hardcoded (2-3 products) | Python dict constant |
| CAT-002 | All products share the same wallet address | Single wallet in config |
| CAT-003 | All products use USDC on base-sepolia network | Hardcoded in product definitions |
| CAT-004 | Product IDs are lowercase slugs (e.g., "coke", "water", "juice") | Dict keys |

## Validation Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| VAL-001 | Product ID must exist in catalog, otherwise return 404 | Lookup in PRODUCTS dict |
| VAL-002 | Only POST method accepted for /purchase/{product_id} | FastAPI route decorator |
| VAL-003 | GET /products always succeeds (no auth, no params) | No validation needed |

## Response Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| RES-001 | Successful purchase returns HTTP 200 with status="dispensed" | Route handler return |
| RES-002 | 402 response body contains: price, currency, network, wallet_address | PaymentTerms model |
| RES-003 | 404 response body contains: error message and product_id | ErrorResponse model |
| RES-004 | All responses are JSON (Content-Type: application/json) | FastAPI default |

## Phase 2 Rules (NOT implemented in MVP)

| Rule ID | Rule | Status |
|---------|------|--------|
| PAY-P2-001 | Validate payment cryptographic proof on-chain | Deferred to Phase 2 |
| PAY-P2-002 | Track payment transaction IDs | Deferred to Phase 2 |
| CAT-P2-001 | Dynamic product catalog from configuration | Deferred to Phase 2 |
| INV-P2-001 | Inventory tracking and stock management | Deferred to Phase 2 |
