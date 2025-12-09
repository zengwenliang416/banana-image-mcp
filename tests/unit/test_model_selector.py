"""
Property-based tests for ModelSelector.

**Feature: service-layer-refactoring**
**Validates: Requirements 8.3**

This module tests:
- Property 9: Model Selection
"""

from unittest.mock import Mock

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
import pytest

from banana_image_mcp.config.settings import ModelSelectionConfig, ModelTier
from banana_image_mcp.services.base_image_service import BaseImageService
from banana_image_mcp.services.model_selector import ModelSelector

# =============================================================================
# Hypothesis Strategies
# =============================================================================

# Strategy for generating prompts
prompt_strategy = st.text(min_size=1, max_size=200)

# Strategy for model tiers
model_tier_strategy = st.sampled_from([ModelTier.FLASH, ModelTier.PRO, ModelTier.AUTO, None])


# =============================================================================
# Property 9: Model Selection
# =============================================================================


class TestModelSelection:
    """
    **Feature: service-layer-refactoring, Property 9: Model Selection**

    *For any* prompt and model tier request:
    - Explicit FLASH request SHALL return FlashImageService
    - Explicit PRO request SHALL return ProImageService
    - AUTO request SHALL return a service based on prompt analysis
    - The returned service SHALL be an instance of BaseImageService
    """

    @pytest.fixture
    def mock_flash_service(self):
        """Create a mock Flash service."""
        service = Mock(spec=BaseImageService)
        service.name = "flash"
        return service

    @pytest.fixture
    def mock_pro_service(self):
        """Create a mock Pro service."""
        service = Mock(spec=BaseImageService)
        service.name = "pro"
        return service

    @pytest.fixture
    def selection_config(self):
        """Create a selection config."""
        return ModelSelectionConfig(
            default_tier=ModelTier.FLASH,
            auto_quality_keywords=["professional", "high-quality", "detailed", "4k"],
            auto_speed_keywords=["quick", "fast", "draft", "prototype"],
        )

    @pytest.fixture
    def model_selector(self, mock_flash_service, mock_pro_service, selection_config):
        """Create a ModelSelector for testing."""
        return ModelSelector(
            flash_service=mock_flash_service,
            pro_service=mock_pro_service,
            selection_config=selection_config,
        )

    @given(prompt=prompt_strategy)
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_explicit_flash_returns_flash_service(
        self, model_selector, mock_flash_service, prompt: str
    ):
        """
        **Feature: service-layer-refactoring, Property 9: Model Selection**

        Explicit FLASH request should return Flash service.
        """
        service, tier = model_selector.select_model(
            prompt=prompt,
            requested_tier=ModelTier.FLASH,
        )

        assert service is mock_flash_service
        assert tier == ModelTier.FLASH

    @given(prompt=prompt_strategy)
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_explicit_pro_returns_pro_service(self, model_selector, mock_pro_service, prompt: str):
        """
        **Feature: service-layer-refactoring, Property 9: Model Selection**

        Explicit PRO request should return Pro service.
        """
        service, tier = model_selector.select_model(
            prompt=prompt,
            requested_tier=ModelTier.PRO,
        )

        assert service is mock_pro_service
        assert tier == ModelTier.PRO

    @given(prompt=prompt_strategy)
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_auto_returns_valid_service(
        self, model_selector, mock_flash_service, mock_pro_service, prompt: str
    ):
        """
        **Feature: service-layer-refactoring, Property 9: Model Selection**

        AUTO request should return a valid service.
        """
        service, tier = model_selector.select_model(
            prompt=prompt,
            requested_tier=ModelTier.AUTO,
        )

        # Should return one of the services
        assert service in [mock_flash_service, mock_pro_service]
        assert tier in [ModelTier.FLASH, ModelTier.PRO]

    @given(prompt=prompt_strategy)
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_none_tier_returns_valid_service(
        self, model_selector, mock_flash_service, mock_pro_service, prompt: str
    ):
        """
        **Feature: service-layer-refactoring, Property 9: Model Selection**

        None tier should behave like AUTO.
        """
        service, tier = model_selector.select_model(
            prompt=prompt,
            requested_tier=None,
        )

        # Should return one of the services
        assert service in [mock_flash_service, mock_pro_service]
        assert tier in [ModelTier.FLASH, ModelTier.PRO]

    def test_quality_keywords_favor_pro(self, model_selector, mock_pro_service):
        """
        **Feature: service-layer-refactoring, Property 9: Model Selection**

        Quality keywords should favor Pro model.
        """
        prompt = "Create a professional high-quality 4k image"
        service, tier = model_selector.select_model(
            prompt=prompt,
            requested_tier=ModelTier.AUTO,
        )

        assert service is mock_pro_service
        assert tier == ModelTier.PRO

    def test_speed_keywords_favor_flash(self, model_selector, mock_flash_service):
        """
        **Feature: service-layer-refactoring, Property 9: Model Selection**

        Speed keywords should favor Flash model.
        """
        prompt = "quick draft prototype image"
        service, tier = model_selector.select_model(
            prompt=prompt,
            requested_tier=ModelTier.AUTO,
        )

        assert service is mock_flash_service
        assert tier == ModelTier.FLASH

    def test_4k_resolution_requires_pro(self, model_selector, mock_pro_service):
        """
        **Feature: service-layer-refactoring, Property 9: Model Selection**

        4K resolution should require Pro model.
        """
        service, tier = model_selector.select_model(
            prompt="simple image",
            requested_tier=ModelTier.AUTO,
            resolution="4k",
        )

        assert service is mock_pro_service
        assert tier == ModelTier.PRO

    def test_grounding_favors_pro(self, model_selector, mock_pro_service):
        """
        **Feature: service-layer-refactoring, Property 9: Model Selection**

        Grounding should favor Pro model.
        """
        service, tier = model_selector.select_model(
            prompt="simple image",
            requested_tier=ModelTier.AUTO,
            enable_grounding=True,
        )

        assert service is mock_pro_service
        assert tier == ModelTier.PRO

    def test_get_model_info_flash(self, model_selector):
        """
        **Feature: service-layer-refactoring, Property 9: Model Selection**

        get_model_info should return Flash info.
        """
        info = model_selector.get_model_info(ModelTier.FLASH)

        assert info["tier"] == "flash"
        assert "Flash" in info["name"]
        assert info["emoji"] == "⚡"

    def test_get_model_info_pro(self, model_selector):
        """
        **Feature: service-layer-refactoring, Property 9: Model Selection**

        get_model_info should return Pro info.
        """
        info = model_selector.get_model_info(ModelTier.PRO)

        assert info["tier"] == "pro"
        assert "Pro" in info["name"]
        assert info["emoji"] == "🏆"
