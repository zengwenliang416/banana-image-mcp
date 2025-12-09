"""Base image service providing common functionality for all image generation services."""

from abc import ABC, abstractmethod
import base64
import logging
from typing import Any, Protocol

from fastmcp.utilities.types import Image as MCPImage

from ..core.progress_tracker import ProgressContext
from ..utils.image_utils import optimize_image_size, validate_image_format


class ImageGenerationConfig(Protocol):
    """Protocol for image generation configuration."""

    model_name: str
    default_image_format: str


class BaseImageService(ABC):
    """Abstract base class for image generation services.

    Provides common functionality for image generation and editing,
    with abstract methods for model-specific behavior.
    """

    def __init__(
        self,
        gemini_client: Any,  # GeminiClient - avoid circular import
        config: ImageGenerationConfig,
        storage_service: Any | None = None,  # ImageStorageService
    ):
        """Initialize base image service.

        Args:
            gemini_client: Gemini API client instance
            config: Image generation configuration
            storage_service: Optional storage service for thumbnails
        """
        self.gemini_client = gemini_client
        self.config = config
        self.storage_service = storage_service
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def _get_operation_name(self) -> str:
        """Get operation name for progress tracking.

        Returns:
            Operation name string (e.g., "flash_image_generation")
        """
        ...

    @abstractmethod
    def _build_generation_config(self, **kwargs: Any) -> dict[str, Any]:
        """Build model-specific generation configuration.

        Args:
            **kwargs: Model-specific parameters

        Returns:
            Configuration dictionary for Gemini API
        """
        ...

    @abstractmethod
    def _build_metadata(
        self,
        prompt: str,
        response_index: int,
        image_index: int,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build model-specific metadata for generated image.

        Args:
            prompt: Generation prompt
            response_index: Index of the response (1-based)
            image_index: Index of the image within response (1-based)
            **kwargs: Additional model-specific parameters

        Returns:
            Metadata dictionary
        """
        ...

    def _enhance_prompt(self, prompt: str, **kwargs: Any) -> str:
        """Enhance prompt with model-specific modifications.

        Override in subclasses to add model-specific prompt enhancements.
        Default implementation returns the original prompt unchanged.

        Args:
            prompt: Original prompt
            **kwargs: Additional parameters

        Returns:
            Enhanced prompt string
        """
        return prompt

    def _build_contents(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        system_instruction: str | None = None,
        input_images: list[tuple[str, str]] | None = None,
        **kwargs: Any,
    ) -> list[Any]:
        """Build API request contents.

        Args:
            prompt: Main generation prompt
            negative_prompt: Optional constraints to avoid
            system_instruction: Optional system-level guidance
            input_images: List of (base64, mime_type) tuples
            **kwargs: Additional parameters for prompt enhancement

        Returns:
            List of content parts for Gemini API
        """
        contents: list[Any] = []

        # Add system instruction if provided
        if system_instruction:
            contents.append(system_instruction)

        # Enhance and add prompt with negative constraints
        enhanced_prompt = self._enhance_prompt(prompt, **kwargs)
        if negative_prompt:
            enhanced_prompt += f"\n\nConstraints (avoid): {negative_prompt}"
        contents.append(enhanced_prompt)

        # Add input images if provided
        if input_images:
            images_b64, mime_types = zip(*input_images, strict=False)
            image_parts = self.gemini_client.create_image_parts(list(images_b64), list(mime_types))
            # Place images before text for better context
            contents = list(image_parts) + contents

        return contents

    def _process_image_output(
        self,
        image_bytes: bytes,
        metadata: dict[str, Any],
        use_storage: bool,
    ) -> MCPImage:
        """Process image output with optional storage.

        Args:
            image_bytes: Raw image bytes
            metadata: Image metadata
            use_storage: Whether to use storage service

        Returns:
            MCPImage for response
        """
        if use_storage and self.storage_service:
            # Store image and return thumbnail
            stored_info = self.storage_service.store_image(
                image_bytes,
                f"image/{self.config.default_image_format}",
                metadata,
            )

            # Get thumbnail for preview
            thumbnail_b64 = self.storage_service.get_thumbnail_base64(stored_info.id)
            if thumbnail_b64:
                thumbnail_bytes = base64.b64decode(thumbnail_b64)
                return MCPImage(data=thumbnail_bytes, format="jpeg")

        # Fallback: optimize and return directly
        optimized_b64 = optimize_image_size(
            base64.b64encode(image_bytes).decode(),
            max_size=2 * 1024 * 1024,
        )
        optimized_bytes = base64.b64decode(optimized_b64)
        return MCPImage(data=optimized_bytes, format=self.config.default_image_format)

    def _generation_loop(
        self,
        contents: list[Any],
        n: int,
        prompt: str,
        gen_config: dict[str, Any] | None,
        use_storage: bool,
        progress: ProgressContext,
        aspect_ratio: str | None = None,
        **kwargs: Any,
    ) -> tuple[list[MCPImage], list[dict[str, Any]]]:
        """Execute generation loop with progress tracking.

        Args:
            contents: API request contents
            n: Number of images to generate
            prompt: Original prompt for metadata
            gen_config: Generation configuration
            use_storage: Whether to use storage
            progress: Progress context
            aspect_ratio: Optional aspect ratio
            **kwargs: Additional parameters for metadata

        Returns:
            Tuple of (images, metadata_list)
        """
        all_images: list[MCPImage] = []
        all_metadata: list[dict[str, Any]] = []

        for i in range(n):
            try:
                progress.update(
                    20 + (i * 60 // n),
                    f"Generating image {i + 1}/{n}...",
                )

                # Call Gemini API with resolution support
                # Extract resolution from kwargs for image_size parameter
                resolution = kwargs.get("resolution", "high")
                response = self.gemini_client.generate_content(
                    contents,
                    config=gen_config if gen_config else None,
                    aspect_ratio=aspect_ratio,
                    image_size=resolution,
                )
                images = self.gemini_client.extract_images(response)

                for j, image_bytes in enumerate(images):
                    progress.update(
                        20 + ((i * 60 + j * 60 // max(len(images), 1)) // n),
                        f"Processing image {i + 1}.{j + 1}...",
                    )

                    # Build metadata (model-specific)
                    metadata = self._build_metadata(
                        prompt=prompt,
                        response_index=i + 1,
                        image_index=j + 1,
                        aspect_ratio=aspect_ratio,
                        **kwargs,
                    )

                    # Process output
                    mcp_image = self._process_image_output(image_bytes, metadata, use_storage)
                    all_images.append(mcp_image)
                    all_metadata.append(metadata)

                    self.logger.info(
                        f"Generated image {i + 1}.{j + 1} (size: {len(image_bytes)} bytes)"
                    )

            except Exception as e:
                self.logger.error(f"Failed to generate image {i + 1}: {e}")
                # Continue with other images
                continue

        return all_images, all_metadata

    def generate_images(
        self,
        prompt: str,
        n: int = 1,
        negative_prompt: str | None = None,
        system_instruction: str | None = None,
        input_images: list[tuple[str, str]] | None = None,
        aspect_ratio: str | None = None,
        use_storage: bool = True,
        **model_specific_params: Any,
    ) -> tuple[list[MCPImage], list[dict[str, Any]]]:
        """Generate images using Gemini API.

        Args:
            prompt: Main generation prompt
            n: Number of images to generate
            negative_prompt: Optional constraints to avoid
            system_instruction: Optional system-level guidance
            input_images: List of (base64, mime_type) tuples
            aspect_ratio: Optional aspect ratio (e.g., "16:9")
            use_storage: Whether to use storage service
            **model_specific_params: Model-specific parameters

        Returns:
            Tuple of (images, metadata_list)
        """
        operation_name = self._get_operation_name()

        with ProgressContext(
            operation_name,
            f"Generating {n} image(s)...",
            {"prompt": prompt[:100], "count": n},
        ) as progress:
            progress.update(10, "Preparing generation request...")

            # Build contents
            contents = self._build_contents(
                prompt,
                negative_prompt,
                system_instruction,
                input_images,
                **model_specific_params,
            )

            # Get model-specific config
            gen_config = self._build_generation_config(**model_specific_params)

            progress.update(20, "Sending requests to Gemini API...")

            # Execute generation loop
            all_images, all_metadata = self._generation_loop(
                contents,
                n,
                prompt,
                gen_config,
                use_storage,
                progress,
                aspect_ratio,
                negative_prompt=negative_prompt,
                system_instruction=system_instruction,
                **model_specific_params,
            )

            progress.update(
                100,
                f"Successfully generated {len(all_images)} image(s)",
            )

            return all_images, all_metadata

    def edit_image(
        self,
        instruction: str,
        base_image_b64: str,
        mime_type: str = "image/png",
        use_storage: bool = True,
        **model_specific_params: Any,
    ) -> tuple[list[MCPImage], int]:
        """Edit an image using natural language instructions.

        Args:
            instruction: Editing instruction
            base_image_b64: Base64 encoded source image
            mime_type: MIME type of source image
            use_storage: Whether to use storage service
            **model_specific_params: Model-specific parameters

        Returns:
            Tuple of (edited_images, count)
        """
        operation_name = self._get_operation_name().replace("generation", "editing")

        with ProgressContext(
            operation_name,
            "Editing image...",
            {"instruction": instruction[:100]},
        ) as progress:
            try:
                progress.update(10, "Validating input image...")
                validate_image_format(mime_type)

                progress.update(20, "Preparing edit request...")

                # Enhance instruction if needed
                enhanced_instruction = self._enhance_prompt(instruction, **model_specific_params)

                # Create image parts
                image_parts = self.gemini_client.create_image_parts([base_image_b64], [mime_type])
                contents = [*list(image_parts), enhanced_instruction]

                progress.update(40, "Sending edit request to Gemini API...")

                # Get model-specific config
                gen_config = self._build_generation_config(**model_specific_params)

                # Generate edited image
                response = self.gemini_client.generate_content(
                    contents,
                    config=gen_config if gen_config else None,
                )
                image_bytes_list = self.gemini_client.extract_images(response)

                progress.update(70, "Processing edited image(s)...")

                mcp_images: list[MCPImage] = []
                for i, image_bytes in enumerate(image_bytes_list):
                    progress.update(
                        70 + (i * 20 // max(len(image_bytes_list), 1)),
                        f"Processing result {i + 1}/{len(image_bytes_list)}...",
                    )

                    # Build edit metadata
                    metadata = self._build_metadata(
                        prompt=instruction,
                        response_index=1,
                        image_index=i + 1,
                        instruction=instruction,
                        source_mime_type=mime_type,
                        edit_index=i + 1,
                        **model_specific_params,
                    )

                    mcp_image = self._process_image_output(image_bytes, metadata, use_storage)
                    mcp_images.append(mcp_image)

                    self.logger.info(f"Edited image {i + 1} (size: {len(image_bytes)} bytes)")

                progress.update(
                    100,
                    f"Successfully edited image, generated {len(mcp_images)} result(s)",
                )
                return mcp_images, len(mcp_images)

            except Exception as e:
                self.logger.error(f"Failed to edit image: {e}")
                raise
