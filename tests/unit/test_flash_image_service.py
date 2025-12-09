"""
Property-based tests for FlashImageService.

**Feature: service-layer-refactoring**
**Validates: Requirements 1.1, 2.1, 2.2, 2.3, 2.4**

This module tests:
- Property 1: Service Initialization and Inheritance
- Property 2: Flash Service Behavior Consistency
"""

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
import pytest

from banana_image_mcp.services.base_image_service import BaseImageService
from banana_image_mcp.services.flash_image_service import FlashImageService

# =============================================================================
# Hypothesis Strategies
# =============================================================================

# Strategy for generating prompts
prompt_strategy = st.text(min_size=1, max_size=200)

# Strategy for generating response/image indices
index_strategy = st.integers(min_value=1, max_value=10)

# Strategy for aspect ratios
aspect_ratio_strategy = st.one_of(
    st.none(),
    st.sampled_from(["1:1", "16:9", "9:16", "4:3", "3:4"]),
)


# =============================================================================
# Property 1: Service Initialization and Inheritance
# =============================================================================


class TestServiceInitializationAndInheritance:
    """
    **Feature: service-layer-refactoring, Property 1: Service Initialization and Inheritance**

    *For any* image service (FlashImageService or ProImageService), when instantiated
    with valid dependencies, the service SHALL be an instance of BaseImageService
    and have all required attributes (gemini_client, config, storage_service, logger)
    properly set.
    """

    def test_flash_service_inherits_from_base(
        self, mock_flash_gemini_client, mock_flash_config, mock_storage_service
    ):
        """
        **Feature: service-layer-refactoring, Property 1: Service Initialization and Inheritance**

        FlashImageService should inherit from BaseImageService.
        """
        service = FlashImageService(
            gemini_client=mock_flash_gemini_client,
            config=mock_flash_config,
            storage_service=mock_storage_service,
        )

        assert isinstance(service, BaseImageService)
        assert isinstance(service, FlashImageService)

    def test_flash_service_has_required_attributes(
        self, mock_flash_gemini_client, mock_flash_config, mock_storage_service
    ):
        """
        **Feature: service-layer-refactoring, Property 1: Service Initialization and Inheritance**

        FlashImageService should have all required attributes properly set.
        """
        service = FlashImageService(
            gemini_client=mock_flash_gemini_client,
            config=mock_flash_config,
            storage_service=mock_storage_service,
        )

        # Check required attributes from BaseImageService
        assert service.gemini_client is mock_flash_gemini_client
        assert service.config is mock_flash_config
        assert service.storage_service is mock_storage_service
        assert service.logger is not None

        # Check FlashImageService-specific attribute
        assert service.flash_config is mock_flash_config

    def test_flash_service_without_storage(
        self, mock_flash_gemini_client, mock_flash_config
    ):
        """
        **Feature: service-layer-refactoring, Property 1: Service Initialization and Inheritance**

        FlashImageService should work without storage service.
        """
        service = FlashImageService(
            gemini_client=mock_flash_gemini_client,
            config=mock_flash_config,
            storage_service=None,
        )

        assert isinstance(service, BaseImageService)
        assert service.storage_service is None


# =============================================================================
# Property 2: Flash Service Behavior Consistency
# =============================================================================


class TestFlashServiceBehaviorConsistency:
    """
    **Feature: service-layer-refactoring, Property 2: Flash Service Behavior Consistency**

    *For any* FlashImageService instance and any valid generation parameters:
    - `_build_generation_config()` SHALL return an empty dictionary
    - `_build_metadata()` SHALL include "model_tier": "flash" and "model": "gemini-2.5-flash-image"
    - `_enhance_prompt(prompt)` SHALL return the original prompt unchanged
    """

    @pytest.fixture
    def flash_service(self, mock_flash_gemini_client, mock_flash_config, mock_storage_service):
        """Create a FlashImageService for testing."""
        return FlashImageService(
            gemini_client=mock_flash_gemini_client,
            config=mock_flash_config,
            storage_service=mock_storage_service,
        )

    def test_build_generation_config_returns_empty_dict(self, flash_service):
        """
        **Feature: service-layer-refactoring, Property 2: Flash Service Behavior Consistency**

        _build_generation_config() should return an empty dictionary.
        """
        result = flash_service._build_generation_config()

        assert result == {}
        assert isinstance(result, dict)

    @given(
        prompt=prompt_strategy,
        response_index=index_strategy,
        image_index=index_strategy,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_build_metadata_includes_required_fields(
        self,
        flash_service,
        prompt: str,
        response_index: int,
        image_index: int,
    ):
        """
        **Feature: service-layer-refactoring, Property 2: Flash Service Behavior Consistency**

        _build_metadata() should include model_tier="flash" and model="gemini-2.5-flash-image".
        """
        metadata = flash_service._build_metadata(
            prompt=prompt,
            response_index=response_index,
            image_index=image_index,
        )

        # Required fields
        assert metadata["model_tier"] == "flash"
        assert metadata["model"] == "gemini-2.5-flash-image"
        assert metadata["synthid_watermark"] is True

        # Passed parameters
        assert metadata["prompt"] == prompt
        assert metadata["response_index"] == response_index
        assert metadata["image_index"] == image_index

    @given(
        prompt=prompt_strategy,
        response_index=index_strategy,
        image_index=index_strategy,
        aspect_ratio=aspect_ratio_strategy,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_build_metadata_with_optional_fields(
        self,
        flash_service,
        prompt: str,
        response_index: int,
        image_index: int,
        aspect_ratio: str | None,
    ):
        """
        **Feature: service-layer-refactoring, Property 2: Flash Service Behavior Consistency**

        _build_metadata() should include optional fields when provided.
        """
        metadata = flash_service._build_metadata(
            prompt=prompt,
            response_index=response_index,
            image_index=image_index,
            aspect_ratio=aspect_ratio,
            negative_prompt="avoid blur",
            system_instruction="be creative",
        )

        # Optional fields should be included
        assert metadata["aspect_ratio"] == aspect_ratio
        assert metadata["negative_prompt"] == "avoid blur"
        assert metadata["system_instruction"] == "be creative"

    @given(prompt=prompt_strategy)
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_enhance_prompt_returns_unchanged(self, flash_service, prompt: str):
        """
        **Feature: service-layer-refactoring, Property 2: Flash Service Behavior Consistency**

        _enhance_prompt() should return the original prompt unchanged.
        """
        result = flash_service._enhance_prompt(prompt)

        assert result == prompt

    @given(prompt=prompt_strategy)
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_enhance_prompt_ignores_kwargs(self, flash_service, prompt: str):
        """
        **Feature: service-layer-refactoring, Property 2: Flash Service Behavior Consistency**

        _enhance_prompt() should ignore any kwargs and return original prompt.
        """
        result = flash_service._enhance_prompt(
            prompt,
            resolution="4k",
            extra_param="ignored",
        )

        assert result == prompt

    def test_get_operation_name(self, flash_service):
        """
        **Feature: service-layer-refactoring, Property 2: Flash Service Behavior Consistency**

        _get_operation_name() should return "flash_image_generation".
        """
        result = flash_service._get_operation_name()

        assert result == "flash_image_generation"
