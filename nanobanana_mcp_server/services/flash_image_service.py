"""Flash image service for speed-optimized image generation."""

from typing import Any

from ..config.settings import FlashImageConfig
from .base_image_service import BaseImageService
from .gemini_client import GeminiClient
from .image_storage_service import ImageStorageService


class FlashImageService(BaseImageService):
    """Gemini Flash image service for speed-optimized generation.

    Uses Gemini 2.5 Flash Image model for fast image generation
    with lower latency and high throughput.
    """

    def __init__(
        self,
        gemini_client: GeminiClient,
        config: FlashImageConfig,
        storage_service: ImageStorageService | None = None,
    ):
        """Initialize Flash image service.

        Args:
            gemini_client: Gemini API client configured for Flash model
            config: Flash model configuration
            storage_service: Optional storage service for thumbnails
        """
        super().__init__(gemini_client, config, storage_service)
        self.flash_config = config

    def _get_operation_name(self) -> str:
        """Get operation name for progress tracking."""
        return "flash_image_generation"

    def _build_generation_config(self, **kwargs: Any) -> dict[str, Any]:
        """Build generation config for Flash model.

        Flash model doesn't require special configuration parameters.

        Returns:
            Empty dictionary (Flash uses defaults)
        """
        return {}

    def _build_metadata(
        self,
        prompt: str,
        response_index: int,
        image_index: int,
        negative_prompt: str | None = None,
        system_instruction: str | None = None,
        aspect_ratio: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build metadata for Flash-generated image.

        Args:
            prompt: Generation prompt
            response_index: Index of the response (1-based)
            image_index: Index of the image within response (1-based)
            negative_prompt: Optional negative prompt used
            system_instruction: Optional system instruction used
            aspect_ratio: Optional aspect ratio used
            **kwargs: Additional parameters (ignored)

        Returns:
            Metadata dictionary with Flash-specific fields
        """
        return {
            "model": "gemini-2.5-flash-image",
            "model_tier": "flash",
            "response_index": response_index,
            "image_index": image_index,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "system_instruction": system_instruction,
            "aspect_ratio": aspect_ratio,
            "mime_type": f"image/{self.config.default_image_format}",
            "synthid_watermark": True,
        }

    def _enhance_prompt(self, prompt: str, **kwargs: Any) -> str:
        """Enhance prompt for Flash model.

        Flash model uses prompts as-is without enhancement.

        Args:
            prompt: Original prompt
            **kwargs: Ignored

        Returns:
            Original prompt unchanged
        """
        return prompt
