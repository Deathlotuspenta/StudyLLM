import unittest
from types import SimpleNamespace
from unittest.mock import patch

from model import Agent


def fake_response(content="", tool_calls=None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls or [])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def fake_tool_call(name, arguments, tool_call_id="call_1"):
    function = SimpleNamespace(name=name, arguments=arguments)
    return SimpleNamespace(
        id=tool_call_id,
        function=function,
        model_dump=lambda: {
            "id": tool_call_id,
            "type": "function",
            "function": {"name": name, "arguments": arguments},
        },
    )


class AgentForTest(Agent):
    def __init__(self, responses):
        with patch("model.OpenAI"):
            super().__init__(api_key="test_key", base_url="http://test.local")
        self._responses = responses

    def call_model(self):
        return self._responses.pop(0)


class AgentTests(unittest.TestCase):
    def test_echo_tool_success(self):
        responses = [
            fake_response(
                content="",
                tool_calls=[fake_tool_call("echo", '{"text":"hello"}')],
            ),
            fake_response(content="已完成"),
        ]
        agent = AgentForTest(responses)
        result = agent.run("帮我回显")

        self.assertEqual(result, "已完成")
        tool_messages = [m for m in agent.messages if m["role"] == "tool"]
        self.assertTrue(any("Echo: hello" in m["content"] for m in tool_messages))

    def test_tool_param_validation_error(self):
        responses = [
            fake_response(
                content="",
                tool_calls=[fake_tool_call("echo", "{}")],
            ),
            fake_response(content="参数处理结束"),
        ]
        agent = AgentForTest(responses)
        result = agent.run("调用 echo")

        self.assertEqual(result, "参数处理结束")
        tool_messages = [m for m in agent.messages if m["role"] == "tool"]
        self.assertTrue(any("参数不合法" in m["content"] for m in tool_messages))

    def test_no_tool_direct_reply(self):
        agent = AgentForTest([fake_response(content="直接回复")])
        result = agent.run("你好")
        self.assertEqual(result, "直接回复")


if __name__ == "__main__":
    unittest.main()
