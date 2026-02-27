"""输入处理模块 - 负责 generate_image 工具的输入收集、验证和加载.

职责:
1. 收集输入图片路径
2. 验证输入参数(模式、路径、file_id)
3. 安全加载图片文件(含 PIL 格式检测)
"""

import base64
import logging
from pathlib import Path

from ..config.constants import MAX_INPUT_IMAGES
from ..core.exceptions import ErrorCode, ValidationError


def collect_input_paths(
    path1: str | None,
    path2: str | None,
    path3: str | None,
) -> list[str] | None:
    """收集非空的输入图片路径.

    Args:
        path1: 第一个可选路径
        path2: 第二个可选路径
        path3: 第三个可选路径

    Returns:
        非空路径列表,如果全为空则返回 None
    """
    paths = [p for p in [path1, path2, path3] if p]
    return paths if paths else None


def validate_inputs(
    mode: str,
    input_paths: list[str] | None,
    file_id: str | None,
) -> None:
    """验证输入参数.

    Args:
        mode: 操作模式
        input_paths: 输入图片路径列表
        file_id: Files API 文件 ID

    Raises:
        ValidationError: 验证失败时
    """
    # 验证模式
    if mode not in ["auto", "generate", "edit"]:
        raise ValidationError(
            "Mode must be 'auto', 'generate', or 'edit'",
            error_code=ErrorCode.VALIDATION_INVALID_MODE,
            field="mode",
            value=mode,
        )

    # 验证输入路径
    if input_paths:
        if len(input_paths) > MAX_INPUT_IMAGES:
            raise ValidationError(
                f"Maximum {MAX_INPUT_IMAGES} input images allowed",
                error_code=ErrorCode.VALIDATION_FILE_COUNT_EXCEEDED,
                field="input_image_paths",
                value=len(input_paths),
            )

        for i, path in enumerate(input_paths):
            # 展开 ~ 路径(os.path.exists 不会自动展开)
            expanded_path = Path(path).expanduser()
            if not expanded_path.exists():
                raise ValidationError(
                    f"Input image {i + 1} not found: {path}",
                    error_code=ErrorCode.FILE_NOT_FOUND,
                    field=f"input_image_path_{i + 1}",
                    value=path,
                )
            if not expanded_path.is_file():
                raise ValidationError(
                    f"Input image {i + 1} is not a file: {path}",
                    error_code=ErrorCode.VALIDATION_INVALID_PATH,
                    field=f"input_image_path_{i + 1}",
                    value=path,
                )


def load_input_images(
    paths: list[str],
    logger: logging.Logger,
    max_size_bytes: int | None = None,
) -> list[tuple[str, str]]:
    """安全加载输入图片文件.

    安全特性:
    1. 路径白名单校验(防止目录遍历和 symlink 逃逸)
    2. PIL 真实图片格式检测(防止 MIME 伪装攻击)
    3. 可选的文件大小限制

    Args:
        paths: 文件路径列表
        logger: 日志实例
        max_size_bytes: 最大文件大小(字节),None 表示不限制

    Returns:
        (base64_data, mime_type) 元组列表

    Raises:
        ValidationError: 加载或验证失败时
    """
    from ..core.validation import validate_local_image_path

    images = []
    for path in paths:
        try:
            # 使用安全验证函数,返回路径 + MIME 类型 + 大小
            validated = validate_local_image_path(path, max_size_bytes=max_size_bytes)

            # 读取文件内容并编码(使用已验证的路径)
            with open(validated.path, "rb") as f:
                image_bytes = f.read()

            base64_data = base64.b64encode(image_bytes).decode("utf-8")
            images.append((base64_data, validated.mime_type))

            logger.debug(
                f"Loaded input image: {path} ({validated.mime_type}, {validated.size_bytes} bytes)"
            )

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(
                f"Failed to load input image {path}: {e}",
                error_code=ErrorCode.FILE_READ_FAILED,
                field="input_image_path",
                value=path,
                cause=e,
            ) from e

    return images


# 向后兼容的私有函数别名(供 generate_image.py 内部使用)
_collect_input_paths = collect_input_paths
_validate_inputs = validate_inputs
_load_input_images = load_input_images
