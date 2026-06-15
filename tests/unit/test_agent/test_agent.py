"""Tests for agent definition."""

from agent.agent import get_system_prompt
from agent.config import AgentConfig


def test_system_prompt_includes_tool_references() -> None:
    config = AgentConfig(
        vending_machine_url="http://localhost:9000",
        _env_file=None,  # type: ignore[call-arg]
    )
    prompt = get_system_prompt(config)
    assert "list_products" in prompt
    assert "get_purchase_quote" in prompt
    assert "execute_purchase" in prompt
    assert "wallet_get_balance" in prompt


def test_system_prompt_enforces_approval_flow() -> None:
    config = AgentConfig(_env_file=None)  # type: ignore[call-arg]
    prompt = get_system_prompt(config)
    assert "approval" in prompt.lower() or "approve" in prompt.lower()
    assert "audited" in prompt.lower()
