"""
Image generation models and data structures.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

class ImageStatus(Enum):
    QUEUED = "queued"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ImageRequest:
    """Request for image generation."""
    title: str
    prompt: str
    rationale: str
    aspect_ratio: str = "16:9"  # Options: "1:1", "16:9", "9:16", "4:3"
    style: Optional[str] = None  # e.g., "infographic", "diagram", "illustration"

@dataclass
class ImageArtifact:
    """Generated image artifact."""
    title: str
    prompt: str
    image_url: Optional[str] = None
    local_path: Optional[str] = None
    source: str = "freepik"
    task_id: Optional[str] = None
    status: ImageStatus = ImageStatus.QUEUED
    created_at: datetime = None
    aspect_ratio: str = "16:9"
    style: Optional[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class ImageSuggestion:
    """LLM suggestion for image generation."""
    should_generate: bool
    images: List[ImageRequest]
    reasoning: Optional[str] = None
