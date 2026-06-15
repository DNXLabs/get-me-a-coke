# Requirements Document

## Introduction

This feature adds Grafana Sigil SDK instrumentation to the existing vending machine purchasing agent. The Sigil SDK provides generation-first AI observability (conversations, cost tracking, quality views) alongside the existing OpenInference trace visualization. Both instrumentation layers coexist — OpenInference transforms Strands native OTel spans into trace-friendly format, while Sigil captures AI-specific generation data, workflow steps, and tool execution metrics for Grafana AI Observability dashboards.

## Glossary

- **Sigil_Client**: The `sigil-sdk` Python client that communicates with Grafana AI Observability. It emits OTel spans and metrics internally and requires a configured TracerProvider and MeterProvider before instantiation.
- **Sigil_Strands_Adapter**: The `sigil-sdk-strands` framework adapter that attaches to a Strands Agent as a callback handler, automatically capturing generations (LLM calls) during agent execution.
- **Generation**: A Sigil concept representing a single LLM invocation with input/output tokens, model metadata, cost, and quality signals.
- **Workflow_Step**: A Sigil concept representing a discrete step in an agentic pipeline (e.g., "list products", "process payment"), used for pipeline visualization.
- **Tool_Execution**: A Sigil concept representing the invocation of an agent tool, capturing input arguments, output, duration, and success/failure status.
- **Parent_Generation_ID**: A Sigil identifier linking child generations to a parent generation, enabling multi-agent dependency tracking and conversation threading.
- **OpenInference_Processor**: The existing `StrandsAgentsToOpenInferenceProcessor` that transforms Strands native OTel spans into OpenInference semantic format for trace visualization.
- **TracerProvider**: The OpenTelemetry SDK TracerProvider that manages span creation and export. Must be configured before Sigil_Client instantiation.
- **MeterProvider**: The OpenTelemetry SDK MeterProvider that manages metric recording and export. Must be configured before Sigil_Client instantiation.
- **Agent**: The Strands SDK Agent instance that orchestrates LLM calls and tool invocations for the vending machine purchasing workflow.

## Requirements

### Requirement 1: Sigil SDK Dependency Installation

**User Story:** As a developer, I want the Sigil SDK packages added to the project dependencies, so that the instrumentation code can import and use them.

#### Acceptance Criteria

1. THE Build_System SHALL include `sigil-sdk>=0.1.2` in the `[project].dependencies` list of pyproject.toml
2. THE Build_System SHALL include `sigil-sdk-strands>=0.1.0` in the `[project].dependencies` list of pyproject.toml
3. WHEN dependencies are installed via `uv sync`, THE Build_System SHALL complete dependency resolution with exit code 0 and produce no version-conflict errors with existing opentelemetry-sdk, opentelemetry-exporter-otlp, and openinference-instrumentation-strands-agents packages
4. WHEN dependencies are installed, THE Build_System SHALL allow `import sigil_sdk` and `import sigil_sdk_strands` to execute in the project's Python environment without ImportError

### Requirement 2: Sigil Configuration Settings

**User Story:** As a developer, I want Sigil-specific configuration loaded from environment variables, so that the SDK can authenticate and connect to Grafana AI Observability.

#### Acceptance Criteria

1. THE AgentConfig SHALL expose a `sigil_endpoint` setting sourced from the `SIGIL_ENDPOINT` environment variable with a default value of empty string ("")
2. THE AgentConfig SHALL expose a `sigil_protocol` setting sourced from the `SIGIL_PROTOCOL` environment variable with a default value of "http/protobuf" and accepted values limited to "http/protobuf" and "grpc"
3. THE AgentConfig SHALL expose a `sigil_auth_mode` setting sourced from the `SIGIL_AUTH_MODE` environment variable with a default value of "token" and accepted values limited to "token", "basic", and "tenant"
4. THE AgentConfig SHALL expose a `sigil_auth_tenant_id` setting sourced from the `SIGIL_AUTH_TENANT_ID` environment variable with a default value of empty string ("")
5. THE AgentConfig SHALL expose a `sigil_auth_token` setting sourced from the `SIGIL_AUTH_TOKEN` environment variable with a default value of empty string ("")
6. THE AgentConfig SHALL expose a `sigil_configured` property that returns true only when `sigil_endpoint`, `sigil_auth_tenant_id`, and `sigil_auth_token` all contain at least one non-whitespace character
7. IF `sigil_protocol` is set to a value other than "http/protobuf" or "grpc", THEN THE AgentConfig SHALL raise a validation error during initialization
8. IF `sigil_auth_mode` is set to a value other than "token", "basic", or "tenant", THEN THE AgentConfig SHALL raise a validation error during initialization

### Requirement 3: Sigil Client Initialization

**User Story:** As a developer, I want the Sigil client initialized after OTel providers are configured, so that Sigil can emit spans and metrics through the existing telemetry pipeline.

#### Acceptance Criteria

1. WHEN observability is configured and all Sigil credentials (`sigil_endpoint`, `sigil_protocol`, `sigil_auth_mode`, `sigil_auth_tenant_id`, and `sigil_auth_token`) are present and non-empty, THE Telemetry_Module SHALL create a Sigil_Client instance after the TracerProvider and MeterProvider are set as global providers
2. IF the `sigil-sdk` package is not installed, THEN THE Telemetry_Module SHALL log a warning at WARNING level and continue without Sigil instrumentation
3. IF Sigil_Client instantiation raises an exception, THEN THE Telemetry_Module SHALL log the exception at ERROR level and continue with OpenInference-only instrumentation without re-raising the exception
4. IF one or more Sigil credentials are missing or empty while at least one credential is present, THEN THE Telemetry_Module SHALL log a warning at WARNING level indicating which credentials are missing and skip Sigil_Client initialization
5. WHEN a Sigil_Client instance is successfully created, THE Telemetry_Module SHALL pass the configured `sigil_endpoint`, `sigil_protocol`, `sigil_auth_mode`, `sigil_auth_tenant_id`, and `sigil_auth_token` values to the Sigil_Client constructor via ClientConfig with GenerationExportConfig and AuthConfig
6. WHEN a Sigil_Client instance is successfully created, THE Telemetry_Module SHALL store the instance in a module-level variable accessible via a public function so that other modules can retrieve it to record generations, workflow steps, or tool executions
7. WHEN the application exits, THE Telemetry_Module SHALL call `shutdown()` on the Sigil_Client instance if one was created, to flush pending telemetry data

### Requirement 4: Sigil Strands Adapter Integration

**User Story:** As a developer, I want the Sigil Strands adapter attached to the agent, so that LLM generations are automatically captured without manual instrumentation of each call.

#### Acceptance Criteria

1. WHEN a Sigil_Client is available, THE Agent_Module SHALL create a Sigil_Strands_Adapter instance with the Sigil_Client, `agent_name` set to "get-me-a-coke-agent", and `conversation_title` set to a human-readable label
2. WHEN the Sigil_Strands_Adapter is created, THE Agent_Module SHALL attach it as a callback handler on the Strands Agent instance so that each LLM generation is automatically captured including input tokens, output tokens, model identifier, and latency
3. IF the `sigil-sdk-strands` package is not installed, THEN THE Agent_Module SHALL log a warning at WARNING level and create the agent without Sigil callback instrumentation
4. IF Sigil_Strands_Adapter instantiation raises an exception, THEN THE Agent_Module SHALL log the error at WARNING level and create the agent without Sigil callback instrumentation
5. THE Sigil_Strands_Adapter SHALL coexist with existing agent plugins (AgentCore Payments) and the OpenInference_Processor without interfering with their operation or altering their output

### Requirement 5: Tool Execution Instrumentation

**User Story:** As a developer, I want tool executions recorded in Sigil, so that I can see tool call duration, success/failure rates, and input/output in Grafana AI Observability.

#### Acceptance Criteria

1. WHEN a tool is invoked by the Agent, THE Sigil_Instrumentation SHALL record a tool execution with the tool name, input arguments as key-value pairs, output result, duration in milliseconds, and a boolean success status
2. IF a tool invocation raises an exception, THEN THE Sigil_Instrumentation SHALL record the tool execution as failed with the exception message, and SHALL re-raise the original exception unchanged
3. THE Sigil_Instrumentation SHALL record tool executions for all four agent tools: `list_products`, `purchase_product`, `wallet_get_balance`, and `wallet_pay`, whether captured automatically by the Sigil_Strands_Adapter or via explicit instrumentation wrapping each tool
4. THE Sigil_Instrumentation SHALL not alter the tool return values or error propagation behavior
5. IF the Sigil_Client is not available when a tool is invoked, THEN THE Sigil_Instrumentation SHALL skip recording and allow the tool to execute and return its result unmodified

### Requirement 6: Workflow Step Tracking

**User Story:** As a developer, I want workflow steps recorded in Sigil, so that I can visualize the agentic pipeline stages in Grafana AI Observability.

#### Acceptance Criteria

1. WHEN the Sigil_Strands_Adapter is attached with `capture_workflow_steps=True`, THE Sigil_Instrumentation SHALL rely on the adapter to automatically detect graph nodes and create workflow steps with proper DAG edges, without manual workflow step creation
2. IF the Sigil_Strands_Adapter does not support automatic workflow step capture, THEN THE Sigil_Instrumentation SHALL manually enqueue a workflow step for the overall conversation turn when the Agent begins processing a user request
3. IF manual workflow step creation is used, THEN WHEN a tool execution completes, THE Sigil_Instrumentation SHALL enqueue a workflow step for that tool invocation with its `parent_step_ids` referencing the conversation turn step identifier
4. THE Workflow_Step SHALL include the step_name set to the tool function name for tool steps (e.g., "list_products", "purchase_product") or "conversation_turn" for the overall request step, started_at as the UTC timestamp when the step began, completed_at as the UTC timestamp when the step finished, and the conversation_id matching the current conversation
5. IF a workflow step completes with a failure, THEN THE Sigil_Instrumentation SHALL populate the WorkflowStep error field with the error message and set the step status to failure
6. THE Sigil_Instrumentation SHALL populate the `linked_generation_ids` field on each workflow step with the identifier of the generation that triggered or is associated with that step

### Requirement 7: Coexistence with OpenInference

**User Story:** As a developer, I want both OpenInference and Sigil instrumentation active simultaneously, so that I get trace visualization from OpenInference and AI-specific observability from Sigil.

#### Acceptance Criteria

1. WHILE both OpenInference and Sigil are configured, THE Telemetry_Module SHALL add the OpenInference_Processor to the TracerProvider before any BatchSpanProcessor, so that spans are transformed to OpenInference format prior to export
2. WHILE both OpenInference and Sigil are configured, THE Telemetry_Module SHALL export spans to the Grafana OTLP endpoint via BatchSpanProcessor AND record generations to the Sigil endpoint via Sigil_Client, with every Agent-produced span processed by both pipelines
3. IF only OpenInference credentials are configured and `sigil_configured` returns false, THEN THE Telemetry_Module SHALL add the OpenInference_Processor and BatchSpanProcessor to the TracerProvider and SHALL NOT instantiate a Sigil_Client
4. IF only Sigil credentials are configured and Grafana OTLP credentials are absent, THEN THE Telemetry_Module SHALL instantiate the Sigil_Client and configure the MeterProvider but SHALL NOT add the OpenInference_Processor or OTLP BatchSpanProcessor to the TracerProvider
5. IF both OpenInference credentials and Sigil credentials are absent, THEN THE Telemetry_Module SHALL skip telemetry configuration entirely and log a warning indicating no observability backend is configured
6. WHILE both instrumentations are active, THE Telemetry_Module SHALL ensure that Sigil_Client internal spans and metrics do not interfere with OpenInference span transformation or OTLP export ordering

### Requirement 8: Environment Variable Documentation

**User Story:** As a developer, I want the Sigil environment variables documented in the .env.example file, so that new team members can configure the integration.

#### Acceptance Criteria

1. THE Environment_Template SHALL include `SIGIL_ENDPOINT` with the placeholder value `https://sigil-prod-REGION.grafana.net` and a preceding comment line explaining it is the Sigil ingest endpoint URL
2. THE Environment_Template SHALL include `SIGIL_PROTOCOL` with the default value `http/protobuf`
3. THE Environment_Template SHALL include `SIGIL_AUTH_MODE` with the default value `token`
4. THE Environment_Template SHALL include `SIGIL_AUTH_TENANT_ID` with the placeholder value `REPLACE_ME`
5. THE Environment_Template SHALL include `SIGIL_AUTH_TOKEN` with the placeholder value `glc_REPLACE_ME`
6. THE Environment_Template SHALL group all Sigil variables under a section header comment `# Observability — Sigil` placed immediately after the existing `# Observability — Grafana Cloud` section and separated from it by one blank line
7. THE Environment_Template SHALL list the Sigil variables in the following order: `SIGIL_ENDPOINT`, `SIGIL_PROTOCOL`, `SIGIL_AUTH_MODE`, `SIGIL_AUTH_TENANT_ID`, `SIGIL_AUTH_TOKEN`

### Requirement 9: Graceful Degradation

**User Story:** As a developer, I want the agent to function normally when Sigil SDK is unavailable or misconfigured, so that observability issues never break the core purchasing workflow.

#### Acceptance Criteria

1. IF the Sigil_Client fails to initialize, THEN THE Agent SHALL log the failure at WARNING level and continue to process user requests and execute tools without Sigil instrumentation for the remainder of the session
2. IF a Sigil generation recording fails at runtime, THEN THE Agent SHALL log the error at WARNING level and complete the current LLM generation, returning the model response to the user unaffected
3. IF a Sigil tool execution recording fails at runtime, THEN THE Agent SHALL log the error at WARNING level and return the original tool result unmodified to the calling agent loop
4. IF network connectivity to the Sigil endpoint is lost, THEN THE Agent SHALL continue processing user requests and tool executions with Sigil recording calls silently failing, without blocking the main execution thread
5. IF the Sigil_Strands_Adapter raises an exception during a callback, THEN THE Agent SHALL catch the exception, log it at WARNING level, and continue the agent execution loop without re-raising
6. IF Sigil_Client was never successfully initialized, THEN THE Telemetry_Module SHALL skip the shutdown call without raising an error during application teardown
