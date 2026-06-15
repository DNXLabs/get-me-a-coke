# Business Logic Model: Vending Machine API

## Overview

The vending machine implements a stateless x402 payment-gated API. Every purchase request follows a two-step flow: first request gets payment terms (402), second request with payment proof gets the product.

## Core Business Flow

```
Client Request
      |
      v
+--[Has X-PAYMENT header?]--+
|                            |
No                          Yes
|                            |
v                            v
Return 402 with         Validate payment
payment terms           (MVP: non-empty = valid)
                             |
                        +----+----+
                        |         |
                      Valid    Invalid
                        |         |
                        v         v
                   Dispense    Return 400
                   product     "Invalid payment"
```

## Business Processes

### 1. Product Catalog Retrieval
- **Input**: None (GET request)
- **Process**: Return all products from hardcoded catalog
- **Output**: List of Product objects with id, name, price, currency, network, wallet_address
- **Business Rule**: Catalog is static (no CRUD operations)

### 2. Purchase Flow
- **Input**: product_id (path param), optional X-PAYMENT header
- **Process**:
  1. Validate product_id exists in catalog → 404 if not found
  2. Check for X-PAYMENT header
  3. If no header → return 402 with payment terms for that product
  4. If header present → validate payment (MVP: any non-empty string is valid)
  5. If valid → return dispensed confirmation
- **Output**: Either PaymentTerms (402) or PurchaseResponse (200)
- **Business Rules**:
  - Product must exist in catalog
  - Payment header must be present AND non-empty
  - Each purchase is independent (no state, no inventory tracking)

### 3. Health Check
- **Input**: None (GET request)
- **Process**: Return service status
- **Output**: `{"status": "healthy"}`
- **Business Rule**: Always returns healthy (no dependencies to check)

## State Management

**None** — the vending machine is completely stateless:
- No database
- No session tracking
- No inventory management
- No purchase history
- Product catalog is hardcoded in code

## Error Scenarios

| Scenario | HTTP Status | Response |
|----------|-------------|----------|
| Unknown product_id | 404 | `{"error": "Product not found", "product_id": "..."}` |
| No payment header | 402 | PaymentTerms JSON + X-PAYMENT-REQUIRED header |
| Empty payment header | 400 | `{"error": "Invalid payment: empty header"}` |
| Valid payment | 200 | PurchaseResponse JSON |
| Invalid HTTP method | 405 | FastAPI default |
