"""
Property-based tests for BaseImageService.

**Feature: service-layer-refactoring**
**Validates: Requirements 1.4, 1.5**

This module tests:
- Property 4: Content Building Completeness
- Property 5: Image Output Processing
"""

from unittest.mock import Mock

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
import pytest

from banana_image_mcp.services.flash_image_service import FlashImageService

# =============================================================================
# Hypothesis Strategies
# =============================================================================

# Strategy for generating prompts
prompt_strategy = st.text(min_size=1, max_size=200)


# =============================================================================
# Property 4: Content Building Completeness
# =============================================================================


class TestContentBuildingCompleteness:
    """
    **Feature: service-layer-refactoring, Property 4: Content Building Completeness**

    *For any* combination of prompt, negative_prompt, system_instruction, and
    input_images, the `_build_contents()` method SHALL return a list where:
    - The prompt (possibly enhanced) is always present
    - Negative prompt constraints are appended when provided
    - System instruction is prepended when provided
    - Input image parts are included when provided
    """

    @pytest.fixture
    def flash_service(self, mock_flash_gemini_client, mock_flash_config, mock_storage_service):
        """Create a FlashImageService for testing _build_contents."""
        return FlashImageService(
            gemini_client=mock_flash_gemini_client,
            config=mock_flash_config,
            storage_service=mock_storage_service,
        )

    @given(prompt=prompt_strategy)
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_prompt_always_present(self, flash_service, prompt: str):
        """
        **Feature: service-layer-refactoring, Property 4: Content Building Completeness**

        The prompt should always be present in the contents.
        """
        contents = flash_service._build_contents(prompt=prompt)

        # Contents should not be empty
        assert len(contents) > 0

        # The prompt should be in the contents (possibly as the last element)
        assert any(prompt in str(c) for c in contents)

    @given(
        prompt=prompt_strategy,
        negative_prompt=st.text(min_size=1, max_size=100),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_negative_prompt_appended(self, flash_service, prompt: str, negative_prompt: str):
        """
        **Feature: service-layer-refactoring, Property 4: Content Building Completeness**

        Negative prompt constraints should be appended when provided.
        """
        contents = flash_service._build_contents(
            prompt=prompt,
            negative_prompt=negative_prompt,
        )

        # The negative prompt should be included in the contents
        contents_str = " ".join(str(c) for c in contents)
        assert negative_prompt in contents_str
        assert "Constraints (avoid)" in contents_str

    @given(
        prompt=prompt_strategy,
        system_instruction=st.text(min_size=1, max_size=100),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_system_instruction_prepended(
        self, flash_service, prompt: str, system_instruction: str
    ):
        """
        **Feature: service-layer-refactoring, Property 4: Content Building Completeness**

        System instruction should be prepended when provided.
        """
        contents = flash_service._build_contents(
            prompt=prompt,
            system_instruction=system_instruction,
        )

        # System instruction should be the first text element
        # (before any image parts are prepended)
        assert len(contents) >= 2
        assert contents[0] == system_instruction

    @given(prompt=prompt_strategy)
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_input_images_included(self, flash_service, prompt: str):
        """
        **Feature: service-layer-refactoring, Property 4: Content Building Completeness**

        Input image parts should be included when provided.
        """
        # Create mock input images
        input_images = [("base64data1", "image/png"), ("base64data2", "image/jpeg")]

        # Mock create_image_parts to return identifiable parts
        mock_parts = [Mock(name="image_part_1"), Mock(name="image_part_2")]
        flash_service.gemini_client.create_image_parts.return_value = mock_parts

        contents = flash_service._build_contents(
            prompt=prompt,
            input_images=input_images,
        )

        # Image parts should be at the beginning of contents
        assert len(contents) >= 3  # 2 image parts + prompt
        assert contents[0] in mock_parts
        assert contents[1] in mock_parts

    @given(
        prompt=prompt_strategy,
        negative_prompt=st.text(min_size=1, max_size=50),
        system_instruction=st.text(min_size=1, max_size=50),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_all_components_combined(
        self,
        flash_service,
        prompt: str,
        negative_prompt: str,
        system_instruction: str,
    ):
        """
        **Feature: service-layer-refactoring, Property 4: Content Building Completeness**

        All components should be properly combined.
        """
        # Mock input images
        input_images = [("base64data", "image/png")]
        mock_parts = [Mock(name="image_part")]
        flash_service.gemini_client.create_image_parts.return_value = mock_parts

        contents = flash_service._build_contents(
            prompt=prompt,
            negative_prompt=negative_prompt,
            system_instruction=system_instruction,
            input_images=input_images,
        )

        # Should have: image_part, system_instruction, enhanced_prompt
        assert len(contents) >= 3

        # Image parts should be first
        assert contents[0] in mock_parts

        # System instruction should follow image parts
        assert contents[1] == system_instruction

        # Prompt with negative constraints should be last
        last_content = str(contents[-1])
        assert prompt in last_content
        assert negative_prompt in last_content


# =============================================================================
# Property 5: Image Output Processing
# =============================================================================


class TestImageOutputProcessing:
    """
    **Feature: service-layer-refactoring, Property 5: Image Output Processing**

    *For any* valid image bytes and metadata, the `_process_image_output()` method SHALL:
    - Return an MCPImage when storage is disabled
    - Store the image and return a thumbnail MCPImage when storage is enabled
    """

    @pytest.fixture
    def flash_service_with_storage(
        self, mock_flash_gemini_client, mock_flash_config, mock_storage_service
    ):
        """Create a FlashImageService with storage enabled."""
        return FlashImageService(
            gemini_client=mock_flash_gemini_client,
            config=mock_flash_config,
            storage_service=mock_storage_service,
        )

    @pytest.fixture
    def flash_service_without_storage(self, mock_flash_gemini_client, mock_flash_config):
        """Create a FlashImageService without storage."""
        return FlashImageService(
            gemini_client=mock_flash_gemini_client,
            config=mock_flash_config,
            storage_service=None,
        )

    def test_returns_mcp_image_without_storage(
        self, flash_service_without_storage, sample_image_bytes
    ):
        """
        **Feature: service-layer-refactoring, Property 5: Image Output Processing**

        Should return an MCPImage when storage is disabled.
        """
        from fastmcp.utilities.types import Image as MCPImage

        metadata = {"prompt": "test", "model": "flash"}

        result = flash_service_without_storage._process_image_output(
            image_bytes=sample_image_bytes,
            metadata=metadata,
            use_storage=False,
        )

        assert isinstance(result, MCPImage)
        # MCPImage has data attribute
        assert result.data is not None

    def test_returns_mcp_image_with_storage_disabled_flag(
        self, flash_service_with_storage, sample_image_bytes
    ):
        """
        **Feature: service-layer-refactoring, Property 5: Image Output Processing**

        Should return an MCPImage when use_storage=False even if storage service exists.
        """
        from fastmcp.utilities.types import Image as MCPImage

        metadata = {"prompt": "test", "model": "flash"}

        result = flash_service_with_storage._process_image_output(
            image_bytes=sample_image_bytes,
            metadata=metadata,
            use_storage=False,
        )

        assert isinstance(result, MCPImage)
        # Storage service should not be called
        flash_service_with_storage.storage_service.store_image.assert_not_called()

    def test_stores_and_returns_thumbnail_with_storage(
        self, flash_service_with_storage, sample_image_bytes
    ):
        """
        **Feature: service-layer-refactoring, Property 5: Image Output Processing**

        Should store the image and return a thumbnail MCPImage when storage is enabled.
        """
        from fastmcp.utilities.types import Image as MCPImage

        metadata = {"prompt": "test", "model": "flash"}

        result = flash_service_with_storage._process_image_output(
            image_bytes=sample_image_bytes,
            metadata=metadata,
            use_storage=True,
        )

        # Storage service should be called
        flash_service_with_storage.storage_service.store_image.assert_called_once()
        flash_service_with_storage.storage_service.get_thumbnail_base64.assert_called_once()

        # Result should be an MCPImage (thumbnail)
        assert isinstance(result, MCPImage)

    @given(prompt=prompt_strategy)
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_metadata_passed_to_storage(
        self, flash_service_with_storage, sample_image_bytes, prompt: str
    ):
        """
        **Feature: service-layer-refactoring, Property 5: Image Output Processing**

        Metadata should be passed to storage service.
        """
        # Reset mock
        flash_service_with_storage.storage_service.store_image.reset_mock()

        metadata = {"prompt": prompt, "model": "flash"}

        flash_service_with_storage._process_image_output(
            image_bytes=sample_image_bytes,
            metadata=metadata,
            use_storage=True,
        )

        # Verify metadata was passed
        call_args = flash_service_with_storage.storage_service.store_image.call_args
        assert call_args is not None
        # Third argument should be metadata
        assert call_args[0][2] == metadata
