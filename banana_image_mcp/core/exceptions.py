"""Custom exceptions for the Nano Banana MCP Server."""

from enum import Enum
from typing import Any


class ErrorCode(Enum):
    """错误码枚举 - Error code enumeration for categorized error handling.

    Categories:
    - E1xxx: Validation errors (输入验证失败)
    - E2xxx: Configuration errors (配置问题)
    - E3xxx: API errors (Gemini API 调用失败)
    - E4xxx: Processing errors (图像处理失败)
    - E5xxx: File errors (文件操作失败)
    """

    # Validation errors (验证错误 - E1xxx)
    VALIDATION_EMPTY_INPUT = "E1001"
    VALIDATION_INVALID_FORMAT = "E1002"
    VALIDATION_SIZE_EXCEEDED = "E1003"
    VALIDATION_INVALID_MODE = "E1004"
    VALIDATION_INVALID_PATH = "E1005"
    VALIDATION_FILE_COUNT_EXCEEDED = "E1006"

    # Configuration errors (配置错误 - E2xxx)
    CONFIG_MISSING_API_KEY = "E2001"
    CONFIG_INVALID_VALUE = "E2002"
    CONFIG_MISSING_REQUIRED = "E2003"

    # API errors (API 错误 - E3xxx)
    API_CONNECTION_FAILED = "E3001"
    API_RATE_LIMITED = "E3002"
    API_AUTHENTICATION_FAILED = "E3003"
    API_INVALID_RESPONSE = "E3004"
    API_TIMEOUT = "E3005"

    # Processing errors (处理错误 - E4xxx)
    PROCESSING_IMAGE_FAILED = "E4001"
    PROCESSING_THUMBNAIL_FAILED = "E4002"
    PROCESSING_ENCODING_FAILED = "E4003"
    PROCESSING_STORAGE_FAILED = "E4004"

    # File errors (文件错误 - E5xxx)
    FILE_NOT_FOUND = "E5001"
    FILE_READ_FAILED = "E5002"
    FILE_WRITE_FAILED = "E5003"
    FILE_INVALID_TYPE = "E5004"
    FILE_ACCESS_DENIED = "E5005"


class NanoBananaError(Exception):
    """Base exception class for all Nano Banana errors.

    Provides error code, context information, and cause exception support
    for better error diagnosis and programmatic handling.
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode | None = None,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        """Initialize NanoBananaError.

        Args:
            message: Human-readable error message
            error_code: Optional ErrorCode enum value for categorization
            context: Optional dictionary with additional context information
            cause: Optional original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.cause = cause

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception to dictionary.

        Returns:
            Dictionary containing error type, message, code, context, and cause
        """
        result: dict[str, Any] = {
            "type": self.__class__.__name__,
            "message": self.message,
        }
        if self.error_code:
            result["code"] = self.error_code.value
        if self.context:
            result["context"] = self.context
        if self.cause:
            result["cause"] = str(self.cause)
        return result

    def __str__(self) -> str:
        """Format as '[ERROR_CODE] message' when error_code exists."""
        if self.error_code:
            return f"[{self.error_code.value}] {self.message}"
        return self.message


class ConfigurationError(NanoBananaError):
    """Raised when there's a configuration issue."""

    pass


class ValidationError(NanoBananaError):
    """Raised when input validation fails.

    Supports optional field and value parameters for detailed context.
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode | None = None,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
        field: str | None = None,
        value: Any = None,
    ):
        """Initialize ValidationError.

        Args:
            message: Human-readable error message
            error_code: Optional ErrorCode enum value
            context: Optional dictionary with additional context
            cause: Optional original exception
            field: Optional field name that failed validation
            value: Optional value that failed validation (truncated to 100 chars)
        """
        # Build context with field and value
        ctx = context.copy() if context else {}
        if field is not None:
            ctx["field"] = field
        if value is not None:
            # Truncate long values to avoid huge error messages
            str_value = str(value)
            ctx["value"] = str_value[:100] if len(str_value) > 100 else str_value

        super().__init__(message, error_code, ctx, cause)
        self.field = field
        self.value = value


class GeminiAPIError(NanoBananaError):
    """Raised when Gemini API calls fail."""

    pass


class ImageProcessingError(NanoBananaError):
    """Raised when image processing fails."""

    pass


class FileOperationError(NanoBananaError):
    """Raised when file operations fail."""

    pass
