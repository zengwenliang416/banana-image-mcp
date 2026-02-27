"""模式检测模块 - 负责 generate_image 工具的操作模式自动检测。

职责：
1. 根据输入参数自动检测操作模式（generate/edit）
"""


def detect_mode(
    mode: str,
    file_id: str | None,
    input_paths: list[str] | None,
) -> str:
    """根据输入参数检测操作模式。

    自动检测逻辑：
    - 如果提供了 file_id → edit 模式
    - 如果只有一个输入图片路径 → edit 模式
    - 其他情况 → generate 模式

    Args:
        mode: 请求的模式（"auto", "generate", 或 "edit"）
        file_id: Files API 文件 ID
        input_paths: 输入图片路径列表

    Returns:
        检测到的模式（"generate" 或 "edit"）
    """
    if mode != "auto":
        return mode

    # 基于输入自动检测
    if file_id or (input_paths and len(input_paths) == 1):
        return "edit"
    return "generate"


# 向后兼容的私有函数别名
_detect_mode = detect_mode
