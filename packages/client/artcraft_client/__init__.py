"""ArtCraft client (Python).

`openclaw-artcraft` is a small Python wrapper around the shipped ArtCraft CLI
contract:

    artcraft invoke <tauri_command_name> [--payload ...] [--unsafe] --json

This package provides a low-level :class:`~artcraft_client.client.ArtCraftClient`.
Unsafe invocation is an explicit opt-in via `tier="unsafe"`.
"""

from .client import AllowedCommands, ArtCraftClient, Tier
from .exceptions import (
    ArtCraftError,
    CommandNotFoundError,
    DisallowedCommand,
    InvalidArgs,
    InvokeError,
    Timeout,
    UnsafeGateDisabled,
)

__version__ = "0.3.0"

__all__ = [
    "AllowedCommands",
    "Tier",
    "ArtCraftClient",
    "ArtCraftError",
    "CommandNotFoundError",
    "InvalidArgs",
    "UnsafeGateDisabled",
    "DisallowedCommand",
    "InvokeError",
    "Timeout",
]
