"""
纯手写 ReAct Agent — 不依赖 LangChain/LangGraph,只用 OpenAI SDK

核心 ReAct 循环：
    Thought → Action → Observation → Thought → ... → Final Answer

设计原则：
    1. 框架帮你做了什么，你就能看到什么
    2. 所有抽象都是可以穿透的
    3. 理解工程取舍，而不只是调 API
"""

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

    def __init__(self, llm, tools: list[Tool], max_steps: int = 10):
        self.llm = llm  # 任何实现了 generate(messages) -> str 的对象
        self.tools = {t.name: t for t in tools}
        self.max_steps = max_steps

        tool_descs = "\n".join(f"- {t.name}: {t.description}" for t in tools)
        # str.format(**kwargs)：把字符串中的 {占位符} 替换为对应的值。
        # SYSTEM_PROMPT 是一个模板（template），里面预留了 {tool_descriptions} 和 {max_steps} 两个"坑"。
        # .format(tool_descriptions=tool_descs, max_steps=max_steps) 会把这两个坑填上：
        #   {tool_descriptions} → 替换为上面拼好的工具列表 "search: xxx\ncalculator: xxx..."
        #   {max_steps}         → 替换为具体的数字（比如 8）
        # 最终得到一段完整的、可以直接发给 LLM 的 system prompt 文本。
        # 这一步叫"模板渲染"——把模板和数据分离，模板定义不变的部分，数据填可变的部分。
        self.system_prompt = SYSTEM_PROMPT.format(
            tool_descriptions=tool_descs,
            max_steps=max_steps,
        )

    def parse_response(self, text: str) -> dict:
        """
        解析 LLM 文本输出为结构化格式。

        LLM 的输出并不总是完美遵循格式——这正是"使用框架的好处"之一：
        框架帮你处理了格式解析的鲁棒性。

        这里我们手动实现，所以你能看到所有边界情况。
        """
        result = {}

        # 正则表达式逐段拆解 r"Thought:\s*(.+)"：
        #
        #   r"..."     原始字符串（raw string），反斜杠 \ 不会被 Python 转义，保持正则原意。
        #             不用 raw string 就得写成 "Thought:\\s*(.+)"，多一层反斜杠很乱。
        #
        #   Thought:   字面量，匹配固定文字 "Thought:"。
        #             因为传了 re.IGNORECASE，所以 "thought:"、"THOUGHT:"、"ThOuGhT:" 都匹配。
        #
        #   \s*        匹配 0 个或多个空白字符（空格、tab、换行）。
        #             \s 是空白字符类的简写，* 是量词"0 次或多次"。
        #             这样 "Thought: " 和 "Thought:" 都能匹配。
        #
        #   (.+)       捕获组：匹配 1 个或多个任意字符，并把匹配到的内容"抓"出来供后续取用。
        #             .  匹配任意一个字符（除换行符 \n，除非传了 re.DOTALL）
        #             +  量词"1 次或多次"（所以至少要有 1 个字符才匹配成功）
        #             () 括号不是匹配内容，而是"分组"——把括号内匹配到的内容保存到 group(1)
        #             group(0) 是整个正则的完整匹配（比如 "Thought: I should search"）
        #             group(1) 是第一个括号内匹配的内容（比如 "I should search"）
        #
        # re.search(pattern, text) 在 text 中搜索第一个匹配位置，找不到返回 None。
        thought_match = re.search(r"Thought:\s*(.+)", text, re.IGNORECASE)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()

        # Final Answer 的匹配逻辑同上，额外加了 re.DOTALL——让 . 也能匹配换行符 \n，
        # 因为 Final Answer 可能有多段文字，跨多行。
        final_match = re.search(r"Final Answer:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
        if final_match:
            result["final_answer"] = final_match.group(1).strip()
            return result

        # Action 使用 \S+ 而非 .+，因为工具名不能包含空格（比如 "search"、"calculator"）。
        # \S 是"非空白字符"，+ 是"1 次或多次"，所以只匹配到第一个空格前就停。
        # 对比 .+ 是贪婪匹配，会吞掉后面所有内容（包括 Action Input 那行）。
        action_match = re.search(r"Action:\s*(\S+)", text, re.IGNORECASE)
        input_match = re.search(r"Action Input:\s*(.+)", text, re.IGNORECASE | re.DOTALL)

        if action_match:
            action = action_match.group(1).strip()
            # 本地小模型（如 qwen3.5:9b）经常不会用 Final Answer 格式，
            # 而是输出 Action: None 表示"不需要调工具了"。
            # 此时把 Thought 当作最终回答，避免把 "None" 当成工具名去执行。
            if action.lower().rstrip("'\"/\\") in ("none", "null", "n/a", "finish", "done", "no action"):
                if "thought" in result:
                    result["final_answer"] = result["thought"]
                else:
                    result["final_answer"] = text.strip()
                return result
            result["action"] = action

        if input_match:
            result["action_input"] = input_match.group(1).strip()

        return result

    def execute_tool(self, tool_name: str, tool_input: str) -> str:
        """执行工具并返回观察结果"""
        if tool_name not in self.tools:
            available = ", ".join(self.tools.keys())
            return f"Error: tool '{tool_name}' not found. Available: {available}"
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
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query},
        ]
        step = 0

        while step < self.max_steps:
            step += 1
            if verbose:
                print(f"\n{'='*60}")
                print(f"Step {step}/{self.max_steps}")
                print(f"{'='*60}")

            response, total_tokens = self.llm.generate(messages)
            if verbose:
                print(f"\n[LLM Response]:\n{response[:500]}")
                print(f'[Tokens Usage]: {total_tokens}')

            parsed = self.parse_response(response)

            if "final_answer" in parsed:
                if verbose:
                    print(f"\n{'='*60}")
                    print(f"[FINAL ANSWER]: {parsed['final_answer'][:300]}")
                return parsed["final_answer"]

            # LLM 输出格式不符合要求时，追加纠正提示并重试（不消耗 step 之外的资源）
            if "action" not in parsed:
                if verbose:
                    print("[WARNING] No action found in response. Retrying...")
                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": "You must output an Action. Format: Action: <tool_name>\\nAction Input: <input>",
                })
                continue

            tool_name = parsed["action"]
            tool_input = parsed.get("action_input", "")
            if verbose:
                print(f"\n[Action]: {tool_name}")
                print(f"[Action Input]: {tool_input[:200]}")

            observation = self.execute_tool(tool_name, tool_input)
            if verbose:
                print(f"\n[Observation]: {observation[:300]}")

            # 把本轮 Thought+Action 和 Observation 追加到对话历史，让 LLM 在下一轮能"看到"发生了什么。
            #
            # 注意：这里用的是 role: "user" 而非 role: "tool" + tool_call_id。
            # 这是两种完全不同的工具调用路径：
            #
            # 【文本式 ReAct（本项目）】
            #   工具定义 → 写在 prompt 文字里
            #   LLM 输出 → 纯文本，用正则解析 Action/Action Input
            #   结果回传 → role: "user"，内容 "Observation: xxx"
            #   兼容性   → 任意 LLM（OpenAI / Ollama / 本地模型），不需要特定 API 格式
            #   本质     → LLM 不知道自己在"调工具"，它只是在参与一个文本格式游戏
            #
            # 【原生 Function Calling】
            #   工具定义 → 通过 API 的 tools 参数，以 JSON Schema 形式传入
            #   LLM 输出 → 结构化的 tool_calls 字段（含 id / name / arguments）
            #   结果回传 → role: "tool" + tool_call_id，否则 API 报错
            #   兼容性   → 仅支持 function calling 的模型（gpt-4、claude 等）
            #   本质     → LLM 明确知道自己调用了工具，API 层面有专门协议
            #
            # 本项目选择文本式 ReAct，是为了兼容 Ollama 本地模型（如 qwen2.5），
            # 这些模型不一定支持 OpenAI 的 tool calling 协议。
            messages.append({"role": "assistant", "content": response})
            messages.append({
                "role": "user",
                "content": f"Observation: {observation}",
            })

        # 超过最大步数，强制要求总结
        messages.append({
            "role": "user",
            "content": "You have reached the maximum number of steps. \
            Please provide your final answer now based on what you've gathered.",
        })
        final = self.llm.generate(messages)
        return self.parse_response(final).get("final_answer", final)


# ============================================================
# 第4层：LLM 适配层
# ============================================================

class OpenAILLM:
    """OpenAI API 适配——可以替换为任意 LLM"""

    def __init__(self, model: str = "deepseek-chat", \
                api_key: str | None = None, \
                base_url: str | None = None):
        import os
        from openai import OpenAI

        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_BASE_URL"),
        )
        self.model = model

    def generate(self, messages: list[dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0,  # Agent 场景下确定性更重要
        )
        return response.choices[0].message.content, response.usage.total_tokens


class OllamaLLM:
    """Ollama 本地模型适配——用于离线开发"""

    def __init__(self, model: str = "qwen3.5:9b", base_url: str = "http://localhost:11434"):
        from openai import OpenAI
        self.client = OpenAI(base_url=base_url + "/v1", api_key="ollama")
        self.model = model

    def generate(self, messages: list[dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0,
        )
        return response.choices[0].message.content, response.usage.total_tokens


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
