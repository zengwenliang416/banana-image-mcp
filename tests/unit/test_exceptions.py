"""
Property-based tests for exception classes.

**Feature: service-layer-refactoring**
**Validates: Requirements 5.2, 5.3, 5.4, 5.5**

This module tests:
- Property 11: Exception Serialization Round-Trip
- Property 12: ValidationError Context Population
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from banana_image_mcp.core.exceptions import (
    ConfigurationError,
    ErrorCode,
    FileOperationError,
    GeminiAPIError,
    ImageProcessingError,
    NanoBananaError,
    ValidationError,
)

# =============================================================================
# Hypothesis Strategies
# =============================================================================

# Strategy for generating error codes
error_code_strategy = st.sampled_from(list(ErrorCode))

# Strategy for generating context dictionaries
context_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N"))),
    values=st.one_of(
        st.text(max_size=50),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.none(),
    ),
    max_size=5,
)

# Strategy for generating error messages
message_strategy = st.text(min_size=1, max_size=200)

# Strategy for generating field names
field_strategy = st.text(
    min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N", "Pc"))
)

# Strategy for generating field values (various types, excluding None)
value_strategy = st.one_of(
    st.text(min_size=1, max_size=150),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.lists(st.integers(), min_size=1, max_size=5),
)

# Strategy for generating field values including None
value_strategy_with_none = st.one_of(
    st.text(max_size=150),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none(),
    st.lists(st.integers(), max_size=5),
)


# =============================================================================
# Property 11: Exception Serialization Round-Trip
# =============================================================================


class TestExceptionSerializationRoundTrip:
    """
    **Feature: service-layer-refactoring, Property 11: Exception Serialization Round-Trip**

    *For any* NanoBananaError with message, error_code, context, and cause,
    calling `to_dict()` SHALL produce a dictionary that contains all provided
    information, and `str()` SHALL format as "[ERROR_CODE] message" when
    error_code is provided.
    """

    @given(
        message=message_strategy,
        error_code=st.one_of(st.none(), error_code_strategy),
        context=st.one_of(st.none(), context_strategy),
    )
    @settings(max_examples=100)
    def test_to_dict_contains_all_information(
        self,
        message: str,
        error_code: ErrorCode | None,
        context: dict | None,
    ):
        """
        **Feature: service-layer-refactoring, Property 11: Exception Serialization Round-Trip**

        to_dict() should contain all provided information.
        """
        error = NanoBananaError(
            message=message,
            error_code=error_code,
            context=context,
        )

        result = error.to_dict()

        # Type should always be present
        assert result["type"] == "NanoBananaError"

        # Message should always be present
        assert result["message"] == message

        # Code should be present only when error_code is provided
        if error_code is not None:
            assert "code" in result
            assert result["code"] == error_code.value
        else:
            assert "code" not in result

        # Context should be present only when non-empty
        if context:
            assert "context" in result
            assert result["context"] == context
        else:
            assert "context" not in result

    @given(
        message=message_strategy,
        error_code=error_code_strategy,
    )
    @settings(max_examples=100)
    def test_str_format_with_error_code(self, message: str, error_code: ErrorCode):
        """
        **Feature: service-layer-refactoring, Property 11: Exception Serialization Round-Trip**

        str() should format as "[ERROR_CODE] message" when error_code is provided.
        """
        error = NanoBananaError(message=message, error_code=error_code)

        result = str(error)

        assert result == f"[{error_code.value}] {message}"

    @given(message=message_strategy)
    @settings(max_examples=100)
    def test_str_format_without_error_code(self, message: str):
        """
        **Feature: service-layer-refactoring, Property 11: Exception Serialization Round-Trip**

        str() should return just the message when error_code is None.
        """
        error = NanoBananaError(message=message, error_code=None)

        result = str(error)

        assert result == message

    @given(
        message=message_strategy,
        error_code=st.one_of(st.none(), error_code_strategy),
        context=st.one_of(st.none(), context_strategy),
    )
    @settings(max_examples=100)
    def test_to_dict_with_cause_exception(
        self,
        message: str,
        error_code: ErrorCode | None,
        context: dict | None,
    ):
        """
        **Feature: service-layer-refactoring, Property 11: Exception Serialization Round-Trip**

        to_dict() should include cause when provided.
        """
        cause = ValueError("original error")
        error = NanoBananaError(
            message=message,
            error_code=error_code,
            context=context,
            cause=cause,
        )

        result = error.to_dict()

        assert "cause" in result
        assert result["cause"] == str(cause)


class TestSubclassSerializationRoundTrip:
    """Test that all exception subclasses properly serialize."""

    @given(
        message=message_strategy,
        error_code=st.one_of(st.none(), error_code_strategy),
    )
    @settings(max_examples=50)
    def test_configuration_error_serialization(self, message: str, error_code: ErrorCode | None):
        """ConfigurationError should serialize correctly."""
        error = ConfigurationError(message=message, error_code=error_code)
        result = error.to_dict()

        assert result["type"] == "ConfigurationError"
        assert result["message"] == message

    @given(
        message=message_strategy,
        error_code=st.one_of(st.none(), error_code_strategy),
    )
    @settings(max_examples=50)
    def test_gemini_api_error_serialization(self, message: str, error_code: ErrorCode | None):
        """GeminiAPIError should serialize correctly."""
        error = GeminiAPIError(message=message, error_code=error_code)
        result = error.to_dict()

        assert result["type"] == "GeminiAPIError"
        assert result["message"] == message

    @given(
        message=message_strategy,
        error_code=st.one_of(st.none(), error_code_strategy),
    )
    @settings(max_examples=50)
    def test_image_processing_error_serialization(self, message: str, error_code: ErrorCode | None):
        """ImageProcessingError should serialize correctly."""
        error = ImageProcessingError(message=message, error_code=error_code)
        result = error.to_dict()

        assert result["type"] == "ImageProcessingError"
        assert result["message"] == message

    @given(
        message=message_strategy,
        error_code=st.one_of(st.none(), error_code_strategy),
    )
    @settings(max_examples=50)
    def test_file_operation_error_serialization(self, message: str, error_code: ErrorCode | None):
        """FileOperationError should serialize correctly."""
        error = FileOperationError(message=message, error_code=error_code)
        result = error.to_dict()

        assert result["type"] == "FileOperationError"
        assert result["message"] == message


# =============================================================================
# Property 12: ValidationError Context Population
# =============================================================================


class TestValidationErrorContextPopulation:
    """
    **Feature: service-layer-refactoring, Property 12: ValidationError Context Population**

    *For any* ValidationError created with field and value parameters,
    the exception's context dictionary SHALL contain "field" and "value"
    keys with the provided values.
    """

    @given(
        message=message_strategy,
        field=field_strategy,
        value=value_strategy,
    )
    @settings(max_examples=100)
    def test_field_and_value_in_context(
        self,
        message: str,
        field: str,
        value,
    ):
        """
        **Feature: service-layer-refactoring, Property 12: ValidationError Context Population**

        Field and value should be automatically added to context.
        """
        error = ValidationError(
            message=message,
            field=field,
            value=value,
        )

        # Field should be in context
        assert "field" in error.context
        assert error.context["field"] == field

        # Value should be in context (possibly truncated)
        assert "value" in error.context
        str_value = str(value)
        expected_value = str_value[:100] if len(str_value) > 100 else str_value
        assert error.context["value"] == expected_value

        # Field and value should also be accessible as attributes
        assert error.field == field
        assert error.value == value

    @given(
        message=message_strategy,
        field=field_strategy,
        value=st.one_of(
            st.text(min_size=1, max_size=150),  # Non-empty text
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.lists(st.integers(), min_size=1, max_size=5),  # Non-empty lists
        ),
        extra_context=context_strategy,
    )
    @settings(max_examples=100)
    def test_field_and_value_merged_with_existing_context(
        self,
        message: str,
        field: str,
        value,
        extra_context: dict,
    ):
        """
        **Feature: service-layer-refactoring, Property 12: ValidationError Context Population**

        Field and value should be merged with any existing context.
        """
        error = ValidationError(
            message=message,
            context=extra_context,
            field=field,
            value=value,
        )

        # Field and value should be present (value is not None in this test)
        assert "field" in error.context
        assert "value" in error.context

        # Extra context should also be preserved (unless overwritten by field/value)
        for key, val in extra_context.items():
            if key not in ("field", "value"):
                assert error.context[key] == val

    @given(message=message_strategy)
    @settings(max_examples=50)
    def test_none_field_not_in_context(self, message: str):
        """
        **Feature: service-layer-refactoring, Property 12: ValidationError Context Population**

        When field is None, it should not be added to context.
        """
        error = ValidationError(message=message, field=None, value=None)

        assert "field" not in error.context
        assert "value" not in error.context

    @given(
        message=message_strategy,
        field=field_strategy,
    )
    @settings(max_examples=50)
    def test_field_only_in_context(self, message: str, field: str):
        """
        **Feature: service-layer-refactoring, Property 12: ValidationError Context Population**

        When only field is provided (value is None), only field should be in context.
        """
        error = ValidationError(message=message, field=field, value=None)

        assert "field" in error.context
        assert error.context["field"] == field
        assert "value" not in error.context

    @given(message=message_strategy)
    @settings(max_examples=50)
    def test_long_value_truncation(self, message: str):
        """
        **Feature: service-layer-refactoring, Property 12: ValidationError Context Population**

        Long values should be truncated to 100 characters.
        """
        long_value = "x" * 200  # 200 character string
        error = ValidationError(message=message, field="test_field", value=long_value)

        # Value in context should be truncated
        assert len(error.context["value"]) == 100
        assert error.context["value"] == "x" * 100

        # Original value should be preserved in attribute
        assert error.value == long_value

    @given(
        message=message_strategy,
        error_code=error_code_strategy,
        field=field_strategy,
        value=value_strategy,
    )
    @settings(max_examples=100)
    def test_validation_error_to_dict_includes_context(
        self,
        message: str,
        error_code: ErrorCode,
        field: str,
        value,
    ):
        """
        **Feature: service-layer-refactoring, Property 12: ValidationError Context Population**

        to_dict() should include the populated context with field and value.
        """
        error = ValidationError(
            message=message,
            error_code=error_code,
            field=field,
            value=value,
        )

        result = error.to_dict()

        assert result["type"] == "ValidationError"
        assert result["message"] == message
        assert result["code"] == error_code.value
        assert "context" in result
        assert result["context"]["field"] == field
