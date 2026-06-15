"""x402 server-side payment handling logic."""

from __future__ import annotations

from vending_machine.models import PaymentTerms, Product


def get_payment_terms(product: Product) -> PaymentTerms:
    """Generate payment terms for a 402 response from a product."""
    return PaymentTerms(
        price=product.price_usd,
        currency=product.currency,
        network=product.network,
        wallet_address=product.wallet_address,
    )


def validate_payment(payment_header: str | None) -> bool:
    """Validate a payment header.

    MVP: Accept any non-empty string as valid payment.
    Phase 2: Validate cryptographic proof on-chain.
    """
    if payment_header is None:
        return False
    return len(payment_header.strip()) > 0
