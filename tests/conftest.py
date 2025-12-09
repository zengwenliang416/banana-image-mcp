"""
Shared test fixtures for Nano Banana MCP Server tests.

This module provides common fixtures for mocking services and configurations
used across the test suite.

Requirements: 6.1, 6.2, 6.3, 6.4
"""

import io
from unittest.mock import MagicMock, Mock

from PIL import Image as PILImage
import pytest

from banana_image_mcp.config.settings import (
    FlashImageConfig,
    GeminiConfig,
    MediaResolution,
    ProImageConfig,
    ServerConfig,
    ThinkingLevel,
)
from banana_image_mcp.services.gemini_client import GeminiClient
from banana_image_mcp.services.image_storage_service import (
    ImageStorageService,
    StoredImageInfo,
)

# =============================================================================
# Configuration Fixtures (Requirements 6.1)
# =============================================================================


@pytest.fixture
def mock_server_config() -> ServerConfig:
    """Create a mock ServerConfig for testing.

    Returns:
        ServerConfig with test API key and default settings.
    """
    return ServerConfig(
        gemini_api_key="test-api-key-12345",
        server_name="test-banana-server",
        transport="stdio",
        host="127.0.0.1",
        port=9000,
        mask_error_details=False,
        max_concurrent_requests=10,
        image_output_dir="/tmp/test-banana-images",
    )


@pytest.fixture
def mock_gemini_config() -> GeminiConfig:
    """Create a mock GeminiConfig for testing (legacy compatibility).

    Returns:
        GeminiConfig with default settings.
    """
    return GeminiConfig(
        model_name="gemini-2.5-flash-image",
        max_images_per_request=4,
        max_inline_image_size=20 * 1024 * 1024,
        default_image_format="png",
        request_timeout=60,
    )


@pytest.fixture
def mock_flash_config() -> FlashImageConfig:
    """Create a mock FlashImageConfig for testing.

    Returns:
        FlashImageConfig with default Flash model settings.
    """
    return FlashImageConfig(
        model_name="gemini-2.5-flash-image",
        max_images_per_request=4,
        max_inline_image_size=20 * 1024 * 1024,
        default_image_format="png",
        request_timeout=60,
        max_resolution=1024,
        supports_thinking=False,
        supports_grounding=False,
        supports_media_resolution=False,
    )


@pytest.fixture
def mock_pro_config() -> ProImageConfig:
    """Create a mock ProImageConfig for testing.

    Returns:
        ProImageConfig with default Pro model settings.
    """
    return ProImageConfig(
        model_name="gemini-3-pro-image-preview",
        max_images_per_request=4,
        max_inline_image_size=20 * 1024 * 1024,
        default_image_format="png",
        request_timeout=90,
        max_resolution=3840,
        default_resolution="high",
        default_thinking_level=ThinkingLevel.HIGH,
        default_media_resolution=MediaResolution.HIGH,
        supports_thinking=True,
        supports_grounding=True,
        supports_media_resolution=True,
        enable_search_grounding=True,
    )


# =============================================================================
# GeminiClient Fixtures (Requirements 6.2)
# =============================================================================


@pytest.fixture
def mock_gemini_client(mock_server_config: ServerConfig, mock_gemini_config: GeminiConfig) -> Mock:
    """Create a mock GeminiClient for testing.

    The mock client has:
    - Mocked internal _client attribute
    - Mocked models attribute for generate_content
    - Mocked create_image_parts method
    - Mocked extract_images method

    Args:
        mock_server_config: Server configuration fixture.
        mock_gemini_config: Gemini configuration fixture.

    Returns:
        Mock GeminiClient with pre-configured mock methods.
    """
    client = Mock(spec=GeminiClient)

    # Mock the internal client
    client._client = MagicMock()
    client._client.models = MagicMock()
    client._client.models.generate_content = MagicMock()

    # Mock configuration attributes
    client.config = mock_server_config
    client.gemini_config = mock_gemini_config

    # Mock create_image_parts to return empty list by default
    client.create_image_parts = Mock(return_value=[])

    # Mock extract_images to return sample image bytes
    client.extract_images = Mock(return_value=[b"fake_image_bytes"])

    # Mock generate_content to return a mock response
    mock_response = MagicMock()
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content = MagicMock()
    mock_response.candidates[0].content.parts = []
    client.generate_content = Mock(return_value=mock_response)

    return client


@pytest.fixture
def mock_flash_gemini_client(
    mock_server_config: ServerConfig, mock_flash_config: FlashImageConfig
) -> Mock:
    """Create a mock GeminiClient configured for Flash model.

    Args:
        mock_server_config: Server configuration fixture.
        mock_flash_config: Flash model configuration fixture.

    Returns:
        Mock GeminiClient configured for Flash model.
    """
    client = Mock(spec=GeminiClient)
    client._client = MagicMock()
    client._client.models = MagicMock()
    client.config = mock_server_config
    client.gemini_config = mock_flash_config
    client.create_image_parts = Mock(return_value=[])
    client.extract_images = Mock(return_value=[b"flash_image_bytes"])
    client.generate_content = Mock(return_value=MagicMock())
    return client


@pytest.fixture
def mock_pro_gemini_client(
    mock_server_config: ServerConfig, mock_pro_config: ProImageConfig
) -> Mock:
    """Create a mock GeminiClient configured for Pro model.

    Args:
        mock_server_config: Server configuration fixture.
        mock_pro_config: Pro model configuration fixture.

    Returns:
        Mock GeminiClient configured for Pro model.
    """
    client = Mock(spec=GeminiClient)
    client._client = MagicMock()
    client._client.models = MagicMock()
    client.config = mock_server_config
    client.gemini_config = mock_pro_config
    client.create_image_parts = Mock(return_value=[])
    client.extract_images = Mock(return_value=[b"pro_image_bytes"])
    client.generate_content = Mock(return_value=MagicMock())
    return client


# =============================================================================
# Storage Service Fixtures (Requirements 6.3)
# =============================================================================


@pytest.fixture
def mock_stored_image_info() -> StoredImageInfo:
    """Create a mock StoredImageInfo for testing.

    Returns:
        StoredImageInfo with predictable test values.
    """
    return StoredImageInfo(
        id="test-image-id-12345",
        filename="test-image-id-12345.png",
        full_path="/tmp/test-images/test-image-id-12345.png",
        thumbnail_path="/tmp/test-images/thumbnails/test-image-id-12345_thumb.jpg",
        size_bytes=1024 * 100,  # 100KB
        thumbnail_size_bytes=1024 * 10,  # 10KB
        mime_type="image/png",
        created_at=1700000000.0,
        expires_at=1700003600.0,  # 1 hour later
        width=1024,
        height=768,
        thumbnail_width=256,
        thumbnail_height=192,
        metadata={
            "prompt": "test prompt",
            "model": "gemini-2.5-flash-image",
        },
    )


@pytest.fixture
def mock_storage_service(mock_stored_image_info: StoredImageInfo) -> Mock:
    """Create a mock ImageStorageService for testing.

    The mock service:
    - Returns predictable StoredImageInfo objects
    - Provides mock thumbnail base64 data
    - Simulates storage operations without file I/O

    Args:
        mock_stored_image_info: StoredImageInfo fixture.

    Returns:
        Mock ImageStorageService with pre-configured mock methods.
    """
    service = Mock(spec=ImageStorageService)

    # Mock store_image to return predictable StoredImageInfo
    service.store_image = Mock(return_value=mock_stored_image_info)

    # Mock get_thumbnail_base64 to return a small base64 string
    # This is a 1x1 red pixel JPEG encoded as base64
    service.get_thumbnail_base64 = Mock(
        return_value="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    )

    # Mock get_image_info
    service.get_image_info = Mock(return_value=mock_stored_image_info)

    # Mock get_image_bytes
    service.get_image_bytes = Mock(return_value=b"mock_image_bytes")

    # Mock list_images
    service.list_images = Mock(return_value=[mock_stored_image_info])

    # Mock delete_image
    service.delete_image = Mock(return_value=True)

    # Mock cleanup_all
    service.cleanup_all = Mock(return_value=1)

    # Mock get_storage_stats
    service.get_storage_stats = Mock(return_value={
        "total_images": 1,
        "total_size_bytes": 102400,
        "total_size_mb": 0.1,
        "total_thumbnail_size_bytes": 10240,
        "total_thumbnail_size_kb": 10.0,
        "base_directory": "/tmp/test-images",
        "default_ttl_seconds": 3600,
    })

    return service


# =============================================================================
# Sample Data Fixtures (Requirements 6.4)
# =============================================================================


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Generate a valid PNG image bytes for testing.

    Creates a 100x100 red image in PNG format.

    Returns:
        Valid PNG image as bytes.
    """
    # Create a simple 100x100 red image
    img = PILImage.new("RGB", (100, 100), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def sample_image_bytes_large() -> bytes:
    """Generate a larger valid PNG image bytes for testing.

    Creates a 1024x768 gradient image in PNG format.

    Returns:
        Valid PNG image as bytes.
    """
    # Create a 1024x768 gradient image
    img = PILImage.new("RGB", (1024, 768))
    pixels = img.load()
    for x in range(1024):
        for y in range(768):
            # Create a gradient effect
            r = int(255 * x / 1024)
            g = int(255 * y / 768)
            b = 128
            pixels[x, y] = (r, g, b)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def sample_image_base64(sample_image_bytes: bytes) -> str:
    """Generate a valid PNG image as base64 string for testing.

    Args:
        sample_image_bytes: PNG image bytes fixture.

    Returns:
        Base64 encoded PNG image string.
    """
    import base64
    return base64.b64encode(sample_image_bytes).decode("utf-8")


@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    """Generate a valid JPEG image bytes for testing.

    Creates a 100x100 blue image in JPEG format.

    Returns:
        Valid JPEG image as bytes.
    """
    img = PILImage.new("RGB", (100, 100), color="blue")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


@pytest.fixture
def sample_webp_bytes() -> bytes:
    """Generate a valid WebP image bytes for testing.

    Creates a 100x100 green image in WebP format.

    Returns:
        Valid WebP image as bytes.
    """
    img = PILImage.new("RGB", (100, 100), color="green")
    buffer = io.BytesIO()
    img.save(buffer, format="WEBP", quality=85)
    return buffer.getvalue()


# =============================================================================
# Helper Fixtures
# =============================================================================


@pytest.fixture
def mock_gemini_response_with_image(sample_image_bytes: bytes) -> MagicMock:
    """Create a mock Gemini API response containing an image.

    Args:
        sample_image_bytes: PNG image bytes fixture.

    Returns:
        Mock response object with image data in candidates.
    """
    response = MagicMock()

    # Create mock inline_data
    inline_data = MagicMock()
    inline_data.data = sample_image_bytes
    inline_data.mime_type = "image/png"

    # Create mock part
    part = MagicMock()
    part.inline_data = inline_data

    # Create mock content
    content = MagicMock()
    content.parts = [part]

    # Create mock candidate
    candidate = MagicMock()
    candidate.content = content

    # Set up response
    response.candidates = [candidate]

    return response


@pytest.fixture
def mock_gemini_response_empty() -> MagicMock:
    """Create a mock Gemini API response with no images.

    Returns:
        Mock response object with empty candidates.
    """
    response = MagicMock()
    response.candidates = []
    return response


@pytest.fixture
def mock_gemini_response_multiple_images(sample_image_bytes: bytes) -> MagicMock:
    """Create a mock Gemini API response containing multiple images.

    Args:
        sample_image_bytes: PNG image bytes fixture.

    Returns:
        Mock response object with multiple images in candidates.
    """
    response = MagicMock()

    parts = []
    for _i in range(3):
        inline_data = MagicMock()
        inline_data.data = sample_image_bytes
        inline_data.mime_type = "image/png"

        part = MagicMock()
        part.inline_data = inline_data
        parts.append(part)

    content = MagicMock()
    content.parts = parts

    candidate = MagicMock()
    candidate.content = content

    response.candidates = [candidate]

    return response
