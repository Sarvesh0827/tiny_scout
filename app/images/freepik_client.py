"""
Freepik Image Generation API Client.
Freepik API returns images synchronously (no async polling needed).
"""
import httpx
import os
import base64
import hashlib
from typing import Optional, Dict, Any
from .models import ImageRequest, ImageArtifact, ImageStatus
from dotenv import load_dotenv

load_dotenv()

class FreepikClient:
    """Client for Freepik Image Generation API."""
    
    BASE_URL = "https://api.freepik.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FREEPIK_API_KEY")
        if not self.api_key:
            raise ValueError("FREEPIK_API_KEY not found in environment")
        
        self.headers = {
            "x-freepik-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def generate_image(self, request: ImageRequest) -> ImageArtifact:
        """
        Generate image using Freepik API (synchronous response).
        Returns ImageArtifact with base64 or URL.
        """
        artifact = ImageArtifact(
            title=request.title,
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            style=request.style,
            status=ImageStatus.QUEUED
        )
        
        # Map aspect ratio to Freepik size format
        size_map = {
            "1:1": "square",
            "16:9": "landscape",  
            "9:16": "portrait",
            "4:3": "landscape"
        }
        
        payload = {
            "prompt": request.prompt,
            "negative_prompt": "text, watermark, logo, brand name, copyright, low quality, blurry",
            "guidance_scale": 7.5,
            "num_images": 1,
            "image": {
                "size": size_map.get(request.aspect_ratio, "landscape")
            }
        }
        
        print(f"[FREEPIK] Generating: {request.title}")
        
        try:
            artifact.status = ImageStatus.GENERATING
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/ai/text-to-image",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract image from response
                if "data" in data and len(data["data"]) > 0:
                    image_data = data["data"][0]
                    
                    # Check if we got a URL or base64
                    if "url" in image_data:
                        artifact.image_url = image_data["url"]
                        print(f"[FREEPIK] Image URL: {artifact.image_url}")
                    elif "base64" in image_data:
                        # Save base64 to local file
                        artifact.local_path = self._save_base64_image(
                            image_data["base64"],
                            request.title
                        )
                        print(f"[FREEPIK] Image saved: {artifact.local_path}")
                    else:
                        raise ValueError("No URL or base64 in response")
                    
                    artifact.status = ImageStatus.COMPLETED
                    print(f"[FREEPIK] ✅ Success: {request.title}")
                else:
                    raise ValueError("No image data in response")
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            artifact.status = ImageStatus.FAILED
            artifact.error_message = error_msg
            print(f"[FREEPIK] ❌ HTTP Error: {error_msg}")
            
        except Exception as e:
            artifact.status = ImageStatus.FAILED
            artifact.error_message = str(e)
            print(f"[FREEPIK] ❌ Error: {e}")
        
        return artifact
    
    def _save_base64_image(self, base64_data: str, title: str) -> str:
        """Save base64 image to local file."""
        import os
        
        # Create images directory
        os.makedirs("cache/images", exist_ok=True)
        
        # Generate filename from title
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        filename = f"{safe_title}_{hashlib.md5(base64_data[:100].encode()).hexdigest()[:8]}.png"
        filepath = os.path.join("cache/images", filename)
        
        # Decode and save
        image_bytes = base64.b64decode(base64_data)
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        
        return filepath

