"""CLI entry point for the AI agent — single-shot and interactive REPL modes."""

from __future__ import annotations

import argparse
import logging
import sys

from agent.agent import create_agent
from agent.config import AgentConfig
from observability.telemetry import configure_telemetry, shutdown_sigil


def main() -> None:
    """Parse CLI arguments and dispatch to single-shot or REPL mode."""
    parser = argparse.ArgumentParser(
        prog="agent",
        description="AI agent that buys items from vending machines using x402 payments",
    )
    parser.add_argument(
        "instruction",
        nargs="?",
        help="Instruction for the agent (single-shot mode). Omit for interactive mode.",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start interactive REPL mode",
    )

    args = parser.parse_args()

    # Load configuration
    config = AgentConfig()

    # Suppress console logging — telemetry still exports to Grafana
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Initialize observability (must happen before agent creation)
    # Always call configure_telemetry with config — it handles all coexistence scenarios:
    # both OpenInference+Sigil, only OpenInference, only Sigil, or neither.
    configure_telemetry(config=config)

    try:
        if args.interactive or args.instruction is None:
            run_interactive(config)
        else:
            run_single_shot(config, args.instruction)
    finally:
        shutdown_sigil()


def run_single_shot(config: AgentConfig, instruction: str) -> None:
    """Execute a single instruction and exit."""
    import os

    os.environ.setdefault("AWS_PROFILE", config.aws_profile)
    os.environ.setdefault("AWS_DEFAULT_REGION", config.aws_region)
    os.environ.setdefault("VENDING_MACHINE_URL", config.vending_machine_url)
    os.environ.setdefault("WALLET_SERVICE_URL", config.wallet_service_url)
    os.environ.setdefault("WALLET_API_KEY", config.wallet_api_key)
    os.environ.setdefault("BEDROCK_PROMPT_ID", config.bedrock_prompt_id)
    os.environ.setdefault("BEDROCK_PROMPT_VERSION", config.bedrock_prompt_version)

    try:
        agent = create_agent(config)
        result = agent(instruction)
        print(result)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def run_interactive(config: AgentConfig) -> None:
    """Start an interactive REPL loop."""
    import os

    os.environ.setdefault("AWS_PROFILE", config.aws_profile)
    os.environ.setdefault("AWS_DEFAULT_REGION", config.aws_region)
    os.environ.setdefault("VENDING_MACHINE_URL", config.vending_machine_url)
    os.environ.setdefault("WALLET_SERVICE_URL", config.wallet_service_url)
    os.environ.setdefault("WALLET_API_KEY", config.wallet_api_key)
    os.environ.setdefault("BEDROCK_PROMPT_ID", config.bedrock_prompt_id)
    os.environ.setdefault("BEDROCK_PROMPT_VERSION", config.bedrock_prompt_version)
    agent = create_agent(config)
    print("🥤 Get Me a Coke — Interactive Mode")
    print("Type your message, or 'exit'/'quit' to leave.\n")

    while True:
        try:
            user_input = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            agent(user_input)
            print()  # newline after streamed output
        except Exception as e:
            print(f"\nError: {e}\n", file=sys.stderr)


if __name__ == "__main__":
    main()
