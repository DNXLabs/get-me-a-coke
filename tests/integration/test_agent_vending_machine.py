"""Integration tests: Agent interacts with local vending machine.

These tests verify the end-to-end flow with real Bedrock (Nemotron Nano)
but mocked AgentCore Payments. They require AWS credentials and network access.

Run with: pytest tests/integration/ -m integration
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient  # noqa: TCH002


@pytest.mark.integration
def test_vending_machine_catalog_accessible(vending_machine_client: TestClient) -> None:
    """Verify the vending machine catalog is accessible for the agent."""
    response = vending_machine_client.get("/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) >= 1
    assert all("id" in p and "price_usd" in p for p in products)


@pytest.mark.integration
def test_vending_machine_402_flow(vending_machine_client: TestClient) -> None:
    """Verify the full 402 → pay → dispense flow works."""
    # Step 1: Attempt purchase without payment
    response = vending_machine_client.post("/purchase/coke")
    assert response.status_code == 402
    terms = response.json()
    assert "price" in terms
    assert "wallet_address" in terms

    # Step 2: Retry with payment proof
    response = vending_machine_client.post(
        "/purchase/coke",
        headers={"X-PAYMENT": "mock-payment-proof-from-agentcore"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "dispensed"


# NOTE: Full agent integration test (agent calls real Bedrock + local vending machine)
# requires AWS credentials and is expensive to run. Uncomment when ready:
#
# @pytest.mark.integration
# @pytest.mark.slow
# def test_agent_autonomous_purchase() -> None:
#     """Full end-to-end: agent discovers, selects, and purchases from local vending machine."""
#     from agent.config import AgentConfig
#     from agent.agent import create_agent
#
#     config = AgentConfig(
#         vending_machine_url="http://testserver",  # TestClient URL
#         _env_file=None,
#     )
#     agent = create_agent(config)
#     result = agent("Buy me a coke from http://testserver")
#     assert "coke" in str(result).lower() or "dispensed" in str(result).lower()
