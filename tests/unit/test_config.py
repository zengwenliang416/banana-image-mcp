"""
Property-based tests for configuration loading.

**Feature: service-layer-refactoring**
**Validates: Requirements 9.3**

This module tests:
- Property 13: Configuration Loading
"""

import os
from unittest.mock import patch

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
import pytest

from banana_image_mcp.config.settings import (
    BaseModelConfig,
    FlashImageConfig,
    ModelSelectionConfig,
    ModelTier,
    ProImageConfig,
    ServerConfig,
)

# =============================================================================
# Property 13: Configuration Loading
# =============================================================================


class TestConfigurationLoading:
    """
    **Feature: service-layer-refactoring, Property 13: Configuration Loading**

    *For any* environment state, `ServerConfig.from_env()` SHALL either:
    - Return a valid ServerConfig when GEMINI_API_KEY or GOOGLE_API_KEY is set
    - Raise ValueError when neither API key is set
    """

    def test_from_env_with_gemini_api_key(self, tmp_path):
        """
        **Feature: service-layer-refactoring, Property 13: Configuration Loading**

        Should return valid config when GEMINI_API_KEY is set.
        """
        with patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "test-api-key-12345",
                "IMAGE_OUTPUT_DIR": str(tmp_path),
            },
            clear=False,
        ):
            config = ServerConfig.from_env()

            assert config.gemini_api_key == "test-api-key-12345"
            assert config.server_name == "banana-image-mcp"

    def test_from_env_with_google_api_key(self, tmp_path):
        """
        **Feature: service-layer-refactoring, Property 13: Configuration Loading**

        Should return valid config when GOOGLE_API_KEY is set.
        """
        with patch.dict(
            os.environ,
            {
                "GOOGLE_API_KEY": "google-api-key-67890",
                "IMAGE_OUTPUT_DIR": str(tmp_path),
            },
            clear=False,
        ):
            # Remove GEMINI_API_KEY if present
            env = os.environ.copy()
            env.pop("GEMINI_API_KEY", None)

            with patch.dict(os.environ, env, clear=True):
                os.environ["GOOGLE_API_KEY"] = "google-api-key-67890"
                os.environ["IMAGE_OUTPUT_DIR"] = str(tmp_path)

                config = ServerConfig.from_env()

                assert config.gemini_api_key == "google-api-key-67890"

    def test_from_env_without_api_key_raises_error(self, tmp_path):
        """
        **Feature: service-layer-refactoring, Property 13: Configuration Loading**

        Should raise ValueError when neither API key is set.
        """
        with patch.dict(
            os.environ,
            {
                "IMAGE_OUTPUT_DIR": str(tmp_path),
            },
            clear=True,
        ):
            with pytest.raises(ValueError) as exc_info:
                ServerConfig.from_env()

            assert "GEMINI_API_KEY" in str(exc_info.value)
            assert "GOOGLE_API_KEY" in str(exc_info.value)

    def test_from_env_creates_output_directory(self, tmp_path):
        """
        **Feature: service-layer-refactoring, Property 13: Configuration Loading**

        Should create output directory if it doesn't exist.
        """
        output_dir = tmp_path / "new_output_dir"
        assert not output_dir.exists()

        with patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "test-key",
                "IMAGE_OUTPUT_DIR": str(output_dir),
            },
            clear=False,
        ):
            config = ServerConfig.from_env()

            assert output_dir.exists()
            assert config.image_output_dir == str(output_dir)

    @given(
        transport=st.sampled_from(["stdio", "http"]),
        port=st.integers(min_value=1024, max_value=65535),
    )
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_from_env_respects_transport_settings(self, tmp_path, transport: str, port: int):
        """
        **Feature: service-layer-refactoring, Property 13: Configuration Loading**

        Should respect transport and port settings from environment.
        """
        with patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "test-key",
                "IMAGE_OUTPUT_DIR": str(tmp_path),
                "FASTMCP_TRANSPORT": transport,
                "FASTMCP_PORT": str(port),
            },
            clear=False,
        ):
            config = ServerConfig.from_env()

            assert config.transport == transport
            assert config.port == port


class TestBaseModelConfigInheritance:
    """Test that model configs properly inherit from BaseModelConfig."""

    def test_flash_config_inherits_base_fields(self):
        """
        **Feature: service-layer-refactoring, Property 13: Configuration Loading**

        FlashImageConfig should inherit BaseModelConfig fields.
        """
        config = FlashImageConfig()

        # Base fields
        assert config.max_images_per_request == 4
        assert config.max_inline_image_size == 20 * 1024 * 1024
        assert config.default_image_format == "png"
        assert config.request_timeout == 60

        # Flash-specific fields
        assert config.model_name == "gemini-2.5-flash-image"
        assert config.max_resolution == 1024
        assert config.supports_thinking is False

    def test_pro_config_inherits_base_fields(self):
        """
        **Feature: service-layer-refactoring, Property 13: Configuration Loading**

        ProImageConfig should inherit BaseModelConfig fields.
        """
        config = ProImageConfig()

        # Base fields (with Pro override for timeout)
        assert config.max_images_per_request == 4
        assert config.max_inline_image_size == 20 * 1024 * 1024
        assert config.default_image_format == "png"
        assert config.request_timeout == 90  # Pro has longer timeout

        # Pro-specific fields
        assert config.model_name == "gemini-3-pro-image-preview"
        assert config.max_resolution == 3840
        assert config.supports_thinking is True

    def test_flash_config_is_instance_of_base(self):
        """FlashImageConfig should be instance of BaseModelConfig."""
        config = FlashImageConfig()
        assert isinstance(config, BaseModelConfig)

    def test_pro_config_is_instance_of_base(self):
        """ProImageConfig should be instance of BaseModelConfig."""
        config = ProImageConfig()
        assert isinstance(config, BaseModelConfig)


class TestModelSelectionConfigLoading:
    """Test ModelSelectionConfig loading from environment."""

    def test_from_env_default_tier(self):
        """
        **Feature: service-layer-refactoring, Property 13: Configuration Loading**

        Should use AUTO tier by default.
        """
        with patch.dict(os.environ, {}, clear=True):
            config = ModelSelectionConfig.from_env()

            assert config.default_tier == ModelTier.AUTO

    @given(tier=st.sampled_from(["flash", "pro", "auto"]))
    @settings(max_examples=10)
    def test_from_env_respects_model_tier(self, tier: str):
        """
        **Feature: service-layer-refactoring, Property 13: Configuration Loading**

        Should respect NANOBANANA_MODEL environment variable.
        """
        with patch.dict(os.environ, {"NANOBANANA_MODEL": tier}, clear=True):
            config = ModelSelectionConfig.from_env()

            assert config.default_tier == ModelTier(tier)

    def test_from_env_invalid_tier_defaults_to_auto(self):
        """
        **Feature: service-layer-refactoring, Property 13: Configuration Loading**

        Should default to AUTO for invalid tier values.
        """
        with patch.dict(os.environ, {"NANOBANANA_MODEL": "invalid"}, clear=True):
            config = ModelSelectionConfig.from_env()

            assert config.default_tier == ModelTier.AUTO

    def test_default_keywords_present(self):
        """
        **Feature: service-layer-refactoring, Property 13: Configuration Loading**

        Should have default quality and speed keywords.
        """
        config = ModelSelectionConfig()

        assert len(config.auto_quality_keywords) > 0
        assert len(config.auto_speed_keywords) > 0
        assert "4k" in config.auto_quality_keywords
        assert "quick" in config.auto_speed_keywords
