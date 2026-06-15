"""Tests for observability telemetry configuration."""


from observability.exporters import build_grafana_auth_headers, build_otlp_endpoint


def test_build_grafana_auth_headers() -> None:
    headers = build_grafana_auth_headers("12345", "my-token")
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Basic ")
    # Decode and verify
    import base64
    decoded = base64.b64decode(headers["Authorization"].split(" ")[1]).decode()
    assert decoded == "12345:my-token"


def test_build_otlp_endpoint_traces() -> None:
    endpoint = build_otlp_endpoint("https://stack.grafana.net/otlp", "traces")
    assert endpoint == "https://stack.grafana.net/otlp/v1/traces"


def test_build_otlp_endpoint_metrics() -> None:
    endpoint = build_otlp_endpoint("https://stack.grafana.net/otlp", "metrics")
    assert endpoint == "https://stack.grafana.net/otlp/v1/metrics"


def test_build_otlp_endpoint_strips_trailing_slash() -> None:
    endpoint = build_otlp_endpoint("https://stack.grafana.net/otlp/", "traces")
    assert endpoint == "https://stack.grafana.net/otlp/v1/traces"


def test_configure_telemetry_skips_when_no_credentials() -> None:
    """Telemetry should not crash when credentials are missing."""
    import observability.telemetry as tel
    # Reset state
    tel._configured = False
    # Call with empty credentials — should log warning and return
    tel.configure_telemetry("", "", "")
    # Should not have set _configured to True
    assert tel._configured is False
