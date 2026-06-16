"""
Function Calling 动手实验 —— 对比文本格式 vs 结构化 JSON 的工具调用

跑完这个实验后，你需要能回答：
1. Function Calling 帮我们省掉了什么？
2. Function Calling 和文本格式不是"好与坏"，而是什么区别？
3. 什么场景下你反而会选文本格式而不是 Function Calling？
"""

import os, json, math
from dotenv import load_dotenv

load_dotenv(".env")
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)
MODEL = "deepseek-chat"  # 非思考模型，Function Calling 稳定。不要用 deepseek-v4-flash（思考模型的 reasoning_content 无法原样传回 API）

# ============================================================
# 实验一：定义两个工具
# ============================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city. Input: city name in English.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name, e.g. 'Beijing' or 'Tokyo'",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a mathematical expression. Use for arithmetic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression, e.g. '2+3*4' or 'sqrt(144)'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
]


# ============================================================
# 实验二：LLM 自动决定调哪个工具
# ============================================================

def ask_llm(user_query: str):
    """发送请求，让 LLM 自己决定是否调用工具、调哪个、传什么参数"""
    messages = [{"role": "user", "content": user_query}]
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",  # LLM 自己决定调不调、调哪个
        temperature=0.0,
    )
    return response.choices[0].message


print("=" * 60)
print("测试 1:需要工具调用的问题")
print("=" * 60)
msg = ask_llm("What's the weather in Tokyo? Also calculate 15% of 250.")
print(f"content:    {msg.content}")  # 应该为 None（模型选择了调工具而不是直接回答）
print(f"tool_calls: {msg.tool_calls}")
if msg.tool_calls:
    for tc in msg.tool_calls:
        print(f"  -> name: {tc.function.name}, args: {tc.function.arguments}")

print()
print("=" * 60)
print("测试 2:不需要工具的问题")
print("=" * 60)
msg = ask_llm("What is the capital of France?")
print(f"content:    {msg.content}")  # 应该有直接回答
print(f"tool_calls: {msg.tool_calls}")  # 应该为 None

# ============================================================
# 实验三：执行工具调用 + 把结果返回给 LLM（完整闭环）
# ============================================================

print()
print("=" * 60)
print("测试 3:完整 Function Calling 闭环")
print("=" * 60)


def execute_tool(tool_name: str, args: dict) -> str:
    """模拟工具执行。真实场景换成真实 API 调用。"""
    if tool_name == "get_weather":
        city = args["city"]
        fake_weather = {"Beijing": "Sunny, 25 C", "Tokyo": "Rainy, 18 C"}
        return fake_weather.get(city, f"Unknown city: {city}")
    elif tool_name == "calculate":
        expr = args["expression"]
        try:
            safe_ns = {
                "sin": math.sin, "cos": math.cos, "sqrt": math.sqrt,
                "pi": math.pi, "abs": abs, "pow": pow, "round": round,
            }
            return str(eval(expr, {"__builtins__": {}}, safe_ns))
        except Exception as e:
            return f"Error: {e}"
    return f"Unknown tool: {tool_name}"


messages = [{"role": "user", "content": "Weather in Beijing, and sqrt(256)?"}]

# Round 1: LLM 决定调什么
msg = client.chat.completions.create(
    model=MODEL, messages=messages, tools=tools,
    tool_choice="auto", temperature=0.0,
).choices[0].message

# 执行每个工具调用
for tc in (msg.tool_calls or []):
    name = tc.function.name
    args = json.loads(tc.function.arguments)
    result = execute_tool(name, args)
    print(f"[Tool] {name}({args}) -> {result}")

    # 把工具调用和结果追加到对话
    messages.append({"role": "assistant", "tool_calls": [tc]})
    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

# Round 2: LLM 汇总工具结果，生成最终回答
final = client.chat.completions.create(
    model=MODEL, messages=messages, temperature=0.0,
).choices[0].message
print(f"\n[Final Answer] {final.content}")

