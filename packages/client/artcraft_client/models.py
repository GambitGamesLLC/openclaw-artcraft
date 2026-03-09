"""
Data models for ArtCraft Client.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Task:
    """Represents a task in the ArtCraft queue."""
    id: str
    status: str  # pending, processing, completed, failed, dismissed
    type: str    # text_to_image, image_to_video, etc.
    prompt: str
    provider: str
    created_at: str
    completed_at: str = None
    error: str = None


@dataclass
class MediaFile:
    """Represents a generated media file."""
    token: str
    type: str  # image, video
    url: str = None
    path: str = None


@dataclass
class GenerationResult:
    """Result of a generation operation."""
    task_id: str
    status: str
    input_prompt: str
    output_files: List[str]  # Paths to generated files
    media_tokens: List[str]
    duration_seconds: float = None
