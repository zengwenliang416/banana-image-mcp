"""generate_image 工具 - MCP 图像生成与编辑的主入口.

该模块是 generate_image 工具的主入口,负责:
1. 注册 FastMCP 工具
2. 协调各子模块完成图像生成/编辑流程

子模块职责:
- generate_image_inputs: 输入收集、验证、加载
- generate_image_mode: 操作模式自动检测
- generate_image_model: 模型智能选择
- generate_image_response: 响应构建
"""

import logging
from typing import Annotated, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from pydantic import Field

from ..config.constants import MAX_INPUT_IMAGE_SIZE_BYTES
from ..config.settings import ModelTier, ThinkingLevel
from ..core.exceptions import ValidationError
from ..services import get_model_selector

# 从子模块导入
from .generate_image_inputs import (
    collect_input_paths,
    load_input_images,
    validate_inputs,
)
from .generate_image_mode import detect_mode
from .generate_image_model import select_model
from .generate_image_response import (
    build_error_response,
    build_structured_content,
    build_summary,
)


def register_generate_image_tool(server: FastMCP):
    """Register the generate_image tool with the FastMCP server."""

    @server.tool(
        annotations={
            "title": "Generate or edit images (Multi-Model: Flash & Pro)",
            "readOnlyHint": True,
            "openWorldHint": True,
        }
    )
    def generate_image(
        prompt: Annotated[
            str,
            Field(
                description="Clear, detailed image prompt. Include subject, composition, "
                "action, location, style, and any text to render. Use the aspect_ratio "
                "parameter to pin a specific canvas shape when needed.",
                min_length=1,
                max_length=8192,
            ),
        ],
        n: Annotated[
            int, Field(description="Requested image count (model may return fewer).", ge=1, le=4)
        ] = 1,
        negative_prompt: Annotated[
            str | None,
            Field(description="Things to avoid (style, objects, text).", max_length=1024),
        ] = None,
        system_instruction: Annotated[
            str | None, Field(description="Optional system tone/style guidance.", max_length=512)
        ] = None,
        input_image_path_1: Annotated[
            str | None,
            Field(description="Path to first input image for composition/conditioning"),
        ] = None,
        input_image_path_2: Annotated[
            str | None,
            Field(description="Path to second input image for composition/conditioning"),
        ] = None,
        input_image_path_3: Annotated[
            str | None,
            Field(description="Path to third input image for composition/conditioning"),
        ] = None,
        file_id: Annotated[
            str | None,
            Field(
                description="Files API file ID to use as input/edit source (e.g., 'files/abc123'). "
                "If provided, this takes precedence over input_image_path_* parameters for the primary input."
            ),
        ] = None,
        mode: Annotated[
            str,
            Field(
                description="Operation mode: 'generate' for new image creation, 'edit' for modifying existing images. "
                "Auto-detected based on input parameters if not specified."
            ),
        ] = "auto",
        model_tier: Annotated[
            str | None,
            Field(
                description="Model tier: 'flash' (speed, 1024px), 'pro' (quality, up to 4K), or 'auto' (smart selection). "
                "Default: 'pro' - uses Pro model for best quality."
            ),
        ] = "pro",
        resolution: Annotated[
            str | None,
            Field(
                description="Output resolution: '4k', '2k', '1k', 'high'. "
                "4K is default for Pro model. Use 'flash' model_tier for faster 1K outputs."
            ),
        ] = "4k",
        thinking_level: Annotated[
            str | None,
            Field(
                description="Reasoning depth for Pro model: 'low' (faster), 'high' (better quality). "
                "Only applies to Pro model. Default: 'high'."
            ),
        ] = "high",
        enable_grounding: Annotated[
            bool,
            Field(
                description="Enable Google Search grounding for factual accuracy (Pro model only). "
                "Useful for real-world subjects. Default: true."
            ),
        ] = True,
        aspect_ratio: Annotated[
            Literal["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"] | None,
            Field(
                description="Optional output aspect ratio (e.g., '16:9'). "
                "See docs for supported values: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9."
            ),
        ] = None,
        _ctx: Context = None,
    ) -> ToolResult:
        """
        Generate new images or edit existing images using natural language instructions.

        Supports multiple input modes:
        1. Pure generation: Just provide a prompt to create new images
        2. Multi-image conditioning: Provide up to 3 input images using input_image_path_1/2/3 parameters
        3. File ID editing: Edit previously uploaded images using Files API ID
        4. File path editing: Edit local images by providing single input image path

        Automatically detects mode based on parameters or can be explicitly controlled.
        Input images are read from the local filesystem to avoid massive token usage.
        Returns both MCP image content blocks and structured JSON with metadata.
        """
        logger = logging.getLogger(__name__)

        try:
            # 1. 收集输入路径
            input_image_paths = collect_input_paths(
                input_image_path_1, input_image_path_2, input_image_path_3
            )

            logger.info(
                f"Generate image request: prompt='{prompt[:50]}...', n={n}, "
                f"paths={input_image_paths}, model_tier={model_tier}, aspect_ratio={aspect_ratio}"
            )

            # 2. 验证输入
            validate_inputs(mode, input_image_paths, file_id)

            # 3. 检测模式
            detected_mode = detect_mode(mode, file_id, input_image_paths)

            # 4. 验证思考深度
            try:
                if thinking_level:
                    _ = ThinkingLevel(thinking_level)
            except ValueError:
                logger.warning(f"Invalid thinking_level '{thinking_level}', defaulting to HIGH")
                thinking_level = "high"

            # 5. 选择模型
            # 注意:select_model 返回的 service 被丢弃,因为 EnhancedImageService 是唯一
            # 实现完整 workflow.md 流程的服务(Files API 上传、数据库记录、缩略图生成).
            # EnhancedImageService 内部始终使用 Pro gemini_client.
            # 此处调用 select_model 仅为获取 model_info 用于报告.
            _selected_service, selected_tier, model_info = select_model(
                prompt=prompt,
                model_tier=model_tier,
                n=n,
                resolution=resolution,
                thinking_level=thinking_level,
                enable_grounding=enable_grounding,
                input_paths=input_image_paths,
                logger=logger,
            )

            # 如果用户请求 Flash 但实际使用 Pro,记录警告
            if selected_tier == ModelTier.FLASH:
                logger.warning(
                    "Flash model requested but EnhancedImageService uses Pro model. "
                    "Using Pro model for full workflow support."
                )
                # 覆盖为 Pro 以保持报告一致性
                selected_tier = ModelTier.PRO
                model_info = get_model_selector().get_model_info(ModelTier.PRO)

            # 解析层级用于结构化内容
            try:
                tier = ModelTier(model_tier) if model_tier else ModelTier.AUTO
            except ValueError:
                tier = ModelTier.AUTO

            # 模式特定验证
            if detected_mode == "edit":
                if not file_id and not input_image_paths:
                    raise ValidationError("Edit mode requires either file_id or input_image_paths")
                if file_id and input_image_paths and len(input_image_paths) > 1:
                    raise ValidationError(
                        "Edit mode with file_id supports only additional input images, not multiple primary inputs"
                    )
                # 编辑模式只支持单张输入图片(无 file_id 时)
                if not file_id and input_image_paths and len(input_image_paths) > 1:
                    raise ValidationError(
                        f"Edit mode supports only 1 input image, got {len(input_image_paths)}. "
                        "Use 'generate' mode for multi-image conditioning."
                    )

            # 获取增强图像服务
            enhanced_image_service = _get_enhanced_image_service()

            # 根据检测到的模式执行
            if detected_mode == "edit" and file_id:
                # 通过 file_id 编辑
                logger.info(f"Edit mode: using file_id {file_id}")
                # 警告:file_id 模式下 input_image_paths 会被忽略
                if input_image_paths:
                    logger.warning(
                        f"file_id provided, input_image_paths ({input_image_paths}) will be ignored. "
                        "Edit by file_id does not support additional input images."
                    )
                thumbnail_images, metadata = enhanced_image_service.edit_image_by_file_id(
                    file_id=file_id, edit_prompt=prompt
                )

            elif detected_mode == "edit" and input_image_paths and len(input_image_paths) == 1:
                # 通过文件路径编辑
                logger.info(f"Edit mode: using file path {input_image_paths[0]}")
                thumbnail_images, metadata = enhanced_image_service.edit_image_by_path(
                    instruction=prompt, file_path=input_image_paths[0]
                )

            else:
                # 生成模式(可选择性使用输入图片进行条件生成)
                logger.info("Generate mode: creating new images")
                if aspect_ratio:
                    logger.info(f"Using aspect ratio override: {aspect_ratio}")

                # 从文件路径读取输入图片
                input_images = None
                if input_image_paths:
                    input_images = load_input_images(
                        input_image_paths, logger, max_size_bytes=MAX_INPUT_IMAGE_SIZE_BYTES
                    )
                    logger.info(f"Loaded {len(input_images)} input images from file paths")

                # 生成图片
                thumbnail_images, metadata = enhanced_image_service.generate_images(
                    prompt=prompt,
                    n=n,
                    negative_prompt=negative_prompt,
                    system_instruction=system_instruction,
                    input_images=input_images,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                )

            # 构建响应
            if metadata:
                # 过滤无效的元数据条目
                metadata = [m for m in metadata if m is not None and isinstance(m, dict)]

                if not metadata:
                    return build_error_response(detected_mode, prompt)

                # 构建摘要
                full_summary = build_summary(
                    mode=detected_mode,
                    metadata=metadata,
                    model_info=model_info,
                    selected_tier=selected_tier,
                    thinking_level=thinking_level,
                    resolution=resolution,
                    enable_grounding=enable_grounding,
                    file_id=file_id,
                    input_paths=input_image_paths,
                    aspect_ratio=aspect_ratio,
                )

                content = [TextContent(type="text", text=full_summary), *thumbnail_images]
            else:
                # 无图片生成时的回退
                summary = "❌ No images were generated. Please check the logs for details."
                content = [TextContent(type="text", text=summary)]

            # 构建结构化内容
            structured_content = build_structured_content(
                mode=detected_mode,
                metadata=metadata,
                model_info=model_info,
                selected_tier=selected_tier,
                tier=tier,
                model_tier=model_tier,
                thinking_level=thinking_level,
                resolution=resolution,
                enable_grounding=enable_grounding,
                n=n,
                thumbnail_count=len(thumbnail_images),
                negative_prompt=negative_prompt,
                input_paths=input_image_paths,
                file_id=file_id,
                aspect_ratio=aspect_ratio,
                prompt=prompt,
            )

            action_verb = "edited" if detected_mode == "edit" else "generated"
            logger.info(
                f"Successfully {action_verb} {len(thumbnail_images)} images in {detected_mode} mode"
            )

            return ToolResult(content=content, structured_content=structured_content)

        except ValidationError as e:
            logger.error(f"Validation error in generate_image: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in generate_image: {e}")
            raise


def _get_enhanced_image_service():
    """获取增强图像服务实例."""
    from ..services import get_enhanced_image_service

    return get_enhanced_image_service()


# ============================================================================
# 向后兼容的重导出(供测试和外部代码使用)
# ============================================================================

# 从子模块重导出私有函数别名
from .generate_image_inputs import (  # noqa: E402
    _collect_input_paths,
    _load_input_images,
    _validate_inputs,
)
from .generate_image_mode import _detect_mode  # noqa: E402
from .generate_image_model import _select_model  # noqa: E402
from .generate_image_response import (  # noqa: E402
    _build_error_response,
    _build_structured_content,
    _build_summary,
)

# 公开 API(按字母排序)
__all__ = [
    "_build_error_response",
    "_build_structured_content",
    "_build_summary",
    "_collect_input_paths",
    "_detect_mode",
    "_load_input_images",
    "_select_model",
    "_validate_inputs",
    "register_generate_image_tool",
]
