"""
Image generation module for TinyScout.
Supports Freepik API integration with caching and LLM-based suggestions.
"""
from .models import ImageRequest, ImageArtifact, ImageSuggestion, ImageStatus
from .generator import ImageGenerator
from .suggestion_agent import ImageSuggestionAgent
from .cache import ImageCache

__all__ = [
    "ImageRequest",
    "ImageArtifact",
    "ImageSuggestion",
    "ImageStatus",
    "ImageGenerator",
    "ImageSuggestionAgent",
    "ImageCache"
]
