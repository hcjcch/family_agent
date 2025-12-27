# app/core/api_config.py
"""
统一的API配置管理模块
集中管理所有第三方API的密钥和配置
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class APIConfig:
    """API配置基类"""

    api_key: str
    base_url: str
    model: str


class APIConfigs:
    """所有API配置的统一管理"""

    # ==================== DeepSeek (LLM) ====================
    DEEPSEEK = APIConfig(
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        model="deepseek-chat",
    )

    # ==================== 千问 Qwen (Embedding) ====================
    QWEN = APIConfig(
        api_key=os.getenv("QWEN_API_KEY", ""),
        base_url=os.getenv(
            "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        ),
        model="text-embedding-v3",
    )

    # ==================== ChromaDB ====================
    CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

    @classmethod
    def validate(cls) -> None:
        """验证所有必需的API配置是否存在"""
        errors = []

        if not cls.DEEPSEEK.api_key:
            errors.append("DEEPSEEK_API_KEY 未配置")

        if not cls.QWEN.api_key:
            errors.append("QWEN_API_KEY 未配置")

        if errors:
            raise ValueError("⚠️ API配置错误:\n" + "\n".join(f"  - {e}" for e in errors))

    @classmethod
    def get_deepseek_config(cls) -> dict:
        """获取DeepSeek LLM配置（用于OpenAI客户端）"""
        return {
            "api_key": cls.DEEPSEEK.api_key,
            "base_url": cls.DEEPSEEK.base_url,
        }

    @classmethod
    def get_qwen_config(cls) -> dict:
        """获取千问Embedding配置（用于OpenAI兼容客户端）"""
        return {
            "api_key": cls.QWEN.api_key,
            "base_url": cls.QWEN.base_url,
        }

    @classmethod
    def get_mem0_config(cls) -> dict:
        """
        获取Mem0配置
        注意：Mem0的embedder使用OpenAI兼容接口，需要显式传入配置
        """
        return {
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "family_memories",
                    "host": cls.CHROMA_HOST,
                    "port": cls.CHROMA_PORT,
                },
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": cls.QWEN.model,
                    "api_key": cls.QWEN.api_key,  # 显式传入千问的key
                    "openai_base_url": cls.QWEN.base_url,  # 千问的base URL
                },
            },
            "llm": {
                "provider": "deepseek",
                "config": {
                    "model": cls.DEEPSEEK.model,
                    "temperature": 0.1,
                    "max_tokens": 1500,
                    "api_key": cls.DEEPSEEK.api_key,
                    "deepseek_base_url": cls.DEEPSEEK.base_url,
                },
            },
        }


# 验证配置（模块加载时自动检查）
APIConfigs.validate()

# 打印配置信息（调试用）
print(f"✅ DeepSeek API: {APIConfigs.DEEPSEEK.base_url}")
print(f"✅ 千问 Embedding: {APIConfigs.QWEN.base_url}")
print(f"✅ ChromaDB: {APIConfigs.CHROMA_HOST}:{APIConfigs.CHROMA_PORT}")
