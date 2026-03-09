"""ArtCraft client (Python).

`openclaw-artcraft` is a small Python wrapper around the shipped ArtCraft CLI
contract:

    artcraft invoke <tauri_command_name> [--payload ...] [--unsafe] --json
"""

from .client import ArtCraftClient
from .exceptions import (
    ArtCraftError,
    CommandNotFoundError,
    DisallowedCommand,
    InvalidArgs,
    InvokeError,
    Timeout,
    UnsafeGateDisabled,
)

__version__ = "0.2.0"

__all__ = [
    "ArtCraftClient",
    "ArtCraftError",
    "CommandNotFoundError",
    "InvalidArgs",
    "UnsafeGateDisabled",
    "DisallowedCommand",
    "InvokeError",
    "Timeout",
]
