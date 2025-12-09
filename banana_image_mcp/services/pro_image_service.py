"""Gemini 3 Pro Image specialized service for high-quality generation."""

from typing import Any

from ..config.settings import MediaResolution, ProImageConfig, ThinkingLevel
from .base_image_service import BaseImageService
from .gemini_client import GeminiClient
from .image_storage_service import ImageStorageService


class ProImageService(BaseImageService):
    """Service for high-quality image generation using Gemini 3 Pro Image model.

    Features:
    - Up to 4K resolution support
    - Google Search grounding for factual accuracy
    - Advanced reasoning with configurable thinking levels
    - Professional-grade outputs
    """

    def __init__(
        self,
        gemini_client: GeminiClient,
        config: ProImageConfig,
        storage_service: ImageStorageService | None = None,
    ):
        """Initialize Pro image service.

        Args:
            gemini_client: Gemini API client configured for Pro model
            config: Pro model configuration
            storage_service: Optional storage service for thumbnails
        """
        super().__init__(gemini_client, config, storage_service)
        self.pro_config = config

    def _get_operation_name(self) -> str:
        """Get operation name for progress tracking."""
        return "pro_image_generation"

    def _build_generation_config(
        self,
        thinking_level: ThinkingLevel | None = None,
        media_resolution: MediaResolution | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build generation config for Pro model.

        Args:
            thinking_level: Reasoning depth (LOW or HIGH)
            media_resolution: Vision processing detail level
            **kwargs: Additional parameters (ignored)

        Returns:
            Configuration dictionary with Pro-specific parameters
        """
        # Apply defaults from config
        level = thinking_level or self.pro_config.default_thinking_level
        resolution = media_resolution or self.pro_config.default_media_resolution

        config: dict[str, Any] = {
            "thinking_level": level.value,
        }

        # Add media resolution if supported
        if self.pro_config.supports_media_resolution:
            config["media_resolution"] = resolution.value

        return config

    def _build_metadata(
        self,
        prompt: str,
        response_index: int,
        image_index: int,
        resolution: str = "high",
        thinking_level: ThinkingLevel | None = None,
        media_resolution: MediaResolution | None = None,
        enable_grounding: bool | None = None,
        negative_prompt: str | None = None,
        system_instruction: str | None = None,
        aspect_ratio: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build metadata for Pro-generated image.

        Args:
            prompt: Generation prompt
            response_index: Index of the response (1-based)
            image_index: Index of the image within response (1-based)
            resolution: Output resolution setting
            thinking_level: Reasoning depth used
            media_resolution: Vision processing detail level used
            enable_grounding: Whether grounding was enabled
            negative_prompt: Optional negative prompt used
            system_instruction: Optional system instruction used
            aspect_ratio: Optional aspect ratio used
            **kwargs: Additional parameters (ignored)

        Returns:
            Metadata dictionary with Pro-specific fields
        """
        # Apply defaults
        level = thinking_level or self.pro_config.default_thinking_level
        media_res = media_resolution or self.pro_config.default_media_resolution
        grounding = (
            enable_grounding
            if enable_grounding is not None
            else self.pro_config.enable_search_grounding
        )

        return {
            "model": self.pro_config.model_name,
            "model_tier": "pro",
            "response_index": response_index,
            "image_index": image_index,
            "resolution": resolution,
            "thinking_level": level.value,
            "media_resolution": media_res.value,
            "grounding_enabled": grounding,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "system_instruction": system_instruction,
            "aspect_ratio": aspect_ratio,
            "mime_type": f"image/{self.config.default_image_format}",
            "synthid_watermark": True,
        }

    def _enhance_prompt(
        self,
        prompt: str,
        resolution: str = "high",
        negative_prompt: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Enhance prompt to leverage Pro model capabilities.

        Pro model benefits from:
        - Narrative, descriptive prompts
        - Specific composition/lighting details
        - Quality and detail emphasis

        Args:
            prompt: Original prompt
            resolution: Target resolution
            negative_prompt: Optional constraints (handled separately in base class)
            **kwargs: Additional parameters (ignored)

        Returns:
            Enhanced prompt string
        """
        enhanced = prompt

        # Pro model benefits from narrative prompts for short inputs
        if len(prompt) < 50:
            enhanced = (
                f"Create a high-quality, detailed image: {prompt}. "
                "Pay attention to composition, lighting, and fine details."
            )

        # Resolution hints for high-res outputs
        if resolution in ["4k", "high", "2k"]:
            if "text" in prompt.lower() or "diagram" in prompt.lower():
                enhanced += " Ensure text is sharp and clearly readable at high resolution."
            if resolution == "4k":
                enhanced += " Render at maximum 4K quality with exceptional detail."

        return enhanced
