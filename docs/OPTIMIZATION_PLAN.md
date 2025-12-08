# Nano Banana MCP Server 优化计划

> 文档版本: 1.0.0
> 生成日期: 2025-12-08
> 分析基于: 当前代码库完整审查

---

## 目录

1. [执行摘要](#执行摘要)
2. [当前架构分析](#当前架构分析)
3. [问题识别与分类](#问题识别与分类)
4. [详细优化方案](#详细优化方案)
5. [实施路线图](#实施路线图)
6. [代码示例](#代码示例)
7. [验收标准](#验收标准)

---

## 执行摘要

### 项目健康度评分

| 维度 | 当前分数 | 目标分数 | 差距 |
|------|---------|---------|------|
| 代码复用 (DRY) | 5/10 | 9/10 | -4 |
| 测试覆盖 | 2/10 | 8/10 | -6 |
| 单一职责 (SRP) | 4/10 | 8/10 | -4 |
| 可维护性 | 6/10 | 9/10 | -3 |
| 文档完整性 | 7/10 | 9/10 | -2 |

### 关键发现

1. **严重代码重复**: `ImageService` 和 `ProImageService` 约 60% 代码重复
2. **测试缺失严重**: 仅 1 个测试文件，覆盖率远低于配置的 80% 要求
3. **函数过于复杂**: `register_generate_image_tool` 超过 400 行
4. **服务层职责不清**: 存在 4 个相似的图像服务类

---

## 当前架构分析

### 项目结构

```
nanobanana_mcp_server/
├── server.py                    # 入口点 (工厂模式)
├── config/
│   ├── settings.py              # 配置类 (9 个 dataclass)
│   └── constants.py             # 常量定义
├── core/
│   ├── server.py                # FastMCP 服务器
│   ├── exceptions.py            # 异常类 (6 个)
│   ├── validation.py            # 输入验证
│   └── progress_tracker.py      # 进度追踪
├── services/                    # ⚠️ 问题集中区域
│   ├── gemini_client.py         # API 客户端 (225 行)
│   ├── image_service.py         # Flash 服务 (282 行)
│   ├── pro_image_service.py     # Pro 服务 (397 行) ← 与上面高度重复
│   ├── enhanced_image_service.py# 增强服务 (481 行)
│   ├── file_image_service.py    # 文件服务
│   ├── model_selector.py        # 模型选择
│   └── ...                      # 其他 6 个服务
├── tools/
│   └── generate_image.py        # ⚠️ 单文件 425 行
├── resources/                   # MCP 资源 (4 个文件)
├── prompts/                     # 提示词模板 (3 个文件)
└── utils/                       # 工具函数 (3 个文件)
```

### 服务依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                     services/__init__.py                     │
│                  (12 个全局单例变量)                          │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  GeminiClient   │  │  ImageService   │  │ ProImageService │
│  (API 封装)      │  │  (Flash 模型)   │  │  (Pro 模型)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         │           ┌───────┴───────┐            │
         │           │               │            │
         ▼           ▼               ▼            │
┌─────────────────────────────────────────────────┘
│              ImageStorageService                 │
│              (存储和缩略图)                       │
└─────────────────────────────────────────────────┘
```

---

## 问题识别与分类

### P0 - 严重问题 (必须立即修复)

#### P0-1: 代码重复 - ImageService vs ProImageService

**位置**:
- `services/image_service.py:25-180` (generate_images)
- `services/pro_image_service.py:29-227` (generate_images)

**问题描述**:
两个服务类的核心方法结构几乎完全相同：

| 代码段 | ImageService | ProImageService |
|--------|-------------|-----------------|
| ProgressContext 使用 | ✓ | ✓ |
| 内容构建逻辑 | ✓ | ✓ |
| 循环生成模式 | ✓ | ✓ |
| 存储处理逻辑 | ✓ | ✓ |
| 错误处理模式 | ✓ | ✓ |

**代码对比**:

```python
# ImageService.generate_images (简化)
def generate_images(self, prompt, n=1, ...):
    with ProgressContext(...) as progress:
        progress.update(10, "Preparing...")
        contents = []
        # ... 构建 contents
        for i in range(n):
            try:
                response = self.gemini_client.generate_content(contents)
                images = self.gemini_client.extract_images(response)
                for image_bytes in images:
                    if use_storage and self.storage_service:
                        # 存储逻辑 (约 30 行)
                    else:
                        # 直接返回逻辑 (约 15 行)
            except Exception as e:
                self.logger.error(...)
                continue

# ProImageService.generate_images (简化) - 几乎相同的结构!
def generate_images(self, prompt, n=1, resolution="high", ...):
    with ProgressContext(...) as progress:
        progress.update(5, "Configuring Pro...")
        contents = []
        # ... 构建 contents (略有不同)
        for i in range(n):
            try:
                response = self.gemini_client.generate_content(contents, config=gen_config)
                images = self.gemini_client.extract_images(response)
                for image_bytes in images:
                    if use_storage and self.storage_service:
                        # 存储逻辑 (约 30 行) - 几乎完全相同!
                    else:
                        # 直接返回逻辑 (约 15 行)
            except Exception as e:
                self.logger.error(...)
                continue
```

**影响**:
- 维护成本翻倍
- Bug 修复需要同步两处
- 新功能需要实现两次

---

#### P0-2: 测试覆盖严重不足

**位置**: `tests/` 目录

**当前状态**:
```
tests/
├── __init__.py
└── test_aspect_ratio.py  # 仅此一个测试文件!
```

**配置矛盾**:
```toml
# pyproject.toml
[tool.coverage.report]
fail_under = 80  # 要求 80% 覆盖率
```

**缺失的测试**:

| 模块 | 类/函数 | 优先级 |
|------|---------|--------|
| services/gemini_client.py | GeminiClient | P0 |
| services/image_service.py | ImageService | P0 |
| services/pro_image_service.py | ProImageService | P0 |
| services/model_selector.py | ModelSelector | P0 |
| core/validation.py | 所有验证函数 | P1 |
| core/exceptions.py | 异常类 | P1 |
| tools/generate_image.py | register_generate_image_tool | P1 |
| utils/image_utils.py | 图像处理函数 | P2 |

---

#### P0-3: 工具函数过于复杂

**位置**: `tools/generate_image.py:16-419`

**问题**: `register_generate_image_tool` 函数超过 **400 行**

**复杂度分析**:
```
函数总行数: 403 行
嵌套层级: 最深 6 层
分支数量: 15+ 个 if/else
职责数量: 7+ 个不同职责
```

**职责混杂**:
1. 参数验证 (约 50 行)
2. 模型选择 (约 30 行)
3. 模式检测 (约 20 行)
4. 输入图像处理 (约 40 行)
5. 服务调用 (约 30 行)
6. 响应构建 (约 100 行)
7. 元数据组装 (约 80 行)

---

### P1 - 中等问题 (应在近期修复)

#### P1-1: 服务层职责不清

**问题**: 存在 4 个相似的图像服务类

```
ImageService          (282 行) - Flash 模型基础服务
ProImageService       (397 行) - Pro 模型服务
EnhancedImageService  (481 行) - 增强版服务
FileImageService      (??  行) - 文件服务
```

**职责重叠**:
- `generate_images` 方法在多个类中重复
- `edit_image` 方法在多个类中重复
- 存储逻辑在多处重复

---

#### P1-2: 异常类层次结构过于简单

**位置**: `core/exceptions.py:3-6`

```python
class NanoBananaError(Exception):
    """Base exception class for all Nano Banana errors."""
    pass  # 没有任何额外功能!
```

**问题**:
- 基类没有提供错误码
- 没有上下文信息
- 没有序列化支持
- 无法区分用户错误和系统错误

---

#### P1-3: 服务定位器模式 (全局单例)

**位置**: `services/__init__.py:40-94`

```python
# 12 个全局变量
_gemini_client = None
_file_image_service = None
_file_service = None
_enhanced_image_service = None
_files_api_service = None
_image_database_service = None
_image_storage_service = None
_maintenance_service = None
_flash_gemini_client = None
_pro_gemini_client = None
_pro_image_service = None
_model_selector = None
```

**问题**:
- 难以进行单元测试 (需要 mock 全局变量)
- 服务生命周期不明确
- 隐式依赖关系

---

### P2 - 轻微问题 (可在后续优化)

#### P2-1: 配置类字段冗余

`FlashImageConfig` 和 `ProImageConfig` 共享多个字段

#### P2-2: 缺少接口/协议抽象

服务类之间没有定义明确的 Protocol/ABC

#### P2-3: 缺少异步支持

所有 I/O 操作都是同步的

---

## 详细优化方案

### 方案 1: 引入抽象基类解决代码重复

**目标**: 消除 ImageService 和 ProImageService 的代码重复

**设计**:

```python
# services/base_image_service.py (新文件)

from abc import ABC, abstractmethod
from typing import Any, Protocol

class ImageGenerationConfig(Protocol):
    """图像生成配置协议"""
    model_name: str
    default_image_format: str


class BaseImageService(ABC):
    """图像服务抽象基类

    提取 ImageService 和 ProImageService 的共同逻辑
    """

    def __init__(
        self,
        gemini_client: GeminiClient,
        config: ImageGenerationConfig,
        storage_service: ImageStorageService | None = None,
    ):
        self.gemini_client = gemini_client
        self.config = config
        self.storage_service = storage_service
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def _build_generation_config(self, **kwargs) -> dict[str, Any]:
        """构建模型特定的生成配置 (子类实现)"""
        ...

    @abstractmethod
    def _build_metadata(self, **kwargs) -> dict[str, Any]:
        """构建模型特定的元数据 (子类实现)"""
        ...

    @abstractmethod
    def _enhance_prompt(self, prompt: str, **kwargs) -> str:
        """增强提示词 (子类可选覆盖)"""
        return prompt

    def generate_images(
        self,
        prompt: str,
        n: int = 1,
        negative_prompt: str | None = None,
        system_instruction: str | None = None,
        input_images: list[tuple[str, str]] | None = None,
        use_storage: bool = True,
        **model_specific_params,
    ) -> tuple[list[MCPImage], list[dict[str, Any]]]:
        """通用图像生成方法

        共同逻辑在基类实现，模型特定逻辑通过抽象方法扩展
        """
        operation_name = self._get_operation_name()

        with ProgressContext(
            operation_name,
            f"Generating {n} image(s)...",
            {"prompt": prompt[:100], "count": n}
        ) as progress:
            # 1. 准备阶段 (共同)
            progress.update(10, "Preparing generation request...")
            contents = self._build_contents(
                prompt, negative_prompt, system_instruction, input_images
            )

            # 2. 获取模型特定配置 (子类实现)
            gen_config = self._build_generation_config(**model_specific_params)

            # 3. 生成循环 (共同)
            all_images, all_metadata = self._generation_loop(
                contents, n, prompt, gen_config, use_storage, progress,
                **model_specific_params
            )

            return all_images, all_metadata

    def _build_contents(
        self,
        prompt: str,
        negative_prompt: str | None,
        system_instruction: str | None,
        input_images: list[tuple[str, str]] | None,
    ) -> list:
        """构建 API 请求内容 (共同逻辑)"""
        contents = []

        if system_instruction:
            contents.append(system_instruction)

        full_prompt = self._enhance_prompt(prompt)
        if negative_prompt:
            full_prompt += f"\n\nConstraints (avoid): {negative_prompt}"
        contents.append(full_prompt)

        if input_images:
            images_b64, mime_types = zip(*input_images)
            image_parts = self.gemini_client.create_image_parts(
                list(images_b64), list(mime_types)
            )
            contents = image_parts + contents

        return contents

    def _generation_loop(
        self,
        contents: list,
        n: int,
        prompt: str,
        gen_config: dict,
        use_storage: bool,
        progress: ProgressContext,
        **kwargs,
    ) -> tuple[list[MCPImage], list[dict]]:
        """生成循环 (共同逻辑)"""
        all_images = []
        all_metadata = []

        for i in range(n):
            try:
                progress.update(
                    20 + (i * 60 // n),
                    f"Generating image {i + 1}/{n}..."
                )

                response = self.gemini_client.generate_content(
                    contents, config=gen_config if gen_config else None
                )
                images = self.gemini_client.extract_images(response)

                for j, image_bytes in enumerate(images):
                    # 构建元数据 (子类特定)
                    metadata = self._build_metadata(
                        prompt=prompt,
                        response_index=i + 1,
                        image_index=j + 1,
                        **kwargs
                    )

                    # 存储处理 (共同)
                    mcp_image = self._process_image_output(
                        image_bytes, metadata, use_storage
                    )
                    all_images.append(mcp_image)
                    all_metadata.append(metadata)

            except Exception as e:
                self.logger.error(f"Failed to generate image {i + 1}: {e}")
                continue

        return all_images, all_metadata

    def _process_image_output(
        self,
        image_bytes: bytes,
        metadata: dict,
        use_storage: bool,
    ) -> MCPImage:
        """处理图像输出 (共同逻辑)"""
        if use_storage and self.storage_service:
            stored_info = self.storage_service.store_image(
                image_bytes,
                f"image/{self.config.default_image_format}",
                metadata
            )

            thumbnail_b64 = self.storage_service.get_thumbnail_base64(stored_info.id)
            if thumbnail_b64:
                thumbnail_bytes = base64.b64decode(thumbnail_b64)
                return MCPImage(data=thumbnail_bytes, format="jpeg")

        # 直接返回
        return MCPImage(
            data=image_bytes,
            format=self.config.default_image_format
        )

    @abstractmethod
    def _get_operation_name(self) -> str:
        """获取操作名称用于进度追踪"""
        ...
```

**子类实现**:

```python
# services/image_service.py (重构后)

class ImageService(BaseImageService):
    """Gemini Flash 图像服务"""

    def _get_operation_name(self) -> str:
        return "flash_image_generation"

    def _build_generation_config(self, **kwargs) -> dict[str, Any]:
        # Flash 不需要特殊配置
        return {}

    def _build_metadata(
        self,
        prompt: str,
        response_index: int,
        image_index: int,
        **kwargs,
    ) -> dict[str, Any]:
        return {
            "model": "gemini-2.5-flash-image",
            "model_tier": "flash",
            "response_index": response_index,
            "image_index": image_index,
            "prompt": prompt,
            "mime_type": f"image/{self.config.default_image_format}",
            "synthid_watermark": True,
        }

    def _enhance_prompt(self, prompt: str, **kwargs) -> str:
        # Flash 使用原始提示词
        return prompt


# services/pro_image_service.py (重构后)

class ProImageService(BaseImageService):
    """Gemini Pro 图像服务"""

    def _get_operation_name(self) -> str:
        return "pro_image_generation"

    def _build_generation_config(
        self,
        thinking_level: ThinkingLevel | None = None,
        media_resolution: MediaResolution | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        thinking = thinking_level or self.config.default_thinking_level
        media_res = media_resolution or self.config.default_media_resolution

        return {
            "thinking_level": thinking.value,
            "media_resolution": media_res.value,
        }

    def _build_metadata(
        self,
        prompt: str,
        response_index: int,
        image_index: int,
        resolution: str = "high",
        thinking_level: ThinkingLevel | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        return {
            "model": self.config.model_name,
            "model_tier": "pro",
            "response_index": response_index,
            "image_index": image_index,
            "resolution": resolution,
            "thinking_level": (thinking_level or self.config.default_thinking_level).value,
            "prompt": prompt,
            "mime_type": f"image/{self.config.default_image_format}",
            "synthid_watermark": True,
        }

    def _enhance_prompt(self, prompt: str, resolution: str = "high", **kwargs) -> str:
        """Pro 模型的提示词增强"""
        resolution_hints = {
            "4k": "Create in ultra-high 4K resolution with exceptional detail.",
            "high": "Create in high resolution with fine details.",
            "2k": "Create in 2K resolution.",
            "1k": "Create in standard resolution.",
        }
        hint = resolution_hints.get(resolution, "")
        return f"{prompt}\n\n{hint}" if hint else prompt
```

**收益**:
- 代码量减少约 40%
- 维护点从 2 个减少到 1 个
- 新模型支持只需创建新子类

---

### 方案 2: 拆分工具函数

**目标**: 将 400+ 行的 `register_generate_image_tool` 拆分为职责单一的函数

**设计**:

```python
# tools/generate_image.py (重构后)

def register_generate_image_tool(server: FastMCP):
    """注册图像生成工具"""

    @server.tool(annotations={...})
    def generate_image(...) -> ToolResult:
        logger = logging.getLogger(__name__)

        try:
            # 1. 输入处理
            input_paths = _collect_input_paths(
                input_image_path_1, input_image_path_2, input_image_path_3
            )

            # 2. 验证
            _validate_inputs(mode, input_paths, file_id)

            # 3. 模式检测
            detected_mode = _detect_mode(mode, file_id, input_paths)

            # 4. 模型选择
            tier, selected_service, model_info = _select_model(
                prompt, model_tier, n, resolution, thinking_level, enable_grounding
            )

            # 5. 执行生成/编辑
            thumbnail_images, metadata = _execute_operation(
                detected_mode, selected_service, prompt, n,
                file_id, input_paths, aspect_ratio, ...
            )

            # 6. 构建响应
            return _build_response(
                detected_mode, thumbnail_images, metadata,
                model_info, tier, ...
            )

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise


def _collect_input_paths(
    path1: str | None,
    path2: str | None,
    path3: str | None,
) -> list[str] | None:
    """收集输入图像路径"""
    paths = [p for p in [path1, path2, path3] if p]
    return paths if paths else None


def _validate_inputs(
    mode: str,
    input_paths: list[str] | None,
    file_id: str | None,
) -> None:
    """验证输入参数"""
    if mode not in ["auto", "generate", "edit"]:
        raise ValidationError("Mode must be 'auto', 'generate', or 'edit'")

    if input_paths:
        if len(input_paths) > MAX_INPUT_IMAGES:
            raise ValidationError(f"Maximum {MAX_INPUT_IMAGES} input images allowed")

        for i, path in enumerate(input_paths):
            if not os.path.exists(path):
                raise ValidationError(f"Input image {i + 1} not found: {path}")
            if not os.path.isfile(path):
                raise ValidationError(f"Input image {i + 1} is not a file: {path}")


def _detect_mode(
    mode: str,
    file_id: str | None,
    input_paths: list[str] | None,
) -> str:
    """检测操作模式"""
    if mode != "auto":
        return mode

    if file_id or (input_paths and len(input_paths) == 1):
        return "edit"
    return "generate"


def _select_model(
    prompt: str,
    requested_tier: str,
    n: int,
    resolution: str,
    thinking_level: str,
    enable_grounding: bool,
) -> tuple[ModelTier, Any, dict]:
    """选择最佳模型"""
    from ..services import get_model_selector

    tier = ModelTier(requested_tier) if requested_tier else ModelTier.AUTO
    model_selector = get_model_selector()

    selected_service, selected_tier = model_selector.select_model(
        prompt=prompt,
        requested_tier=tier,
        n=n,
        resolution=resolution,
        thinking_level=thinking_level,
        enable_grounding=enable_grounding,
    )

    model_info = model_selector.get_model_info(selected_tier)
    return selected_tier, selected_service, model_info


def _execute_operation(
    mode: str,
    service: Any,
    prompt: str,
    n: int,
    file_id: str | None,
    input_paths: list[str] | None,
    aspect_ratio: str | None,
    **kwargs,
) -> tuple[list, list]:
    """执行图像操作"""
    enhanced_service = _get_enhanced_image_service()

    if mode == "edit" and file_id:
        return enhanced_service.edit_image_by_file_id(
            file_id=file_id, edit_prompt=prompt
        )

    if mode == "edit" and input_paths and len(input_paths) == 1:
        return enhanced_service.edit_image_by_path(
            instruction=prompt, file_path=input_paths[0]
        )

    # 生成模式
    input_images = _load_input_images(input_paths) if input_paths else None
    return enhanced_service.generate_images(
        prompt=prompt,
        n=n,
        input_images=input_images,
        aspect_ratio=aspect_ratio,
        **kwargs,
    )


def _load_input_images(paths: list[str]) -> list[tuple[str, str]]:
    """加载输入图像"""
    images = []
    for path in paths:
        with open(path, "rb") as f:
            image_bytes = f.read()

        mime_type, _ = mimetypes.guess_type(path)
        if not mime_type or not mime_type.startswith("image/"):
            mime_type = "image/png"

        base64_data = base64.b64encode(image_bytes).decode("utf-8")
        images.append((base64_data, mime_type))

    return images


def _build_response(
    mode: str,
    thumbnail_images: list,
    metadata: list,
    model_info: dict,
    tier: ModelTier,
    **kwargs,
) -> ToolResult:
    """构建工具响应"""
    if not metadata:
        return _build_error_response(mode)

    summary = _build_summary(mode, metadata, model_info, tier, **kwargs)
    structured = _build_structured_content(mode, metadata, model_info, tier, **kwargs)

    content = [TextContent(type="text", text=summary), *thumbnail_images]
    return ToolResult(content=content, structured_content=structured)


def _build_summary(mode: str, metadata: list, model_info: dict, tier: ModelTier, **kwargs) -> str:
    """构建摘要文本"""
    action = "Edited" if mode == "edit" else "Generated"
    lines = [
        f"✅ {action} {len(metadata)} image(s) with {model_info['emoji']} {model_info['name']}.",
        f"📊 **Model**: {tier.value.upper()} tier",
    ]

    # ... 其他摘要内容

    return "\n".join(lines)


def _build_structured_content(
    mode: str,
    metadata: list,
    model_info: dict,
    tier: ModelTier,
    **kwargs,
) -> dict:
    """构建结构化内容"""
    return {
        "mode": mode,
        "model_tier": tier.value,
        "model_name": model_info["name"],
        "images": metadata,
        # ... 其他字段
    }


def _build_error_response(mode: str) -> ToolResult:
    """构建错误响应"""
    summary = f"❌ Failed to {mode} image(s): No valid results returned."
    return ToolResult(
        content=[TextContent(type="text", text=summary)],
        structured_content={"error": "no_valid_metadata", "mode": mode},
    )
```

**收益**:
- 每个函数职责单一，平均 20-30 行
- 更易于单元测试
- 更易于理解和维护

---

### 方案 3: 增强异常类

**目标**: 提供更丰富的错误信息

**设计**:

```python
# core/exceptions.py (重构后)

from enum import Enum
from typing import Any


class ErrorCode(Enum):
    """错误码枚举"""
    # 验证错误 (1xxx)
    VALIDATION_EMPTY_INPUT = "E1001"
    VALIDATION_INVALID_FORMAT = "E1002"
    VALIDATION_SIZE_EXCEEDED = "E1003"
    VALIDATION_SECURITY_RISK = "E1004"

    # 配置错误 (2xxx)
    CONFIG_MISSING_API_KEY = "E2001"
    CONFIG_INVALID_VALUE = "E2002"

    # API 错误 (3xxx)
    API_CONNECTION_FAILED = "E3001"
    API_RATE_LIMITED = "E3002"
    API_INVALID_RESPONSE = "E3003"

    # 处理错误 (4xxx)
    PROCESSING_IMAGE_FAILED = "E4001"
    PROCESSING_STORAGE_FAILED = "E4002"

    # 文件错误 (5xxx)
    FILE_NOT_FOUND = "E5001"
    FILE_READ_FAILED = "E5002"
    FILE_WRITE_FAILED = "E5003"


class NanoBananaError(Exception):
    """基础异常类

    提供错误码、上下文信息和序列化支持
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode | None = None,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.cause = cause

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        result = {
            "error": self.__class__.__name__,
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
        parts = [self.message]
        if self.error_code:
            parts.insert(0, f"[{self.error_code.value}]")
        return " ".join(parts)


class ValidationError(NanoBananaError):
    """验证错误"""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if field:
            context["field"] = field
        if value is not None:
            context["value"] = str(value)[:100]  # 截断长值

        super().__init__(message, context=context, **kwargs)


class GeminiAPIError(NanoBananaError):
    """Gemini API 错误"""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if status_code:
            context["status_code"] = status_code
        if response_body:
            context["response"] = response_body[:500]

        super().__init__(message, context=context, **kwargs)


class ImageProcessingError(NanoBananaError):
    """图像处理错误"""
    pass


class FileOperationError(NanoBananaError):
    """文件操作错误"""
    pass


class ConfigurationError(NanoBananaError):
    """配置错误"""
    pass
```

**使用示例**:

```python
# 使用增强的异常
raise ValidationError(
    "Prompt too long",
    error_code=ErrorCode.VALIDATION_SIZE_EXCEEDED,
    field="prompt",
    value=prompt,
)

# 输出:
# [E1003] Prompt too long
# context: {"field": "prompt", "value": "..."}
```

---

### 方案 4: 补充测试

**目标**: 达到 80% 测试覆盖率

**测试结构**:

```
tests/
├── __init__.py
├── conftest.py                 # 共享 fixtures
├── unit/
│   ├── __init__.py
│   ├── test_gemini_client.py   # GeminiClient 单元测试
│   ├── test_image_service.py   # ImageService 单元测试
│   ├── test_pro_image_service.py
│   ├── test_model_selector.py
│   ├── test_validation.py
│   └── test_exceptions.py
├── integration/
│   ├── __init__.py
│   ├── test_generate_image_tool.py
│   └── test_service_integration.py
└── fixtures/
    ├── sample_image.png
    └── mock_responses.json
```

**conftest.py 示例**:

```python
# tests/conftest.py

import pytest
from unittest.mock import Mock, MagicMock

from nanobanana_mcp_server.config.settings import (
    ServerConfig,
    GeminiConfig,
    FlashImageConfig,
    ProImageConfig,
)


@pytest.fixture
def mock_server_config():
    """模拟服务器配置"""
    return ServerConfig(gemini_api_key="test-api-key")


@pytest.fixture
def mock_gemini_config():
    """模拟 Gemini 配置"""
    return GeminiConfig()


@pytest.fixture
def mock_flash_config():
    """模拟 Flash 配置"""
    return FlashImageConfig()


@pytest.fixture
def mock_pro_config():
    """模拟 Pro 配置"""
    return ProImageConfig()


@pytest.fixture
def mock_gemini_client(mock_server_config, mock_gemini_config):
    """模拟 Gemini 客户端"""
    from nanobanana_mcp_server.services.gemini_client import GeminiClient

    client = GeminiClient(mock_server_config, mock_gemini_config)
    client._client = Mock()
    client._client.models = Mock()
    client._client.models.generate_content = Mock()

    return client


@pytest.fixture
def mock_storage_service():
    """模拟存储服务"""
    service = Mock()
    service.store_image = Mock(return_value=Mock(
        id="test-id",
        size_bytes=1024,
        thumbnail_size_bytes=256,
        width=1024,
        height=1024,
        expires_at=None,
    ))
    service.get_thumbnail_base64 = Mock(return_value="base64data")
    return service


@pytest.fixture
def sample_image_bytes():
    """示例图像字节数据"""
    # 创建一个最小的有效 PNG
    import io
    from PIL import Image

    img = Image.new("RGB", (100, 100), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
```

**单元测试示例**:

```python
# tests/unit/test_image_service.py

import pytest
from unittest.mock import Mock, patch

from nanobanana_mcp_server.services.image_service import ImageService
from nanobanana_mcp_server.core.exceptions import ValidationError


class TestImageServiceGenerate:
    """ImageService.generate_images 测试"""

    def test_generate_single_image_success(
        self,
        mock_gemini_client,
        mock_gemini_config,
        mock_storage_service,
        sample_image_bytes,
    ):
        """测试成功生成单张图像"""
        # Arrange
        mock_gemini_client._client.models.generate_content.return_value = Mock(
            candidates=[Mock(content=Mock(parts=[Mock(inline_data=Mock(data=sample_image_bytes))]))]
        )
        mock_gemini_client.extract_images = Mock(return_value=[sample_image_bytes])

        service = ImageService(
            mock_gemini_client,
            mock_gemini_config,
            mock_storage_service,
        )

        # Act
        images, metadata = service.generate_images(
            prompt="A red apple",
            n=1,
            use_storage=True,
        )

        # Assert
        assert len(images) == 1
        assert len(metadata) == 1
        assert metadata[0]["prompt"] == "A red apple"
        mock_storage_service.store_image.assert_called_once()

    def test_generate_multiple_images(
        self,
        mock_gemini_client,
        mock_gemini_config,
        mock_storage_service,
        sample_image_bytes,
    ):
        """测试生成多张图像"""
        mock_gemini_client.extract_images = Mock(return_value=[sample_image_bytes])

        service = ImageService(
            mock_gemini_client,
            mock_gemini_config,
            mock_storage_service,
        )

        images, metadata = service.generate_images(
            prompt="Test prompt",
            n=3,
            use_storage=True,
        )

        assert len(images) == 3
        assert len(metadata) == 3

    def test_generate_without_storage(
        self,
        mock_gemini_client,
        mock_gemini_config,
        sample_image_bytes,
    ):
        """测试不使用存储的生成"""
        mock_gemini_client.extract_images = Mock(return_value=[sample_image_bytes])

        service = ImageService(
            mock_gemini_client,
            mock_gemini_config,
            storage_service=None,
        )

        images, metadata = service.generate_images(
            prompt="Test prompt",
            n=1,
            use_storage=False,
        )

        assert len(images) == 1

    def test_generate_with_negative_prompt(
        self,
        mock_gemini_client,
        mock_gemini_config,
        mock_storage_service,
        sample_image_bytes,
    ):
        """测试带负面提示词的生成"""
        mock_gemini_client.extract_images = Mock(return_value=[sample_image_bytes])

        service = ImageService(
            mock_gemini_client,
            mock_gemini_config,
            mock_storage_service,
        )

        images, metadata = service.generate_images(
            prompt="A beautiful landscape",
            negative_prompt="blurry, low quality",
            n=1,
        )

        # 验证负面提示词被添加到内容中
        call_args = mock_gemini_client.generate_content.call_args
        contents = call_args[0][0]
        assert "blurry, low quality" in str(contents)

    def test_generate_handles_api_error(
        self,
        mock_gemini_client,
        mock_gemini_config,
        mock_storage_service,
    ):
        """测试 API 错误处理"""
        mock_gemini_client.generate_content = Mock(
            side_effect=Exception("API Error")
        )

        service = ImageService(
            mock_gemini_client,
            mock_gemini_config,
            mock_storage_service,
        )

        # 应该继续而不是崩溃
        images, metadata = service.generate_images(
            prompt="Test",
            n=2,
        )

        # 没有图像生成但不应该抛出异常
        assert len(images) == 0


class TestImageServiceEdit:
    """ImageService.edit_image 测试"""

    def test_edit_image_success(
        self,
        mock_gemini_client,
        mock_gemini_config,
        mock_storage_service,
        sample_image_bytes,
    ):
        """测试成功编辑图像"""
        mock_gemini_client.extract_images = Mock(return_value=[sample_image_bytes])

        service = ImageService(
            mock_gemini_client,
            mock_gemini_config,
            mock_storage_service,
        )

        import base64
        base64_image = base64.b64encode(sample_image_bytes).decode()

        images, count = service.edit_image(
            instruction="Make it blue",
            base_image_b64=base64_image,
            mime_type="image/png",
        )

        assert len(images) == 1
        assert count == 1

    def test_edit_invalid_mime_type(
        self,
        mock_gemini_client,
        mock_gemini_config,
        mock_storage_service,
    ):
        """测试无效 MIME 类型"""
        service = ImageService(
            mock_gemini_client,
            mock_gemini_config,
            mock_storage_service,
        )

        with pytest.raises(ValidationError):
            service.edit_image(
                instruction="Edit",
                base_image_b64="base64data",
                mime_type="text/plain",  # 无效
            )
```

---

## 实施路线图

### 阶段 1: 基础设施 (1-2 天)

| 任务 | 文件 | 复杂度 | 预计时间 |
|------|------|--------|----------|
| 1.1 创建测试基础设施 | `tests/conftest.py` | 低 | 2h |
| 1.2 增强异常类 | `core/exceptions.py` | 低 | 2h |
| 1.3 添加 ErrorCode 枚举 | `core/exceptions.py` | 低 | 1h |

### 阶段 2: 核心重构 (3-5 天)

| 任务 | 文件 | 复杂度 | 预计时间 |
|------|------|--------|----------|
| 2.1 创建 BaseImageService | `services/base_image_service.py` | 高 | 4h |
| 2.2 重构 ImageService | `services/image_service.py` | 中 | 3h |
| 2.3 重构 ProImageService | `services/pro_image_service.py` | 中 | 3h |
| 2.4 添加服务单元测试 | `tests/unit/test_*_service.py` | 中 | 4h |

### 阶段 3: 工具层重构 (2-3 天)

| 任务 | 文件 | 复杂度 | 预计时间 |
|------|------|--------|----------|
| 3.1 拆分 generate_image_tool | `tools/generate_image.py` | 高 | 4h |
| 3.2 添加工具单元测试 | `tests/unit/test_generate_image.py` | 中 | 3h |
| 3.3 添加集成测试 | `tests/integration/` | 中 | 3h |

### 阶段 4: 清理与优化 (1-2 天)

| 任务 | 文件 | 复杂度 | 预计时间 |
|------|------|--------|----------|
| 4.1 整合/删除冗余服务类 | `services/` | 中 | 3h |
| 4.2 更新文档 | `docs/`, `README.md` | 低 | 2h |
| 4.3 最终测试覆盖率检查 | - | 低 | 1h |

### 依赖关系图

```
阶段 1 ─────┬────────────────────────────────────────┐
            │                                        │
            ▼                                        │
阶段 2 (核心重构)                                    │
  2.1 → 2.2 → 2.3 → 2.4                             │
            │                                        │
            └──────────────┐                         │
                           │                         │
                           ▼                         ▼
                    阶段 3 (工具层)            阶段 4 (清理)
                      3.1 → 3.2 → 3.3  ────────→ 4.1 → 4.2 → 4.3
```

---

## 验收标准

### 代码质量

| 指标 | 当前值 | 目标值 | 验证方法 |
|------|--------|--------|----------|
| 测试覆盖率 | ~5% | ≥80% | `pytest --cov` |
| Ruff 检查 | 通过 | 通过 | `ruff check .` |
| Mypy 检查 | 通过 | 通过 | `mypy .` |
| 函数复杂度 | >10 | ≤10 | `ruff --select C901` |
| 最大函数行数 | 400+ | ≤50 | 手动检查 |

### 架构质量

| 指标 | 验证方法 |
|------|----------|
| 无代码重复 | ImageService 和 ProImageService 共享基类 |
| 单一职责 | 每个函数 ≤50 行，职责单一 |
| 可测试性 | 所有服务可通过依赖注入进行测试 |

### 功能验证

```bash
# 1. 服务器正常启动
./scripts/cleanup-ports.sh && fastmcp dev nanobanana_mcp_server.server:create_app

# 2. 测试通过
pytest --cov=. --cov-report=term-missing

# 3. 类型检查通过
mypy .

# 4. 代码检查通过
ruff check .
```

---

## 附录

### A. 相关文件清单

**需要修改的文件**:
- `services/base_image_service.py` (新建)
- `services/image_service.py` (重构)
- `services/pro_image_service.py` (重构)
- `tools/generate_image.py` (拆分)
- `core/exceptions.py` (增强)

**需要新建的文件**:
- `tests/conftest.py`
- `tests/unit/test_gemini_client.py`
- `tests/unit/test_image_service.py`
- `tests/unit/test_pro_image_service.py`
- `tests/unit/test_model_selector.py`
- `tests/unit/test_validation.py`
- `tests/integration/test_generate_image_tool.py`

### B. 参考资料

- [Python ABC 文档](https://docs.python.org/3/library/abc.html)
- [pytest 文档](https://docs.pytest.org/)
- [FastMCP 文档](https://github.com/jlowin/fastmcp)
- [Google Gemini API](https://ai.google.dev/docs)

---

*文档结束*
