# Implementation Plan: Sigil Instrumentation

## Overview

Add Grafana Sigil SDK instrumentation to the vending machine purchasing agent. The implementation layers Sigil on top of the existing OTel pipeline, providing AI-specific observability (generation tracking, tool execution metrics, workflow visualization) alongside existing OpenInference traces. All Sigil operations are defensively wrapped so failures never interrupt the core agent loop.

## Tasks
NEVER EXECUTE multiline python conde with python -c "multiline", create .py file instaead
- [x] 1. Add Sigil SDK dependencies and environment documentation
  - [x] 1.1 Add Sigil SDK packages to pyproject.toml
    - Add `sigil-sdk>=0.1.2` and `sigil-sdk-strands>=0.1.0` to `[project].dependencies` in pyproject.toml
    - Add `hypothesis>=6.100.0` to `[dependency-groups].dev` for property-based testing
    - Run `uv sync` to verify dependency resolution completes without conflicts
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 1.2 Add Sigil environment variables to .env.example
    - Add a blank line after the existing `# Observability — Grafana Cloud` section
    - Add `# Observability — Sigil` section header
    - Add `SIGIL_ENDPOINT=https://sigil-prod-REGION.grafana.net` with a comment explaining it is the Sigil ingest endpoint URL
    - Add `SIGIL_PROTOCOL=http/protobuf`
    - Add `SIGIL_AUTH_MODE=token`
    - Add `SIGIL_AUTH_TENANT_ID=REPLACE_ME`
    - Add `SIGIL_AUTH_TOKEN=glc_REPLACE_ME`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [x] 2. Implement Sigil configuration settings
  - [x] 2.1 Extend AgentConfig with Sigil fields
    - Add `sigil_endpoint: str = ""` field
    - Add `sigil_protocol: Literal["http/protobuf", "grpc"] = "http/protobuf"` field
    - Add `sigil_auth_mode: Literal["token", "basic", "tenant"] = "token"` field
    - Add `sigil_auth_tenant_id: str = ""` field
    - Add `sigil_auth_token: str = ""` field
    - Add `sigil_configured` property that returns True only when endpoint, tenant_id, and token all contain non-whitespace
    - Import `Literal` from `typing`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [ ]* 2.2 Write property test for enum field validation (Property 1)
    - **Property 1: Enum field validation rejects invalid values**
    - Use Hypothesis `st.text()` filtered to exclude valid enum values
    - Verify that constructing AgentConfig with invalid `sigil_protocol` or `sigil_auth_mode` raises ValidationError
    - **Validates: Requirements 2.2, 2.3, 2.7, 2.8**

  - [ ]* 2.3 Write property test for sigil_configured completeness (Property 2)
    - **Property 2: sigil_configured reflects credential completeness**
    - Use Hypothesis `st.text()` for each of the 3 credential fields (including whitespace-only strings)
    - Verify `sigil_configured` returns True iff all three fields contain at least one non-whitespace character
    - **Validates: Requirements 2.6**

  - [ ]* 2.4 Write unit tests for AgentConfig Sigil fields
    - Test default values for all Sigil fields
    - Test env var loading for each field
    - Test `sigil_configured` returns False when any credential is missing or whitespace-only
    - Test `sigil_configured` returns True when all credentials are present
    - Test Literal validation rejects invalid protocol and auth_mode values
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

- [x] 3. Checkpoint - Ensure configuration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement Sigil client initialization in telemetry module
  - [x] 4.1 Add Sigil client initialization to telemetry.py
    - Add module-level `_sigil_client: Optional[SigilClient] = None` variable
    - Add `get_sigil_client() -> Optional[Client]` public accessor function
    - Add `shutdown_sigil() -> None` function that calls `_sigil_client.shutdown()` if not None, wrapped in try/except
    - Update `configure_telemetry()` to accept AgentConfig (or Sigil params) and initialize Sigil Client after TracerProvider and MeterProvider are set
    - Create `ClientConfig` with `GenerationExportConfig` and `AuthConfig` from config values
    - Handle ImportError for `sigil-sdk` with WARNING log
    - Handle Client construction exceptions with ERROR log, leaving `_sigil_client` as None
    - Log WARNING when partial credentials are detected (some present but not all)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 9.1, 9.6_

  - [ ]* 4.2 Write property test for partial credentials prevention (Property 3)
    - **Property 3: Partial Sigil credentials prevent client creation**
    - Use Hypothesis `st.tuples(st.text(), st.text(), st.text())` with at least one empty field
    - Verify that when credentials are partially present, no Sigil Client is created and a warning is logged
    - **Validates: Requirements 3.4**

  - [ ]* 4.3 Write unit tests for telemetry Sigil initialization
    - Test Sigil client created when all credentials present (mock sigil_sdk)
    - Test graceful skip when credentials missing
    - Test WARNING logged when sigil-sdk not installed (ImportError)
    - Test ERROR logged when Client constructor raises
    - Test WARNING logged for partial credentials
    - Test `get_sigil_client()` returns client when initialized, None otherwise
    - Test `shutdown_sigil()` calls shutdown when client exists, no-op when None
    - Test shutdown exception is caught and logged
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 9.6_

- [x] 5. Implement Sigil Strands adapter integration in agent module
  - [x] 5.1 Attach SigilStrandsHandler in create_agent()
    - Import `get_sigil_client` from `observability.telemetry`
    - When `get_sigil_client()` returns a client, create `SigilStrandsHandler` with `sigil_client`, `agent_name="get-me-a-coke-agent"`, and `conversation_title="Vending Machine Purchase"`
    - Pass the handler as `callback_handler` to the Agent constructor
    - Handle ImportError for `sigil_sdk_strands` with WARNING log
    - Handle any exception during adapter creation with WARNING log, creating agent without callback_handler
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 5.2 Write unit tests for agent Sigil adapter attachment
    - Test adapter attached when Sigil client available (mock sigil_sdk_strands)
    - Test agent created without callback_handler when Sigil client is None
    - Test WARNING logged when sigil-sdk-strands not installed
    - Test WARNING logged when adapter constructor raises
    - Test existing plugins (AgentCore Payments) unaffected by adapter presence
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 6. Implement CLI shutdown integration
  - [ ] 6.1 Add shutdown_sigil() call to CLI main()
    - Import `shutdown_sigil` from `observability.telemetry`
    - Wrap the mode dispatch (interactive/single-shot) in a try/finally block
    - Call `shutdown_sigil()` in the finally block to flush pending telemetry on exit
    - _Requirements: 3.7, 9.6_

  - [ ]* 6.2 Write unit tests for CLI shutdown
    - Test `shutdown_sigil()` is called on normal exit
    - Test `shutdown_sigil()` is called even when agent raises an exception
    - _Requirements: 3.7, 9.6_

- [x] 7. Checkpoint - Ensure core integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement tool execution instrumentation
  - [x] 8.1 Create sigil_tool_wrapper decorator
    - Create a decorator function in a new file `src/observability/sigil_tools.py` (or within telemetry.py)
    - The wrapper calls `get_sigil_client()` — if None, executes tool directly
    - On success: records tool execution with tool_name, input_args, output, duration_ms, success=True
    - On failure: records with success=False and exception message, then re-raises the original exception
    - Wrap recording calls in try/except so Sigil failures never affect tool behavior
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.3_

  - [ ]* 8.2 Write property test for tool instrumentation transparency (Property 4)
    - **Property 4: Tool instrumentation transparency**
    - Use Hypothesis `st.dictionaries()` for tool kwargs, `st.booleans()` for client availability
    - Verify instrumented tool returns exact same value as uninstrumented version regardless of Sigil client state
    - **Validates: Requirements 5.4, 5.5, 9.3**

  - [ ]* 8.3 Write property test for failed tool re-raise (Property 5)
    - **Property 5: Failed tool execution records failure and re-raises**
    - Use Hypothesis `st.sampled_from([ValueError, RuntimeError, TypeError, IOError])` for exception types
    - Verify exception is re-raised with type and message unchanged, and recording shows success=False
    - **Validates: Requirements 5.2**

  - [ ]* 8.4 Write property test for recording completeness (Property 6)
    - **Property 6: Tool execution recording captures all required fields**
    - Use Hypothesis `st.text()` for tool name, `st.dictionaries()` for args
    - Verify recorded execution contains: tool_name, input_args, output, duration_ms (non-negative), success (boolean)
    - **Validates: Requirements 5.1**

  - [ ]* 8.5 Write property test for generation failure isolation (Property 7)
    - **Property 7: Generation recording failure does not affect LLM response**
    - Use Hypothesis `st.text()` for model response, various exception types for recording failures
    - Verify agent returns complete model response unchanged when Sigil recording raises
    - **Validates: Requirements 9.2**

  - [ ]* 8.6 Write unit tests for tool wrapper
    - Test successful tool execution is recorded with correct fields
    - Test failed tool execution records failure and re-raises
    - Test wrapper is no-op when Sigil client is None
    - Test Sigil recording failure does not affect tool return value
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.3_

- [x] 9. Wire coexistence and update telemetry initialization order
  - [x] 9.1 Update configure_telemetry to handle coexistence scenarios
    - Ensure OpenInference processor is added before BatchSpanProcessor
    - Handle scenario: both OpenInference + Sigil configured
    - Handle scenario: only OpenInference configured (no Sigil client)
    - Handle scenario: only Sigil configured (no OTLP export)
    - Handle scenario: neither configured (skip telemetry, log warning)
    - Update `configure_telemetry` signature to accept Sigil config params alongside existing Grafana params
    - Update CLI `main()` to pass Sigil config to `configure_telemetry`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [ ]* 9.2 Write integration tests for coexistence
    - Test both pipelines active simultaneously (OpenInference + Sigil)
    - Test OpenInference-only mode when Sigil credentials absent
    - Test Sigil-only mode when Grafana OTLP credentials absent
    - Test no-telemetry mode when all credentials absent
    - Test Sigil internal spans don't interfere with OpenInference transformation
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation language is Python, matching the existing codebase and design document
- All Sigil operations must be defensively wrapped — no Sigil failure should ever propagate to the user

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4"] },
    { "id": 3, "tasks": ["4.1"] },
    { "id": 4, "tasks": ["4.2", "4.3", "5.1", "6.1"] },
    { "id": 5, "tasks": ["5.2", "6.2", "8.1"] },
    { "id": 6, "tasks": ["8.2", "8.3", "8.4", "8.5", "8.6"] },
    { "id": 7, "tasks": ["9.1"] },
    { "id": 8, "tasks": ["9.2"] }
  ]
}
```
