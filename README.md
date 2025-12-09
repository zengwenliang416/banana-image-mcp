# Banana Image MCP

<div align="center">

**Let Claude Generate Images for You**

[English](#english) | [中文](#中文)

[![PyPI version](https://badge.fury.io/py/banana-image-mcp.svg)](https://badge.fury.io/py/banana-image-mcp)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

<a name="english"></a>

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

<a name="中文"></a>

## 这是什么？

**Banana Image MCP** 是一个 MCP 服务器，让 Claude（及其他 AI 助手）能够使用 Google Gemini 模型生成图片。

只需告诉 Claude 你想要什么图片，它就会为你创建 - 从快速草图到专业级 4K 作品。

## 功能特性

| 功能 | 说明 |
|------|------|
| **双模型支持** | Flash（快速，2-3秒）+ Pro（4K画质，5-8秒）|
| **智能自动选择** | 根据需求自动选择最佳模型 |
| **4K 分辨率** | 最高 3840px 专业级输出 |
| **Google 搜索增强** | Pro 模型利用真实世界知识提升准确性 |
| **灵活宽高比** | 1:1、16:9、9:16、21:9 等多种比例 |
| **图片编辑** | 使用 AI 编辑现有图片 |

## 快速开始

### 1. 获取 Gemini API Key

从 [Google AI Studio](https://makersuite.google.com/app/apikey) 免费获取 API Key

### 2. 安装配置

**Claude Desktop 用户**，编辑 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "banana-image": {
      "command": "uvx",
      "args": ["banana-image-mcp"],
      "env": {
        "GEMINI_API_KEY": "你的API密钥"
      }
    }
  }
}
```

<details>
<summary>配置文件位置</summary>

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
</details>

### 3. 开始使用

直接让 Claude 生成图片：

> "生成一只穿着宇航服的可爱猫咪"
>
> "创建一张咖啡杯的专业产品照片，4K 画质"
>
> "制作一个 16:9 的 YouTube 烹饪视频缩略图"

## 模型对比

| 模型 | 速度 | 最大分辨率 | 适用场景 |
|------|------|-----------|----------|
| **Flash** | 2-3秒 | 1024px | 快速草图、迭代、原型 |
| **Pro** | 5-8秒 | 4K (3840px) | 成品、营销素材、专业作品 |

服务器会自动选择最佳模型，你也可以指定：
- 说 "快速草图" 或 "草稿" → 使用 Flash
- 说 "4K"、"专业" 或 "高质量" → 使用 Pro

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `GEMINI_API_KEY` | 是 | - | Gemini API 密钥 |
| `IMAGE_OUTPUT_DIR` | 否 | `~/banana-images` | 图片保存目录 |

## 相关链接

- [PyPI 包](https://pypi.org/project/banana-image-mcp/)
- [GitHub 仓库](https://github.com/zengwenliang416/banana-image-mcp)
- [问题反馈](https://github.com/zengwenliang416/banana-image-mcp/issues)

---

<div align="center">

**Made with by [Wenliang Zeng](https://github.com/zengwenliang416)**

MIT License

</div>
