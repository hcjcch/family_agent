# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

这是一个AI家庭管家系统，采用FastAPI + MySQL + Mem0架构，提供智能物品管理和对话功能。项目主要面向中文用户，所有AI交互和文档都使用中文。

## Common Development Commands

### 运行应用
```bash
# Docker方式（推荐）
docker-compose up -d

# 本地开发方式
uvicorn app.main:app --reload
```

### 数据库操作
```bash
# 查看数据库状态
docker-compose exec db mysql -uroot -prootpassword family_butler -e "SHOW TABLES;"

# 重置数据库（删除所有数据）
docker-compose down -v
docker-compose up -d
```

### 代码检查
```bash
# 检查Python语法
python -m py_compile app/main.py

# 检查所有Python文件
find app -name "*.py" -exec python -m py_compile {} \;
```

## Architecture Overview

### 核心架构
- **FastAPI应用**: `app/main.py`是入口点，所有API路由都在这里注册
- **工具系统**: 使用装饰器模式注册AI工具，`app/core/tool_registry.py`管理所有工具
- **服务层**: `app/services/`包含业务逻辑，如聊天服务、LLM服务
- **数据库**: SQLAlchemy模型在`app/models.py`，CRUD操作在`app/crud.py`

### AI功能架构
- **LLM集成**: DeepSeek API，配置在`app/core/config.py`
- **记忆系统**: Mem0 + ChromaDB，用于存储用户交互历史
- **工具调用**: 支持多工具并行调用，工具定义在`app/tools/`目录

### 关键设计模式
1. **工具注册**: 使用`@tool_registry.register()`装饰器注册AI工具
2. **会话管理**: ChatService管理用户会话和消息历史
3. **多任务处理**: 一次AI响应可调用多个工具

### 数据库模型关系
- Item -> Inventory <- Location （多对多关系）
- Session -> ChatMessage （一对多关系）
- 所有模型都继承自Base，使用UUID主键

## Important Notes

1. **中文优先**: 所有用户交互、AI回复都使用中文
2. **工具调用规则**: AI响应中工具调用必须放在普通文本之前
3. **会话状态**: 每个用户只有一个活跃的会话，存储在sessions表中
4. **虚拟环境**: 运行Python代码前确保激活虚拟环境（项目根目录的venv）
5. **API文档**: 访问http://localhost:8000/docs查看Swagger文档