"""Domain models for the Vending Machine API."""

from __future__ import annotations

from pydantic import BaseModel


class Product(BaseModel):
    """A product available in the vending machine catalog."""

    id: str
    name: str
    price_usd: str
    currency: str = "USDC"
    network: str = "base-sepolia"
    wallet_address: str = "0xVendingMachineWallet1234567890abcdef"


class PaymentTerms(BaseModel):
    """Payment terms returned in a 402 response."""

    price: str
    currency: str
    network: str
    wallet_address: str


class PurchaseResponse(BaseModel):
    """Successful purchase confirmation."""

    status: str = "dispensed"
    product_id: str
    product_name: str


class ErrorResponse(BaseModel):
    """Error response body."""

    error: str
    product_id: str | None = None


# Hardcoded product catalog (MVP)
PRODUCTS: dict[str, Product] = {
    "coke": Product(
        id="coke",
        name="Coke",
        price_usd="0.01",
    ),
    "water": Product(
        id="water",
        name="Water",
        price_usd="0.005",
    ),
    "juice": Product(
        id="juice",
        name="Orange Juice",
        price_usd="0.02",
    ),
}
