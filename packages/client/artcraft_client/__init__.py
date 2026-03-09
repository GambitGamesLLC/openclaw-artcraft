"""
ArtCraft Client - Python library for controlling ArtCraft AI generation via CLI.

This package provides a Python interface to the ArtCraft CLI wrapper,
enabling programmatic control of AI image/video generation workflows.
"""

from .client import ArtCraftClient
from .models import Task, MediaFile, GenerationResult
from .exceptions import (
    ArtCraftError,
    CommandNotFoundError,
    TaskFailedError,
    TimeoutError,
    CLIExecutionError,
)

__version__ = "0.1.0"
__all__ = [
    "ArtCraftClient",
    "Task",
    "MediaFile",
    "GenerationResult",
    "ArtCraftError",
    "CommandNotFoundError",
    "TaskFailedError",
    "TimeoutError",
    "CLIExecutionError",
]
