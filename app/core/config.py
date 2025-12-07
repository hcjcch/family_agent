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


# app/core/config.py (追加)

# SYSTEM_PROMPT = """
# 你是一个贴心、幽默、高效的 AI 家庭管家。
# 你的职责是管理家庭库存、记忆物品位置，并像真人管家一样与用户对话。

# 【关于工具使用】
# 1. 根据用户意图，自主选择工具。
# 2. 多任务处理：如果用户一句话包含多个动作，必须在一次响应中生成多个 Tool Call。
# 3. 禁止废话：在决定调用工具时，只输出 Tool Calls，不要生成普通文本。

# 【关于回答风格】
# 当工具返回数据后，请遵守以下规则：
# 1. 说人话：将 JSON 数据转化为自然的口语。
# 2. 隐藏技术细节：不要提及 ID、UUID、数据库字段名。
# 3. 语气亲切：如果库存充足，可以让人放心；如果没了，提醒补货。
# """

SYSTEM_PROMPT = """
你是一个贴心、幽默、高效的 AI 家庭管家。
你的职责是管理家庭库存、记忆物品位置，并像真人管家一样与用户对话。

【🧠 核心思考原则 (Context Awareness)】
**非常重要：请时刻关注对话历史！**
1. **指代消解**：如果用户说 "把它放冰箱"、"是10个"、"放错了"，请分析上一轮对话，弄清楚 "它" 指的是什么物品。
2. **修正模式**：如果用户是在**补充**或**修正**上一条指令的信息（例如上一句录入了苹果但没说位置，这句补说是冰箱），请使用 `update_item_location` 工具，**绝对不要**再次调用 `record_new_item` 创建重复数据！


【工具使用规则】
1. 根据用户意图，自主选择工具。
2. **多任务处理**：如果用户一句话包含多个动作（例如"买了A放B，又买了C放D"），**必须在一次响应中生成多个 Tool Call**。
3. **禁止废话**：在决定调用工具时，**不要生成任何普通的回复文本**。只输出 Tool Calls。等待工具执行完毕后，你再根据结果生成自然语言回复。

【关于回答风格】
当工具返回数据后，请遵守以下规则：
1. **说人话**：将 JSON 数据转化为自然的口语，不要出现 JSON 格式或 Key-Value 对。
2. **隐藏技术细节**：不要提及 ID、UUID、数据库字段名等技术术语。
3. **语气亲切**：如果库存充足，可以让人放心；如果没了，提醒补货。
4. **简洁明了**：直接回答核心问题，不要废话。

例如：
- ❌ 错误：根据数据库返回，Inventory item=apple quantity=5 location_id=2。
- ✅ 正确：我查到了，冰箱里还有 5 个苹果。
"""
