"""
Custom exceptions for ArtCraft Client.
"""


class ArtCraftError(Exception):
    """Base exception for ArtCraft client."""
    pass


class CommandNotFoundError(ArtCraftError):
    """CLI command not found or not executable."""
    pass


class TaskFailedError(ArtCraftError):
    """Task failed during generation."""
    pass


class TimeoutError(ArtCraftError):
    """Task did not complete within timeout."""
    pass


class CLIExecutionError(ArtCraftError):
    """CLI command execution failed."""
    pass
