"""Tests for vending machine domain models."""

from vending_machine.models import PRODUCTS, PaymentTerms, PurchaseResponse


def test_product_catalog_has_three_products() -> None:
    assert len(PRODUCTS) == 3
    assert "coke" in PRODUCTS
    assert "water" in PRODUCTS
    assert "juice" in PRODUCTS


def test_product_fields() -> None:
    coke = PRODUCTS["coke"]
    assert coke.id == "coke"
    assert coke.name == "Coke"
    assert coke.price_usd == "0.01"
    assert coke.currency == "USDC"
    assert coke.network == "base-sepolia"


def test_payment_terms_serialization() -> None:
    terms = PaymentTerms(price="0.01", currency="USDC", network="base-sepolia", wallet_address="0x123")
    data = terms.model_dump()
    assert data["price"] == "0.01"
    assert data["currency"] == "USDC"


def test_purchase_response_defaults() -> None:
    resp = PurchaseResponse(product_id="coke", product_name="Coke")
    assert resp.status == "dispensed"
