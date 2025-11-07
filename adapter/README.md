# Dify Adapter Service

轻量级 API 服务，用于获取 Dify 平台中所有应用及其 API Key。

## 功能

- 获取所有启用 API 的应用列表
- 返回应用的基本信息和 API Key（明文）
- 使用 `ADAPTER_API_KEY` 环境变量进行鉴权
- 使用 uv 进行依赖管理，构建更快

## API 端点

通过 nginx 反向代理访问，路径前缀为 `/adapter`

### 健康检查

```bash
GET /adapter/health
```

响应：
```json
{
  "status": "healthy"
}
```

### 获取应用列表

```bash
GET /adapter/apps
Authorization: Bearer <ADAPTER_API_KEY>
```

响应示例：
```json
{
  "data": [
    {
      "code": "my-chatbot",
      "name": "my-chatbot",
      "description": "Customer support chatbot",
      "api_key": "app-1a2b3c4d5e6f7g8h",
      "mode": "chat",
      "enable_api": true
    }
  ],
  "total": 1
}
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ADAPTER_API_KEY` | API 鉴权密钥（必需） | `change-me-in-production` |
| `DB_USERNAME` | PostgreSQL 用户名 | `postgres` |
| `DB_PASSWORD` | PostgreSQL 密码 | `difyai123456` |
| `DB_HOST` | PostgreSQL 主机 | `db` |
| `DB_PORT` | PostgreSQL 端口 | `5432` |
| `DB_DATABASE` | 数据库名称 | `dify` |

## 使用方式

### 通过 Docker Compose 启动（推荐）

1. 在 `docker/.env` 文件中配置（或使用默认值）：
```bash
ADAPTER_API_KEY=1q2w3e4r#@!
```

2. 启动所有服务（包括 adapter）：
```bash
cd docker
docker-compose up -d
```

3. 调用 API（通过 nginx 代理）：
```bash
# 通过 nginx 访问 (推荐)
curl -X GET http://localhost/adapter/apps \
  -H "Authorization: Bearer 1q2w3e4r#@!"

# 或者在生产环境使用域名
curl -X GET https://your-domain.com/adapter/apps \
  -H "Authorization: Bearer 1q2w3e4r#@!"
```

### 本地开发

```bash
# 安装 uv（如果还没安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖
uv pip install -r pyproject.toml

# 设置环境变量
export ADAPTER_API_KEY=test-key
export DB_HOST=localhost

# 运行应用
python app.py
```

### 直接访问 adapter 服务（调试用）

如果需要直接访问 adapter 服务（不通过 nginx），可以修改 `docker-compose.yaml` 添加端口映射：

```yaml
adapter:
  # ... 其他配置
  ports:
    - "5003:5003"  # 添加此行
```

然后访问：
```bash
curl http://localhost:5003/apps \
  -H "Authorization: Bearer 1q2w3e4r#@!"
```

## 安全建议

1. **生产环境必须修改** `ADAPTER_API_KEY`，使用强密码
2. ✅ 服务通过 nginx 反向代理，不直接暴露端口，更加安全
3. 建议配置 HTTPS，确保传输安全
4. 可以在 nginx 层面添加 IP 白名单限制访问
5. API Key 以明文返回，仅在内网可信环境使用

## 故障排查

### 服务无法启动
```bash
# 查看日志
docker logs dify-adapter-1

# 检查数据库连接
docker exec -it dify-adapter-1 python -c "from app import engine; engine.connect()"
```

### 认证失败
- 确认 `ADAPTER_API_KEY` 环境变量已正确设置
- 确认请求头格式为 `Authorization: Bearer <key>`

### 数据库连接失败
- 确认 `DB_HOST`, `DB_PORT` 等环境变量配置正确
- 确认数据库服务已启动：`docker ps | grep db`
