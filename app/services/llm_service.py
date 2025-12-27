# app/services/llm_service.py
"""
LLM服务模块
使用统一的API配置管理DeepSeek LLM
"""

import json
from openai import OpenAI
from typing import List, Optional, Any, Dict
from app.core.api_config import APIConfigs

# 使用统一配置初始化DeepSeek客户端
client_config = APIConfigs.get_deepseek_config()
client = OpenAI(**client_config)


def classify_intent(text: str):
    """
    多意图识别分类
    返回: QUERY, ADD, USE, CHAT
    """
    prompt = f"""
    你是一个智能管家。请分析用户的自然语言指令，严格返回以下 4 个单词中的一个：

    1. QUERY - 用户在询问位置、数量、或者寻找物品。 (e.g. "在哪?", "还有没?", "找一下X")
    2. ADD   - 用户在录入新物品，或者归位物品。 (e.g. "买了X", "把X放Y了", "新到了X")
    3. USE   - 用户在消耗、使用、扔掉物品。 (e.g. "喝了X", "用了X", "X过期扔了")
    4. CHAT  - 纯闲聊、打招呼、感谢，没有涉及具体物品操作。 (e.g. "你好", "谢谢", "笨蛋")

    用户输入: "{text}"

    只返回分类单词，不要标点。
    """
    try:
        response = client.chat.completions.create(
            model=APIConfigs.DEEPSEEK.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # 低温度，保证分类准确
        )
        return response.choices[0].message.content.strip().upper()
    except:
        return "CHAT"  # 默认兜底为闲聊，比较安全


def extract_item_info(user_text: str):
    """
    从文本中提取物品信息
    返回: {"name": "...", "quantity": ..., "unit": "...", "location": "...", "category": "..."}
    """
    prompt = f"""
    从文本中提取物品信息。返回 JSON:
    {{
        "name": "物品名",
        "quantity": 数字,
        "unit": "单位",
        "location": "位置",
        "category": "分类"
    }}
    用户输入: "{user_text}"
    如果无法提取，返回 null。
    """
    try:
        response = client.chat.completions.create(
            model=APIConfigs.DEEPSEEK.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except:
        return None


def generate_natural_response(user_text: str, action_type: str, data: Any):
    """
    生成自然语言回复
    """
    system_prompt = "你是一个贴心的家庭管家 AI。请根据系统数据，用自然口语回答。"

    user_content = f"用户说: {user_text}\n"

    if action_type == "CHAT":
        user_content += (
            "这不是指令，只是闲聊。请热情、幽默地回应用户。你是管家，可以叫用户'主人'。"
        )
    elif action_type == "USE":
        user_content += (
            f"系统操作结果: {json.dumps(data, ensure_ascii=False, default=str)}\n"
            "用户消耗了物品。请确认已记录消耗。提醒用户如果快没了记得补货。"
        )
    elif action_type == "RECORD" or action_type == "ADD":
        user_content += (
            f"系统操作结果: {json.dumps(data, ensure_ascii=False, default=str)}\n"
            "请告诉用户你已经记下来了。"
        )
    elif action_type == "QUERY":
        user_content += (
            f"系统搜索结果: {json.dumps(data, ensure_ascii=False, default=str)}\n"
            "请汇报位置和数量。"
        )

    print("User Content for LLM:\n", user_content)

    try:
        response = client.chat.completions.create(
            model=APIConfigs.DEEPSEEK.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except:
        return "好的，处理完了。"


def chat(messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Any:
    """
    统一的对话接口

    :param messages: 对话历史 [{"role": "user", "content": "..."}]
    :param tools: 工具定义 (JSON Schema 列表)
    :return: LLM 的响应消息对象 (包含 content 和 tool_calls)
    """
    try:
        # 构造参数字典
        params = {
            "model": APIConfigs.DEEPSEEK.model,
            "messages": messages,
            "temperature": 0.1,
        }

        # 只有当传入工具时，才添加 tools 参数
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        # 调用大模型
        response = client.chat.completions.create(**params)

        # 返回 message 对象 (包含 content, tool_calls 等)
        return response.choices[0].message

    except Exception as e:
        print(f"❌ LLM 调用失败: {str(e)}")
        raise e
