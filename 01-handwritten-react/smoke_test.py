"""
API 冒烟测试——验证 LLM 调用环境正常

用法：
    cd 01-handwritten-react
    cp .env.example .env   # 编辑 .env 填入真实 key
    python smoke_test.py

期望输出：
    Model: gpt-4o-mini-2024-...
    Response: Agent environment is ready now!
    Tokens used: 25
    Environment OK!
"""

import os
from dotenv import load_dotenv

load_dotenv(".env")

from openai import OpenAI

# ---- 配置 ----
# 改这里切换模型
# MODEL = "deepseek-v4-flash"          # DeepSeek API
# MODEL = "gpt-4o-mini"          # OpenAI API
MODEL = "qwen3.5:9b"           # 本地 Ollama

api_key = os.getenv("OPENAI_API_KEY", "ollama")
base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")

print(f"Base URL: {base_url}")
print(f"Model:    {MODEL}")
print(f"Key set:  {'Yes' if api_key != 'your_key_here' and api_key != 'ollama' else 'No (using fallback)'}")
print()

client = OpenAI(api_key=api_key, base_url=base_url)

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": "Say 'Agent environment is ready now!' and your model name only.",
            }
        ],
        temperature=0.0,
    )
    print(f"Model:    {response.model}")
    print(f"Response: {response.choices[0].message.content}")
    print(f"Tokens:   {response.usage.total_tokens}")
    print()
    print("Environment OK!")
except Exception as e:
    print(f"FAILED: {e}")
    print()
    print("Troubleshooting:")
    print("  1. Check your API key in .env")
    print("  2. Check BASE_URL matches your provider")
    print("  3. Check model name is correct for your provider")
    print("  4. If using Ollama: run 'ollama serve' first, then 'ollama pull qwen2.5:7b'")
