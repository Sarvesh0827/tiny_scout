"""
Main image generation service with caching and rate limiting.
"""
import asyncio
from typing import List, Optional
from .models import ImageRequest, ImageArtifact, ImageStatus
from .freepik_client import FreepikClient
from .cache import ImageCache
import os

class ImageGenerator:
    """
    Main interface for image generation with caching and rate limiting.
    """
    
    MAX_IMAGES_PER_RUN = 3
    MAX_RETRIES = 1
    
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        self.cache = ImageCache() if use_cache else None
        
        # Only initialize client if API key is available
        try:
            self.client = FreepikClient()
            self.enabled = True
        except ValueError as e:
            print(f"[IMAGE_GEN] Freepik disabled: {e}")
            self.enabled = False
            self.client = None
    
    async def generate_images(
        self, 
        requests: List[ImageRequest],
        max_images: Optional[int] = None
    ) -> List[ImageArtifact]:
        """
        Generate multiple images with caching and rate limiting.
        """
        if not self.enabled:
            print("[IMAGE_GEN] Image generation disabled (no API key)")
            return []
        
        # Apply rate limit
        max_count = min(max_images or self.MAX_IMAGES_PER_RUN, self.MAX_IMAGES_PER_RUN)
        requests = requests[:max_count]
        
        print(f"[IMAGE_GEN] Generating {len(requests)} images...")
        
        artifacts = []
        
        for req in requests:
            artifact = await self._generate_single(req)
            artifacts.append(artifact)
        
        return artifacts
    
    async def _generate_single(self, request: ImageRequest) -> ImageArtifact:
        """Generate a single image with caching."""
        
        # Check cache first
        if self.use_cache and self.cache:
            cache_key = ImageCache.generate_cache_key(
                request.title,
                request.prompt,
                request.aspect_ratio,
                request.style
            )
            
            cached = self.cache.get(cache_key)
            if cached and cached.status == ImageStatus.COMPLETED:
                print(f"[IMAGE_GEN] Cache hit: {request.title}")
                return cached
        
        # Generate new image
        print(f"[IMAGE_GEN] Generating: {request.title}")
        
        artifact = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                artifact = await self.client.generate_image(request)
                
                if artifact.status == ImageStatus.COMPLETED:
                    break
                    
            except Exception as e:
                print(f"[IMAGE_GEN] Attempt {attempt + 1} failed: {e}")
                if attempt == self.MAX_RETRIES:
                    artifact = ImageArtifact(
                        title=request.title,
                        prompt=request.prompt,
                        aspect_ratio=request.aspect_ratio,
                        style=request.style,
                        status=ImageStatus.FAILED,
                        error_message=str(e)
                    )
        
        # Cache result
        if self.use_cache and self.cache and artifact:
            cache_key = ImageCache.generate_cache_key(
                request.title,
                request.prompt,
                request.aspect_ratio,
                request.style
            )
            self.cache.set(cache_key, artifact)
        
        return artifact
    
    def is_enabled(self) -> bool:
        """Check if image generation is available."""
        return self.enabled
