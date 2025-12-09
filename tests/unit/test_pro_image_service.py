"""
Property-based tests for ProImageService.

**Feature: service-layer-refactoring**
**Validates: Requirements 3.2, 3.3, 3.4**

This module tests:
- Property 3: Pro Service Behavior Consistency
"""

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
import pytest

from banana_image_mcp.config.settings import MediaResolution, ThinkingLevel
from banana_image_mcp.services.base_image_service import BaseImageService
from banana_image_mcp.services.pro_image_service import ProImageService

# =============================================================================
# Hypothesis Strategies
# =============================================================================

# Strategy for generating prompts
prompt_strategy = st.text(min_size=1, max_size=200)

# Strategy for short prompts (< 50 chars) that trigger enhancement
short_prompt_strategy = st.text(min_size=1, max_size=49)

# Strategy for long prompts (>= 50 chars) that don't trigger enhancement
long_prompt_strategy = st.text(min_size=50, max_size=200)

# Strategy for response/image indices
index_strategy = st.integers(min_value=1, max_value=10)

# Strategy for thinking levels
thinking_level_strategy = st.sampled_from([ThinkingLevel.LOW, ThinkingLevel.HIGH])

# Strategy for media resolutions
media_resolution_strategy = st.sampled_from([MediaResolution.LOW, MediaResolution.HIGH])

# Strategy for resolution strings
resolution_strategy = st.sampled_from(["4k", "high", "2k", "1k"])


# =============================================================================
# Property 3: Pro Service Behavior Consistency
# =============================================================================


class TestProServiceBehaviorConsistency:
    """
    **Feature: service-layer-refactoring, Property 3: Pro Service Behavior Consistency**

    *For any* ProImageService instance and any valid generation parameters:
    - `_build_generation_config()` SHALL include "thinking_level" and "media_resolution" keys
    - `_build_metadata()` SHALL include "model_tier": "pro" and "resolution" key
    - `_enhance_prompt(prompt, resolution)` SHALL return a string containing the original prompt
    """

    @pytest.fixture
    def pro_service(self, mock_pro_gemini_client, mock_pro_config, mock_storage_service):
        """Create a ProImageService for testing."""
        return ProImageService(
            gemini_client=mock_pro_gemini_client,
            config=mock_pro_config,
            storage_service=mock_storage_service,
        )

    def test_pro_service_inherits_from_base(
        self, mock_pro_gemini_client, mock_pro_config, mock_storage_service
    ):
        """ProImageService should inherit from BaseImageService."""
        service = ProImageService(
            gemini_client=mock_pro_gemini_client,
            config=mock_pro_config,
            storage_service=mock_storage_service,
        )

        assert isinstance(service, BaseImageService)
        assert isinstance(service, ProImageService)

    @given(
        thinking_level=thinking_level_strategy,
        media_resolution=media_resolution_strategy,
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_build_generation_config_includes_required_keys(
        self,
        pro_service,
        thinking_level: ThinkingLevel,
        media_resolution: MediaResolution,
    ):
        """
        **Feature: service-layer-refactoring, Property 3: Pro Service Behavior Consistency**

        _build_generation_config() should include thinking_level and media_resolution keys.
        """
        config = pro_service._build_generation_config(
            thinking_level=thinking_level,
            media_resolution=media_resolution,
        )

        assert "thinking_level" in config
        assert config["thinking_level"] == thinking_level.value

        # media_resolution is included when supports_media_resolution is True
        if pro_service.pro_config.supports_media_resolution:
            assert "media_resolution" in config
            assert config["media_resolution"] == media_resolution.value

    def test_build_generation_config_uses_defaults(self, pro_service):
        """
        **Feature: service-layer-refactoring, Property 3: Pro Service Behavior Consistency**

        _build_generation_config() should use defaults when parameters not provided.
        """
        config = pro_service._build_generation_config()

        assert "thinking_level" in config
        assert config["thinking_level"] == pro_service.pro_config.default_thinking_level.value

    @given(
        prompt=prompt_strategy,
        response_index=index_strategy,
        image_index=index_strategy,
        resolution=resolution_strategy,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_build_metadata_includes_required_fields(
        self,
        pro_service,
        prompt: str,
        response_index: int,
        image_index: int,
        resolution: str,
    ):
        """
        **Feature: service-layer-refactoring, Property 3: Pro Service Behavior Consistency**

        _build_metadata() should include model_tier="pro" and resolution key.
        """
        metadata = pro_service._build_metadata(
            prompt=prompt,
            response_index=response_index,
            image_index=image_index,
            resolution=resolution,
        )

        # Required fields
        assert metadata["model_tier"] == "pro"
        assert metadata["resolution"] == resolution
        assert metadata["model"] == pro_service.pro_config.model_name
        assert metadata["synthid_watermark"] is True

        # Passed parameters
        assert metadata["prompt"] == prompt
        assert metadata["response_index"] == response_index
        assert metadata["image_index"] == image_index

    @given(
        prompt=prompt_strategy,
        response_index=index_strategy,
        image_index=index_strategy,
        thinking_level=thinking_level_strategy,
        media_resolution=media_resolution_strategy,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_build_metadata_includes_pro_specific_fields(
        self,
        pro_service,
        prompt: str,
        response_index: int,
        image_index: int,
        thinking_level: ThinkingLevel,
        media_resolution: MediaResolution,
    ):
        """
        **Feature: service-layer-refactoring, Property 3: Pro Service Behavior Consistency**

        _build_metadata() should include Pro-specific fields.
        """
        metadata = pro_service._build_metadata(
            prompt=prompt,
            response_index=response_index,
            image_index=image_index,
            thinking_level=thinking_level,
            media_resolution=media_resolution,
        )

        # Pro-specific fields
        assert "thinking_level" in metadata
        assert metadata["thinking_level"] == thinking_level.value
        assert "media_resolution" in metadata
        assert metadata["media_resolution"] == media_resolution.value
        assert "grounding_enabled" in metadata

    @given(prompt=prompt_strategy)
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_enhance_prompt_contains_original(self, pro_service, prompt: str):
        """
        **Feature: service-layer-refactoring, Property 3: Pro Service Behavior Consistency**

        _enhance_prompt() should return a string containing the original prompt.
        """
        result = pro_service._enhance_prompt(prompt)

        assert prompt in result

    @given(
        prompt=prompt_strategy,
        resolution=resolution_strategy,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_enhance_prompt_with_resolution(
        self, pro_service, prompt: str, resolution: str
    ):
        """
        **Feature: service-layer-refactoring, Property 3: Pro Service Behavior Consistency**

        _enhance_prompt() should handle resolution parameter.
        """
        result = pro_service._enhance_prompt(prompt, resolution=resolution)

        # Original prompt should always be present
        assert prompt in result

    @given(prompt=short_prompt_strategy)
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_enhance_prompt_enhances_short_prompts(self, pro_service, prompt: str):
        """
        **Feature: service-layer-refactoring, Property 3: Pro Service Behavior Consistency**

        Short prompts (< 50 chars) should be enhanced with additional context.
        """
        result = pro_service._enhance_prompt(prompt)

        # Short prompts get enhanced
        assert len(result) > len(prompt)
        assert prompt in result
        assert "high-quality" in result.lower() or "detailed" in result.lower()

    def test_enhance_prompt_adds_4k_hint(self, pro_service):
        """
        **Feature: service-layer-refactoring, Property 3: Pro Service Behavior Consistency**

        4K resolution should add quality hints.
        """
        prompt = "A beautiful landscape with mountains and a lake at sunset"
        result = pro_service._enhance_prompt(prompt, resolution="4k")

        assert prompt in result
        assert "4K" in result

    def test_get_operation_name(self, pro_service):
        """
        **Feature: service-layer-refactoring, Property 3: Pro Service Behavior Consistency**

        _get_operation_name() should return "pro_image_generation".
        """
        result = pro_service._get_operation_name()

        assert result == "pro_image_generation"
