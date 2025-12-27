# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

这是一个AI家庭管家系统，采用FastAPI + MySQL + Mem0架构，提供智能物品管理和对话功能。项目主要面向中文用户，所有AI交互和文档都使用中文。

## Common Development Commands

### 运行应用
```bash
# Docker方式（推荐）
docker-compose up -d

# 本地开发方式（需先激活虚拟环境）
source venv/bin/activate  # 或在Windows上使用 venv\Scripts\activate
uvicorn app.main:app --reload
```

### 虚拟环境管理
```bash
# 如果虚拟环境不存在，创建新的虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖到虚拟环境
pip install -r requirements.txt
```

### 数据库操作
```bash
# 查看数据库状态
docker-compose exec db mysql -uroot -prootpassword family_butler -e "SHOW TABLES;"

# 重置数据库（删除所有数据）
docker-compose down -v
docker-compose up -d
```

### 调试接口
```bash
# 查看所有数据库内容
curl http://localhost:8000/debug/dump

# 查看物品-位置关系
curl http://localhost:8000/debug/relationship

# 查看Mem0记忆存储
curl http://localhost:8000/debug/memories
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
- **FastAPI应用入口**: `app/main.py` - 所有API路由都在这里注册
- **工具注册系统**: `app/core/tool_registry.py` - 使用装饰器模式管理AI工具
- **服务层**: `app/services/` - 包含业务逻辑
  - `chat_service.py` - 会话和消息历史管理
  - `llm_service.py` - DeepSeek LLM集成
  - `business.py` - 业务逻辑封装
- **数据层**:
  - `app/models.py` - SQLAlchemy数据模型
  - `app/crud.py` - 数据库CRUD操作
- **工具目录**: `app/tools/` - AI可调用的工具函数
  - `inventory_tools.py` - 物品录入、消耗、移动
  - `search_tools.py` - 物品搜索
  - `report_tools.py` - 库存报表

### AI功能架构
- **LLM集成**: DeepSeek API，配置在`app/core/config.py`
  - API Key通过环境变量`OPENAI_API_KEY`配置
  - Base URL通过`OPENAI_BASE_URL`配置
- **记忆系统**: Mem0 + ChromaDB
  - ChromaDB运行在8001端口（docker-compose中映射）
  - Mem0配置在`app/core/config.py`的`m`实例
- **工具调用**: 支持多工具并行调用

### 工具系统工作流程
1. **注册阶段**: 工具函数使用`@registry.register()`装饰器注册（在`app/tools/`各文件中）
2. **Schema生成**: `registry.get_schemas()`返回工具的JSON Schema给LLM
3. **工具调用**: LLM返回tool_calls后，通过`registry.execute(name, args, context)`执行
4. **上下文注入**: context参数包含`db`和`user_id`，自动注入到工具函数

### 对话上下文管理（ChatService）
- **会话创建**: `ensure_session(session_id)` - 确保会话存在，不存在则创建
- **消息历史**: `get_context_messages(session_id, limit)` - 构建发给LLM的上下文
  - 包含System Prompt（来自`app/core/config.py`的`SYSTEM_PROMPT`）
  - 包含会话摘要（session.summary，长期记忆）
  - 包含最近N条消息
- **标题管理**: `update_session_title(session_id, title)` - 更新会话标题（截取前30字符）

### 数据库模型关系
- **Item → Inventory ← Location**: 多对多关系，通过Inventory表连接
- **Session → ChatMessage**: 一对多关系，一个会话包含多条消息
- **唯一约束**:
  - `(user_id, name)` - 同一用户下物品名唯一
  - `(item_id, location_id)` - 同一物品在同一位置只有一条库存记录

### 关键设计模式
1. **工具注册装饰器**: `@registry.register(name, description, parameters)`
2. **会话管理**: ChatService管理用户会话和消息历史
3. **多任务处理**: 一次AI响应可调用多个工具（通过一次响应中的多个tool_calls）

## Important Notes

1. **中文优先**: 所有用户交互、AI回复都使用中文
2. **工具调用规则**: AI响应中工具调用必须放在普通文本之前（在Tool Call阶段不生成文本）
3. **会话状态**: 每个用户只有一个活跃的会话，存储在sessions表中
4. **虚拟环境**: 运行Python代码前确保激活虚拟环境（项目根目录的venv）
5. **API文档**: 访问http://localhost:8000/docs查看Swagger文档
6. **指代消解**: SYSTEM_PROMPT中特别强调需要处理上下文中的"它"、"这个"等指代
7. **修正模式**: 当用户补充/修正上一条指令时，应使用`update_item_location`而非`record_new_item`

## Environment Variables

在`docker-compose.yml`中配置的关键环境变量：
- `DATABASE_URL` - MySQL连接字符串（使用pymysql驱动）
- `OPENAI_API_KEY` - DeepSeek API密钥
- `OPENAI_BASE_URL` - DeepSeek API基础URL（默认：https://api.deepseek.com）
- `CHROMA_HOST` / `CHROMA_PORT` - ChromaDB连接信息
