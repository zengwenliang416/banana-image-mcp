# 代码风格和约定

## Python 版本
- 目标版本: Python 3.11+
- 使用现代 Python 特性 (类型注解, dataclass, Literal 等)

## 代码格式
- **行长度**: 100 字符
- **格式化工具**: Ruff (也可用 Black)
- **导入排序**: isort (通过 ruff 配置)

## 类型注解
- **强制要求**: 所有函数必须有类型注解
- **mypy 配置**: 严格模式
  - `disallow_untyped_defs = true`
  - `disallow_incomplete_defs = true`
  - `check_untyped_defs = true`

## 命名约定
- **类名**: PascalCase (如 `ImageService`, `GeminiClient`)
- **函数/方法**: snake_case (如 `generate_images`, `edit_image`)
- **常量**: UPPER_SNAKE_CASE (如 `MAX_INPUT_IMAGES`)
- **私有方法**: 前缀下划线 (如 `_enhance_prompt_for_pro`)
- **模块级私有变量**: 前缀下划线 (如 `_gemini_client`)

## 文档字符串
- 使用三引号文档字符串
- 包含 Args, Returns, Raises 部分
- 示例:
```python
def generate_images(
    self,
    prompt: str,
    n: int = 1,
) -> Tuple[List[MCPImage], List[Dict[str, Any]]]:
    """
    Generate images using Gemini API.

    Args:
        prompt: Main generation prompt
        n: Number of images to generate

    Returns:
        Tuple of (image_blocks, metadata_list)
    """
```

## 异常处理
- 使用自定义异常类 (`ValidationError`, `GeminiAPIError` 等)
- 异常继承自 `NanoBananaError`
- 记录错误日志后重新抛出

## 日志
- 使用 `logging` 模块
- 每个类/模块创建自己的 logger
- 日志输出到 stderr (避免干扰 MCP STDIO)

## Ruff 规则
启用的规则:
- E/W: pycodestyle
- F: pyflakes
- I: isort
- B: flake8-bugbear
- C4: flake8-comprehensions
- UP: pyupgrade
- N: pep8-naming
- S: flake8-bandit
- SIM: flake8-simplify

## 测试约定
- 测试文件: `test_*.py` 或 `*_test.py`
- 测试函数: `test_*`
- 使用 pytest markers: unit, integration, slow, network
