# Domain Entities: Vending Machine API

## Entity: Product

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | str | Unique product identifier (slug) | `"coke"` |
| `name` | str | Human-readable product name | `"Coke"` |
| `price_usd` | str | Price in USD (string for precision) | `"0.01"` |
| `currency` | str | Payment currency | `"USDC"` |
| `network` | str | Blockchain network for payment | `"base-sepolia"` |
| `wallet_address` | str | Seller wallet address | `"0x1234..."` |

## Entity: PaymentTerms

Returned in 402 response body when payment is required.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `price` | str | Amount to pay | `"0.01"` |
| `currency` | str | Payment currency | `"USDC"` |
| `network` | str | Blockchain network | `"base-sepolia"` |
| `wallet_address` | str | Where to send payment | `"0x1234..."` |

## Entity: PurchaseResponse

Returned in 200 response body on successful purchase.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `status` | str | Always "dispensed" | `"dispensed"` |
| `product_id` | str | ID of purchased product | `"coke"` |
| `product_name` | str | Name of purchased product | `"Coke"` |

## Entity: ErrorResponse

Returned for error conditions.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `error` | str | Error description | `"Product not found"` |
| `product_id` | str (optional) | Related product ID if applicable | `"unknown"` |

## Product Catalog (Hardcoded)

```python
PRODUCTS = {
    "coke": Product(
        id="coke",
        name="Coke",
        price_usd="0.01",
        currency="USDC",
        network="base-sepolia",
        wallet_address="0xVendingMachineWallet1234567890abcdef",
    ),
    "water": Product(
        id="water",
        name="Water",
        price_usd="0.005",
        currency="USDC",
        network="base-sepolia",
        wallet_address="0xVendingMachineWallet1234567890abcdef",
    ),
    "juice": Product(
        id="juice",
        name="Orange Juice",
        price_usd="0.02",
        currency="USDC",
        network="base-sepolia",
        wallet_address="0xVendingMachineWallet1234567890abcdef",
    ),
}
```

## Entity Relationships

```
Product (catalog) --[generates]--> PaymentTerms (402 response)
Product (catalog) --[referenced by]--> PurchaseResponse (200 response)
```

No complex relationships — entities are simple value objects with no persistence or lifecycle.
