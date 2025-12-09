# Banana Image MCP

<div align="center">

**Let Claude Generate Images for You**

[![PyPI version](https://badge.fury.io/py/banana-image-mcp.svg)](https://badge.fury.io/py/banana-image-mcp)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[中文文档](./README_CN.md)

</div>

---

## What is this?

**Banana Image MCP** is an MCP server that gives Claude (and other AI assistants) the ability to generate images using Google's Gemini models.

Simply tell Claude what image you want, and it will create it for you - from quick sketches to professional 4K artwork.

## Features

| Feature | Description |
|---------|-------------|
| **Dual Model Support** | Flash (fast, 2-3s) + Pro (4K quality, 5-8s) |
| **Smart Auto-Selection** | Automatically picks the best model for your needs |
| **4K Resolution** | Up to 3840px professional-grade output |
| **Google Search Grounding** | Pro model uses real-world knowledge for accuracy |
| **Flexible Aspect Ratios** | 1:1, 16:9, 9:16, 21:9, and more |
| **Image Editing** | Edit existing images with AI |

## Quick Start

### 1. Get a Gemini API Key

Get your free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### 2. Install & Configure

**For Claude Desktop**, add to `claude_desktop_config.json`:

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
<summary>Config file location</summary>

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
</details>

<details>
<summary>Other clients (Cursor, VS Code, etc.)</summary>

**Cursor / VS Code Claude Extension:**
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

### 3. Start Using

Just ask Claude to generate images:

> "Generate a cute cat wearing a space suit"
>
> "Create a professional product photo of a coffee cup, 4K quality"
>
> "Make a 16:9 thumbnail for my YouTube video about cooking"

## Models

| Model | Speed | Max Resolution | Best For |
|-------|-------|----------------|----------|
| **Flash** | 2-3s | 1024px | Quick drafts, iterations, prototypes |
| **Pro** | 5-8s | 4K (3840px) | Final assets, marketing, professional work |

The server automatically selects the best model, or you can specify:
- Say "quick sketch" or "draft" → Flash
- Say "4K", "professional", or "high quality" → Pro

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | Your Gemini API key |
| `IMAGE_OUTPUT_DIR` | No | `~/banana-images` | Where to save images |

## Links

- [PyPI Package](https://pypi.org/project/banana-image-mcp/)
- [GitHub Repository](https://github.com/zengwenliang416/banana-image-mcp)
- [Report Issues](https://github.com/zengwenliang416/banana-image-mcp/issues)

---

<div align="center">

**Made by [Wenliang Zeng](https://github.com/zengwenliang416)**

MIT License

</div>
