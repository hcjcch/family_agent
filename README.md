# 家庭管家 AI (Family Butler AI)

一个基于 FastAPI 的家庭物品管理系统，帮助您跟踪和管理家庭物品库存。

## 功能特性

- 📦 **物品管理**: 创建和管理家庭物品清单
- 📍 **位置跟踪**: 记录物品存放位置，支持层级位置结构
- 📊 **库存管理**: 跟踪物品数量和状态
- 🗓️ **过期提醒**: 记录物品过期日期
- 🔍 **智能搜索**: 快速查找物品和位置
- 🤖 **AI 助手**: 集成 AI 功能提供智能建议

## 技术栈

- **后端框架**: FastAPI
- **数据库**: SQLAlchemy + MySQL
- **AI 功能**: mem0ai, chromadb
- **容器化**: Docker & Docker Compose
- **Python 版本**: 3.11+

## 快速开始

### 环境要求

- Python 3.11+
- Docker & Docker Compose (推荐)
- MySQL 数据库

### 使用 Docker 运行

1. 克隆仓库：
```bash
git clone git@github.com:hcjcch/family_agent.git
cd family_agent
```

2. 启动服务：
```bash
docker-compose up -d
```

3. 访问应用：
```
http://localhost:8000
```

### 本地开发

1. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 运行应用：
```bash
uvicorn app.main:app --reload
```

## 数据模型

### 主要实体

- **Item (物品)**: 家庭物品的基本信息
- **Location (位置)**: 物品存放位置，支持层级结构
- **Inventory (库存)**: 物品在特定位置的库存记录

### 数据库关系

- 一个物品可以有多个库存记录
- 一个位置可以有多个库存记录
- 物品和位置通过库存记录建立多对多关系

## API 文档

启动应用后，可以访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 项目结构

```
family-butler-ai/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 应用入口
│   ├── database.py      # 数据库连接配置
│   ├── models.py        # SQLAlchemy 数据模型
│   ├── schemas.py       # Pydantic 数据验证模型
│   ├── crud.py          # 数据库操作函数
│   └── routers/         # API 路由模块
├── requirements.txt     # Python 依赖
├── Dockerfile          # Docker 镜像配置
└── docker-compose.yml  # Docker Compose 配置
```

## 配置说明

### 数据库配置

在 `docker-compose.yml` 中配置 MySQL 数据库连接信息：

```yaml
environment:
  MYSQL_ROOT_PASSWORD: your_password
  MYSQL_DATABASE: family_butler
```

### 环境变量

您可以通过环境变量配置以下参数：
- `DATABASE_URL`: 数据库连接字符串
- `SECRET_KEY`: 应用密钥
- `DEBUG`: 调试模式开关

## 贡献指南

1. Fork 本仓库
2. 创建您的功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目地址: [https://github.com/hcjcch/family_agent](https://github.com/hcjcch/family_agent)
- 问题反馈: [GitHub Issues](https://github.com/hcjcch/family_agent/issues)

---

⭐ 如果这个项目对您有帮助，请给它一个星标！