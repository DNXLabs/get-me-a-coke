"""Tests for agent configuration."""


from agent.config import AgentConfig


def test_default_config() -> None:
    config = AgentConfig(
        _env_file=None,  # type: ignore[call-arg]
    )
    assert config.vending_machine_url == "http://localhost:8000"
    assert config.bedrock_model_id == "nvidia.nemotron-nano-3-30b"
    assert config.aws_region == "ap-southeast-2"


def test_payments_configured_when_credentials_present() -> None:
    config = AgentConfig(
        payment_manager_arn="arn:aws:bedrock-agentcore:ap-southeast-2:123:payment-manager/test",
        payment_instrument_id="instr-123",
        _env_file=None,  # type: ignore[call-arg]
    )
    assert config.payments_configured is True


def test_payments_not_configured_when_empty() -> None:
    config = AgentConfig(
        payment_manager_arn="",
        payment_instrument_id="",
        _env_file=None,  # type: ignore[call-arg]
    )
    assert config.payments_configured is False


def test_observability_configured_when_all_present() -> None:
    config = AgentConfig(
        grafana_otlp_endpoint="https://stack.grafana.net/otlp",
        grafana_instance_id="12345",
        grafana_api_token="token",
        _env_file=None,  # type: ignore[call-arg]
    )
    assert config.observability_configured is True


def test_observability_not_configured_when_partial() -> None:
    config = AgentConfig(
        grafana_otlp_endpoint="https://stack.grafana.net/otlp",
        grafana_instance_id="",
        grafana_api_token="",
        _env_file=None,  # type: ignore[call-arg]
    )
    assert config.observability_configured is False
