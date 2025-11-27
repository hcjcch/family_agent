# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 从环境变量获取数据库连接信息，如果在 Docker 里，DB_HOST 就是 'db'
# 格式: mysql+pymysql://user:password@host/dbname
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", "mysql+pymysql://root:rootpassword@db/family_butler"
)

# 创建引擎
# pool_pre_ping=True 可以防止数据库连接超时断开
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 所有模型的基类
Base = declarative_base()


# 依赖项：用于在 API 请求中获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
