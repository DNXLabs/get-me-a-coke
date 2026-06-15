"""Sigil tool execution instrumentation — decorator for recording tool calls in Grafana AI Observability."""

from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from typing import Any

from observability.telemetry import get_sigil_client

logger = logging.getLogger(__name__)


def sigil_tool_wrapper[F: Callable[..., Any]](tool_fn: F) -> F:
    """Wrap a tool function to record execution in Sigil.

    Behavior:
    - If Sigil client is not available, executes the tool directly (no-op wrapper).
    - On success: records tool execution with tool_name, input_args, output, duration_ms, success=True.
    - On failure: records with success=False and exception message, then re-raises the original exception.
    - Recording calls are wrapped in try/except so Sigil failures never affect tool behavior.

    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.3
    """

    @functools.wraps(tool_fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        client = get_sigil_client()
        if client is None:
            return tool_fn(*args, **kwargs)

        start = time.time()
        try:
            result = tool_fn(*args, **kwargs)
            duration_ms = (time.time() - start) * 1000
            try:
                client.start_tool_execution(
                    tool_name=tool_fn.__name__,
                    input_args={**{f"arg_{i}": v for i, v in enumerate(args)}, **kwargs} if args else kwargs,
                    output=result,
                    duration_ms=duration_ms,
                    success=True,
                )
            except Exception as rec_err:
                logger.warning("Sigil tool recording failed for %s: %s", tool_fn.__name__, rec_err)
            return result
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            try:
                client.start_tool_execution(
                    tool_name=tool_fn.__name__,
                    input_args={**{f"arg_{i}": v for i, v in enumerate(args)}, **kwargs} if args else kwargs,
                    output=str(e),
                    duration_ms=duration_ms,
                    success=False,
                )
            except Exception as rec_err:
                logger.warning("Sigil tool recording failed for %s: %s", tool_fn.__name__, rec_err)
            raise

    return wrapper  # type: ignore[return-value]
