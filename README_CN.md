# Banana Image MCP

<div align="center">

<img src="https://img.shields.io/badge/MCP-AI%20%E5%9B%BE%E5%83%8F%E7%94%9F%E6%88%90-ff6b6b?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0yMSAxOVY1YzAtMS4xLS45LTItMi0ySDVjLTEuMSAwLTIgLjktMiAydjE0YzAgMS4xLjkgMiAyIDJoMTRjMS4xIDAgMi0uOSAyLTJ6TTguNSAxMy41bDIuNSAzLjAxTDE0LjUgMTJsNC41IDZINWwzLjUtNC41eiIvPjwvc3ZnPg==" alt="MCP AI 图像生成">

### 让 Claude 为你生成精美图片

[![PyPI version](https://img.shields.io/pypi/v/banana-image-mcp?style=flat-square&color=blue)](https://pypi.org/project/banana-image-mcp/)
[![Downloads](https://img.shields.io/pypi/dm/banana-image-mcp?style=flat-square&color=green)](https://pypi.org/project/banana-image-mcp/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?style=flat-square)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

[English](./README.md) | [问题反馈](https://github.com/zengwenliang416/banana-image-mcp/issues)

</div>

---

## 这是什么？

**Banana Image MCP** 是一个 MCP（模型上下文协议）服务器，让 Claude 和其他 AI 助手能够使用 Google 最新的 Gemini 图像模型生成高质量图片。

只需描述你想要的内容，Claude 就会为你创建——从快速概念草图到令人惊艳的 **4K 专业级作品**。

## 核心功能

| 功能 | 说明 |
|------|------|
| **4K 超高清** | Pro 模型支持最高 3840px 输出 |
| **双模型支持** | Flash（快速，2-3秒）+ Pro（4K画质，5-8秒）|
| **智能模型选择** | 根据提示词自动选择最佳模型 |
| **Google 搜索增强** | Pro 模型利用真实世界知识提升准确性 |
| **灵活宽高比** | 1:1、16:9、9:16、4:3、3:2、21:9 等多种比例 |
| **图片编辑** | 使用自然语言编辑现有图片 |
| **高级推理** | 可配置思考级别，优化复杂构图 |

## 快速开始

### 1. 获取 Gemini API Key

从 [Google AI Studio](https://aistudio.google.com/apikey) **免费**获取 API Key

### 2. 安装配置

**Claude Desktop 用户**，编辑配置文件：

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
<summary><strong>配置文件位置</strong></summary>

| 平台 | 路径 |
|------|------|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |

</details>

<details>
<summary><strong>其他 MCP 客户端（Cursor、VS Code、Cline 等）</strong></summary>

其他 MCP 兼容客户端的配置类似：

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

</details>

<details>
<summary><strong>更新到最新版本</strong></summary>

使用 `uvx` 时，包会被缓存到本地。要获取最新版本：

```bash
# 清除该包的缓存
uv cache clean banana-image-mcp

# 然后重启 MCP 客户端（Claude Desktop 等）
```

或者指定具体版本：

```json
{
  "mcpServers": {
    "banana-image": {
      "command": "uvx",
      "args": ["banana-image-mcp==1.0.0"],
      "env": {
        "GEMINI_API_KEY": "你的API密钥"
      }
    }
  }
}
```

</details>

### 3. 开始创作

直接让 Claude 生成图片：

```
"生成一只穿着宇航服的可爱猫咪"

"创建一张咖啡杯的专业产品照片，4K 画质"

"制作一个 16:9 的 YouTube 烹饪视频缩略图"

"编辑这张图片：让天空更有戏剧性"
```

## 模型对比

| 模型 | 速度 | 最大分辨率 | 适用场景 |
|------|------|-----------|----------|
| **Gemini 2.5 Flash** | 2-3秒 | 1024px | 快速草图、迭代、原型 |
| **Gemini 3 Pro** | 5-8秒 | **4K (3840px)** | 成品、营销素材、专业作品 |

### 模型选择

服务器**默认使用 Pro 模型**以获得最佳质量。你也可以控制它：

| 这样说... | 使用模型 |
|-----------|----------|
| "快速草图"、"草稿"、"原型" | Flash |
| "4K"、"专业"、"高质量" | Pro |
| （默认） | Pro |

## 工具参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `prompt` | string | 必填 | 图片描述 |
| `model_tier` | string | `"pro"` | `"flash"`、`"pro"` 或 `"auto"` |
| `resolution` | string | `"4k"` | `"1k"`、`"2k"`、`"4k"`、`"high"` |
| `aspect_ratio` | string | - | `"1:1"`、`"16:9"`、`"9:16"`、`"4:3"`、`"21:9"` 等 |
| `thinking_level` | string | `"high"` | `"low"` 或 `"high"`（仅 Pro） |
| `enable_grounding` | bool | `true` | 启用 Google 搜索增强（仅 Pro） |
| `n` | int | `1` | 生成数量（1-4） |
| `negative_prompt` | string | - | 需要避免的内容 |

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `GEMINI_API_KEY` | **是** | - | Gemini API 密钥 |
| `IMAGE_OUTPUT_DIR` | 否 | `~/banana-images` | 图片保存目录 |

## 可以创作什么

以下是一些创作示例：

- **产品摄影**：专业的产品照片，带有影棚布光效果
- **概念艺术**：奇幻风景、角色设计、科幻场景
- **营销素材**：社交媒体图片、横幅、缩略图
- **技术图表**：流程图、架构图（带文字）
- **写实照片**：肖像、自然风光、城市摄影

## 开发指南

```bash
# 克隆仓库
git clone https://github.com/zengwenliang416/banana-image-mcp.git
cd banana-image-mcp

# 安装依赖
uv sync

# 开发模式运行
fastmcp dev banana_image_mcp.server:create_app

# 运行测试
pytest

# 代码检查和格式化
ruff check .
ruff format .
```

## 更新日志

### v1.0.0
- 首个稳定版本发布
- 4K 分辨率输出支持（最高 3840px）
- 双模型支持：Flash（快速）+ Pro（4K 画质）
- 基于提示词的智能模型选择
- Pro 模型 Google 搜索增强
- 灵活宽高比（1:1、16:9、9:16、4:3、21:9 等）
- 自然语言图片编辑
- GitHub Actions CI/CD 工作流

### v0.1.2
- 添加 4K 分辨率输出支持
- 默认使用 Pro 模型和 4K 分辨率
- 修复 image_size 参数传递到 Gemini API 的问题

### v0.1.1
- 更新包元数据和作者信息

### v0.1.0
- 首次发布，支持双模型

## 相关链接

- [PyPI 包](https://pypi.org/project/banana-image-mcp/)
- [GitHub 仓库](https://github.com/zengwenliang416/banana-image-mcp)
- [问题反馈](https://github.com/zengwenliang416/banana-image-mcp/issues)

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

---

<div align="center">

**由 [Wenliang Zeng](https://github.com/zengwenliang416) 用心打造**

如果觉得有用，欢迎给个 Star！

</div>
