# 开发命令参考

## 环境设置
```bash
# 使用 uv 安装依赖 (推荐)
uv sync

# 设置环境变量
cp .env.example .env
# 编辑 .env 添加 GEMINI_API_KEY
```

## 运行服务器
```bash
# FastMCP CLI (开发推荐)
fastmcp dev nanobanana_mcp_server.server:create_app

# 清理端口后启动
./scripts/cleanup-ports.sh && fastmcp dev nanobanana_mcp_server.server:create_app

# 直接 Python 执行
python -m nanobanana_mcp_server.server

# HTTP 传输模式
FASTMCP_TRANSPORT=http python -m nanobanana_mcp_server.server
```

## 代码质量
```bash
# 格式化代码
ruff format .

# 代码检查
ruff check .

# 类型检查
mypy .
```

## 测试
```bash
# 运行所有测试
pytest

# 带覆盖率报告
pytest --cov=. --cov-report=html

# 运行特定类别
pytest -m unit
pytest -m integration
```

## Git 操作
```bash
# 查看状态
git status

# 提交更改
git add .
git commit -m "描述"

# 查看日志
git log --oneline -10
```

## 构建和发布
```bash
# 构建包
python scripts/build.py

# 上传到 PyPI
python scripts/upload.py
```

## 调试
```bash
# 调试模式运行
LOG_LEVEL=DEBUG fastmcp dev nanobanana_mcp_server.server:create_app

# JSON 格式日志
LOG_LEVEL=INFO LOG_FORMAT=json python -m nanobanana_mcp_server.server
```
