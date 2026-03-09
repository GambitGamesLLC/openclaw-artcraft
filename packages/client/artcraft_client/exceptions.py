"""artcraft_client.exceptions

Typed exceptions raised by :class:`~artcraft_client.client.ArtCraftClient`.

ArtCraft's CLI contract (shipped) is:

    artcraft invoke <tauri_command_name> [--payload ...] [--unsafe] --json

Known exit codes:
- 0: success
- 2: invalid args OR unsafe gate disabled
- 3: unknown/disallowed command
- 4: invoke runtime error
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ArtCraftError(Exception):
    """Base error for the ArtCraft Python client."""

    message: str
    command: Optional[str] = None
    returncode: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None

    def __str__(self) -> str:  # pragma: no cover (tiny)
        return self.message


class CommandNotFoundError(ArtCraftError):
    """The `artcraft` executable was not found or is not executable."""


class InvalidArgs(ArtCraftError):
    """The CLI rejected the arguments (exit code 2)."""


class UnsafeGateDisabled(ArtCraftError):
    """The unsafe gate is disabled and `--unsafe` is not permitted (exit code 2)."""


class DisallowedCommand(ArtCraftError):
    """The command was unknown or disallowed (exit code 3)."""


class InvokeError(ArtCraftError):
    """The invoke succeeded but returned an error, or output could not be parsed (exit code 4 or JSON parse error)."""


class Timeout(ArtCraftError):
    """The CLI invocation timed out."""


# Backwards-compat aliases (older versions exposed these names)
TimeoutError = Timeout
CLIExecutionError = InvokeError

# Legacy names kept for compatibility with older client versions.
class TaskFailedError(ArtCraftError):
    pass
