# Nano Banana MCP Server 项目概览

## 项目目的
这是一个生产就绪的 **MCP (Model Context Protocol) 服务器**，用于 AI 图像生成和编辑。
利用 Google Gemini 模型通过 FastMCP 框架提供服务。

## 核心功能
- **图像生成**: 支持文本到图像的生成
- **图像编辑**: 支持基于自然语言指令的图像编辑
- **多模型支持**: 
  - Gemini 2.5 Flash Image (速度优化, 1024px)
  - Gemini 3 Pro Image (质量优化, 最高 4K)
- **智能模型选择**: 根据提示词自动选择最佳模型
- **文件管理**: 通过 Gemini Files API 管理图像文件

## 技术栈
- **语言**: Python 3.11+
- **框架**: FastMCP >= 2.11.0
- **API**: Google GenAI >= 1.41.0
- **图像处理**: Pillow >= 10.4.0
- **数据验证**: Pydantic >= 2.0.0
- **环境管理**: python-dotenv

## 项目结构
```
nanobanana_mcp_server/
├── server.py              # 应用入口点和工厂函数
├── config/                # 配置管理
│   ├── settings.py        # 配置类定义
│   └── constants.py       # 常量定义
├── core/                  # 核心组件
│   ├── server.py          # FastMCP 服务器设置
│   ├── exceptions.py      # 自定义异常
│   ├── validation.py      # 输入验证
│   └── progress_tracker.py# 进度追踪
├── services/              # 业务逻辑层
│   ├── gemini_client.py   # Gemini API 客户端
│   ├── image_service.py   # Flash 图像服务
│   ├── pro_image_service.py # Pro 图像服务
│   ├── model_selector.py  # 模型选择器
│   └── ...                # 其他服务
├── tools/                 # MCP 工具实现
│   ├── generate_image.py  # 图像生成工具
│   ├── upload_file.py     # 文件上传工具
│   └── maintenance.py     # 维护工具
├── resources/             # MCP 资源实现
├── prompts/               # 提示词模板
└── utils/                 # 工具函数
```

## 架构模式
- **分层架构**: Entry Point → Core → Services → Tools/Resources
- **工厂模式**: `create_app()` 函数创建服务器实例
- **服务定位器**: 全局单例管理服务实例
- **策略模式**: 模型选择基于提示词分析
