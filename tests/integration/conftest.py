"""Integration test fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from vending_machine.app import app


@pytest.fixture
def vending_machine_client() -> TestClient:
    """Provide a TestClient for the vending machine API."""
    return TestClient(app)
