"""Centralized Rich console for the application.

Auto-detects MCP mode (non-TTY stdout) and redirects output to stderr
to avoid conflicts with the MCP protocol.
"""

import sys
from rich.console import Console

# When stdout isn't a terminal (e.g., MCP mode), use stderr instead
_use_stderr = not sys.stdout.isatty()

console = Console(
    file=sys.stderr if _use_stderr else sys.stdout,
    force_terminal=True
)
