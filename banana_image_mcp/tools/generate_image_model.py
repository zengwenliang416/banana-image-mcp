"""模型选择模块 - 负责 generate_image 工具的模型智能路由。

职责：
1. 解析模型层级参数
2. 调用 ModelSelector 进行智能选择
3. 返回选定的服务、层级和模型信息
"""

import logging
from typing import Any

from ..config.settings import ModelTier


def select_model(
    prompt: str,
    model_tier: str | None,
    n: int,
    resolution: str | None,
    thinking_level: str | None,
    enable_grounding: bool,
    input_paths: list[str] | None,
    logger: logging.Logger,
) -> tuple[Any, ModelTier, dict]:
    """根据参数选择合适的模型。

    智能选择逻辑委托给 ModelSelector 服务，基于：
    - 请求的模型层级
    - 分辨率需求
    - 是否启用 grounding
    - 输入图片数量

    Args:
        prompt: 生成提示词
        model_tier: 请求的模型层级
        n: 图片数量
        resolution: 输出分辨率
        thinking_level: Pro 模型的思考深度
        enable_grounding: 是否启用 grounding
        input_paths: 输入图片路径
        logger: 日志实例

    Returns:
        (service, selected_tier, model_info) 元组
    """
    from ..services import get_model_selector

    # 解析模型层级
    try:
        tier = ModelTier(model_tier) if model_tier else ModelTier.AUTO
    except ValueError:
        logger.warning(f"Invalid model_tier '{model_tier}', defaulting to AUTO")
        tier = ModelTier.AUTO

    model_selector = get_model_selector()

    selected_service, selected_tier = model_selector.select_model(
        prompt=prompt,
        requested_tier=tier,
        n=n,
        resolution=resolution,
        input_images=input_paths,
        thinking_level=thinking_level,
        enable_grounding=enable_grounding,
    )

    model_info = model_selector.get_model_info(selected_tier)
    logger.info(
        f"Selected {model_info['emoji']} {model_info['name']} "
        f"({selected_tier.value}) for this request"
    )

    return selected_service, selected_tier, model_info


# 向后兼容的私有函数别名
_select_model = select_model
