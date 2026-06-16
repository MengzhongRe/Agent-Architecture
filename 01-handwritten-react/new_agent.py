"""
纯手写 ReAct Agent — 不依赖 LangChain/LangGraph,只用 OpenAI SDK

核心 ReAct 循环：
    Thought → Action → Observation → Thought → ... → Final Answer

设计原则：
    1. 框架帮你做了什么，你就能看到什么
    2. 所有抽象都是可以穿透的
    3. 理解工程取舍，而不只是调 API
"""

from __future__ import annotations
from typing import List
import re
import json
import math
from typing import Any


# ============================================================
# 第1层：工具定义（Tool Definitions）
# ============================================================

class Tool:
    """工具基类——每个工具需要一个 name、description 和 execute 方法"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def execute(self, input_str: str) -> str:
        raise NotImplementedError

    def to_openai_tool(self) -> dict:
        """转换为 OpenAI 兼容的 tool 定义（后续 LangGraph 学习用）"""
        raise NotImplementedError


class CalculatorTool(Tool):
    """安全计算器——只允许数学表达式，不能执行任意代码"""

    def __init__(self):
        # 子类在 __init__ 中直接调用父类 __init__，并把 name/description 硬编码传入。
        # 效果：使用者只需 CalculatorTool()，不需要知道内部的 name 和 description。
        # 注意行尾的 \ 是 Python 显式行连接符，让字符串跨行书写（\ 会吞掉下一行的前导空格）。
        super().__init__(
            name="calculator",
            description="Evaluate a mathematical expression. \
                Use for arithmetic. Input: a valid math expression like '2+3*4' \
                or 'sqrt(16)' or 'sin(pi/2)'.",
        )

    def execute(self, input_str: str) -> str:
        # set("abc") 把字符串拆成单个字符的集合：{'a', 'b', 'c'}。
        # 这里列出所有"安全字符"——数字、运算符、小数点、以及 math 函数名会用到的字母。
        # 例如 "e" 是自然常数，"E" 是科学计数法，"sqrtincopah" 包含了 sin/cos/tan/sqrt/log/pi/abs/pow/round/ceil/floor 的字母拼写。
        allowed = set("0123456789+-*/().,%^eE sqrtincopah ")
        # all(c in allowed for c in input_str)：逐字符检查，有任何不在白名单内的字符就拒绝执行。
        if not all(c in allowed for c in input_str):
            return "Error: expression contains disallowed characters"
        try:
            # 安全命名空间（locals）：只暴露无害的数学函数和常量，eval 中使用的变量名会在这里查找。
            safe_ns = {
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
                "pi": math.pi, "e": math.e, "abs": abs, "pow": pow,
                "round": round, "ceil": math.ceil, "floor": math.floor,
            }
            # eval(expression, globals, locals)：
            #   - 第1个参数：要执行的 Python 表达式字符串
            #   - 第2个参数 globals：{"__builtins__": {}} 把内置函数全部禁用（exec、open、__import__ 等），防止任意代码执行
            #   - 第3个参数 locals：safe_ns，表达式里可用的变量/函数只能来自这个字典
            # 两层沙箱：字符白名单 + eval 命名空间隔离。即使绕过字符过滤，也调不了危险函数。
            result = eval(input_str, {"__builtins__": {}}, safe_ns)
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {e}"


class SearchTool(Tool):
    """搜索工具——使用 DuckDuckGo 进行搜索"""

    def __init__(self):
        # 同样的模式：子类不需要外部传参，所有配置锁定在内部
        super().__init__(
            name="search",
            description="Search the web for information. Input: a search query string.",
        )

    def execute(self, input_str: str) -> str:
        try:
            # duckduckgo_search 是一个第三方库（pip install duckduckgo-search），
            # 通过 DuckDuckGo 的 instant answer API 免费做网页搜索，无需 API Key。
            # DDGS 是一个上下文管理器（支持 with 语句），内部管理 HTTP 连接池。
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                # .text() 执行文本搜索，返回一个生成器（generator），每次 yield 一条结果 dict。
                # max_results=3 限制最多返回 3 条。
                # list() 把生成器"耗尽"，转成普通列表。
                results = list(ddgs.text(input_str, max_results=3))
            if not results:
                return "No results found."
            # "\n".join(可迭代对象)：用换行符把所有结果拼成一条多行文本。
            # f"- {r['title']}: {r['body'][:200]}..." 是生成器表达式：
            #   - r['title']：结果标题
            #   - r['body'][:200]：正文截取前 200 个字符（[:200] 是 Python 切片语法）
            #   - "..." 表示正文被截断了
            #   每条结果前加 "- " 是 Markdown 无序列表格式。
            return "\n".join(
                f"- {r['title']}: {r['body'][:200]}..." for r in results
            )
        except ImportError:
            return "Error: duckduckgo-search not installed. Run: pip install duckduckgo-search"


class FileReadTool(Tool):
    """文件读取工具"""

    def __init__(self, base_dir: str = "."):
        # 这个子类除了固定 name/description，还额外接受 base_dir 参数并存在自己身上
        super().__init__(
            name="read_file",
            description="Read the contents of a file. Input: a file path.",
        )
        self.base_dir = base_dir

    def execute(self, input_str: str) -> str:
        import os
        path = os.path.join(self.base_dir, input_str)
        if not os.path.exists(path):
            return f"Error: file not found: {input_str}"
        try:
            with open(path, "r") as f:
                content = f.read(2000)
            return content + ("...(truncated)" if len(content) >= 2000 else "")
        except Exception as e:
            return f"Error reading file: {e}"


class FileWriteTool(Tool):
    """文件写入工具"""

    def __init__(self, base_dir: str = "."):
        super().__init__(
            name="write_file",
            description="Write content to a file. Input format: 'filename|content'",
        )
        self.base_dir = base_dir

    def execute(self, input_str: str) -> str:
        import os
        parts = input_str.split("|", 1)
        if len(parts) != 2:
            return "Error: format is 'filename|content'"
        filename, content = parts
        # os.path.join(a, b)：跨平台地拼接路径。在 Mac/Linux 上用 / 拼接，Windows 上用 \ 拼接。
        # filename.strip()：去掉用户输入首尾的多余空格（比如 " foo.txt " → "foo.txt"）。
        path = os.path.join(self.base_dir, filename.strip())
        try:
            # os.path.dirname(path) 不修改 path 本身——它是纯函数，只返回一个新字符串。
            #   例如 path="foo/bar/baz.txt" → dirname 返回 "foo/bar"，path 仍然是 "foo/bar/baz.txt"。
            # 如果 dirname 返回 ""（即用户只给了文件名，没有目录层级），
            #   则 "" or "." 的短路求值结果为 "."，表示"当前目录"——makedirs(".") 不会报错。
            # os.makedirs(目录, exist_ok=True)：递归创建所有需要的父目录（类似 mkdir -p）。
            #   exist_ok=True 表示目录已存在时不报错直接跳过，没有这个参数时会抛 FileExistsError。
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            # open(path, "w")：以写入模式打开文件。
            #   - 文件不存在 → 自动创建新文件
            #   - 文件已存在 → 清空后覆盖写入（不是追加）
            #   要追加内容用 "a"（append mode）。
            with open(path, "w") as f:
                f.write(content)
            return f"File written: {filename.strip()} ({len(content)} chars)"
        except Exception as e:
            return f"Error writing file: {e}"


# ============================================================
# 第2层：提示词模板（Prompt Templates）
# ============================================================

SYSTEM_PROMPT = """You are an intelligent agent that can use tools to accomplish tasks.

You operate in a loop of Thought → Action → Action Input → Observation.

Available tools:
{tool_descriptions}

Respond strictly in the following format:

Thought: <your reasoning about what to do next>
Action: <tool_name>
Action Input: <input to the tool>

... after receiving the observation ...

Thought: <your reasoning about the observation>
Action: <tool_name>
Action Input: <input to the tool>

... or when you have the answer ...

Thought: I now have enough information to answer.
Final Answer: <your final response to the user>

Rules:
- You must respond with EXACTLY one Thought + one Action/Action Input pair, OR one Thought + one Final Answer.
- Do not output multiple actions at once. Wait for the observation before the next action.
- If a tool returns an error, try a different approach or explain the issue to the user.
- You can use at most {max_steps} actions before you must give a final answer.
"""


# ============================================================
# 第3层：ReAct 循环（Agent Loop）
# ============================================================

class SimpleReActAgent:
    """
    最简 ReAct Agent——手动实现 Thought → Action → Observation 循环。

    这 100 行代码就是 LangChain AgentExecutor 的简化版。
    理解它之后，你再看 LangGraph 的源码就不会觉得神秘了。
    """
    def __init__(self, llm: OllamaLLM | OpenAILLM, tools: List[Tool], \
                max_steps: int = 10):
        self.llm = llm  # 任何实现了 llm.generate(messages) -> (str, dict) 的类
        self.tools = {t.name: t for t in tools}
        self.max_steps = max_steps
        description = '\n'.join(f'- {t.name}: {t.description}' for t in tools)

        self.system_prompt = SYSTEM_PROMPT.format(
            max_steps=max_steps,
            tool_descriptions=description,
        )

    def parse_response(self, text: str) -> str:
        """
        解析LLM文本输出为结构化格式
        """
        result = {}
        thought_match = re.search(r'Thought:\s*(.+)',text, re.IGNORECASE)
        if thought_match:
            result['thought'] = thought_match.group(1).strip()
        
        final_match = re.search(r'Final Answer:\s*(.+)', text, re.IGNORECASE | re.DOTALL)
        if final_match:
            result['final_answer'] = final_match.group(1).strip()
            return result

        # Action 后面匹配任意非空白字符,因为工具名不含任意空格
        action_match = re.search(r'Action:\s*(\S+)', text, re.IGNORECASE)
        input_match = re.search(r'Action Input:\s*(.+)', text, re.IGNORECASE | re.DOTALL)

        if action_match:
            action = action_match.group(1).strip()
            # 模型输出 Action: None / Action: Final 时，不是合法工具调用
            # 不设置 action，让 run() 的 retry 逻辑提示模型输出 Final Answer
            if action.lower() not in ('none', 'final'):
                result['action'] = action

        if input_match:
            action_input = input_match.group(1).strip()
            result['action_input'] = action_input

        return result

    def execute_tool(self, tool_name: str, tool_input: str) -> str:
        """
        执行工具调用并返回调用结果
        """
        if tool_name not in self.tools:
            available = ', '.join(self.tools.keys())
            return f'Error: tool {tool_name} not found! Available: {available}'

        return self.tools[tool_name].execute(tool_input)
    
    def run(self, user_query: str, verbose: bool = True) -> str:
        """
        主运行循环——ReAct 的核心。

        Thought → Action → Observation 循环：
        1. 把 system prompt + 用户问题发给 LLM
        2. LLM 返回 Thought + Action(或 Final Answer)
        3. 如果是 Action → 执行工具，把结果作为 Observation 追加到对话
        4. 把整段历史再发给 LLM,重复步骤 2
        5. 直到 LLM 输出 Final Answer 或超过 max_steps
        返回:
            最终的LLM的输出答案
        """
        

        messages = [
            {'role': 'system', 'content': self.system_prompt,},
            {'role': 'user', 'content': user_query,},
        ]
        step = 0
        fail_time = 0
        while step < self.max_steps and fail_time < 3:
            step += 1
            if verbose:
                print(f'\n{"="*60}')
                print(f'Step {step}/{self.max_steps}')
                print(f'{"="*60}')

            response, usage = self.llm.generate(messages)
            if verbose:
                print(f'[Context]: {usage["prompt_tokens"]} prompt tokens (+{usage["completion_tokens"]} completion = {usage["total_tokens"]} total) [{len(messages)} msgs]')
            if verbose:
                print(f'\n[LLM response]:\n{response[:500]}')
            
            # 解析LLM输出文本到结构化字典
            parsed = self.parse_response(response)
            # 先检查Final Answer在不在字典,在直接返回最终答案
            if 'final_answer' in parsed:
                if verbose:
                    print(f'\n{"="*60}')
                    print(f'[Final Answer]: {parsed["final_answer"][:300]}')
                return parsed['final_answer']

            # 如果LLM没有返回最终答案并且也没有返回任何工具调用,说明它没有按照我们的要求生成
            # 我们需要把历史内容拼接回去并且让它重试
            if 'action' not in parsed:
                fail_time += 1  # 解析失败,计数
                if verbose:
                    print(f'[WARNING] No action found. Retrying...')
                messages.append({
                    'role': 'assistant', 'content': response,
                })
                messages.append({
                    'role': 'user', 'content': r'You must output an Action. Format: Action: <action_name>\nAction Input: <action_input>'
                })
                # 跳过后续解析直接进入下一次训话
                continue

            # 解析成功一次,fail_time清零
            fail_time = 0
            # 如果解析到了action工具调用,则获取
            tool_name = parsed['action']
            tool_input = parsed.get('action_input', '')
            if verbose:
                print(f'\n[Action]: {tool_name}')
                print(f'\n[Action Input]: {tool_input[:200]}')

            observation = self.execute_tool(tool_name, tool_input)
            if verbose:
                print(f'\n[Observation]: {observation[:200]}')
            
            # 把本轮的Thought + Action + Action Input追加到历史对话中去,让LLM知道
            # 刚才发生了什么
            # 同时把Observation也追加到对话中去,让LLM看到工具调用结果
            # 从而返回新生成的答案
            messages.append({'role': 'assistant', 'content': response,})
            messages.append({'role': 'user', 'content': f'Observation: {observation}'})
        
        # 超过最大步数或连续三次解析失败,强制要求LLM根据已有的内容生成最终答案
        messages.append({'role': 'user', 'content': 'You have reached the maximum number of steps \
                        or reached the maximum fail time.\
                        Please provide the final answer now based on what you have got.'})

        final, _ = self.llm.generate(messages)
        return self.parse_response(final).get('final_answer',final)


# ============================================================
# 第4层：LLM 适配层
# ============================================================

class OpenAILLM:
    """OpenAI API,适配任何大模型"""
    
    def __init__(self, model: str = 'deepseek-caht', 
                api_key: str | None = None,
                base_url: str | None = None):
        import os
        from openai import OpenAI

        self.client = OpenAI(
            api_key = api_key or os.getenv('OPENAI_API_KEY'),
            base_url = base_url or os.getenv('OPENAI_BASE_URL'),
        )
        self.model = model
    
    def generate(self, messages: List[dict]) -> tuple[str, dict]:
        """返回 (文本, usage字典)。usage 含 prompt_tokens/completion_tokens/total_tokens"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0, # ReAct 确定性更重要
        )
        text = response.choices[0].message.content
        usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens,
        }
        return text, usage
        

class OllamaLLM:
    """Ollama LLM -适配本地大模型开发"""

    def __init__(self, model: str = 'qwen3.5:9b',
                base_url = 'http://localhost:11434/v1'):
        from openai import OpenAI
        self.client = OpenAI(
            base_url = base_url,
            api_key='ollma',
        )
        self.model = model

    def generate(self, messages: List[dict]) -> tuple[str, dict]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0,
        )
        text = response.choices[0].message.content
        usage = {
            'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
            'completion_tokens': response.usage.completion_tokens if response.usage else 0,
            'total_tokens': response.usage.total_tokens if response.usage else 0,
        }
        return text, usage


# ============================================================
# 第5层：运行入口
# ============================================================

def create_agent(model: str = "deepseek-chat", use_local: bool = False) -> SimpleReActAgent:
    """工厂函数——创建带默认工具的 Agent"""
    from datetime_tool import DateTimeTool

    tools = [
        CalculatorTool(),
        DateTimeTool(),
        FileReadTool(base_dir="."),
        FileWriteTool(base_dir="."),
    ]

    if use_local:
        llm = OllamaLLM(model="qwen3.5:9b")
    else:
        llm = OpenAILLM(model=model)

    return SimpleReActAgent(llm=llm, tools=tools, max_steps=8)


# if __name__ == "__main__" 是 Python 的标准入口守卫：
#   当直接运行 `python agent.py` 时，__name__ 变量等于 "__main__" → 执行下面的代码
#   当被 `import agent` 导入时，__name__ 变量等于 "agent" → 不执行
# 这样这个文件既可以当脚本运行，也可以被别人导入使用。
if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv

    load_dotenv('.env')

    # sys.argv 是一个列表，包含命令行的所有参数。
    # 例如：$ python agent.py --local "What is 2+2?"
    # sys.argv = ["agent.py", "--local", "What is 2+2?"]
    #           sys.argv[0] 总是脚本名本身
    #           sys.argv[1:] 是用户传入的参数
    #
    # "--local" in sys.argv：检查用户有没有传 --local 标志。
    # 如果有 → create_agent(use_local=True) → 用 Ollama 本地模型
    # 如果没有 → create_agent(use_local=False) → 默认用 OpenAI API
    agent = create_agent(use_local="--local" in sys.argv)

    print("=" * 60)
    print("SimpleReAct Agent — 手写 ReAct 实现")
    print("Tools:", ", ".join(agent.tools.keys()))
    print("=" * 60)

    # 默认问题（不传参数时使用）
    query = "What is the square root of 144 plus the cube of 3?"
    # len(sys.argv) > 1：用户传了参数（不止脚本名）
    # sys.argv[-1]：取最后一个参数，因为问题中可能包含空格，无法知道它是第几个参数，
    #   但问题肯定是最后一个（标志如 --local 通常不放在最后）
    # not sys.argv[-1].startswith("--")：确保最后一个参数不是标志（防止误把 --local 当问题）
    if len(sys.argv) > 1 and not sys.argv[-1].startswith("--"):
        query = sys.argv[-1]

    print(f"\n[Query]: {query}")
    result = agent.run(query, verbose=True)
    print(f"\n{'='*60}")
    print(f"[Result]: {result}")
