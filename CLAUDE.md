# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains a production-ready **Banana Image MCP Server** - an AI-powered image generation and editing server that leverages Google's Gemini models through the FastMCP framework. The codebase implements a complete MCP (Model Context Protocol) server with modular architecture, comprehensive error handling, and production-ready features.

### Key Capabilities

- **4K Resolution**: Up to 3840px professional-grade outputs
- **Google Search Grounding**: Real-world knowledge integration for factual accuracy
- **Advanced Reasoning**: Configurable thinking levels (LOW/HIGH) for complex compositions
- **Media Resolution Control**: Fine-grained vision processing tuning
- **Intelligent Model Selection**: Automatic routing based on prompt analysis

### Architecture

- `ModelSelector`: Service for intelligent model routing and selection logic
- `ProImageService`: Dedicated service for Gemini 3 Pro Image operations
- `FlashImageService`: Service for Gemini 2.5 Flash Image operations
- `BaseImageService`: Abstract base class for image services
- Multi-tier configuration: `ModelSelectionConfig`, `ProImageConfig` alongside existing `GeminiConfig`

## Development Commands

### Environment Setup
```bash
# Using uv (recommended)
uv sync

# Set up environment
cp .env.example .env
# Edit .env to add your GEMINI_API_KEY
```

### Running the Server
```bash
# FastMCP CLI (recommended for development)
fastmcp dev banana_image_mcp.server:create_app

# Direct Python execution
python -m banana_image_mcp.server

# HTTP transport mode
FASTMCP_TRANSPORT=http python -m banana_image_mcp.server
```

### Development Workflow
```bash
# Start development server (clean startup)
./scripts/cleanup-ports.sh && fastmcp dev banana_image_mcp.server:create_app

# Code formatting and linting
ruff format .
ruff check .

# Type checking
mypy .

# Run tests
pytest
pytest --cov=. --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
```

## Architecture & Implementation

### Core Architecture Pattern

The codebase follows a **layered architecture** with clear separation of concerns:

1. **Entry Point Layer** (`server.py`) - Application factory and main entry point
2. **Core Layer** (`core/`) - FastMCP server setup and fundamental components
3. **Service Layer** (`services/`) - Business logic and external API integration
4. **Tool Layer** (`tools/`) - MCP tool implementations (generate_image, edit_image, upload_file)
5. **Resource Layer** (`resources/`) - MCP resource implementations (file metadata, templates)
6. **Prompt Layer** (`prompts/`) - Reusable prompt templates organized by category
7. **Configuration Layer** (`config/`) - Settings management and environment handling
8. **Utilities Layer** (`utils/`) - Shared utilities and helper functions

### Key Components

**Server Factory Pattern** (`server.py:create_app()`):
- Factory function used by FastMCP CLI: `fastmcp dev server:create_app`
- Handles configuration loading, service initialization, and dependency injection
- Returns configured `BananaImageMCP` instance ready to run

**Service Layer Architecture**:
- `GeminiClient`: Low-level API wrapper with error handling and retry logic
- `BaseImageService`: Abstract base class for image services
- `FlashImageService`: Service for Gemini 2.5 Flash Image operations
- `ProImageService`: Specialized service for Gemini 3 Pro Image with 4K support and grounding
- `ModelSelector`: Intelligent routing between Flash and Pro models based on prompt analysis
- `ImageStorageService`: Image persistence with thumbnail generation and resource management
- `FileService`: File management and Gemini Files API integration
- `TemplateService`: Prompt template management and parameterization

## License

MIT License - Copyright (c) 2025 Wenliang Zeng
