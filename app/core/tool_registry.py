# app/core/tool_registry.py
import json
import functools
from typing import Callable, Dict, List, Any


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: List[Dict[str, Any]] = []

    def register(self, name: str, description: str, parameters: dict):
        """
        装饰器：用于注册工具
        """

        def decorator(func: Callable):
            # 1. 注册函数本身
            self._tools[name] = func

            # 2. 注册给 LLM 看的 Schema
            schema = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            }
            self._schemas.append(schema)

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def get_schemas(self):
        """获取所有工具的 Schema 给 LLM"""
        return self._schemas

    def get_tool(self, name: str):
        """获取工具函数"""
        return self._tools.get(name)

    def execute(self, name: str, args: dict, context: dict = None):
        """
        执行工具
        context: 用于注入 db, user_id 等上下文依赖
        """
        func = self.get_tool(name)
        if not func:
            return f"Error: Tool '{name}' not found."

        try:
            # 将 args (来自LLM) 和 context (来自后端) 合并传给函数
            # 注意：工具函数定义时需要接收 **kwargs 或者明确的参数名
            return func(**args, **(context or {}))
        except Exception as e:
            return f"Error executing tool '{name}': {str(e)}"


# 全局单例
registry = ToolRegistry()
