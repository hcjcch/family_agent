# app/services/chat_service.py

from sqlalchemy.orm import Session
from app import models
import uuid
import json
from app.core.config import SYSTEM_PROMPT


class ChatService:
    def __init__(self, db: Session, user_id: int = 1):
        self.db = db
        self.user_id = user_id

    def get_or_create_active_session(self):
        """
        获取当前活跃的会话，没有就新建
        """
        session = (
            self.db.query(models.Session)
            .filter(
                models.Session.user_id == self.user_id, models.Session.is_active == 1
            )
            .order_by(models.Session.updated_at.desc())
            .first()
        )

        if not session:
            session = models.Session(user_id=self.user_id)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

        return session

    def add_message(
        self, session_id: str, role: str, content: str, tool_call_id: str = None
    ):
        """
        存入一条新消息
        """
        # 如果 content 是对象/列表（比如工具结果），转成 JSON 字符串存
        if not isinstance(content, str) and content is not None:
            content = json.dumps(content, ensure_ascii=False, default=str)

        msg = models.ChatMessage(
            session_id=session_id, role=role, content=content, tool_call_id=tool_call_id
        )
        self.db.add(msg)
        self.db.commit()
        return msg

    def get_context_messages(self, session_id: str, limit: int = 10):
        """
        【核心逻辑】构建发给 LLM 的上下文
        策略：摘要 + 最近 N 条
        """
        session = (
            self.db.query(models.Session)
            .filter(models.Session.id == session_id)
            .first()
        )

        # 1. 取出最近 N 条记录
        # 注意：倒序取最后10条，然后再正序排回来
        recent_msgs = (
            self.db.query(models.ChatMessage)
            .filter(models.ChatMessage.session_id == session_id)
            .order_by(models.ChatMessage.id.desc())
            .limit(limit)
            .all()
        )

        recent_msgs.reverse()  # 翻转为时间正序

        context = []

        # 2. 注入系统提示词 (System Prompt)
        system_content = SYSTEM_PROMPT

        # 3. 注入摘要 (如果有) - 这就是长期记忆！
        if session.summary:
            system_content += f"\n【前情提要】: {session.summary}"

        context.append({"role": "system", "content": system_content})

        # 4. 注入最近对话
        for msg in recent_msgs:
            msg_dict = {"role": msg.role, "content": msg.content}
            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id

            # 对于 tool 类型的消息，必须带上 tool_call_id
            # 对于 assistant 类型的消息，如果有 tool_calls (我们这里简化了，只存了文本)，
            # 在复杂场景下需要还原 tool_calls 结构。
            # V1 简化：假设 assistant 只是纯回复，tool_calls 我们在下一轮 prompt 里可能没法完美复现
            # 但对于"记忆"来说，文本内容最重要。

            context.append(msg_dict)

        print("Context Messages for LLM:\n", context)
        return context

    def update_summary(self, session_id: str):
        """
        (高级功能) 调用 LLM 生成摘要并更新 Session
        可以在每 N 轮对话后触发
        """
        # 这里可以调用 llm_engine 生成摘要
        pass
