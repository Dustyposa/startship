# Docker 部署指南

## 快速开始

### 1. 一键启动

```bash
docker-compose up -d
```

服务将在以下地址运行：
- **前端**: http://localhost:3001
- **后端**: http://localhost:8889

### 2. 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 3. 停止服务

```bash
docker-compose down
```

## 配置说明

### 环境变量

在 `docker-compose.yml` 中配置以下环境变量（可选）：

```yaml
environment:
  # OpenAI API Key (用于 AI 对话功能)
  - OPENAI_API_KEY=your_openai_api_key_here

  # GitHub Token (用于提高 API 限制)
  - GITHUB_TOKEN=your_github_token_here
```

### 数据持久化

SQLite 数据库存储在 `./data` 目录中，该目录已挂载到容器内，数据会持久保存。

### 端口配置

默认端口映射：
- 前端: `3001:3000`
- 后端: `8889:8888`

如需修改端口，编辑 `docker-compose.yml`：

```yaml
services:
  frontend:
    ports:
      - "8080:3001"  # 将前端改为 8080 端口

  backend:
    ports:
      - "9000:8889"  # 将后端改为 9000 端口
```

## 高级用法

### 重新构建镜像

```bash
# 重新构建并启动
docker-compose up -d --build

# 重新构建特定服务
docker-compose build backend
docker-compose build frontend
```

### 清理数据

```bash
# 停止并删除容器、网络、卷
docker-compose down -v

# 删除数据目录
rm -rf ./data
```

### 生产环境部署

建议使用生产级配置：

1. **使用反向代理** (Nginx/Caddy)
2. **启用 HTTPS** (Let's Encrypt)
3. **设置资源限制**：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  frontend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
```

## 健康检查

服务包含健康检查，自动监控服务状态：

```bash
# 查看服务健康状态
docker-compose ps
```

## 故障排查

### 服务无法启动

```bash
# 查看详细日志
docker-compose logs backend
docker-compose logs frontend

# 检查端口占用
lsof -i :3001
lsof -i :8889
```

### 数据库问题

```bash
# 进入后端容器
docker-compose exec backend bash

# 查看数据库
ls -la /app/data

# 删除数据库重新初始化
rm /app/data/github_stars.db
```

### 重建所有内容

```bash
# 完全清理
docker-compose down -v
docker system prune -a

# 重新构建
docker-compose up -d --build
```

## 服务状态

```bash
# 查看运行状态
docker-compose ps

# 查看资源使用
docker stats
```

## 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 重启服务
docker-compose restart
```
