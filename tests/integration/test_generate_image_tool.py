"""
Integration tests for generate_image tool.

Tests the complete flow of image generation and editing with mocked Gemini API.

Requirements: 7.1, 7.2
"""

import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest

from banana_image_mcp.config.settings import (
    FlashImageConfig,
    ModelSelectionConfig,
    ModelTier,
    ProImageConfig,
    ServerConfig,
)
from banana_image_mcp.services.flash_image_service import FlashImageService
from banana_image_mcp.services.gemini_client import GeminiClient
from banana_image_mcp.services.image_storage_service import ImageStorageService
from banana_image_mcp.services.model_selector import ModelSelector
from banana_image_mcp.services.pro_image_service import ProImageService
from banana_image_mcp.tools.generate_image import (
    _build_structured_content,
    _build_summary,
    _collect_input_paths,
    _detect_mode,
    _select_model,
    _validate_inputs,
)


class TestGenerateImageToolIntegration:
    """
    Integration tests for generate_image tool.

    **Feature: service-layer-refactoring, Integration Tests**

    Tests the complete flow from tool invocation through service layer
    to response building.
    """

    @pytest.fixture
    def mock_services(
        self,
        mock_server_config,
        mock_flash_config,
        mock_pro_config,
        mock_storage_service,
        sample_image_bytes,
    ):
        """Set up mock services for integration testing."""
        # Create mock Gemini clients
        flash_client = Mock(spec=GeminiClient)
        pro_client = Mock(spec=GeminiClient)

        # Configure mock responses with image data
        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = sample_image_bytes
        mock_part.inline_data.mime_type = "image/png"
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [mock_part]

        flash_client.generate_content = Mock(return_value=mock_response)
        flash_client.extract_images = Mock(return_value=[sample_image_bytes])
        flash_client.create_image_parts = Mock(return_value=[])

        pro_client.generate_content = Mock(return_value=mock_response)
        pro_client.extract_images = Mock(return_value=[sample_image_bytes])
        pro_client.create_image_parts = Mock(return_value=[])

        # Create services
        flash_service = FlashImageService(
            gemini_client=flash_client,
            config=mock_flash_config,
            storage_service=mock_storage_service,
        )

        pro_service = ProImageService(
            gemini_client=pro_client,
            config=mock_pro_config,
            storage_service=mock_storage_service,
        )

        # Create model selector
        selection_config = ModelSelectionConfig(
            default_tier=ModelTier.AUTO,
            auto_quality_keywords=["4k", "high quality", "detailed"],
            auto_speed_keywords=["fast", "quick", "simple"],
        )

        model_selector = ModelSelector(
            flash_service=flash_service,
            pro_service=pro_service,
            selection_config=selection_config,
        )

        return {
            "flash_service": flash_service,
            "pro_service": pro_service,
            "model_selector": model_selector,
            "flash_client": flash_client,
            "pro_client": pro_client,
            "storage_service": mock_storage_service,
        }

    def test_complete_generation_flow(self, mock_services, mock_stored_image_info):
        """
        Test complete image generation flow.

        **Validates: Requirements 7.1**

        Tests:
        1. Input collection
        2. Input validation
        3. Mode detection
        4. Model selection
        5. Response building
        """
        # Step 1: Collect input paths (no inputs for pure generation)
        input_paths = _collect_input_paths(None, None, None)
        assert input_paths is None

        # Step 2: Validate inputs
        _validate_inputs("generate", input_paths, None)  # Should not raise

        # Step 3: Detect mode
        mode = _detect_mode("auto", None, input_paths)
        assert mode == "generate"

        # Step 4: Model selection (mock the service registry)
        with patch(
            "banana_image_mcp.services.get_model_selector"
        ) as mock_get_selector:
            mock_get_selector.return_value = mock_services["model_selector"]

            import logging

            logger = logging.getLogger(__name__)

            service, tier, model_info = _select_model(
                prompt="A beautiful sunset over the ocean",
                model_tier="flash",
                n=1,
                resolution="high",
                thinking_level="high",
                enable_grounding=False,
                input_paths=None,
                logger=logger,
            )

            assert service is mock_services["flash_service"]
            assert tier == ModelTier.FLASH
            assert "Flash" in model_info["name"]

        # Step 5: Build response
        metadata = [
            {
                "full_path": "/tmp/test/image.png",
                "size_bytes": 102400,
                "width": 1024,
                "height": 768,
                "files_api": {"name": "files/abc123"},
            }
        ]

        summary = _build_summary(
            mode="generate",
            metadata=metadata,
            model_info=model_info,
            selected_tier=tier,
            thinking_level="high",
            resolution="high",
            enable_grounding=False,
            file_id=None,
            input_paths=None,
            aspect_ratio=None,
        )

        assert "Generated" in summary
        assert "1 image" in summary
        assert "Flash" in summary

    def test_complete_edit_flow_with_file_id(self, mock_services):
        """
        Test complete image editing flow with file_id.

        **Validates: Requirements 7.2**

        Tests editing an existing image using Files API ID.
        """
        # Step 1: Collect input paths (none for file_id edit)
        input_paths = _collect_input_paths(None, None, None)
        assert input_paths is None

        # Step 2: Validate inputs
        _validate_inputs("edit", input_paths, "files/abc123")  # Should not raise

        # Step 3: Detect mode
        mode = _detect_mode("auto", "files/abc123", input_paths)
        assert mode == "edit"

        # Step 4: Model selection
        with patch(
            "banana_image_mcp.services.get_model_selector"
        ) as mock_get_selector:
            mock_get_selector.return_value = mock_services["model_selector"]

            import logging

            logger = logging.getLogger(__name__)

            service, tier, model_info = _select_model(
                prompt="Make the sky more blue",
                model_tier="pro",
                n=1,
                resolution="high",
                thinking_level="high",
                enable_grounding=True,
                input_paths=None,
                logger=logger,
            )

            assert service is mock_services["pro_service"]
            assert tier == ModelTier.PRO

        # Step 5: Build response
        metadata = [
            {
                "full_path": "/tmp/test/edited.png",
                "size_bytes": 102400,
                "width": 1024,
                "height": 768,
                "files_api": {"name": "files/xyz789"},
                "parent_file_id": "files/abc123",
            }
        ]

        summary = _build_summary(
            mode="edit",
            metadata=metadata,
            model_info=model_info,
            selected_tier=tier,
            thinking_level="high",
            resolution="high",
            enable_grounding=True,
            file_id="files/abc123",
            input_paths=None,
            aspect_ratio=None,
        )

        assert "Edited" in summary
        assert "files/abc123" in summary

    def test_complete_edit_flow_with_file_path(self, mock_services, sample_image_bytes):
        """
        Test complete image editing flow with local file path.

        **Validates: Requirements 7.2**

        Tests editing an existing image using local file path.
        """
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(sample_image_bytes)
            temp_path = f.name

        try:
            # Step 1: Collect input paths
            input_paths = _collect_input_paths(temp_path, None, None)
            assert input_paths == [temp_path]

            # Step 2: Validate inputs
            _validate_inputs("edit", input_paths, None)  # Should not raise

            # Step 3: Detect mode (single input = edit)
            mode = _detect_mode("auto", None, input_paths)
            assert mode == "edit"

            # Step 4: Model selection
            with patch(
                "banana_image_mcp.services.get_model_selector"
            ) as mock_get_selector:
                mock_get_selector.return_value = mock_services["model_selector"]

                import logging

                logger = logging.getLogger(__name__)

                service, tier, model_info = _select_model(
                    prompt="Add a rainbow to the sky",
                    model_tier="flash",
                    n=1,
                    resolution="high",
                    thinking_level=None,
                    enable_grounding=False,
                    input_paths=input_paths,
                    logger=logger,
                )

                assert service is mock_services["flash_service"]
                assert tier == ModelTier.FLASH

            # Step 5: Build response
            metadata = [
                {
                    "full_path": "/tmp/test/edited.png",
                    "size_bytes": 102400,
                    "width": 1024,
                    "height": 768,
                }
            ]

            summary = _build_summary(
                mode="edit",
                metadata=metadata,
                model_info=model_info,
                selected_tier=tier,
                thinking_level=None,
                resolution="high",
                enable_grounding=False,
                file_id=None,
                input_paths=input_paths,
                aspect_ratio=None,
            )

            assert "Edited" in summary
            assert temp_path in summary

        finally:
            os.unlink(temp_path)

    def test_model_switching_flash_to_pro(self, mock_services):
        """
        Test model switching from Flash to Pro based on parameters.

        **Validates: Requirements 7.1, 7.2**

        Tests that the model selector correctly switches between models.
        """
        with patch(
            "banana_image_mcp.services.get_model_selector"
        ) as mock_get_selector:
            mock_get_selector.return_value = mock_services["model_selector"]

            import logging

            logger = logging.getLogger(__name__)

            # Test 1: Explicit Flash request
            service, tier, _ = _select_model(
                prompt="A simple cat",
                model_tier="flash",
                n=1,
                resolution="high",
                thinking_level="low",
                enable_grounding=False,
                input_paths=None,
                logger=logger,
            )
            assert tier == ModelTier.FLASH
            assert service is mock_services["flash_service"]

            # Test 2: Explicit Pro request
            service, tier, _ = _select_model(
                prompt="A simple cat",
                model_tier="pro",
                n=1,
                resolution="high",
                thinking_level="high",
                enable_grounding=True,
                input_paths=None,
                logger=logger,
            )
            assert tier == ModelTier.PRO
            assert service is mock_services["pro_service"]

            # Test 3: Auto with 4K resolution (should select Pro)
            service, tier, _ = _select_model(
                prompt="A simple cat",
                model_tier="auto",
                n=1,
                resolution="4k",
                thinking_level="high",
                enable_grounding=False,
                input_paths=None,
                logger=logger,
            )
            assert tier == ModelTier.PRO
            assert service is mock_services["pro_service"]

            # Test 4: Auto with quality keywords (should select Pro)
            service, tier, _ = _select_model(
                prompt="A highly detailed 4k portrait",
                model_tier="auto",
                n=1,
                resolution="high",
                thinking_level="high",
                enable_grounding=False,
                input_paths=None,
                logger=logger,
            )
            assert tier == ModelTier.PRO
            assert service is mock_services["pro_service"]

            # Test 5: Auto with speed keywords (should select Flash)
            service, tier, _ = _select_model(
                prompt="A quick simple sketch",
                model_tier="auto",
                n=1,
                resolution="1k",  # Low resolution to favor Flash
                thinking_level="low",
                enable_grounding=False,
                input_paths=None,
                logger=logger,
            )
            assert tier == ModelTier.FLASH
            assert service is mock_services["flash_service"]

    def test_structured_content_generation(self, mock_services):
        """
        Test structured content generation for tool response.

        **Validates: Requirements 7.1**

        Tests that structured content contains all required fields.
        """
        metadata = [
            {
                "full_path": "/tmp/test/image1.png",
                "size_bytes": 102400,
                "width": 1024,
                "height": 768,
                "files_api": {"name": "files/abc123"},
            },
            {
                "full_path": "/tmp/test/image2.png",
                "size_bytes": 204800,
                "width": 1024,
                "height": 768,
                "files_api": {"name": "files/def456"},
            },
        ]

        model_info = {
            "name": "Gemini 2.5 Flash Image",
            "model_id": "gemini-2.5-flash-image",
            "tier": "flash",
            "emoji": "⚡",
        }

        content = _build_structured_content(
            mode="generate",
            metadata=metadata,
            model_info=model_info,
            selected_tier=ModelTier.FLASH,
            tier=ModelTier.AUTO,
            model_tier="auto",
            thinking_level=None,
            resolution="high",
            enable_grounding=False,
            n=2,
            thumbnail_count=2,
            negative_prompt=None,
            input_paths=None,
            file_id=None,
            aspect_ratio="16:9",
            prompt="A beautiful landscape",
        )

        # Verify required fields
        assert content["mode"] == "generate"
        assert content["model_tier"] == "flash"
        assert content["model_name"] == "Gemini 2.5 Flash Image"
        assert content["requested"] == 2
        assert content["returned"] == 2
        assert content["aspect_ratio"] == "16:9"
        assert content["auto_selected"] is True
        assert len(content["file_paths"]) == 2
        assert len(content["files_api_ids"]) == 2

    def test_multi_image_conditioning(self, mock_services, sample_image_bytes):
        """
        Test generation with multiple input images for conditioning.

        **Validates: Requirements 7.1**

        Tests that multiple input images are correctly collected and validated.
        """
        # Create temporary image files
        temp_paths = []
        try:
            for i in range(3):
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    f.write(sample_image_bytes)
                    temp_paths.append(f.name)

            # Step 1: Collect input paths
            input_paths = _collect_input_paths(temp_paths[0], temp_paths[1], temp_paths[2])
            assert input_paths == temp_paths
            assert len(input_paths) == 3

            # Step 2: Validate inputs
            _validate_inputs("generate", input_paths, None)  # Should not raise

            # Step 3: Detect mode (multiple inputs = generate with conditioning)
            mode = _detect_mode("auto", None, input_paths)
            assert mode == "generate"  # Multiple inputs = generate mode

            # Step 4: Build summary with input paths
            metadata = [
                {
                    "full_path": "/tmp/test/output.png",
                    "size_bytes": 102400,
                    "width": 1024,
                    "height": 768,
                }
            ]

            model_info = {
                "name": "Gemini 2.5 Flash Image",
                "model_id": "gemini-2.5-flash-image",
                "tier": "flash",
                "emoji": "⚡",
            }

            summary = _build_summary(
                mode="generate",
                metadata=metadata,
                model_info=model_info,
                selected_tier=ModelTier.FLASH,
                thinking_level=None,
                resolution="high",
                enable_grounding=False,
                file_id=None,
                input_paths=input_paths,
                aspect_ratio=None,
            )

            assert "Generated" in summary
            assert "3 input image" in summary

        finally:
            for path in temp_paths:
                os.unlink(path)

    def test_error_handling_invalid_mode(self):
        """
        Test error handling for invalid mode.

        **Validates: Requirements 7.1**
        """
        from banana_image_mcp.core.exceptions import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            _validate_inputs("invalid_mode", None, None)

        assert "mode" in str(exc_info.value).lower()

    def test_error_handling_nonexistent_path(self):
        """
        Test error handling for non-existent file path.

        **Validates: Requirements 7.2**
        """
        from banana_image_mcp.core.exceptions import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            _validate_inputs("edit", ["/nonexistent/path/image.png"], None)

        assert "not found" in str(exc_info.value).lower()
