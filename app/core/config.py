# app/core/config.py
import os
from mem0 import Memory

# 获取 DeepSeek Key
deepseek_api_key = os.getenv("OPENAI_API_KEY")
deepseek_base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
print(f"DeepSeek API Key: {deepseek_api_key}")
print(f"DeepSeek Base URL: {deepseek_base_url}")

if not deepseek_api_key:
    raise ValueError("⚠️ 未找到 OPENAI_API_KEY docker-compose.yml 配置")

config = {
    # 1. 向量存储 (保持不变: ChromaDB)
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "family_memories",
            "host": os.getenv("CHROMA_HOST", "chromadb"),
            "port": int(os.getenv("CHROMA_PORT", 8000)),
        },
    },
    # 2. 嵌入模型 (保持不变: 本地 HuggingFace)
    # 这样向量化是不花钱的，而且数据隐私更好
    "embedder": {
        "provider": "huggingface",
        "config": {"model": "shibing624/text2vec-base-chinese"},
    },
    # 3. 大语言模型 (切换为: DeepSeek)
    "llm": {
        "provider": "deepseek",
        "config": {
            "model": "deepseek-chat",  # DeepSeek 的模型名称
            "temperature": 0.1,  # 低温度让回答更严谨
            "max_tokens": 1500,
            "deepseek_base_url": deepseek_base_url,  # DeepSeek API 基础地址
            "api_key": deepseek_api_key,  # DeepSeek API 密钥
        },
    },
}

print("正在初始化 Mem0 (DeepSeek + Local Chroma)...")
m = Memory.from_config(config)
print("Mem0 初始化完成！")
