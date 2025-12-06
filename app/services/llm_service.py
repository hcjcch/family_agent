# app/services/llm_service.py
import os
import json
from openai import OpenAI

# 使用环境变量配置
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL")
)


def classify_intent(text: str):
    """
    [升级版] 多意图识别
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
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # 低温度，保证分类准确
        )
        return response.choices[0].message.content.strip().upper()
    except:
        return "CHAT"  # 默认兜底为闲聊，比较安全


def extract_item_info(user_text: str):
    """
    (保持之前的逻辑不变) 提取物品 JSON
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
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except:
        return None


# app/services/llm_service.py


def generate_natural_response(user_text: str, action_type: str, data: any):
    system_prompt = "你是一个贴心的家庭管家 AI。请根据系统数据，用自然口语回答。"

    user_content = f"用户说: {user_text}\n"

    if action_type == "CHAT":
        user_content += (
            "这不是指令，只是闲聊。请热情、幽默地回应用户。你是管家，可以叫用户'主人'。"
        )

    elif action_type == "USE":
        user_content += (
            f"系统操作结果: {json.dumps(data, ensure_ascii=False, default=str)}\n"
        )
        user_content += "用户消耗了物品。请确认已记录消耗。提醒用户如果快没了记得补货。"

    elif action_type == "RECORD" or action_type == "ADD":  # 兼容旧名为 RECORD
        user_content += (
            f"系统操作结果: {json.dumps(data, ensure_ascii=False, default=str)}\n"
        )
        user_content += "请告诉用户你已经记下来了。"

    elif action_type == "QUERY":
        user_content += (
            f"系统搜索结果: {json.dumps(data, ensure_ascii=False, default=str)}\n"
        )
        user_content += "请汇报位置和数量。"

    # ... (发送请求代码不变)

    # 打印 user_content 以便调试
    print("User Content for LLM:\n", user_content)

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.7,  # 稍微高一点，让说话更自然
        )
        return response.choices[0].message.content
    except:
        return "好的，处理完了。"
