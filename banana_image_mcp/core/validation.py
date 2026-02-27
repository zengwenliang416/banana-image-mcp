"""Input validation utilities."""

import contextlib
import os
from pathlib import Path
import re
from typing import NamedTuple

from ..config.constants import SUPPORTED_IMAGE_TYPES
from .exceptions import ValidationError

# ============================================================================
# 路径验证工具
# ============================================================================


class ValidatedImagePath(NamedTuple):
    """验证后的图片路径信息,包含路径、MIME 类型和文件大小.

    用于避免重复打开文件进行检测.
    """

    path: Path
    mime_type: str
    size_bytes: int


def normalize_path(path: str) -> Path:
    """将用户输入的路径规范化为真实绝对路径.

    处理 ~(home 目录)、相对路径、符号链接等情况.

    Args:
        path: 用户输入的路径字符串

    Returns:
        规范化后的绝对路径(已解析符号链接)

    Raises:
        ValidationError: 路径不存在或无法解析时
    """
    if not path or not path.strip():
        raise ValidationError("路径不能为空")

    try:
        # 展开 ~ 并转换为绝对路径
        expanded = Path(path).expanduser()
        # resolve(strict=True) 会解析符号链接并验证路径存在
        resolved = expanded.resolve(strict=True)
        return resolved
    except FileNotFoundError as e:
        raise ValidationError(f"路径不存在: {path}") from e
    except OSError as e:
        raise ValidationError(f"无法解析路径 {path}: {e}") from e


def _get_allowed_roots() -> list[Path]:
    """获取允许访问的目录白名单.

    白名单来源(按优先级):
    1. IMAGE_OUTPUT_DIR 环境变量(图片输出目录),未设置时使用默认 ~/banana-images
    2. NANOBANANA_ALLOWED_INPUT_DIRS 环境变量(逗号分隔的额外目录)
    3. 如果 NANOBANANA_ALLOW_HOME_DIR=true,则允许用户 home 目录

    安全策略:
    - 默认只允许输出目录,确保"编辑已生成图片"的主流程可用
    - 用户需要读取其他目录时,显式配置 NANOBANANA_ALLOWED_INPUT_DIRS

    Returns:
        允许访问的目录列表(至少包含默认输出目录)
    """
    roots: list[Path] = []

    # 1. 图片输出目录(始终允许读取已生成的图片)
    output_dir = os.environ.get("IMAGE_OUTPUT_DIR", "").strip()
    if not output_dir:
        # 使用默认输出目录,与 settings.py 保持一致
        output_dir = "~/banana-images"
    with contextlib.suppress(Exception):
        roots.append(Path(output_dir).expanduser().resolve())

    # 2. 额外允许的输入目录
    extra_dirs = os.environ.get("NANOBANANA_ALLOWED_INPUT_DIRS", "")
    if extra_dirs:
        for dir_path in extra_dirs.split(","):
            dir_path = dir_path.strip()
            if dir_path:
                with contextlib.suppress(Exception):
                    roots.append(Path(dir_path).expanduser().resolve())

    # 3. 可选: 允许 home 目录(需显式启用,范围较大,谨慎使用)
    allow_home = os.environ.get("NANOBANANA_ALLOW_HOME_DIR", "").lower() in ("true", "1", "yes")
    if allow_home:
        with contextlib.suppress(Exception):
            roots.append(Path.home().resolve())

    return roots


def validate_local_file_path(path: str, allowed_roots: list[Path] | None = None) -> Path:
    """校验本地文件路径,确保在白名单目录内.

    防护措施:
    1. 符号链接解析(防止 symlink 逃逸)
    2. 目录白名单检查
    3. 文件存在性验证

    Args:
        path: 用户输入的文件路径
        allowed_roots: 允许的根目录列表,为 None 时使用默认白名单

    Returns:
        验证后的绝对路径

    Raises:
        ValidationError: 路径无效、不在白名单内或不是文件时
    """
    resolved = normalize_path(path)

    # 验证是文件
    if not resolved.is_file():
        raise ValidationError(f"路径不是文件: {path}")

    # 获取白名单
    roots = allowed_roots if allowed_roots is not None else _get_allowed_roots()

    # 如果没有配置任何白名单,允许所有路径(向后兼容)
    if not roots:
        return resolved

    # 检查路径是否在白名单目录内
    for root in roots:
        try:
            resolved.relative_to(root)
            return resolved
        except ValueError:
            continue

    # 构建安全的错误信息(不泄露完整目录列表)
    import logging

    logger = logging.getLogger(__name__)
    root_strs = [str(r) for r in roots]
    logger.warning(f"路径访问被拒绝: {path} 不在允许的目录内.允许的目录: {root_strs}")
    raise ValidationError(
        "文件路径不在允许的目录内. 请检查 NANOBANANA_ALLOWED_INPUT_DIRS 环境变量配置."
    )


def validate_local_image_path(
    path: str,
    max_size_bytes: int | None = None,
    allowed_roots: list[Path] | None = None,
) -> ValidatedImagePath:
    """校验本地图片路径,返回路径、MIME 类型和大小.

    综合验证:
    1. 路径白名单校验
    2. 文件大小限制
    3. PIL 真实图片格式检测(防止伪装文件)

    Args:
        path: 用户输入的图片路径
        max_size_bytes: 最大文件大小(字节),None 表示不限制
        allowed_roots: 允许的根目录列表

    Returns:
        ValidatedImagePath 包含验证后的路径、MIME 类型和文件大小

    Raises:
        ValidationError: 验证失败时
    """
    # 1. 路径白名单校验
    resolved = validate_local_file_path(path, allowed_roots)

    # 2. 获取文件大小
    size_bytes = resolved.stat().st_size

    # 3. 大小限制检查
    if max_size_bytes is not None and size_bytes > max_size_bytes:
        size_mb = round(size_bytes / (1024 * 1024), 2)
        max_mb = round(max_size_bytes / (1024 * 1024), 2)
        raise ValidationError(f"图片文件过大: {size_mb}MB,最大允许 {max_mb}MB")

    # 4. PIL 真实图片格式检测
    try:
        from PIL import Image

        with Image.open(resolved) as img:
            img.verify()  # 验证图片完整性
            pil_format = img.format  # PNG, JPEG, WEBP, GIF 等

        if not pil_format:
            raise ValidationError(f"无法识别图片格式: {path}")

        # PIL 格式转 MIME 类型
        format_to_mime = {
            "PNG": "image/png",
            "JPEG": "image/jpeg",
            "JPG": "image/jpeg",
            "WEBP": "image/webp",
            "GIF": "image/gif",
            "BMP": "image/bmp",
            "TIFF": "image/tiff",
        }
        mime_type = format_to_mime.get(pil_format.upper(), f"image/{pil_format.lower()}")

        # 验证是否为支持的格式
        if mime_type.lower() not in SUPPORTED_IMAGE_TYPES:
            raise ValidationError(
                f"不支持的图片格式: {pil_format}.支持的格式: {', '.join(SUPPORTED_IMAGE_TYPES)}"
            )

        return ValidatedImagePath(path=resolved, mime_type=mime_type, size_bytes=size_bytes)

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"无效的图片文件 {path}: {e}") from e


def validate_prompt(prompt: str) -> None:
    """Validate image generation prompt."""
    if not prompt or not prompt.strip():
        raise ValidationError("Prompt cannot be empty")

    if len(prompt) > 8192:
        raise ValidationError("Prompt too long (max 8192 characters)")

    # Check for potentially harmful content patterns
    harmful_patterns = [
        r"\b(?:nude|naked|nsfw)\b",
        r"\b(?:violence|gore|blood)\b",
        r"\b(?:hate|racist|offensive)\b",
    ]

    for pattern in harmful_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            raise ValidationError("Prompt contains potentially inappropriate content")


def validate_image_count(n: int) -> None:
    """Validate requested image count."""
    if not isinstance(n, int):
        raise ValidationError("Image count must be an integer")

    if n < 1 or n > 4:
        raise ValidationError("Image count must be between 1 and 4")


def validate_image_format(mime_type: str) -> None:
    """Validate image MIME type."""
    if not mime_type:
        raise ValidationError("MIME type cannot be empty")

    if mime_type.lower() not in SUPPORTED_IMAGE_TYPES:
        raise ValidationError(
            f"Unsupported image format: {mime_type}. "
            f"Supported types: {', '.join(SUPPORTED_IMAGE_TYPES)}"
        )


def validate_base64_image(image_b64: str) -> None:
    """Validate base64 encoded image."""
    if not image_b64:
        raise ValidationError("Base64 image data cannot be empty")

    try:
        import base64

        base64.b64decode(image_b64, validate=True)
    except Exception as e:
        raise ValidationError(f"Invalid base64 image data: {e}")


def validate_image_list_consistency(
    images_b64: list[str] | None, mime_types: list[str] | None
) -> None:
    """Validate that image lists are consistent."""
    if images_b64 is None and mime_types is None:
        return

    if images_b64 is None or mime_types is None:
        raise ValidationError("Both images_b64 and mime_types must be provided together")

    if len(images_b64) != len(mime_types):
        raise ValidationError(
            f"images_b64 ({len(images_b64)}) and mime_types ({len(mime_types)}) "
            "must have the same length"
        )

    if len(images_b64) > 4:
        raise ValidationError("Maximum 4 input images allowed")

    # Validate each image and MIME type
    for i, (img_b64, mime_type) in enumerate(zip(images_b64, mime_types, strict=False)):
        try:
            validate_base64_image(img_b64)
            validate_image_format(mime_type)
        except ValidationError as e:
            raise ValidationError(f"Invalid image {i + 1}: {e}")


def validate_file_path(path: str) -> Path:
    """Validate file path for uploads.

    现在支持绝对路径,使用白名单机制替代简单的路径过滤.
    通过 resolve(strict=True) 防止符号链接逃逸.

    Args:
        path: 用户输入的文件路径(支持绝对路径、相对路径、~ 展开)

    Returns:
        验证后的绝对路径

    Raises:
        ValidationError: 路径无效或验证失败时
    """
    return validate_local_file_path(path)


def validate_edit_instruction(instruction: str) -> None:
    """Validate image edit instruction."""
    if not instruction or not instruction.strip():
        raise ValidationError("Edit instruction cannot be empty")

    if len(instruction) > 2048:
        raise ValidationError("Edit instruction too long (max 2048 characters)")

    # Check for harmful edit instructions
    harmful_patterns = [
        r"\b(?:remove|delete)\s+(?:clothes|clothing)\b",
        r"\b(?:add|create)\s+(?:nude|naked|nsfw)\b",
    ]

    for pattern in harmful_patterns:
        if re.search(pattern, instruction, re.IGNORECASE):
            raise ValidationError("Edit instruction contains inappropriate content")
