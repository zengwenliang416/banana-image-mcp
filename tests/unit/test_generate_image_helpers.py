"""
Property-based tests for generate_image helper functions.

**Feature: service-layer-refactoring**
**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.6**

This module tests:
- Property 6: Input Path Collection
- Property 7: Input Validation
- Property 8: Mode Detection
- Property 9: Model Selection (partial - requires service mocking)
- Property 10: Response Building
"""

import os
import tempfile

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
import pytest

from banana_image_mcp.config.settings import ModelTier
from banana_image_mcp.core.exceptions import ValidationError
from banana_image_mcp.tools.generate_image import (
    _build_structured_content,
    _build_summary,
    _collect_input_paths,
    _detect_mode,
    _validate_inputs,
)

# =============================================================================
# Hypothesis Strategies
# =============================================================================

# Strategy for generating file paths (non-empty strings)
path_strategy = st.text(
    min_size=1,
    max_size=100,
    alphabet=st.characters(whitelist_categories=("L", "N", "Pc"), whitelist_characters="/-_."),
)

# Strategy for optional paths
optional_path_strategy = st.one_of(st.none(), path_strategy)

# Strategy for mode values
mode_strategy = st.sampled_from(["auto", "generate", "edit"])

# Strategy for invalid mode values
invalid_mode_strategy = st.text(min_size=1, max_size=20).filter(
    lambda x: x not in ["auto", "generate", "edit"]
)

# Strategy for file IDs
file_id_strategy = st.one_of(
    st.none(),
    st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
)


# =============================================================================
# Property 6: Input Path Collection
# =============================================================================


class TestInputPathCollection:
    """
    **Feature: service-layer-refactoring, Property 6: Input Path Collection**

    *For any* combination of three optional path strings, `_collect_input_paths()`
    SHALL return a list containing only the non-None values, or None if all inputs are None.
    """

    @given(
        path1=optional_path_strategy,
        path2=optional_path_strategy,
        path3=optional_path_strategy,
    )
    @settings(max_examples=100)
    def test_collects_non_none_paths(
        self,
        path1: str | None,
        path2: str | None,
        path3: str | None,
    ):
        """
        **Feature: service-layer-refactoring, Property 6: Input Path Collection**

        Should return list of non-None paths.
        """
        result = _collect_input_paths(path1, path2, path3)

        # Count non-None inputs
        non_none_inputs = [p for p in [path1, path2, path3] if p]

        if non_none_inputs:
            assert result is not None
            assert len(result) == len(non_none_inputs)
            for p in non_none_inputs:
                assert p in result
        else:
            assert result is None

    def test_all_none_returns_none(self):
        """
        **Feature: service-layer-refactoring, Property 6: Input Path Collection**

        Should return None when all inputs are None.
        """
        result = _collect_input_paths(None, None, None)
        assert result is None

    def test_single_path_returns_list(self):
        """
        **Feature: service-layer-refactoring, Property 6: Input Path Collection**

        Should return list with single path.
        """
        result = _collect_input_paths("/path/to/image.png", None, None)
        assert result == ["/path/to/image.png"]

    def test_preserves_order(self):
        """
        **Feature: service-layer-refactoring, Property 6: Input Path Collection**

        Should preserve order of paths.
        """
        result = _collect_input_paths("/first.png", "/second.png", "/third.png")
        assert result == ["/first.png", "/second.png", "/third.png"]


# =============================================================================
# Property 7: Input Validation
# =============================================================================


class TestInputValidation:
    """
    **Feature: service-layer-refactoring, Property 7: Input Validation**

    *For any* mode, input_paths, and file_id combination:
    - Invalid mode values SHALL raise ValidationError
    - Non-existent paths SHALL raise ValidationError
    - Exceeding MAX_INPUT_IMAGES SHALL raise ValidationError
    - Valid inputs SHALL not raise any exception
    """

    @given(mode=invalid_mode_strategy)
    @settings(max_examples=50)
    def test_invalid_mode_raises_error(self, mode: str):
        """
        **Feature: service-layer-refactoring, Property 7: Input Validation**

        Invalid mode values should raise ValidationError.
        """
        with pytest.raises(ValidationError) as exc_info:
            _validate_inputs(mode, None, None)

        assert "mode" in str(exc_info.value).lower() or exc_info.value.field == "mode"

    @given(mode=mode_strategy)
    @settings(max_examples=50)
    def test_valid_mode_no_error(self, mode: str):
        """
        **Feature: service-layer-refactoring, Property 7: Input Validation**

        Valid mode values should not raise error.
        """
        # Should not raise
        _validate_inputs(mode, None, None)

    def test_nonexistent_path_raises_error(self):
        """
        **Feature: service-layer-refactoring, Property 7: Input Validation**

        Non-existent paths should raise ValidationError.
        """
        with pytest.raises(ValidationError) as exc_info:
            _validate_inputs("auto", ["/nonexistent/path/image.png"], None)

        assert "not found" in str(exc_info.value).lower()

    def test_exceeding_max_images_raises_error(self):
        """
        **Feature: service-layer-refactoring, Property 7: Input Validation**

        Exceeding MAX_INPUT_IMAGES should raise ValidationError.
        """
        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = []
            for i in range(10):  # More than MAX_INPUT_IMAGES (3)
                path = os.path.join(tmpdir, f"image_{i}.png")
                with open(path, "wb") as f:
                    f.write(b"fake image data")
                paths.append(path)

            with pytest.raises(ValidationError) as exc_info:
                _validate_inputs("auto", paths, None)

            assert "maximum" in str(exc_info.value).lower()

    def test_valid_existing_paths_no_error(self):
        """
        **Feature: service-layer-refactoring, Property 7: Input Validation**

        Valid existing paths should not raise error.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_image.png")
            with open(path, "wb") as f:
                f.write(b"fake image data")

            # Should not raise
            _validate_inputs("auto", [path], None)


# =============================================================================
# Property 8: Mode Detection
# =============================================================================


class TestModeDetection:
    """
    **Feature: service-layer-refactoring, Property 8: Mode Detection**

    *For any* mode, file_id, and input_paths combination:
    - When mode is "auto" and file_id is provided, detected mode SHALL be "edit"
    - When mode is "auto" and single input_path is provided, detected mode SHALL be "edit"
    - When mode is "auto" and no file_id and multiple/no input_paths, detected mode SHALL be "generate"
    - When mode is explicit ("edit" or "generate"), detected mode SHALL match
    """

    @given(file_id=st.text(min_size=5, max_size=20))
    @settings(max_examples=50)
    def test_auto_with_file_id_returns_edit(self, file_id: str):
        """
        **Feature: service-layer-refactoring, Property 8: Mode Detection**

        Auto mode with file_id should return "edit".
        """
        result = _detect_mode("auto", file_id, None)
        assert result == "edit"

    def test_auto_with_single_path_returns_edit(self):
        """
        **Feature: service-layer-refactoring, Property 8: Mode Detection**

        Auto mode with single input path should return "edit".
        """
        result = _detect_mode("auto", None, ["/path/to/image.png"])
        assert result == "edit"

    def test_auto_with_no_inputs_returns_generate(self):
        """
        **Feature: service-layer-refactoring, Property 8: Mode Detection**

        Auto mode with no inputs should return "generate".
        """
        result = _detect_mode("auto", None, None)
        assert result == "generate"

    def test_auto_with_multiple_paths_returns_generate(self):
        """
        **Feature: service-layer-refactoring, Property 8: Mode Detection**

        Auto mode with multiple input paths should return "generate".
        """
        result = _detect_mode("auto", None, ["/path1.png", "/path2.png"])
        assert result == "generate"

    @given(mode=st.sampled_from(["edit", "generate"]))
    @settings(max_examples=50)
    def test_explicit_mode_returns_same(self, mode: str):
        """
        **Feature: service-layer-refactoring, Property 8: Mode Detection**

        Explicit mode should return the same mode.
        """
        result = _detect_mode(mode, None, None)
        assert result == mode

    @given(
        mode=st.sampled_from(["edit", "generate"]),
        file_id=file_id_strategy,
    )
    @settings(max_examples=50)
    def test_explicit_mode_ignores_inputs(self, mode: str, file_id: str | None):
        """
        **Feature: service-layer-refactoring, Property 8: Mode Detection**

        Explicit mode should ignore file_id and input_paths.
        """
        result = _detect_mode(mode, file_id, ["/some/path.png"])
        assert result == mode


# =============================================================================
# Property 10: Response Building
# =============================================================================


class TestResponseBuilding:
    """
    **Feature: service-layer-refactoring, Property 10: Response Building**

    *For any* valid metadata list and model info, `_build_response()` SHALL return
    a ToolResult containing:
    - TextContent with summary
    - Thumbnail images
    - structured_content with mode, model_tier, and images fields
    """

    @pytest.fixture
    def sample_metadata(self):
        """Sample metadata for testing."""
        return [
            {
                "full_path": "/tmp/image_001.png",
                "size_bytes": 1024 * 100,
                "width": 1024,
                "height": 768,
                "files_api": {"name": "files/abc123"},
            }
        ]

    @pytest.fixture
    def sample_model_info(self):
        """Sample model info for testing."""
        return {
            "name": "Gemini Flash",
            "emoji": "⚡",
            "model_id": "gemini-2.5-flash-image",
        }

    def test_build_summary_contains_required_info(self, sample_metadata, sample_model_info):
        """
        **Feature: service-layer-refactoring, Property 10: Response Building**

        Summary should contain required information.
        """
        summary = _build_summary(
            mode="generate",
            metadata=sample_metadata,
            model_info=sample_model_info,
            selected_tier=ModelTier.FLASH,
            thinking_level="high",
            resolution="high",
            enable_grounding=False,
            file_id=None,
            input_paths=None,
            aspect_ratio=None,
        )

        # Should contain key information
        assert "Generated" in summary
        assert "1 image" in summary
        assert "Gemini Flash" in summary
        assert "FLASH" in summary

    def test_build_summary_edit_mode(self, sample_metadata, sample_model_info):
        """
        **Feature: service-layer-refactoring, Property 10: Response Building**

        Summary should reflect edit mode.
        """
        summary = _build_summary(
            mode="edit",
            metadata=sample_metadata,
            model_info=sample_model_info,
            selected_tier=ModelTier.FLASH,
            thinking_level="high",
            resolution="high",
            enable_grounding=False,
            file_id="files/abc123",
            input_paths=None,
            aspect_ratio=None,
        )

        assert "Edited" in summary
        assert "files/abc123" in summary

    def test_build_structured_content_contains_required_fields(
        self, sample_metadata, sample_model_info
    ):
        """
        **Feature: service-layer-refactoring, Property 10: Response Building**

        Structured content should contain required fields.
        """
        content = _build_structured_content(
            mode="generate",
            metadata=sample_metadata,
            model_info=sample_model_info,
            selected_tier=ModelTier.FLASH,
            tier=ModelTier.AUTO,
            model_tier="auto",
            thinking_level="high",
            resolution="high",
            enable_grounding=False,
            n=1,
            thumbnail_count=1,
            negative_prompt=None,
            input_paths=None,
            file_id=None,
            aspect_ratio=None,
            prompt="test prompt",
        )

        # Required fields
        assert content["mode"] == "generate"
        assert content["model_tier"] == "flash"
        assert "images" in content
        assert content["images"] == sample_metadata

    @given(mode=st.sampled_from(["generate", "edit"]))
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_build_structured_content_mode_specific_fields(
        self, sample_metadata, sample_model_info, mode: str
    ):
        """
        **Feature: service-layer-refactoring, Property 10: Response Building**

        Structured content should have mode-specific fields.
        """
        content = _build_structured_content(
            mode=mode,
            metadata=sample_metadata,
            model_info=sample_model_info,
            selected_tier=ModelTier.FLASH,
            tier=ModelTier.AUTO,
            model_tier="auto",
            thinking_level="high",
            resolution="high",
            enable_grounding=False,
            n=1,
            thumbnail_count=1,
            negative_prompt=None,
            input_paths=None,
            file_id=None,
            aspect_ratio=None,
            prompt="test prompt",
        )

        if mode == "edit":
            assert content["edit_instruction"] == "test prompt"
            assert content["generation_prompt"] is None
        else:
            assert content["generation_prompt"] == "test prompt"
            assert content["edit_instruction"] is None
