# 任务完成检查清单

## 代码更改后必须执行

### 1. 代码格式化
```bash
ruff format .
```

### 2. 代码检查
```bash
ruff check .
```
如有错误，使用 `ruff check . --fix` 自动修复

### 3. 类型检查
```bash
mypy .
```

### 4. 运行测试
```bash
pytest
```

### 5. 验证服务器启动
```bash
# 清理端口并启动
./scripts/cleanup-ports.sh && fastmcp dev nanobanana_mcp_server.server:create_app
```

## 提交前检查

- [ ] 所有 ruff 检查通过
- [ ] mypy 类型检查通过
- [ ] 测试通过
- [ ] 服务器可正常启动
- [ ] 新功能有对应测试 (如适用)
- [ ] 文档已更新 (如适用)

## 常见问题处理

### 端口冲突
```bash
./scripts/cleanup-ports.sh
```

### JSON 解析错误 (STDIO 模式)
确保所有日志输出到 stderr，不要输出到 stdout

### 依赖问题
```bash
uv sync
```
