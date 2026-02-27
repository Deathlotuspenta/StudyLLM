import functools
from typing import Callable
import jsonschema  # pyright: ignore[reportMissingModuleSource]

all_tool = {}
tool_meta = {}

def tool(name=None,description=None, parameters: dict = None, timeout: int = 5):
    """装饰器注册工具"""
    parameters = parameters or {}

    def decorator(func:Callable):
        tool_name = name or func.__name__
        tool_meta[tool_name] = {
            "description": description or "",
            "parameters": parameters,
            "timeout": timeout,
        }

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                jsonschema.validate(instance=kwargs, schema=parameters)
            except Exception as e:
                print(str(e))
                return {"error":f"参数不合法{str(e)}"}

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                print(str(e))
                return {"error":f"工具执行失败{str(e)}"}

            return result
        all_tool[tool_name] = wrapper
        return wrapper
    return decorator
            