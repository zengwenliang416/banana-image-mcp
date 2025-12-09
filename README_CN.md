<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
<div align="center">

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![PyPI version][pypi-shield]][pypi-url]
[![Downloads][downloads-shield]][pypi-url]

</div>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/zengwenliang416/banana-image-mcp">
    <img src="./assets/logo.svg" alt="Logo" width="120" height="120">
  </a>

  <h1 align="center">Banana Image MCP</h1>

  <p align="center">
    <b>让 Claude 为你生成精美的 4K 图片</b>
    <br />
    为 Claude Desktop 带来 AI 图像生成能力的 MCP 服务器
    <br />
    <br />
    <a href="#%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B"><strong>快速开始</strong></a>
    &nbsp;&middot;&nbsp;
    <a href="https://github.com/zengwenliang416/banana-image-mcp/issues/new?labels=bug">报告问题</a>
    &nbsp;&middot;&nbsp;
    <a href="https://github.com/zengwenliang416/banana-image-mcp/issues/new?labels=enhancement">功能建议</a>
  </p>

  <p align="center">
    <a href="./README.md">English</a>
  </p>
</div>

<!-- DEMO VIDEO -->
<div align="center">
  <video src="https://github.com/zengwenliang416/banana-image-mcp/raw/main/assets/demo.mp4" width="700" autoplay loop muted playsinline>
    Your browser does not support the video tag.
  </video>
</div>

<br />

<!-- ABOUT THE PROJECT -->
## 关于项目

**Banana Image MCP** 是一个生产就绪的 [MCP（模型上下文协议）](https://modelcontextprotocol.io/)服务器，让 Claude 和其他 AI 助手能够使用 Google 最新的 Gemini 图像模型生成高质量图片。

只需描述你想要的内容，Claude 就会为你创建——从快速概念草图到令人惊艳的 **4K 专业级作品**。

### 为什么选择 Banana Image MCP？

- **零配置复杂度** — 添加 API Key 即可开始生成
- **生产就绪** — 基于 FastMCP 框架构建，完整测试，CI/CD 支持
- **最佳画质** — 使用 Gemini 最先进的图像模型，支持 4K 输出
- **智能默认** — 根据提示词自动选择最佳模型
- **真实世界知识** — Google 搜索增强，生成准确、真实的图像

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

### 技术栈

* [![Python][Python-badge]][Python-url]
* [![FastMCP][FastMCP-badge]][FastMCP-url]
* [![Google Gemini][Gemini-badge]][Gemini-url]
* [![uv][uv-badge]][uv-url]

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

<!-- FEATURES -->
## 核心功能

<table>
<tr>
<td width="50%">

### 4K 超高清输出
使用 Pro 模型生成高达 **3840px** 的图像。适合专业工作、营销素材和印刷品。

</td>
<td width="50%">

### 双模型支持
- **Flash**: 2-3秒，最高 1024px — 快速迭代
- **Pro**: 5-8秒，最高 4K — 最终成品

</td>
</tr>
<tr>
<td width="50%">

### 智能模型选择
服务器根据提示词自动选择最佳模型。说"快速草图"用 Flash，说"4K 专业"用 Pro。

</td>
<td width="50%">

### Google 搜索增强
Pro 模型使用来自 Google 搜索的真实世界知识，生成更准确、更真实的图像。

</td>
</tr>
<tr>
<td width="50%">

### 灵活宽高比
支持所有常用比例：`1:1`、`16:9`、`9:16`、`4:3`、`3:2`、`21:9` 等。

</td>
<td width="50%">

### 自然语言编辑
使用简单的文字指令编辑现有图片，如"让天空更有戏剧性"或"移除背景"。

</td>
</tr>
</table>

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

<!-- GETTING STARTED -->
## 快速开始

2 分钟内完成配置。

### 前置条件

* 从 [Google AI Studio](https://aistudio.google.com/apikey) **免费**获取 Gemini API Key
* 已安装 [Claude Desktop](https://claude.ai/download)

### 安装配置

**添加到 Claude Desktop 配置文件：**

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
<summary>📁 <b>配置文件位置</b></summary>

| 平台 | 路径 |
|------|------|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |

</details>

<details>
<summary>🔄 <b>更新到最新版本</b></summary>

使用 `uvx` 时，包会被缓存到本地。要获取最新版本：

```bash
# 清除该包的缓存
uv cache clean banana-image-mcp

# 然后重启 Claude Desktop
```

或在配置中指定具体版本：

```json
"args": ["banana-image-mcp==1.0.1"]
```

</details>

<details>
<summary>🔌 <b>其他 MCP 客户端（Cursor、VS Code、Cline 等）</b></summary>

其他 MCP 兼容客户端的配置相同。只需将服务器配置添加到客户端的 MCP 配置文件中。

</details>

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

<!-- USAGE EXAMPLES -->
## 使用方式

直接让 Claude 生成图片：

```text
"生成一只穿着宇航服的可爱猫咪"

"创建一张咖啡杯的专业产品照片，4K 画质"

"制作一个 16:9 的 YouTube 烹饪视频缩略图"

"编辑这张图片：让天空更有戏剧性"
```

### 模型对比

| 模型 | 速度 | 最大分辨率 | 适用场景 |
|------|------|-----------|----------|
| **Gemini 2.5 Flash** | 2-3秒 | 1024px | 快速草图、迭代、原型 |
| **Gemini 3 Pro** | 5-8秒 | **4K (3840px)** | 成品、营销素材、专业作品 |

服务器**默认使用 Pro 模型**以获得最佳画质。通过关键词控制：

| 这样说... | 使用模型 |
|-----------|----------|
| "快速草图"、"草稿"、"原型" | Flash |
| "4K"、"专业"、"高质量" | Pro |
| （默认） | Pro |

### 参数说明

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

### 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `GEMINI_API_KEY` | **是** | - | Gemini API 密钥 |
| `IMAGE_OUTPUT_DIR` | 否 | `~/banana-images` | 图片保存目录 |

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

<!-- USE CASES -->
## 创作示例

<table>
<tr>
<td align="center" width="33%">
<b>产品摄影</b><br/>
专业的影棚布光效果
</td>
<td align="center" width="33%">
<b>概念艺术</b><br/>
奇幻风景、角色设计
</td>
<td align="center" width="33%">
<b>营销素材</b><br/>
社交图片、横幅、缩略图
</td>
</tr>
<tr>
<td align="center" width="33%">
<b>技术图表</b><br/>
流程图、架构图
</td>
<td align="center" width="33%">
<b>写实照片</b><br/>
肖像、自然、城市摄影
</td>
<td align="center" width="33%">
<b>UI/UX 原型</b><br/>
应用界面、网页设计
</td>
</tr>
</table>

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

<!-- ROADMAP -->
## 路线图

- [x] 4K 分辨率输出（最高 3840px）
- [x] 双模型支持（Flash + Pro）
- [x] Google 搜索增强
- [x] 灵活宽高比
- [x] 自然语言图片编辑
- [x] GitHub Actions CI/CD
- [ ] 批量图片生成
- [ ] 图生图转换
- [ ] 视频生成支持
- [ ] 本地模型支持（Ollama）

查看 [open issues](https://github.com/zengwenliang416/banana-image-mcp/issues) 获取完整的功能建议和已知问题列表。

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

<!-- DEVELOPMENT -->
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

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

<!-- CONTRIBUTING -->
## 参与贡献

贡献让开源社区变得精彩。欢迎任何形式的贡献！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 发起 Pull Request

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

<!-- LICENSE -->
## 许可证

基于 MIT 许可证分发。详见 `LICENSE` 文件。

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

<!-- CONTACT -->
## 联系方式

Wenliang Zeng - [@zengwenliang416](https://github.com/zengwenliang416)

项目链接：[https://github.com/zengwenliang416/banana-image-mcp](https://github.com/zengwenliang416/banana-image-mcp)

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

<!-- ACKNOWLEDGMENTS -->
## 致谢

* [FastMCP](https://github.com/jlowin/fastmcp) - 本服务器使用的 MCP 框架
* [Google Gemini](https://ai.google.dev/) - 图像生成背后的 AI 模型
* [Anthropic MCP](https://modelcontextprotocol.io/) - 协议规范
* [Best-README-Template](https://github.com/othneildrew/Best-README-Template) - README 设计灵感

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/zengwenliang416/banana-image-mcp.svg?style=for-the-badge
[contributors-url]: https://github.com/zengwenliang416/banana-image-mcp/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/zengwenliang416/banana-image-mcp.svg?style=for-the-badge
[forks-url]: https://github.com/zengwenliang416/banana-image-mcp/network/members
[stars-shield]: https://img.shields.io/github/stars/zengwenliang416/banana-image-mcp.svg?style=for-the-badge
[stars-url]: https://github.com/zengwenliang416/banana-image-mcp/stargazers
[issues-shield]: https://img.shields.io/github/issues/zengwenliang416/banana-image-mcp.svg?style=for-the-badge
[issues-url]: https://github.com/zengwenliang416/banana-image-mcp/issues
[license-shield]: https://img.shields.io/github/license/zengwenliang416/banana-image-mcp.svg?style=for-the-badge
[license-url]: https://github.com/zengwenliang416/banana-image-mcp/blob/main/LICENSE
[pypi-shield]: https://img.shields.io/pypi/v/banana-image-mcp?style=for-the-badge&color=blue
[pypi-url]: https://pypi.org/project/banana-image-mcp/
[downloads-shield]: https://img.shields.io/pypi/dm/banana-image-mcp?style=for-the-badge&color=green

[Python-badge]: https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[FastMCP-badge]: https://img.shields.io/badge/FastMCP-2.0+-00ADD8?style=for-the-badge
[FastMCP-url]: https://github.com/jlowin/fastmcp
[Gemini-badge]: https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white
[Gemini-url]: https://ai.google.dev/
[uv-badge]: https://img.shields.io/badge/uv-Package_Manager-DE5FE9?style=for-the-badge
[uv-url]: https://github.com/astral-sh/uv
