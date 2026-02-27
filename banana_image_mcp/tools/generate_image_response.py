"""响应构建模块 - 负责 generate_image 工具的响应格式化和组装。

职责：
1. 构建人类可读的摘要文本
2. 构建结构化内容（供程序化访问）
3. 构建错误响应
"""

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..config.settings import ModelTier


def build_summary(
    mode: str,
    metadata: list[dict],
    model_info: dict,
    selected_tier: ModelTier,
    thinking_level: str | None,
    resolution: str | None,
    enable_grounding: bool,
    file_id: str | None,
    input_paths: list[str] | None,
    aspect_ratio: str | None,
) -> str:
    """构建响应摘要文本。

    Args:
        mode: 操作模式
        metadata: 图片元数据列表
        model_info: 模型信息字典
        selected_tier: 选定的模型层级
        thinking_level: 使用的思考深度
        resolution: 使用的分辨率
        enable_grounding: 是否启用了 grounding
        file_id: 源文件 ID（编辑模式）
        input_paths: 输入图片路径
        aspect_ratio: 使用的宽高比

    Returns:
        摘要文本字符串
    """
    action_verb = "Edited" if mode == "edit" else "Generated"
    model_name = model_info["name"]
    model_emoji = model_info["emoji"]

    lines = [
        f"✅ {action_verb} {len(metadata)} image(s) with {model_emoji} {model_name}.",
        f"📊 **Model**: {selected_tier.value.upper()} tier",
    ]

    # Pro 模型特有信息
    if selected_tier == ModelTier.PRO:
        lines.append(f"🧠 **Thinking Level**: {thinking_level or 'high'}")
        lines.append(f"📏 **Resolution**: {resolution or '4k'}")
        if enable_grounding:
            lines.append("🔍 **Grounding**: Enabled (Google Search)")
    lines.append("")

    # 来源信息
    if mode == "edit":
        if file_id:
            lines.append(f"📎 **Edit Source**: Files API {file_id}")
        elif input_paths and len(input_paths) == 1:
            lines.append(f"📁 **Edit Source**: {input_paths[0]}")
    elif input_paths:
        lines.append(
            f"🖼️ Conditioned on {len(input_paths)} input image(s): {', '.join(input_paths)}"
        )
    if aspect_ratio and mode == "generate":
        lines.append(f"📐 Aspect ratio: {aspect_ratio}")

    # 文件信息
    result_label = "Edited Images" if mode == "edit" else "Generated Images"
    lines.append(f"\n📁 **{result_label}:**")

    for i, meta in enumerate(metadata, 1):
        if not meta or not isinstance(meta, dict):
            lines.append(f"  {i}. ❌ Invalid metadata entry")
            continue

        size_bytes = meta.get("size_bytes", 0)
        size_mb = round(size_bytes / (1024 * 1024), 1) if size_bytes else 0
        full_path = meta.get("full_path", "Unknown path")
        width = meta.get("width", "?")
        height = meta.get("height", "?")

        extra_info = ""
        if mode == "edit":
            files_api_info = meta.get("files_api") or {}
            if files_api_info.get("name"):
                extra_info += f" • 🌐 Files API: {files_api_info['name']}"
            if meta.get("parent_file_id"):
                extra_info += f" • 👨‍👩‍👧 Parent: {meta.get('parent_file_id')}"

        lines.append(f"  {i}. `{full_path}`\n     📏 {width}x{height} • 💾 {size_mb}MB{extra_info}")

    lines.append("\n🖼️ **Thumbnail previews shown below** (actual images saved to disk)")
    return "\n".join(lines)


def build_structured_content(
    mode: str,
    metadata: list[dict],
    model_info: dict,
    selected_tier: ModelTier,
    tier: ModelTier,
    model_tier: str | None,
    thinking_level: str | None,
    resolution: str | None,
    enable_grounding: bool,
    n: int,
    thumbnail_count: int,
    negative_prompt: str | None,
    input_paths: list[str] | None,
    file_id: str | None,
    aspect_ratio: str | None,
    prompt: str,
) -> dict:
    """构建结构化内容字典。

    Args:
        mode: 操作模式
        metadata: 图片元数据列表
        model_info: 模型信息字典
        selected_tier: 选定的模型层级
        tier: 解析后的模型层级
        model_tier: 原始模型层级参数
        thinking_level: 思考深度
        resolution: 分辨率
        enable_grounding: 是否启用 grounding
        n: 请求的图片数量
        thumbnail_count: 实际返回的缩略图数量
        negative_prompt: 负面提示词
        input_paths: 输入图片路径
        file_id: 文件 ID
        aspect_ratio: 宽高比
        prompt: 原始提示词

    Returns:
        结构化内容字典
    """
    return {
        "mode": mode,
        "model_tier": selected_tier.value,
        "model_name": model_info["name"],
        "model_id": model_info["model_id"],
        "requested_tier": model_tier,
        "auto_selected": tier == ModelTier.AUTO,
        "thinking_level": thinking_level if selected_tier == ModelTier.PRO else None,
        "resolution": resolution,
        "grounding_enabled": enable_grounding if selected_tier == ModelTier.PRO else False,
        "requested": n,
        "returned": thumbnail_count,
        "negative_prompt_applied": bool(negative_prompt),
        "used_input_images": bool(input_paths) or bool(file_id),
        "input_image_paths": input_paths or [],
        "input_image_count": len(input_paths) if input_paths else (1 if file_id else 0),
        "aspect_ratio": aspect_ratio,
        "source_file_id": file_id,
        "edit_instruction": prompt if mode == "edit" else None,
        "generation_prompt": prompt if mode == "generate" else None,
        "output_method": "file_system_with_files_api",
        "workflow": f"workflows.md_{mode}_sequence",
        "images": metadata,
        "file_paths": [
            m.get("full_path") for m in metadata if m and isinstance(m, dict) and m.get("full_path")
        ],
        "files_api_ids": [
            m.get("files_api", {}).get("name")
            for m in metadata
            if m
            and isinstance(m, dict)
            and m.get("files_api", {})
            and m.get("files_api", {}).get("name")
        ],
        "parent_relationships": (
            [
                (m.get("parent_file_id"), m.get("files_api", {}).get("name"))
                for m in metadata
                if m and isinstance(m, dict)
            ]
            if mode == "edit"
            else []
        ),
        "total_size_mb": round(
            sum(m.get("size_bytes", 0) for m in metadata if m and isinstance(m, dict))
            / (1024 * 1024),
            2,
        ),
    }


def build_error_response(mode: str, prompt: str) -> ToolResult:
    """构建无有效结果时的错误响应。

    Args:
        mode: 操作模式
        prompt: 原始提示词

    Returns:
        包含错误信息的 ToolResult
    """
    summary = f"❌ Failed to {mode} image(s): {prompt[:50]}... No valid results returned."
    return ToolResult(
        content=[TextContent(type="text", text=summary)],
        structured_content={
            "error": "no_valid_metadata",
            "message": summary,
            "mode": mode,
        },
    )


# 向后兼容的私有函数别名
_build_summary = build_summary
_build_structured_content = build_structured_content
_build_error_response = build_error_response
