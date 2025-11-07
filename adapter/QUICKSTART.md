# Adapter 服务快速入门

## 一、启动服务

### 1. 配置环境变量（可选）

编辑 `docker/.env` 文件，修改以下配置：

```bash
# 默认 API Key（生产环境建议修改）
ADAPTER_API_KEY=1q2w3e4r#@!
```

> 注意：adapter 服务通过 nginx 反向代理访问，路径为 `/adapter/*`，不需要单独暴露端口。

### 2. 启动所有服务

```bash
cd docker
docker-compose up -d
```

这将自动构建并启动 adapter 服务以及所有 Dify 相关服务。

### 3. 查看服务状态

```bash
# 查看所有服务
docker-compose ps

# 查看 adapter 服务日志
docker-compose logs -f adapter

# 检查 adapter 是否健康（通过 nginx）
curl http://localhost/adapter/health
```

## 二、使用 API

### 健康检查

```bash
curl http://localhost/adapter/health
```

响应：
```json
{
  "status": "healthy"
}
```

### 获取应用列表

```bash
curl -X GET http://localhost/adapter/apps \
  -H "Authorization: Bearer 1q2w3e4r#@!"
```

成功响应：
```json
{
  "data": [
    {
      "id": "12345678-1234-1234-1234-123456789abc",
      "code": "my-app",
      "name": "my-app",
      "description": "My application",
      "api_key": "app-xxxxxxxxx",
      "mode": "chat",
      "enable_api": true
    }
  ],
  "total": 1
}
```

失败响应（认证错误）：
```json
{
  "error": "Unauthorized",
  "message": "Invalid API key"
}
```

## 三、常见操作

### 重启 adapter 服务

```bash
cd docker
docker-compose restart adapter
```

### 重新构建 adapter 服务

```bash
cd docker
docker-compose up -d --build adapter
```

### 停止服务

```bash
cd docker
docker-compose stop adapter
```

### 完全移除服务

```bash
cd docker
docker-compose down
```

## 四、集成示例

### Python 示例

```python
import requests

# 通过 nginx 访问
ADAPTER_URL = "http://localhost/adapter"
API_KEY = "1q2w3e4r#@!"

# 获取所有应用
response = requests.get(
    f"{ADAPTER_URL}/apps",
    headers={"Authorization": f"Bearer {API_KEY}"}
)

if response.status_code == 200:
    data = response.json()
    print(f"找到 {data['total']} 个应用")
    for app in data['data']:
        print(f"- {app['name']}: {app['api_key']}")
else:
    print(f"错误: {response.status_code}")
    print(response.json())
```

### JavaScript 示例

```javascript
// 通过 nginx 访问
const ADAPTER_URL = 'http://localhost/adapter';
const API_KEY = '1q2w3e4r#@!';

async function getApps() {
  const response = await fetch(`${ADAPTER_URL}/apps`, {
    headers: {
      'Authorization': `Bearer ${API_KEY}`
    }
  });

  if (response.ok) {
    const data = await response.json();
    console.log(`找到 ${data.total} 个应用`);
    data.data.forEach(app => {
      console.log(`- ${app.name}: ${app.api_key}`);
    });
  } else {
    console.error('错误:', response.status);
  }
}

getApps();
```

### Bash/cURL 示例

```bash
#!/bin/bash

# 通过 nginx 访问
ADAPTER_URL="http://localhost/adapter"
API_KEY="1q2w3e4r#@!"

# 获取应用列表并格式化输出
curl -s -X GET "${ADAPTER_URL}/apps" \
  -H "Authorization: Bearer ${API_KEY}" | jq .
```

## 五、故障排查

### 问题 1: adapter 服务无法启动

```bash
# 查看详细日志
docker-compose logs adapter

# 检查 nginx 是否正常
docker-compose logs nginx

# 确认 adapter 服务运行状态
docker-compose ps adapter
```

### 问题 2: 认证失败

确认：
1. `.env` 文件中的 `ADAPTER_API_KEY` 已设置
2. 请求头格式正确：`Authorization: Bearer <your-key>`
3. API Key 没有多余的空格或换行符

### 问题 3: 数据库连接失败

```bash
# 确认数据库服务正常
docker-compose ps db

# 测试数据库连接
docker exec -it dify-adapter-1 python -c "from app import engine; print(engine.connect())"
```

### 问题 4: 返回空列表

确认：
1. Dify 中已创建应用
2. 应用已开启 API 访问（enable_api=true）
3. 应用状态为正常（status=normal）
4. 已为应用生成 API Token

## 六、安全建议

1. **生产环境必须修改** `ADAPTER_API_KEY`
2. 使用强密码（建议 32 字符以上）
3. 配置防火墙，仅允许内网访问
4. 定期轮换 API Key
5. 监控异常访问日志

## 七、性能优化

如果需要处理大量请求，可以调整以下配置：

编辑 `adapter/Dockerfile`：
```dockerfile
# 增加 worker 数量
CMD ["gunicorn", "--bind", "0.0.0.0:5003", "--workers", "4", "--timeout", "120", "app:app"]
```

然后重新构建：
```bash
cd docker
docker-compose up -d --build adapter
```
