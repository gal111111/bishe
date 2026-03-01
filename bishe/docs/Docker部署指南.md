# Docker 部署指南

## 概述

本指南说明如何使用 Docker 和 Docker Compose 一键部署上海迪士尼舆情分析系统。

## 前置要求

- Docker 20.10 或更高版本
- Docker Compose 2.0 或更高版本
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间

## 快速开始

### 方式一：使用 Docker Compose（推荐）

1. 克隆或下载项目代码到本地

2. 进入项目根目录：
   ```bash
   cd bishe
   ```

3. 构建并启动服务：
   ```bash
   docker-compose up -d --build
   ```

4. 访问系统：
   - 前端界面：http://localhost:8502
   - Redis（可选）：localhost:6379

5. 查看日志：
   ```bash
   docker-compose logs -f
   ```

6. 停止服务：
   ```bash
   docker-compose down
   ```

### 方式二：使用 Docker 单独构建

1. 构建镜像：
   ```bash
   docker build -t disney-sentiment-analysis .
   ```

2. 运行容器：
   ```bash
   docker run -d \
     --name disney-sentiment-analysis \
     -p 8502:8502 \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     disney-sentiment-analysis
   ```

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| TZ | 时区 | Asia/Shanghai |
| PYTHONUNBUFFERED | Python 输出缓冲 | 1 |
| PYTHONIOENCODING | Python 编码 | utf-8 |

### 端口映射

| 容器端口 | 主机端口 | 说明 |
|----------|----------|------|
| 8502 | 8502 | Streamlit 前端界面 |
| 6379 | 6379 | Redis 缓存（可选） |

### 数据卷挂载

| 容器路径 | 主机路径 | 说明 |
|----------|----------|------|
| /app/data | ./data | 数据存储目录 |
| /app/logs | ./logs | 日志存储目录 |
| /data | redis_data | Redis 数据持久化 |

## 高级配置

### 修改 Streamlit 端口

编辑 `docker-compose.yml`：
```yaml
services:
  sentiment-analysis:
    ports:
      - "8080:8502"  # 将主机端口改为 8080
```

### 禁用 Redis

编辑 `docker-compose.yml`，删除或注释掉 redis 服务部分：
```yaml
#  redis:
#    image: redis:7-alpine
#    ...
```

### 使用自定义配置文件

1. 创建自定义的 `config.yaml`
2. 挂载配置文件：
   ```yaml
   volumes:
     - ./config.yaml:/app/config.yaml
   ```

## 常见问题

### 1. 端口被占用

错误信息：`Bind for 0.0.0.0:8502 failed: port is already allocated`

解决方案：
- 修改 `docker-compose.yml` 中的端口映射
- 或停止占用该端口的进程

### 2. 权限问题

错误信息：`Permission denied`

解决方案：
```bash
# 确保数据目录有正确的权限
chmod -R 755 data/ logs/
```

### 3. 内存不足

错误信息：`Killed` 或 OOM

解决方案：
- 增加 Docker 内存限制（Docker Desktop → Settings → Resources）
- 或减少分析的数据量

### 4. 爬虫无法访问网络

问题：容器内无法访问外部网站

解决方案：
- 确保宿主机网络正常
- 检查防火墙设置
- 考虑使用 `--network=host` 模式（仅 Linux）

## 维护与监控

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f sentiment-analysis
```

### 进入容器

```bash
docker exec -it disney-sentiment-analysis /bin/bash
```

### 备份数据

```bash
# 备份数据目录
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/
```

### 更新系统

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

## 性能优化

### 1. 使用多阶段构建

Dockerfile 已优化为多阶段构建，减小镜像大小。

### 2. 启用 Redis 缓存

配置使用 Redis 缓存分析结果，提升响应速度。

### 3. 资源限制

在 `docker-compose.yml` 中添加资源限制：
```yaml
services:
  sentiment-analysis:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## 安全建议

1. **不要在生产环境暴露 Redis 端口**
   - 修改 `docker-compose.yml`，移除 Redis 的端口映射
   - 或使用 Docker 网络内部通信

2. **使用 HTTPS**
   - 配置反向代理（如 Nginx）
   - 使用 Let's Encrypt 证书

3. **定期更新基础镜像**
   ```bash
   docker pull python:3.10-slim
   docker-compose build --no-cache
   ```

4. **限制容器权限**
   - 使用非 root 用户运行
   - 只读挂载文件系统（除数据目录外）

## 技术支持

如遇到问题，请参考：
- 项目 README.md
- 用户使用手册.md
- GitHub Issues（如有）
