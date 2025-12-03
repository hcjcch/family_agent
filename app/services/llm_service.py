# app/services/llm_service.py
import os
import json
from openai import OpenAI

# 使用环境变量里的 DeepSeek 配置
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL")
)


def extract_item_info(user_text: str):
    """
    调用 LLM 从自然语言中提取结构化 JSON
    """
    prompt = f"""
    你是一个家庭物品管理助手。请从用户的输入中提取物品信息。
    用户输入: "{user_text}"
    
    请严格按照以下 JSON 格式返回，不要包含 markdown 格式或其他废话：
    {{
        "name": "物品名称",
        "quantity": 数字 (默认1),
        "unit": "单位" (如: 个, 箱, 瓶. 默认为'个'),
        "location": "位置名称" (如果未提及，返回 null),
        "category": "分类" (推断一个分类，如: 食品, 电器)
    }}
    
    如果无法提取，返回 null。
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},  # 强制返回 JSON
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"LLM Extraction Error: {e}")
        return None
