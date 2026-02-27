import os
from openai import OpenAI
import json

import all_tool
import message
import tool 
from dotenv import load_env_file

class Agent:
    def __init__(self, api_key=None, base_url=None, max_steps=5):
        load_env_file()
        api_key = api_key or os.getenv("APIKEY")
        base_url = base_url or os.getenv("BASE_URL")
        if not api_key or not base_url:
            raise ValueError("缺少 APIKEY 或 BASE_URL，请检查 .env 配置")

        self.messages = [{"role":"system","content":"你是一个会根据语境是使用工具的助手，名字叫做准OK，用户问你叫什么的时候就可以亲切"}]
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.max_steps = max_steps
        self.tools = self._build_tools()

    def _build_tools(self):
        tools = []
        for name, meta in all_tool.tool_meta.items():
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": meta.get("description", ""),
                        "parameters": meta.get("parameters", {"type": "object", "properties": {}}),
                    },
                }
            )
        return tools

    def call_model(self):
        return self.client.chat.completions.create(
            model="qwen3-max",
            messages=self.messages,
            tools=self.tools,
            tool_choice="auto",
        )

    def run(self, user_input: str):
        # 1) 把用户输入加入对话历史，作为本轮推理起点
        self.messages.append({"role": "user", "content": user_input})
        step = 0
        # 调试输出：打印当前完整消息上下文，便于观察模型看到的内容
        # for message in self.messages:
        #     print(message)

        # 2) 在最大步数内循环：模型回复 -> (可选)工具执行 -> 再次请求模型
        while step < self.max_steps:
            step += 1
            response = self.call_model()
            assistant_msg = response.choices[0].message
            # 如果模型决定调用工具，assistant_msg.tool_calls 会有内容
            if assistant_msg.tool_calls:
                # 先把“模型提出的工具调用意图”写回历史，保持上下文完整
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_msg.content or "",
                        "tool_calls": [tc.model_dump() for tc in assistant_msg.tool_calls],
                    }
                )

                print("assistant_msg.tool_calls:", assistant_msg.tool_calls)

                # 3) 逐个执行工具调用
                for tool_call in assistant_msg.tool_calls:
                    tool_name = tool_call.function.name
                    tool_func = all_tool.all_tool.get(tool_name)
                    try:
                        # 模型传入的 arguments 是 JSON 字符串，先反序列化
                        arguments = json.loads(tool_call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        # 参数解析失败时，兜底为空参数，避免流程中断
                        arguments = {}

                    if not tool_func:
                        result = {"error": f"未找到工具: {tool_name}"}
                    else:
                        result = tool_func(**arguments)

                    # 把工具执行结果写回对话，供下一次模型调用继续推理
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result),
                        }
                    )
                # 本轮已处理工具，回到循环顶部让模型基于工具结果继续回答
                continue

            # 没有工具调用时，说明是最终自然语言回复，直接返回给用户
            model_output = assistant_msg.content or ""
            self.messages.append({"role": "assistant", "content": model_output})
            return model_output

        # 超过最大步数仍未产出最终回答，返回保护性提示
        return "达到最大调用步数，未完成。"

if __name__ == "__main__":
    agent = Agent()

    while True:
        user_input = input("你: ")
        answer = agent.run(user_input)
        print("助手:", answer)