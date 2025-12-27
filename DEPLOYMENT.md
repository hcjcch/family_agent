# 服务器部署指南

## 前置准备

### 1. 安全组配置
在云服务器控制台开放端口：
- **8000** - API 访问端口（必须）
- **22** - SSH 登录（如需）

### 2. 安装 Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# 重新登录后生效
```

## 部署步骤

### 1. 上传代码到服务器
```bash
# 方式1: 使用 git
git clone <你的仓库地址> /opt/family-butler-ai
cd /opt/family-butler-ai

# 方式2: 使用 scp 打包上传（在本地执行）
tar czf family-butler-ai.tar.gz family-butler-ai
scp family-butler-ai.tar.gz root@your-server:/opt/
# 在服务器上解压
cd /opt && tar xzf family-butler-ai.tar.gz
```

### 2. 配置环境变量
```bash
cd /opt/family-butler-ai

# 复制模板并编辑
cp .env.example .env
nano .env  # 或使用 vi

# 修改以下配置：
# DB_PASSWORD=your_secure_password_here
# OPENAI_API_KEY=your_deepseek_api_key
```

### 3. 构建并启动服务
```bash
# 构建镜像（首次运行需要）
docker-compose build

# 后台启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 验证部署
```bash
# 检查服务健康状态
curl http://localhost:8000/docs

# 从外部访问（替换为你的服务器公网IP）
curl http://<你的服务器IP>:8000/docs
```

## 服务管理

```bash
# 查看所有服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
docker-compose logs -f db

# 重启服务
docker-compose restart backend

# 停止所有服务
docker-compose down

# 停止并删除数据（危险操作！）
docker-compose down -v
```

## 数据备份

```bash
# 备份数据库
docker-compose exec db mysqldump -uroot -p${DB_PASSWORD} family_butler > backup_$(date +%Y%m%d).sql

# 备份 ChromaDB 数据
docker run --rm -v butler_chromadata:/data -v $(pwd):/backup alpine tar czf /backup/chromadb_$(date +%Y%m%d).tar.gz -C /data .
```

## 故障排查

### 服务无法启动
```bash
# 查看详细日志
docker-compose logs backend

# 检查端口占用
netstat -tlnp | grep 8000
```

### 数据库连接失败
```bash
# 等待数据库健康检查完成
docker-compose ps

# 查看数据库日志
docker-compose logs db
```

## 后续优化建议

1. **配置域名和 HTTPS**：使用 Nginx 反向代理 + Let's Encrypt
2. **配置防火墙**：只开放必要端口
3. **定期备份**：设置 cron 任务自动备份数据
4. **监控告警**：配置服务健康监控
