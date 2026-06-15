"""Tests for vending machine API routes."""

from fastapi.testclient import TestClient

from vending_machine.app import app

client = TestClient(app)


def test_list_products_returns_all() -> None:
    response = client.get("/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 3
    ids = [p["id"] for p in products]
    assert "coke" in ids
    assert "water" in ids
    assert "juice" in ids


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_purchase_without_payment_returns_402() -> None:
    response = client.post("/purchase/coke")
    assert response.status_code == 402
    body = response.json()
    assert body["price"] == "0.01"
    assert body["currency"] == "USDC"
    assert body["network"] == "base-sepolia"
    assert response.headers.get("x-payment-required") == "true"


def test_purchase_with_payment_dispenses() -> None:
    response = client.post("/purchase/coke", headers={"X-PAYMENT": "valid-proof"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "dispensed"
    assert body["product_id"] == "coke"
    assert body["product_name"] == "Coke"


def test_purchase_unknown_product_returns_404() -> None:
    response = client.post("/purchase/unknown")
    assert response.status_code == 404
    body = response.json()
    assert body["error"] == "Product not found"
    assert body["product_id"] == "unknown"


def test_purchase_with_empty_payment_returns_400() -> None:
    response = client.post("/purchase/coke", headers={"X-PAYMENT": ""})
    assert response.status_code == 400
    body = response.json()
    assert "Invalid payment" in body["error"]
