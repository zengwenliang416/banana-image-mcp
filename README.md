# Banana Image MCP Server

A production-ready **Model Context Protocol (MCP)** server that provides AI-powered image generation capabilities through Google's **Gemini** models with intelligent model selection.

## Features

- **Multi-Model AI Image Generation**: Intelligent selection between Flash (speed) and Pro (quality) models
- **Gemini 2.5 Flash Image**: Fast generation (1024px) for rapid prototyping
- **Gemini 3 Pro Image**: High-quality up to 4K with Google Search grounding
- **Smart Model Selection**: Automatically chooses optimal model based on your prompt
- **Aspect Ratio Control**: Specify output dimensions (1:1, 16:9, 9:16, 21:9, and more)
- **Smart Templates**: Pre-built prompt templates for photography, design, and editing
- **File Management**: Upload and manage files via Gemini Files API
- **Resource Discovery**: Browse templates and file metadata through MCP resources
- **Production Ready**: Comprehensive error handling, logging, and validation
- **High Performance**: Optimized architecture with intelligent caching

## Quick Start

### Prerequisites

1. **Google Gemini API Key** - [Get one free here](https://makersuite.google.com/app/apikey)
2. **Python 3.11+** (for development only)

### Installation

Using `uvx` (Recommended):

```bash
uvx banana-image-mcp
```

Using `pip`:

```bash
pip install banana-image-mcp
```

## Configuration

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "banana-image": {
      "command": "uvx",
      "args": ["banana-image-mcp"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here"
      }
    }
  }
}
```

**Configuration file locations:**

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Claude Code (VS Code Extension)

Install and configure in VS Code:

1. Install the Claude Code extension
2. Open Command Palette (`Cmd/Ctrl + Shift + P`)
3. Run "Claude Code: Add MCP Server"
4. Configure:
   ```json
   {
     "name": "banana-image",
     "command": "uvx",
     "args": ["banana-image-mcp"],
     "env": {
       "GEMINI_API_KEY": "your-gemini-api-key-here"
     }
   }
   ```

### Cursor

Add to Cursor's MCP configuration:

```json
{
  "mcpServers": {
    "banana-image": {
      "command": "uvx",
      "args": ["banana-image-mcp"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here"
      }
    }
  }
}
```

## Model Selection

Banana Image MCP supports two Gemini models with intelligent automatic selection:

### Pro Model (Gemini 3 Pro Image)

- **Quality**: Professional-grade, production-ready
- **Resolution**: Up to 4K (3840px)
- **Speed**: ~5-8 seconds per image
- **Special Features**:
  - Google Search Grounding for accurate, contextual images
  - Advanced Reasoning with configurable thinking levels
  - Superior Text Rendering
- **Best for**: Production assets, marketing materials, professional photography

### Flash Model (Gemini 2.5 Flash Image)

- **Speed**: Very fast (2-3 seconds)
- **Resolution**: Up to 1024px
- **Quality**: High quality for everyday use
- **Best for**: Rapid prototyping, iterations, drafts, sketches

### Automatic Selection (Recommended)

By default, the server uses **AUTO** mode which intelligently analyzes your prompt:

**Pro Model Selected When**:
- Quality keywords: "4K", "professional", "production", "high-res"
- High resolution requested: `resolution="4k"`
- Google Search grounding enabled
- High thinking level requested

**Flash Model Selected When**:
- Speed keywords: "quick", "draft", "sketch", "rapid"
- High-volume batch generation
- Standard resolution requested

### Usage Examples

```python
# Automatic selection (recommended)
"Generate a professional 4K product photo"  # Pro model
"Quick sketch of a cat"                     # Flash model

# Explicit model selection
generate_image(
    prompt="A scenic landscape",
    model_tier="flash"  # Force Flash model
)

# Pro model with all features
generate_image(
    prompt="Professional product photo",
    model_tier="pro",
    resolution="4k",
    thinking_level="HIGH",
    enable_grounding=True
)

# Aspect ratio control
generate_image(
    prompt="Cinematic landscape",
    aspect_ratio="21:9"  # Ultra-wide format
)
```

### Aspect Ratio Control

Supported aspect ratios:
- `1:1` - Square (Instagram, profile pictures)
- `4:3` - Classic photo format
- `3:4` - Portrait orientation
- `16:9` - Widescreen (YouTube thumbnails)
- `9:16` - Mobile portrait (phone wallpapers)
- `21:9` - Ultra-wide cinematic
- `2:3`, `3:2`, `4:5`, `5:4` - Various photo formats

## Environment Variables

```bash
# Required
GEMINI_API_KEY=your-gemini-api-key-here

# Model Selection (optional)
BANANA_IMAGE_MODEL=auto  # Options: flash, pro, auto (default: auto)

# Optional
IMAGE_OUTPUT_DIR=/path/to/image/directory  # Default: ~/banana-images
LOG_LEVEL=INFO                             # DEBUG, INFO, WARNING, ERROR
```

## Development

```bash
# Clone repository
git clone https://github.com/zengwenliang416/banana-image-mcp.git
cd banana-image-mcp

# Install with uv
uv sync

# Set environment
export GEMINI_API_KEY=your-api-key-here

# Run locally
uv run python -m banana_image_mcp.server
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/zengwenliang416/banana-image-mcp/issues)
- **Author**: Wenliang Zeng
