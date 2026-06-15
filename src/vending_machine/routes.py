"""API endpoint handlers for the Vending Machine."""

from __future__ import annotations

from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from vending_machine.models import PRODUCTS, ErrorResponse, Product, PurchaseResponse
from vending_machine.x402 import get_payment_terms, validate_payment

router = APIRouter()


@router.get("/products")
async def list_products() -> list[Product]:
    """Return all available products from the catalog."""
    return list(PRODUCTS.values())


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return service health status."""
    return {"status": "healthy"}


@router.post("/purchase/{product_id}", response_model=None)
async def purchase(product_id: str, request: Request) -> JSONResponse | PurchaseResponse:
    """Handle purchase flow: return 402 with payment terms or dispense product."""
    # Check product exists
    product = PRODUCTS.get(product_id)
    if product is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(error="Product not found", product_id=product_id).model_dump(),
        )

    # Check for payment header
    payment_header = request.headers.get("X-PAYMENT")

    if payment_header is None:
        # No payment — return 402 with payment terms
        terms = get_payment_terms(product)
        return JSONResponse(
            status_code=402,
            content=terms.model_dump(),
            headers={"X-PAYMENT-REQUIRED": "true"},
        )

    # Validate payment
    if not validate_payment(payment_header):
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(error="Invalid payment: empty header").model_dump(),
        )

    # Payment valid — dispense product
    return PurchaseResponse(
        product_id=product.id,
        product_name=product.name,
    )
