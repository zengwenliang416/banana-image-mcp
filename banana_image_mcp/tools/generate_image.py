import base64
import logging
import mimetypes
import os
from typing import Annotated, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from pydantic import Field

from ..config.constants import MAX_INPUT_IMAGES
from ..config.settings import ModelTier, ThinkingLevel
from ..core.exceptions import ValidationError


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
            # 1. Collect input paths
            input_image_paths = _collect_input_paths(
                input_image_path_1, input_image_path_2, input_image_path_3
            )

            logger.info(
                f"Generate image request: prompt='{prompt[:50]}...', n={n}, "
                f"paths={input_image_paths}, model_tier={model_tier}, aspect_ratio={aspect_ratio}"
            )

            # 2. Validate inputs
            _validate_inputs(mode, input_image_paths, file_id)

            # 3. Detect mode
            detected_mode = _detect_mode(mode, file_id, input_image_paths)

            # 4. Validate thinking level
            try:
                if thinking_level:
                    _ = ThinkingLevel(thinking_level)
            except ValueError:
                logger.warning(f"Invalid thinking_level '{thinking_level}', defaulting to HIGH")
                thinking_level = "high"

            # 5. Select model
            selected_service, selected_tier, model_info = _select_model(
                prompt=prompt,
                model_tier=model_tier,
                n=n,
                resolution=resolution,
                thinking_level=thinking_level,
                enable_grounding=enable_grounding,
                input_paths=input_image_paths,
                logger=logger,
            )

            # Parse tier for structured content
            try:
                tier = ModelTier(model_tier) if model_tier else ModelTier.AUTO
            except ValueError:
                tier = ModelTier.AUTO

            # Mode-specific validation
            if detected_mode == "edit":
                if not file_id and not input_image_paths:
                    raise ValidationError("Edit mode requires either file_id or input_image_paths")
                if file_id and input_image_paths and len(input_image_paths) > 1:
                    raise ValidationError(
                        "Edit mode with file_id supports only additional input images, not multiple primary inputs"
                    )

            # Get enhanced image service (would be injected in real implementation)
            enhanced_image_service = _get_enhanced_image_service()

            # Execute based on detected mode
            if detected_mode == "edit" and file_id:
                # Edit by file_id following workflows.md sequence
                logger.info(f"Edit mode: using file_id {file_id}")
                thumbnail_images, metadata = enhanced_image_service.edit_image_by_file_id(
                    file_id=file_id, edit_prompt=prompt
                )

            elif detected_mode == "edit" and input_image_paths and len(input_image_paths) == 1:
                # Edit by file path
                logger.info(f"Edit mode: using file path {input_image_paths[0]}")
                thumbnail_images, metadata = enhanced_image_service.edit_image_by_path(
                    instruction=prompt, file_path=input_image_paths[0]
                )

            else:
                # Generation mode (with optional input images for conditioning)
                logger.info("Generate mode: creating new images")
                if aspect_ratio:
                    logger.info(f"Using aspect ratio override: {aspect_ratio}")

                # Prepare input images by reading from file paths
                input_images = None
                if input_image_paths:
                    input_images = _load_input_images(input_image_paths, logger)
                    logger.info(f"Loaded {len(input_images)} input images from file paths")

                # Generate images following workflows.md pattern:
                # M->G->FS->F->D (save full-res, create thumbnail, upload to Files API, track in DB)
                thumbnail_images, metadata = enhanced_image_service.generate_images(
                    prompt=prompt,
                    n=n,
                    negative_prompt=negative_prompt,
                    system_instruction=system_instruction,
                    input_images=input_images,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                )

            # Create response with file paths and thumbnails
            if metadata:
                # Filter out any None entries from metadata (defensive programming)
                metadata = [m for m in metadata if m is not None and isinstance(m, dict)]

                if not metadata:
                    return _build_error_response(detected_mode, prompt)

                # Build summary using helper function
                full_summary = _build_summary(
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
                # Fallback if no images generated
                summary = "❌ No images were generated. Please check the logs for details."
                content = [TextContent(type="text", text=summary)]

            # Build structured content using helper function
            structured_content = _build_structured_content(
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
    """Get the enhanced image service instance."""
    from ..services import get_enhanced_image_service
    return get_enhanced_image_service()


# ============================================================================
# Helper functions for generate_image tool
# ============================================================================


def _collect_input_paths(
    path1: str | None,
    path2: str | None,
    path3: str | None,
) -> list[str] | None:
    """Collect non-None input image paths into a list.

    Args:
        path1: First optional path
        path2: Second optional path
        path3: Third optional path

    Returns:
        List of non-None paths, or None if all are None
    """
    paths = [p for p in [path1, path2, path3] if p]
    return paths if paths else None


def _validate_inputs(
    mode: str,
    input_paths: list[str] | None,
    file_id: str | None,
) -> None:
    """Validate input parameters.

    Args:
        mode: Operation mode
        input_paths: List of input image paths
        file_id: Files API file ID

    Raises:
        ValidationError: If validation fails
    """
    from ..core.exceptions import ErrorCode

    # Validate mode
    if mode not in ["auto", "generate", "edit"]:
        raise ValidationError(
            "Mode must be 'auto', 'generate', or 'edit'",
            error_code=ErrorCode.VALIDATION_INVALID_MODE,
            field="mode",
            value=mode,
        )

    # Validate input paths
    if input_paths:
        if len(input_paths) > MAX_INPUT_IMAGES:
            raise ValidationError(
                f"Maximum {MAX_INPUT_IMAGES} input images allowed",
                error_code=ErrorCode.VALIDATION_FILE_COUNT_EXCEEDED,
                field="input_image_paths",
                value=len(input_paths),
            )

        for i, path in enumerate(input_paths):
            if not os.path.exists(path):
                raise ValidationError(
                    f"Input image {i + 1} not found: {path}",
                    error_code=ErrorCode.FILE_NOT_FOUND,
                    field=f"input_image_path_{i + 1}",
                    value=path,
                )
            if not os.path.isfile(path):
                raise ValidationError(
                    f"Input image {i + 1} is not a file: {path}",
                    error_code=ErrorCode.VALIDATION_INVALID_PATH,
                    field=f"input_image_path_{i + 1}",
                    value=path,
                )


def _detect_mode(
    mode: str,
    file_id: str | None,
    input_paths: list[str] | None,
) -> str:
    """Detect operation mode based on inputs.

    Args:
        mode: Requested mode ("auto", "generate", or "edit")
        file_id: Files API file ID
        input_paths: List of input image paths

    Returns:
        Detected mode ("generate" or "edit")
    """
    if mode != "auto":
        return mode

    # Auto-detect based on inputs
    if file_id or (input_paths and len(input_paths) == 1):
        return "edit"
    return "generate"


def _select_model(
    prompt: str,
    model_tier: str | None,
    n: int,
    resolution: str | None,
    thinking_level: str | None,
    enable_grounding: bool,
    input_paths: list[str] | None,
    logger: logging.Logger,
) -> tuple[any, ModelTier, dict]:
    """Select appropriate model based on parameters.

    Args:
        prompt: Generation prompt
        model_tier: Requested model tier
        n: Number of images
        resolution: Output resolution
        thinking_level: Thinking level for Pro model
        enable_grounding: Whether to enable grounding
        input_paths: Input image paths
        logger: Logger instance

    Returns:
        Tuple of (service, selected_tier, model_info)
    """
    from ..services import get_model_selector

    # Parse model tier
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


def _load_input_images(
    paths: list[str],
    logger: logging.Logger,
) -> list[tuple[str, str]]:
    """Load input images from file paths.

    Args:
        paths: List of file paths
        logger: Logger instance

    Returns:
        List of (base64_data, mime_type) tuples

    Raises:
        ValidationError: If loading fails
    """
    from ..core.exceptions import ErrorCode

    images = []
    for path in paths:
        try:
            with open(path, "rb") as f:
                image_bytes = f.read()

            mime_type, _ = mimetypes.guess_type(path)
            if not mime_type or not mime_type.startswith("image/"):
                mime_type = "image/png"

            base64_data = base64.b64encode(image_bytes).decode("utf-8")
            images.append((base64_data, mime_type))

            logger.debug(f"Loaded input image: {path} ({mime_type})")

        except Exception as e:
            raise ValidationError(
                f"Failed to load input image {path}: {e}",
                error_code=ErrorCode.FILE_READ_FAILED,
                field="input_image_path",
                value=path,
                cause=e,
            ) from e

    return images


def _build_summary(
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
    """Build summary text for response.

    Args:
        mode: Operation mode
        metadata: List of image metadata
        model_info: Model information dict
        selected_tier: Selected model tier
        thinking_level: Thinking level used
        resolution: Resolution used
        enable_grounding: Whether grounding was enabled
        file_id: Source file ID (for edits)
        input_paths: Input image paths
        aspect_ratio: Aspect ratio used

    Returns:
        Summary text string
    """
    action_verb = "Edited" if mode == "edit" else "Generated"
    model_name = model_info["name"]
    model_emoji = model_info["emoji"]

    lines = [
        f"✅ {action_verb} {len(metadata)} image(s) with {model_emoji} {model_name}.",
        f"📊 **Model**: {selected_tier.value.upper()} tier",
    ]

    # Pro-specific information
    if selected_tier == ModelTier.PRO:
        lines.append(f"🧠 **Thinking Level**: {thinking_level}")
        lines.append(f"📏 **Resolution**: {resolution}")
        if enable_grounding:
            lines.append("🔍 **Grounding**: Enabled (Google Search)")
    lines.append("")

    # Source information
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

    # File information
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

        lines.append(
            f"  {i}. `{full_path}`\n"
            f"     📏 {width}x{height} • 💾 {size_mb}MB{extra_info}"
        )

    lines.append("\n🖼️ **Thumbnail previews shown below** (actual images saved to disk)")
    return "\n".join(lines)


def _build_structured_content(
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
    """Build structured content for response.

    Returns:
        Structured content dictionary
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
            m.get("full_path")
            for m in metadata
            if m and isinstance(m, dict) and m.get("full_path")
        ],
        "files_api_ids": [
            m.get("files_api", {}).get("name")
            for m in metadata
            if m and isinstance(m, dict) and m.get("files_api", {}) and m.get("files_api", {}).get("name")
        ],
        "parent_relationships": [
            (m.get("parent_file_id"), m.get("files_api", {}).get("name"))
            for m in metadata
            if m and isinstance(m, dict)
        ] if mode == "edit" else [],
        "total_size_mb": round(
            sum(m.get("size_bytes", 0) for m in metadata if m and isinstance(m, dict)) / (1024 * 1024),
            2,
        ),
    }


def _build_error_response(mode: str, prompt: str) -> ToolResult:
    """Build error response when no valid results.

    Args:
        mode: Operation mode
        prompt: Original prompt

    Returns:
        ToolResult with error information
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
