from math import log
from all_tool import tool


@tool(name="getWeather", description="返回城市天气", parameters={
    "type": "object",
    "properties": {"city": {"type": "string"}},
    "required": ["city"]
})
def weather_tool(city: str):
    print("触发了天气工具")
    return f"{city} 今天晴"

@tool(name="echo", description="返回原文", parameters={
    "type": "object",
    "properties": {"text": {"type": "string"}},
    "required": ["text"]
})
def echo_tool(text: str):
    print("触发了文案本")
    return f"Echo: {text}"

@tool(name="deepMatch", description="返回深度匹配结果", parameters={
    "type": "object",
    "properties": {"text": {"type": "string"}},
    "required": ["text"]
})
def echo_tool(text: str):
    print("触发了深度匹配工具")
    return f"深度匹配结果: {text}"