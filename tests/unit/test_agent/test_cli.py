"""Tests for agent CLI entry point."""

import contextlib
from unittest.mock import MagicMock, patch


def test_cli_parses_single_shot_instruction() -> None:
    """Verify argparse correctly parses a positional instruction."""
    from agent.cli import main

    with (
        patch("agent.cli.run_single_shot") as mock_run,
        patch("agent.cli.AgentConfig") as mock_config_cls,
        patch("agent.cli.shutdown_sigil") as mock_shutdown,
        patch("sys.argv", ["agent", "Buy me a coke"]),
    ):
        mock_config = MagicMock()
        mock_config.observability_configured = False
        mock_config_cls.return_value = mock_config

        main()
        mock_run.assert_called_once_with(mock_config, "Buy me a coke")
        mock_shutdown.assert_called_once()


def test_cli_parses_interactive_flag() -> None:
    """Verify --interactive flag triggers REPL mode."""
    from agent.cli import main

    with (
        patch("agent.cli.run_interactive") as mock_run,
        patch("agent.cli.AgentConfig") as mock_config_cls,
        patch("agent.cli.shutdown_sigil") as mock_shutdown,
        patch("sys.argv", ["agent", "--interactive"]),
    ):
        mock_config = MagicMock()
        mock_config.observability_configured = False
        mock_config_cls.return_value = mock_config

        main()
        mock_run.assert_called_once_with(mock_config)
        mock_shutdown.assert_called_once()


def test_cli_calls_shutdown_sigil_on_exception() -> None:
    """Verify shutdown_sigil is called even when mode dispatch raises."""
    from agent.cli import main

    with (
        patch("agent.cli.run_single_shot", side_effect=RuntimeError("boom")),
        patch("agent.cli.AgentConfig") as mock_config_cls,
        patch("agent.cli.shutdown_sigil") as mock_shutdown,
        patch("sys.argv", ["agent", "Buy me a coke"]),
    ):
        mock_config = MagicMock()
        mock_config.observability_configured = False
        mock_config_cls.return_value = mock_config

        with contextlib.suppress(RuntimeError):
            main()

        mock_shutdown.assert_called_once()
