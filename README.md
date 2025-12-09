# Banana Image MCP

<div align="center">

<img src="https://img.shields.io/badge/MCP-Image%20Generation-ff6b6b?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0yMSAxOVY1YzAtMS4xLS45LTItMi0ySDVjLTEuMSAwLTIgLjktMiAydjE0YzAgMS4xLjkgMiAyIDJoMTRjMS4xIDAgMi0uOSAyLTJ6TTguNSAxMy41bDIuNSAzLjAxTDE0LjUgMTJsNC41IDZINWwzLjUtNC41eiIvPjwvc3ZnPg==" alt="MCP Image Generation">

### Let Claude Generate Stunning Images for You

[![PyPI version](https://img.shields.io/pypi/v/banana-image-mcp?style=flat-square&color=blue)](https://pypi.org/project/banana-image-mcp/)
[![Downloads](https://img.shields.io/pypi/dm/banana-image-mcp?style=flat-square&color=green)](https://pypi.org/project/banana-image-mcp/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?style=flat-square)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

[中文文档](./README_CN.md) | [Report Issues](https://github.com/zengwenliang416/banana-image-mcp/issues)

</div>

---

## What is Banana Image MCP?

**Banana Image MCP** is an MCP (Model Context Protocol) server that enables Claude and other AI assistants to generate high-quality images using Google's latest Gemini image models.

Simply describe what you want, and Claude will create it - from quick concept sketches to stunning **4K professional artwork**.

## Key Features

| Feature | Description |
|---------|-------------|
| **4K Ultra HD** | Generate images up to 3840px with Pro model |
| **Dual Model Support** | Flash (fast, 2-3s) + Pro (4K quality, 5-8s) |
| **Smart Model Selection** | Automatically picks the best model based on your prompt |
| **Google Search Grounding** | Pro model uses real-world knowledge for accuracy |
| **Flexible Aspect Ratios** | 1:1, 16:9, 9:16, 4:3, 3:2, 21:9 and more |
| **Image Editing** | Edit existing images with natural language |
| **Advanced Reasoning** | Configurable thinking levels for complex compositions |

## Quick Start

### 1. Get a Gemini API Key

Get your **free** API key from [Google AI Studio](https://aistudio.google.com/apikey)

### 2. Install & Configure

**For Claude Desktop**, add to your config file:

```json
{
  "mcpServers": {
    "banana-image": {
      "command": "uvx",
      "args": ["banana-image-mcp"],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

<details>
<summary><strong>Config file locations</strong></summary>

| Platform | Path |
|----------|------|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |

</details>

<details>
<summary><strong>Other MCP clients (Cursor, VS Code, Cline, etc.)</strong></summary>

The configuration is similar for other MCP-compatible clients:

```json
{
  "mcpServers": {
    "banana-image": {
      "command": "uvx",
      "args": ["banana-image-mcp"],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Updating to the latest version</strong></summary>

When using `uvx`, packages are cached locally. To get the latest version after an update:

```bash
# Clear the cache for this package
uv cache clean banana-image-mcp

# Then restart your MCP client (Claude Desktop, etc.)
```

Or specify a version explicitly:

```json
{
  "mcpServers": {
    "banana-image": {
      "command": "uvx",
      "args": ["banana-image-mcp==1.0.0"],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

</details>

### 3. Start Creating

Just ask Claude to generate images:

```
"Generate a cute cat wearing a space suit"

"Create a professional product photo of a coffee cup, 4K quality"

"Make a 16:9 YouTube thumbnail about cooking"

"Edit this image: make the sky more dramatic"
```

## Models Comparison

| Model | Speed | Max Resolution | Best For |
|-------|-------|----------------|----------|
| **Gemini 2.5 Flash** | 2-3s | 1024px | Quick drafts, iterations, prototypes |
| **Gemini 3 Pro** | 5-8s | **4K (3840px)** | Final assets, marketing, professional work |

### Model Selection

The server **defaults to Pro model** for best quality. You can also control it:

| Say this... | Model Used |
|-------------|------------|
| "quick sketch", "draft", "prototype" | Flash |
| "4K", "professional", "high quality" | Pro |
| (default) | Pro |

## Tool Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | required | Image description |
| `model_tier` | string | `"pro"` | `"flash"`, `"pro"`, or `"auto"` |
| `resolution` | string | `"4k"` | `"1k"`, `"2k"`, `"4k"`, `"high"` |
| `aspect_ratio` | string | - | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"21:9"`, etc. |
| `thinking_level` | string | `"high"` | `"low"` or `"high"` (Pro only) |
| `enable_grounding` | bool | `true` | Enable Google Search grounding (Pro only) |
| `n` | int | `1` | Number of images (1-4) |
| `negative_prompt` | string | - | What to avoid in the image |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | **Yes** | - | Your Gemini API key |
| `IMAGE_OUTPUT_DIR` | No | `~/banana-images` | Where to save generated images |

## Example Outputs

Here are some examples of what you can create:

- **Product Photography**: Professional product shots with studio lighting
- **Concept Art**: Fantasy landscapes, character designs, sci-fi scenes
- **Marketing Materials**: Social media graphics, banners, thumbnails
- **Technical Diagrams**: Flowcharts, architecture diagrams with text
- **Photo-realistic Images**: Portraits, nature, urban photography

## Development

```bash
# Clone the repository
git clone https://github.com/zengwenliang416/banana-image-mcp.git
cd banana-image-mcp

# Install dependencies
uv sync

# Run in development mode
fastmcp dev banana_image_mcp.server:create_app

# Run tests
pytest

# Lint and format
ruff check .
ruff format .
```

## Changelog

### v1.0.0
- First stable release
- 4K resolution output support (up to 3840px)
- Dual model support: Flash (fast) + Pro (4K quality)
- Intelligent model selection based on prompt
- Google Search grounding for Pro model
- Flexible aspect ratios (1:1, 16:9, 9:16, 4:3, 21:9, etc.)
- Image editing with natural language
- GitHub Actions CI/CD workflow

### v0.1.2
- Added 4K resolution output support
- Default to Pro model and 4K resolution
- Fixed image_size parameter passing to Gemini API

### v0.1.1
- Updated package metadata and author info

### v0.1.0
- Initial release with dual model support

## Links

- [PyPI Package](https://pypi.org/project/banana-image-mcp/)
- [GitHub Repository](https://github.com/zengwenliang416/banana-image-mcp)
- [Report Issues](https://github.com/zengwenliang416/banana-image-mcp/issues)

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Made with by [Wenliang Zeng](https://github.com/zengwenliang416)**

If you find this useful, please consider giving it a star!

</div>
