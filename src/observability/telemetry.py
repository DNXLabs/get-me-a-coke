"""Telemetry configuration — OpenInference + OTLP export to Grafana, with optional Sigil AI observability."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

if TYPE_CHECKING:
    from agent.config import AgentConfig

logger = logging.getLogger(__name__)

_configured = False
_sigil_client: object | None = None  # Optional[SigilClient] — typed as object to avoid import at module level


def get_sigil_client() -> object | None:
    """Return the Sigil client instance, or None if not initialized."""
    return _sigil_client


def shutdown_telemetry() -> None:
    """Flush and shut down all telemetry: TracerProvider, MeterProvider, and Sigil client."""
    global _sigil_client, _configured  # noqa: PLW0603

    # Shutdown TracerProvider (flushes buffered spans)
    provider = trace.get_tracer_provider()
    if hasattr(provider, "shutdown"):
        try:
            provider.shutdown()
        except Exception as e:
            logger.warning("TracerProvider shutdown failed: %s", e)

    # Shutdown Sigil client
    if _sigil_client is not None:
        try:
            _sigil_client.shutdown()
        except Exception as e:
            logger.warning("Sigil shutdown failed: %s", e)
        _sigil_client = None

    _configured = False


def shutdown_sigil() -> None:
    """Flush and shut down the Sigil client if initialized.

    Deprecated: use shutdown_telemetry() for complete cleanup.
    """
    shutdown_telemetry()


def _initialize_sigil_client(config: AgentConfig) -> None:
    """Initialize the Sigil client from AgentConfig if credentials are complete.

    Must be called AFTER TracerProvider and MeterProvider are set globally,
    since the Sigil SDK emits internal OTel spans and metrics.

    Handles:
    - Partial credentials (some present but not all) → WARNING log, skip
    - ImportError (sigil-sdk not installed) → WARNING log, skip
    - Client construction failure → ERROR log, skip
    """
    global _sigil_client  # noqa: PLW0603

    # Determine which credentials are present
    creds = {
        "sigil_endpoint": bool(config.sigil_endpoint.strip()),
        "sigil_auth_tenant_id": bool(config.sigil_auth_tenant_id.strip()),
        "sigil_auth_token": bool(config.sigil_auth_token.strip()),
    }
    present = [k for k, v in creds.items() if v]
    missing = [k for k, v in creds.items() if not v]

    # No credentials at all — silently skip
    if not present:
        return

    # Partial credentials — warn and skip
    if missing:
        logger.warning(
            "Partial Sigil credentials detected. Present: %s. Missing: %s. "
            "Sigil instrumentation disabled.",
            present,
            missing,
        )
        return

    # All credentials present — attempt initialization
    try:
        from sigil_sdk import Client as SigilClient
        from sigil_sdk import ClientConfig
        from sigil_sdk.config import AuthConfig, GenerationExportConfig
    except ImportError:
        logger.warning(
            "sigil-sdk package not installed. Install sigil-sdk>=0.1.2 to enable "
            "Sigil AI observability. Continuing without Sigil instrumentation."
        )
        return

    try:
        auth_kwargs = {"mode": config.sigil_auth_mode, "tenant_id": config.sigil_auth_tenant_id}
        if config.sigil_auth_mode == "basic":
            auth_kwargs["basic_password"] = config.sigil_auth_token
        else:
            auth_kwargs["bearer_token"] = config.sigil_auth_token
        auth_config = AuthConfig(**auth_kwargs)
        client_config = ClientConfig(
            generation_export=GenerationExportConfig(
                endpoint=config.sigil_endpoint,
                protocol=config.sigil_protocol,
                auth=auth_config,
            ),
        )
        _sigil_client = SigilClient(config=client_config)
        logger.info("Sigil client initialized: endpoint=%s", config.sigil_endpoint)
    except Exception as e:
        logger.error("Failed to initialize Sigil client: %s", e)
        _sigil_client = None


def configure_telemetry(
    grafana_otlp_endpoint: str = "",
    grafana_instance_id: str = "",
    grafana_api_token: str = "",
    service_name: str = "get-me-a-coke-agent",
    config: AgentConfig | None = None,
) -> None:
    """Initialize OpenTelemetry and Sigil instrumentation based on available configuration.

    Handles four coexistence scenarios:
    1. Both OpenInference + Sigil configured: Full OTel pipeline (OpenInference processor +
       BatchSpanProcessor for OTLP export) + Sigil client for AI observability.
    2. Only OpenInference configured (no Sigil): OTel pipeline with OpenInference + OTLP export.
       No Sigil client instantiated.
    3. Only Sigil configured (no OTLP export): TracerProvider + MeterProvider set up (without
       OpenInference processor or OTLP BatchSpanProcessor) so Sigil can emit internal
       spans/metrics. Sigil client initialized.
    4. Neither configured: Skip telemetry entirely, log warning.

    Supports two OTLP configuration modes:
    1. Standard OTEL env vars (OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_EXPORTER_OTLP_HEADERS)
    2. Explicit Grafana params (grafana_otlp_endpoint, grafana_instance_id, grafana_api_token)

    Must be called BEFORE creating the Strands agent so the global TracerProvider
    is set when Strands emits its native spans.
    """
    global _configured  # noqa: PLW0603

    if _configured:
        logger.debug("Telemetry already configured, skipping.")
        return

    # If config is provided, extract Grafana params from it (backward-compatible)
    if config is not None and not grafana_otlp_endpoint:
        grafana_otlp_endpoint = config.grafana_otlp_endpoint
        grafana_instance_id = config.grafana_instance_id
        grafana_api_token = config.grafana_api_token

    # Check if OTEL standard env vars are set (preferred)
    otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    otel_headers = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")

    has_otel_env = bool(otel_endpoint and otel_headers)
    has_explicit_config = bool(grafana_otlp_endpoint and grafana_instance_id and grafana_api_token)
    has_otlp = has_otel_env or has_explicit_config
    has_sigil = config is not None and config.sigil_configured

    # Scenario 4: Neither configured — skip telemetry entirely
    if not has_otlp and not has_sigil:
        logger.warning(
            "No telemetry configuration found. Set OTEL_EXPORTER_OTLP_ENDPOINT + "
            "OTEL_EXPORTER_OTLP_HEADERS, or GRAFANA_OTLP_ENDPOINT + GRAFANA_INSTANCE_ID + "
            "GRAFANA_API_TOKEN for OpenInference export, or SIGIL_ENDPOINT + "
            "SIGIL_AUTH_TENANT_ID + SIGIL_AUTH_TOKEN for Sigil AI observability. "
            "Telemetry disabled."
        )
        # Still attempt Sigil init for partial credentials warning
        if config is not None:
            _initialize_sigil_client(config)
        return

    # Set service name via OTEL env var (ensures all signals use it)
    os.environ.setdefault("OTEL_SERVICE_NAME", service_name)

    # Enable latest GenAI semantic conventions for richer span content
    existing_opt_in = os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN", "")
    required_opts = {"gen_ai_latest_experimental", "gen_ai_tool_definitions", "gen_ai_use_latest_invocation_tokens"}
    current_opts = {o.strip() for o in existing_opt_in.split(",") if o.strip()}
    missing_opts = required_opts - current_opts
    if missing_opts:
        combined = ",".join(sorted(current_opts | required_opts))
        os.environ["OTEL_SEMCONV_STABILITY_OPT_IN"] = combined

    # Resource with service metadata
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "0.1.0",
        "deployment.environment": "dev",
        "ai.model.id": "nvidia.nemotron-nano-3-30b",
        "ai.model.provider": "aws.bedrock",
    })

    # Create TracerProvider with resource
    provider = TracerProvider(resource=resource)

    if has_otlp:
        # Scenarios 1 & 2: OTLP export configured — add OpenInference + BatchSpanProcessor
        try:
            from openinference.instrumentation.strands_agents import StrandsAgentsToOpenInferenceProcessor
        except ImportError:
            logger.warning(
                "openinference-instrumentation-strands-agents not installed. "
                "OpenInference span transformation disabled."
            )
        else:
            # Req 7.1: OpenInference processor added BEFORE BatchSpanProcessor
            provider.add_span_processor(StrandsAgentsToOpenInferenceProcessor())

        # Export transformed spans to Grafana Tempo via OTLP
        if has_otel_env:
            otlp_exporter = OTLPSpanExporter()
        else:
            from observability.exporters import build_grafana_auth_headers, build_otlp_endpoint

            headers = build_grafana_auth_headers(grafana_instance_id, grafana_api_token)
            traces_endpoint = build_otlp_endpoint(grafana_otlp_endpoint, "traces")
            otlp_exporter = OTLPSpanExporter(endpoint=traces_endpoint, headers=headers)

        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set TracerProvider as global — needed for both OTLP and Sigil scenarios
    trace.set_tracer_provider(provider)

    if has_otlp:
        # Configure logging export to Grafana (structured logs)
        _configure_logging(has_otel_env, grafana_otlp_endpoint, grafana_instance_id, grafana_api_token, resource)

    # Configure metrics — needed for both OTLP export and Sigil (Sigil emits internal metrics)
    has_otel_for_metrics = has_otel_env if has_otlp else False
    _configure_metrics(
        has_otel_for_metrics, grafana_otlp_endpoint, grafana_instance_id, grafana_api_token, resource
    )

    # Instrument httpx for trace context propagation on outbound HTTP calls
    _instrument_httpx()

    # Initialize Sigil client AFTER TracerProvider and MeterProvider are set
    if config is not None:
        _initialize_sigil_client(config)

    _configured = True

    if has_otlp and has_sigil:
        logger.info(
            "Telemetry configured: service=%s, exporting traces + logs + metrics via OTLP "
            "AND Sigil AI observability active",
            service_name,
        )
    elif has_otlp:
        logger.info(
            "Telemetry configured: service=%s, exporting traces + logs + metrics via OTLP",
            service_name,
        )
    else:
        logger.info(
            "Telemetry configured: service=%s, Sigil AI observability active (no OTLP export)",
            service_name,
        )


def _instrument_httpx() -> None:
    """Instrument httpx to propagate trace context on outbound HTTP calls.

    This ensures the agent's trace_id is sent via W3C traceparent header
    to downstream services (wallet, vending machine), creating distributed traces.
    """
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
        logger.debug("httpx instrumentation active — outbound calls will propagate trace context.")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-httpx not installed, skipping client instrumentation.")
    except Exception as e:
        logger.debug("Failed to instrument httpx: %s", e)


def _configure_logging(
    has_otel_env: bool,
    grafana_otlp_endpoint: str,
    grafana_instance_id: str,
    grafana_api_token: str,
    resource: Resource,
) -> None:
    """Configure OpenTelemetry log export to Grafana Loki."""
    try:
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

        logger_provider = LoggerProvider(resource=resource)

        if has_otel_env:
            log_exporter = OTLPLogExporter()
        else:
            from observability.exporters import build_grafana_auth_headers, build_otlp_endpoint

            headers = build_grafana_auth_headers(grafana_instance_id, grafana_api_token)
            logs_endpoint = build_otlp_endpoint(grafana_otlp_endpoint, "logs")
            log_exporter = OTLPLogExporter(endpoint=logs_endpoint, headers=headers)

        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        set_logger_provider(logger_provider)

        # Attach OTel handler to root logger so all Python logs get exported
        handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
        logging.getLogger().addHandler(handler)

    except ImportError:
        logger.debug("OTel log exporter not available, skipping log export.")
    except Exception as e:
        logger.debug("Failed to configure log export: %s", e)



def _configure_metrics(
    has_otel_env: bool,
    grafana_otlp_endpoint: str,
    grafana_instance_id: str,
    grafana_api_token: str,
    resource: Resource,
) -> None:
    """Configure OpenTelemetry metrics export.

    When OTLP is configured, exports to Grafana Mimir.
    When only Sigil is configured (no OTLP), sets up a basic MeterProvider
    so Sigil can emit internal metrics without export.
    """
    try:
        from opentelemetry import metrics
        from opentelemetry.sdk.metrics import MeterProvider

        if has_otel_env or (grafana_otlp_endpoint and grafana_instance_id and grafana_api_token):
            # OTLP export configured — set up periodic metric export
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

            if has_otel_env:
                metric_exporter = OTLPMetricExporter()
            else:
                from observability.exporters import build_grafana_auth_headers, build_otlp_endpoint

                headers = build_grafana_auth_headers(grafana_instance_id, grafana_api_token)
                metrics_endpoint = build_otlp_endpoint(grafana_otlp_endpoint, "metrics")
                metric_exporter = OTLPMetricExporter(endpoint=metrics_endpoint, headers=headers)

            reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=30000)
            meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        else:
            # Sigil-only scenario — basic MeterProvider without OTLP export
            # Sigil SDK emits internal metrics that need a MeterProvider set
            meter_provider = MeterProvider(resource=resource)

        metrics.set_meter_provider(meter_provider)

    except ImportError:
        logger.debug("OTel metric exporter not available, skipping metrics export.")
    except Exception as e:
        logger.debug("Failed to configure metrics export: %s", e)
