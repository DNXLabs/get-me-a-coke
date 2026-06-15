"""Tests for x402 payment handling logic."""

from vending_machine.models import Product
from vending_machine.x402 import get_payment_terms, validate_payment


def test_get_payment_terms_from_product() -> None:
    product = Product(id="coke", name="Coke", price_usd="0.01")
    terms = get_payment_terms(product)
    assert terms.price == "0.01"
    assert terms.currency == "USDC"
    assert terms.network == "base-sepolia"
    assert terms.wallet_address == product.wallet_address


def test_validate_payment_accepts_non_empty_string() -> None:
    assert validate_payment("some-payment-proof") is True


def test_validate_payment_rejects_none() -> None:
    assert validate_payment(None) is False


def test_validate_payment_rejects_empty_string() -> None:
    assert validate_payment("") is False


def test_validate_payment_rejects_whitespace_only() -> None:
    assert validate_payment("   ") is False
