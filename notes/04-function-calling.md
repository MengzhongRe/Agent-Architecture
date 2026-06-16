# Fuanction Calling 系统性知识笔记

> 学习日期：2026-06-08 | 前置概念：ReAct、Lilian Weng Agent 框架
> 定位：Agent 架构 Tool Use 层的一种核心实现方式

---

## 目录

- [0. 什么是 Function Calling，为什么它存在](#0-什么是-function-calling为什么它存在)
  - [0.1 LLM 的天然局限](#01-llm-的天然局限)
  - [0.2 Function Calling 是什么：一个比喻](#02-function-calling-是什么一个比喻)
  - [0.3 在 Agent 架构中的位置](#03-在-agent-架构中的位置)
  - [0.4 一个最小的完整例子](#04-一个最小的完整例子)
- [1. 核心机制：完整生命周期](#1-核心机制完整生命周期)
  - [1.1 预备知识：Chat API 的 messages 结构](#11-预备知识chat-api-的-messages-结构)
  - [1.2 五阶段闭环](#12-五阶段闭环)
  - [1.3 数据流：messages 的完整生命周期](#13-数据流messages-的完整生命周期)
  - [1.4 与 ReAct 文本格式的逐阶段对比](#14-与-react-文本格式的逐阶段对比)
- [2. Tool Schema 设计：最重要的工程能力](#2-tool-schema-设计最重要的工程能力)
  - [2.0 前置：工具定义的完整结构](#20-前置工具定义的完整结构)
  - [2.1 name：命名规范](#21-name命名规范)
  - [2.2 description：LLM 决策的唯一信息源](#22-descriptionllm-决策的唯一信息源)
  - [2.3 parameters：JSON Schema 核心概念](#23-parametersjson-schema-核心概念)
  - [2.4 设计演进：从"能用"到"好用"](#24-设计演进从能用到好用)
  - [2.5 strict: true](#25-strict-true)
- [3. tool_choice：控制 LLM 的调用行为](#3-tool_choice控制-llm-的调用行为)
  - [3.0 为什么需要 tool_choice](#30-为什么需要-tool_choice)
  - [3.1 四种模式详解](#31-四种模式详解)
  - [3.2 翻车场景与根因分析](#32-翻车场景与根因分析)
- [4. 并行调用 vs 串行调用](#4-并行调用-vs-串行调用)
  - [4.0 为什么会有并行调用](#40-为什么会有并行调用)
  - [4.1 parallel_tool_calls 参数](#41-parallel_tool_calls-参数)
  - [4.2 决策规则](#42-决策规则)
  - [4.3 多工具结果合并](#43-多工具结果合并)
  - [4.4 何时主动禁用并行](#44-何时主动禁用并行)
- [5. 错误处理：让 LLM 从失败中恢复](#5-错误处理让-llm-从失败中恢复)
  - [5.0 错误发生在哪里](#50-错误发生在哪里)
  - [5.1 失败类型分类](#51-失败类型分类)
  - [5.2 为什么纯文本错误信息不够](#52-为什么纯文本错误信息不够)
  - [5.3 结构化错误的设计](#53-结构化错误的设计)
  - [5.4 错误恢复在 ReAct 循环中的表现](#54-错误恢复在-react-循环中的表现)
  - [5.5 致命错误与终止策略](#55-致命错误与终止策略)
- [6. Function Calling vs 其他方案](#6-function-calling-vs-其他方案)
- [7. 安全性设计](#7-安全性设计)
- [8. 与 LangGraph 的关系](#8-与-langgraph-的关系第3周预习)
- [9. 实战 Checklist](#9-实战-checklist)
- [附录 A：5 分钟速查表](#附录-a5-分钟速查表)
- [附录 B：知识来源与参考链接](#附录-b知识来源与参考链接)

---

## 0. 什么是 Function Calling，为什么它存在

### 0.1 LLM 的天然局限

LLM 的能力边界是理解 Function Calling 的起点。考虑这三个场景：

**场景 1 — 实时信息**：用户问"北京今天天气怎么样？"LLM 的训练数据截止到某个时间点——它不知道今天的天气。它能生成一个高度逼真但完全虚构的天气描述（幻觉），但无法给出真实答案。

**场景 2 — 精确计算**：用户问"12345 × 67890 等于多少？"对于人类来说这是一个计算器一秒能解决的事。但 LLM 必须在 token-by-token 的自回归生成过程中"算"出每一位数字——它不是在做数学运算，而是在预测"最可能出现在这个位置的数字是什么"。位数一多，精度快速下降。

**场景 3 — 外部数据**：用户问"我上周三的订单发货了吗？"这个信息在你们的订单数据库中，不在 LLM 的参数里。LLM 要回答这个问题，唯一的办法是**访问那个数据库**。

这三个场景指向同一个问题：**LLM 需要一种机制来调用外部能力，而不只是生成文本**。这就是 Function Calling 被设计出来的根本原因。

### 0.2 Function Calling 是什么：一个比喻

把 LLM 想象成一个**瘫痪的天才**——它什么都知道（训练数据里的知识），什么都能推理，但没有手。它不能自己查天气、不能自己算数学、不能自己读数据库。

Function Calling 就是给这个天才装上一排**按钮**。每个按钮上贴了标签——"查天气""计算器""查订单"。天才能做出聪明的决策——"现在该按哪个按钮、按多大的力度"——但按钮本身是由外面的代码来实际执行的。天才不直接动手，它只是告诉外面的世界：**"请帮我按这个按钮，用这些参数。"**

这跟你平常调用 API 的方向完全相反：
- 平常：**你**决定调什么 API，**你**指定参数，**你**执行
- Function Calling：**LLM** 决定调什么 API，**LLM** 指定参数，**你的代码**执行

你是调用 LLM 的那个人，但 LLM 反过来又是调用你工具的那个人。你俩互为调用方。

### 0.3 在 Agent 架构中的位置

回到 Day 1 的核心框架：

```
Agent = LLM + Planning + Memory + Tool Use
```

Function Calling 属于 **Tool Use 层**。它是 Tool Use 的三种主要实现方式之一：

```
Tool Use 层
├── 文本格式工具调用（ReAct）  → LLM 输出自然语言 "Action: xxx"，你的代码正则解析
├── Function Calling          → LLM 输出结构化 JSON {"name":"...", "arguments":{...}}
└── MCP 协议                  → 跨模型的标准化工具生态，工具定义独立于 LLM
```

三种方案解决的**是同一个问题**——怎么让 LLM 告诉你的代码"我想调哪个工具、传什么参数"。它们的差别在于**消息格式**和**可靠性保证**：

| 维度 | ReAct 文本格式 | Function Calling | MCP 协议 |
|---|---|---|---|
| 输出格式 | 自然语言 `Action: xxx` | JSON `{"name":"...","arguments":{...}}` | 协议标准消息 |
| 解析方式 | 正则表达式（可能失败） | `json.loads`（100% 可靠） | 协议层自动反序列化 |
| Thought 推理 | 有——每步 Action 前有推理步骤 | 无——跳过推理直接调工具 | 取决于实现 |
| 并行多工具 | 几乎不可能 | 原生支持 | 取决于实现 |
| 模型要求 | 任何能生成文本的 LLM | 需模型原生训练了 tool calling | 需 MCP Client/Server |

**一句话总结**：Function Calling 用"结构化约束"换来了"可靠性和并行性能"，ReAct 文本格式用"自然语言灵活性"换来了"可解释性和通用性"。两者互补——LangGraph 允许在同一个 graph 的不同节点中混用。

### 0.4 一个最小的完整例子

在深入机制之前，先看一个能跑的完整例子（15 行核心代码）：

```python
from openai import OpenAI
client = OpenAI()

# 步骤 1：定义工具——告诉 LLM "你可以用这个函数"
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a city. Use when user asks about weather.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name in English"}},
            "required": ["city"]
        }
    }
}]

# 步骤 2：向 LLM 发起请求，带上工具定义
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=tools
)

# 步骤 3：LLM 决定调用工具，返回结构化 JSON
msg = response.choices[0].message
# msg.tool_calls[0].function.name = "get_weather"
# msg.tool_calls[0].function.arguments = '{"city": "Tokyo"}'

# 步骤 4：你的代码执行工具，把结果返回
import json
result = fake_weather_api(json.loads(msg.tool_calls[0].function.arguments)["city"])
messages = [
    {"role": "user", "content": "What's the weather in Tokyo?"},
    msg,  # assistant role，包含 tool_calls
    {"role": "tool", "tool_call_id": msg.tool_calls[0].id, "content": result}
]
final = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
print(final.choices[0].message.content)
# "The current weather in Tokyo is sunny, 22 C."
```

**关键观察**：这个过程中 LLM 被调用了**两次**。第一次是"决策"——我该调什么工具？第二次是"理解"——工具返回了这个结果，意味着什么？两次调用之间是你的代码在做事。这就是 Function Calling 的核心模式——**LLM 做决策，你执行，LLM 再理解**。

### 0.5 环境变量与 .env 文件：API 密钥从哪里来

你可能注意到了——上面的代码里 `client = OpenAI()` 没有传 API key。那 key 是从哪来的？

答案在**环境变量**。当你调用 `OpenAI()` 不传参数时，SDK 会自动读取系统环境变量 `OPENAI_API_KEY`。这是一种安全实践——把密钥和代码分离。

#### 为什么不能把 key 硬编码在代码里

```python
# 危险——key 会暴露在 Git 历史中
client = OpenAI(api_key="sk-bb5fc4b8c39545308071ab9e8b811213")
```

三个致命问题：
1. **Git 泄露**：一旦 `git push`，你的 key 就永远留在了仓库历史中，即使你删掉这行再 commit，之前的 commit 里还有
2. **环境切换痛苦**：开发环境用 DeepSeek key，本地测试用 Ollama——硬编码意味着每次切换都要改代码
3. **协作风险**：别人 clone 你的仓库时也需要你的 key，但他们不应该知道你的 key

#### .env 文件的作用

`.env` 是一个纯文本文件，每一行是 `KEY=VALUE` 格式：

```bash
# .env 文件内容（存放在项目目录中，但不会被 git 追踪）
OPENAI_API_KEY=sk-your-real-key
OPENAI_BASE_URL=https://api.deepseek.com
```

Python 代码中通过 `python-dotenv` 库读取：

```python
from dotenv import load_dotenv
load_dotenv(".env")           # 把 .env 中的键值对加载为环境变量
import os
key = os.getenv("OPENAI_API_KEY")   # 现在可以读到了
```

#### .env.example 文件的作用

如果 `.env` 不该提交到 Git，别人 clone 你的项目后怎么知道需要哪些环境变量？答案就是 `.env.example`——**它是 .env 的模板，可以安全地提交到 Git**：

```bash
# .env.example（提交到 Git——所有人都能看到这个文件）
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.deepseek.com
# 或者本地模型（Ollama）
# OPENAI_BASE_URL=http://localhost:11434/v1
```

使用流程：
1. 你 clone 一个项目 → 看到 `.env.example`
2. `cp .env.example .env` → 复制一份真正的 `.env`
3. 在 `.env` 中填入你自己的真实 key
4. `.gitignore` 中已经有 `.env`（确保它不会被提交）

#### 两种实践对照

| | `.env` | `.env.example` |
|---|---|---|
| **包含真实密钥？** | 是 | 否（只有占位符如 `your_key_here`） |
| **提交到 Git？** | **绝对不行** | **可以** |
| **作用** | 程序运行时读取 | 告诉协作者"你需要设置哪些变量" |
| **一个项目中有几份？** | 一份（每个人的不同） | 一份（统一的模板） |

#### 在你的项目中的实际情况

你的 `agent-learning-journey/01-handwritten-react/` 目录中：

```
.env.example   ← 模板文件，包含变量名、示例值、注释说明。已提交到 Git
.env           ← 真实配置，包含你的 DeepSeek key。已在 .gitignore 中，不会被提交
```

`.env.example` 中写的是：

```bash
OPENAI_API_KEY=your_key_here          # 占位符——真实 key 在 .env 中
OPENAI_BASE_URL=https://api.deepseek.com
# 或者本地模型（Ollama）
# OPENAI_BASE_URL=http://localhost:11434/v1
```

这是一个**工程规范**，不是 API 特有的机制。几乎所有需要密钥、数据库连接串、第三方服务 Token 的项目都遵循这个模式——模板公开 + 真实配置私密。

下面我们来拆解这每一步到底发生了什么。

---

## 1. 核心机制：完整生命周期

### 1.1 预备知识：Chat API 的 messages 结构

在深入 Function Calling 的细节之前，必须先理解 OpenAI Chat Completion API 的 messages 机制——这是所有 Agent 系统的通信基础。

**Chat API 是无状态的**。每次调用 `client.chat.completions.create(messages=...)`，你都必须把完整的对话历史传过去。API 本身不保存任何状态——它只是一个"回声机"：你给它 messages 数组，它根据数组中的内容生成一个 response。下次调用时如果你不带上之前的对话，LLM 就会"失忆"。

**messages 数组中每条消息都有一个 `role` 字段**，它标明"这句话是谁说的"。Chat API 支持四种 role：

| role | 谁说的 | 什么时候出现 |
|---|---|---|
| `"system"` | 开发者 | 对话开始时设置行为规则、格式约束。只传一次 |
| `"user"` | 用户 | 用户的每次输入。也可以用来注入 Observation（你在 ReAct 中就是这样做的） |
| `"assistant"` | LLM | LLM 的每次回复。如果 LLM 选择了调用工具，这条消息的 `content` 为 `None`，`tool_calls` 不为空 |
| `"tool"` | 你的代码 | 工具执行后，你把结果以这个 role 返回给 LLM。**必须**带上 `tool_call_id` 来匹配是哪个工具调用的结果 |

前三种 role（system/user/assistant）你在 Day 1-2 已经用过了。第四种 `"tool"` 是 Function Calling 引入的新角色——它是 LLM 和你的代码之间传递工具执行结果的"专用通道"。

**一条关键规则**（你下周写 Agent 循环时必须牢记）：**当 `assistant` role 的消息中包含 `tool_calls` 时，`content` 一定为 `None`**。LLM 在每一步只能做一件事——要么"说话"（content 不为空），要么"调工具"（tool_calls 不为空），不能同时做两件。这不是 API 的 bug，而是一个刻意的设计选择：把"推理/表达"和"发出指令"分成两个正交的行为，让解析变简单。代价是——你丢掉了 ReAct 中"边思考边调工具"的流畅性。

### 1.2 五阶段闭环

每一次完整的 Function Calling 对话包含五个阶段。把这个闭环理解透彻，你就能理解 LangGraph 的 ToolNode（第 3 周）到底自动化了什么。

```
阶段 1  ──→  阶段 2  ──→  阶段 3  ──→  阶段 4  ──→  阶段 5
定义工具     LLM 决策     解析调用     执行工具     返回结果
(你的代码)   (API 内)   (你的代码)   (你的代码)   (你的代码 → API)
```

---

**阶段 1：定义工具 (Tool Definition)**。你在代码中构造 `tools` 参数，把它传给 API。`tools` 是一个 list，其中每一项是一个 dict，结构为：

```python
{
    "type": "function",       # 固定值。OpenAI 预留此字段以支持未来非函数工具（如 web_search、MCP server）
    "function": {             # 具体的函数定义——name + description + parameters 三要素
        "name": "...",
        "description": "...",
        "parameters": { ... } # JSON Schema 格式
    }
}
```

这个结构是 Function Calling 与 LLM 之间唯一的"接口契约"。LLM 无法看到函数体的代码——它只能通过 name、description 和 parameters schema 来理解一个工具能做什么、什么时候该用、需要什么参数。

**阶段 2：LLM 决策 (Model Inference)**。你把 messages + tools 发给 API。在模型内部，它逐 token 地生成响应。当它读到 `tools` 定义后，在每个 token 位置都可能"拐弯"进入工具调用模式——即生成的不是自然语言文本，而是结构化的 `tool_calls` 数组。

模型做出这个决策的依据是什么？只有两点：
1. **用户说了什么**（messages 的内容）
2. **工具的描述说了什么**（tools 的定义）

因此，工具 schema 的质量（尤其是 description）直接决定了 LLM 会不会在正确的时机选择正确的工具——第 2 节专门讲这个。

**阶段 3：解析调用 (Parse Response)**。API 返回 response。你需要从 `response.choices[0].message` 中提取两类信息：
- `message.content`：自然语言文本。如果 LLM 调了工具，这个值为 `None`
- `message.tool_calls`：工具调用列表。每一项包含 `id`（UUID 字符串）、`function.name`（工具名）、`function.arguments`（参数 JSON 字符串，需要 `json.loads`）

这里的关键差异在于：ReAct 文本格式中，工具调用和推理混在 `content` 字符串里，需要正则提取。Function Calling 把它们放在了不同的数据结构中——`content` 和 `tool_calls` 是两件独立的事。100% 可靠，但代价是你在这一轮失去了 LLM 的"思考过程"（Thought）。

**阶段 4：执行工具 (Execute)**。**这是整个闭环中最容易被误解的一步**。LLM 只生成了 JSON——它没有"执行"任何东西。真正的工具执行发生在你的代码中。你可以查数据库、调天气 API、读文件、运行 Python 脚本——LLM 不知道也不关心你的实现。它只负责告诉你"我想调这个工具、用这些参数"，你负责把结果算出来。

这就意味着：Function Calling 中的 "function call" 跟你写 Python 时的函数调用是两回事。在 Python 中，`get_weather("Tokyo")` 是一行代码，函数体在同一进程中被执行。在 Function Calling 中，LLM 生成 JSON → API 返回给你的服务器 → 你的服务器执行函数 → 结果返回给 LLM。这是一个跨进程、跨网络的三步协作。

**阶段 5：返回结果 (Return Result)**。你把工具执行的结果以 `{"role": "tool", "tool_call_id": "...", "content": "..."}` 的格式追加回 messages 数组。然后**第二次**调用 API。这一次 LLM 看到了用户的问题 + 自己的 tool_calls + 你返回的工具结果，它综合这些信息，生成最终的自然语言回答。

为什么需要两轮 API 调用？这是"**生成 → 执行 → 理解**"三步设计模式的必然结果。第一轮 LLM 生成调用指令；你的代码执行指令；第二轮 LLM 理解执行结果并生成回答。不是效率低下——LLM 没办法在生成 tool_calls 的同时等待工具执行，它是无状态的。

### 1.3 数据流：messages 的完整生命周期

这是 Function Calling 中最容易出错的部分——messages 数组在整个过程中的形态变化。用一个表格来展示五个关键时刻：

| 时刻 | messages 的内容 | 说明 |
|---|---|---|
| **T0** 请求前 | `[{"role": "user", "content": "北京天气和 sqrt(256)?"}]` | 只有一条用户消息 |
| **T1** Round 1 响应后 | T0 + `{"role": "assistant", "content": None, "tool_calls": [call_abc(get_weather), call_def(calculate)]}` | LLM 决定调两个工具，content 为 None |
| **T2** 工具执行中 | T1 + `{"role": "tool", "tool_call_id": "call_abc", "content": "Beijing: Sunny 25 C"}` + `{"role": "tool", "tool_call_id": "call_def", "content": "16"}` | 每个 tool call 对应一条 tool role 消息 |
| **T3** Round 2 请求 | T2（完整历史） | 把所有消息传给 LLM 做第二轮推理 |
| **T4** Round 2 响应 | T3 + `{"role": "assistant", "content": "北京今天晴，25 C。sqrt(256) = 16。"}` | LLM 汇总工具结果，生成最终回答 |

**`tool_call_id` 为什么不能省略**：并行调用 (T1→T2) 时，LLM 一次返回了多个 tool_calls。如果你在返回结果时不带上 `tool_call_id`，LLM 收到两条结果但不知道哪条对应哪个工具——天气结果可能被当成计算结果，输出变成 "sqrt(256) = Beijing: Sunny 25 C"。

这是你下周手写 ReAct Agent 时不会遇到的问题（ReAct 文本格式不支持并行调用），但在生产环境中——不论是 Function Calling 还是 MCP 协议——`tool_call_id` 的精确匹配都是工具调用可靠性的基础。

### 1.4 与 ReAct 文本格式的逐阶段对比

把我们刚讲的五阶段和你下周要手写的 ReAct 放在一起对比：

| 阶段 | ReAct 文本格式 | Function Calling |
|---|---|---|
| 定义工具 | 在 system prompt 中用自然语言写 "You have the following tools: ..." | JSON Schema 结构化定义，放在请求的 `tools` 参数中 |
| LLM 决策 | 生成 `Thought: ... \n Action: xxx \n Action Input: ...` 文本 | 生成独立的 `tool_calls` 数组，content 为 None |
| 解析调用 | 你的代码用 `re.search(r"Action: (\S+)", text)` 解析 | `json.loads(tc.function.arguments)` 直接解析，0 失败率 |
| 执行工具 | `execute_tool(name, input_str)` | 同左——执行逻辑由你控制 |
| 返回结果 | 拼接字符串 `f"Observation: {result}"`，以 `role: user` 追加入 messages | 结构化 `{"role": "tool", "tool_call_id": ..., "content": ...}` 追加入 messages |

**核心差异对 Agent 架构的影响**：在 Function Calling 中，工具调用和自然语言对话走的是**不同的数据通道**。`tool_calls` 不是 `content` 的子字符串——它是 API 响应对象上的独立字段。这意味着工具调用的解析是 **100% 可靠的**。但这也有代价：你在这一轮**看不到 LLM 的推理过程**（"为什么选这个工具？""之前的信息告诉我什么？"）。你下周用 ReAct 文本格式时，Thought 会完整地展现在你面前——你失去了可靠性的保证，但获得了推理链的可解释性。这个 tradeoff 是你理解 LangGraph 为什么能同时支持两种模式的关键。

---

## 2. Tool Schema 设计：最重要的工程能力

在五阶段闭环中，阶段 1（定义工具）决定了后续所有阶段的质量。如果工具的定义不清晰，LLM 在阶段 2 会选错工具或传错参数——后面的步骤就全乱了。

### 2.0 前置：工具定义的完整结构

先从一个完整的工具定义开始，理解每一层是什么、为什么存在：

```python
{                                          # ← 最外层：tools 列表的一项
    "type": "function",                    # ← ① 工具类型（固定值，预留扩展点）
    "function": {                          # ← ② 实际的函数定义
        "name": "get_weather",             # ← ③ 工具名（LLM 做路由时引用的标识符）
        "description": "Get current ...",  # ← ④ 工具描述（LLM 决策的唯一信息源）
        "strict": True,                    # ← ⑤ 严格模式（2025+，生成即符合 Schema）
        "parameters": {                    # ← ⑥ 参数定义（JSON Schema 格式）
            "type": "object",
            "properties": { ... },
            "required": [...],
            "additionalProperties": False
        }
    }
}
```

**① `"type": "function"`**：为什么需要这个包装？2025 年后，OpenAI API 的 `tools` 参数不只支持"函数"——它还支持 `"type": "web_search"`（让 LLM 直接搜索网页）、`"type": "file_search"`（搜索上传的文件）、以及未来的 MCP server 工具。这个字段是扩展点。目前你只用 `"function"`。

**② `"function"`**：函数定义的容器。三个必填字段——name、description、parameters——分别对应"我是谁""我做什么""我需要什么"。还有两个可选但强烈推荐的字段——strict（本节 2.5）和 description 的措辞（本节 2.2）。

**③ `"name"`** 和 **④ `"description"`** 在下面两节详讲。先看 ⑥ 为什么选 JSON Schema。

**⑥ 为什么是 JSON Schema**？OpenAI 需要一个跨语言的、标准化的方式来描述函数参数。JSON Schema 是 Web 生态中最成熟的 schema 描述语言——它自己就是 JSON 格式，LLM 的训练数据中包含大量 JSON Schema 文档，所以模型天然理解它的语义。Python type hints 不行——LLM 没学过；Protobuf 不行——解析成本太高且不是 LLM 训练数据中的常见格式；自然语言描述不行——没有结构化约束，LLM 会产生格式不一致的参数。

### 2.1 name：命名规范

工具名是 LLM 做工具路由时引用的标识符。它需要一眼就能看出"这个工具做什么"。

```python
# 好——动词_宾语，自解释
"get_weather", "search_documents", "create_invoice", "cancel_order"

# 坏——模糊、不一致、无意义
"weather"           # 是查询还是设置？不清楚
"do_stuff"          # 完全不知道做什么
"getWeatherData"    # 风格不一致（与其他 snake_case 工具混用）
```

原则：**动词_宾语**（verb_noun），全小写 + 下划线。名称本身就说明了操作——你不需要看 description 也能猜出大概。如果一个工具的 name 需要 description 才能理解，那 name 就有问题。

### 2.2 description：LLM 决策的唯一信息源

这是整个工具定义中**最重要的一行**。LLM 不是通过读你的函数体代码来理解工具的——它只能看到这个 schema。description 是它判断"是否调用这个工具、什么时候调用"的**唯一依据**。

**想象这个场景**：你的 tools 列表中有 20 个工具。用户问了一个问题，LLM 要从这 20 个中选出 0 到多个。它看到的是什么？只有 name + description + parameters schema 三样东西。它看不到函数体的代码、看不到你的业务逻辑、看不到工具之间的依赖关系。你的 description 是它唯一的"使用手册"。

**一个坏 description 的代价**：不是"LLM 选错了工具但还能用"——LLM 会直接忽略这个工具，或者在不该用时调用它。下面是对比：

```python
# 坏——LLM 无从判断何时用、有什么限制
"description": "Get data from the system."

# 好——LLM 有完整的决策依据
"description": (
    "Get current weather conditions for a city. "
    "Use when the user asks about weather, temperature, humidity, or forecasts. "
    "Returns: temperature (C or F), condition (sunny/rainy/etc.), humidity %. "
    "Requires: city name in English. "
    "Note: does NOT support date-based forecasts or historical data."
)
```

好 description 包含**四个要素**：

| 要素 | 回答的问题 | 在例子中的体现 |
|---|---|---|
| **做什么** | 这个工具的功能是什么？ | "Get current weather conditions for a city" |
| **什么时候用** | LLM 该在什么场景下选择这个工具？ | "Use when the user asks about weather, temperature..." |
| **返回什么** | 调了这个工具后，能获得什么信息？ | "Returns: temperature, condition, humidity %" |
| **限制是什么** | 什么情况下不该用？有什么边界？ | "does NOT support date-based forecasts" |

**负面引导（Negative Guidance）**：第四要素"限制"是最容易被忽略但同样重要的。告诉 LLM "什么时候不要用这个工具"能大幅降低误调用。如果工具 A 和工具 B 功能相近（如 `search_web` 和 `search_knowledge_base`），两者的 description 都必须包含关于对方的区分性说明。

**长度规则**：太短（< 20 词）LLM 信息不足，容易误用。太长（> 100 词）占用 context window 且 LLM 可能忽略后半部分。20-60 词是 sweet spot。

**不应该包含的**：内部实现细节（"调用 WeatherAPI v3 endpoint"）、与其他工具的调用顺序（这是 Agent 编排层的事）、具体的参数值（去 parameters 里定义）。

### 2.3 parameters：JSON Schema 核心概念

现在来到工具定义中最"技术"的部分——`parameters`。它的任务是精确描述"调用这个工具时，LLM 需要传什么参数，每个参数是什么类型、是否必填、有什么取值范围"。

这部分使用 **JSON Schema** 来描述。所以在深入 parameters 的设计技巧之前，需要先理解 JSON Schema 本身——它是什么、有哪些核心概念、怎么写。

#### 2.3.0 什么是 JSON Schema

**一句话定义**：JSON Schema 是一种用来描述"JSON 数据应该长什么样"的语言——并且它自己也是 JSON 格式。

举个例子。假设你的工具需要接收这样一个参数：

```json
{"city": "Beijing", "unit": "celsius"}
```

你希望约束它：`city` 必须是字符串且必填，`unit` 必须是 `"celsius"` 或 `"fahrenheit"` 之一。用自然语言写出来就是一段描述，但 LLM 可能不严格遵守。JSON Schema 用结构化的方式来表达同样的约束：

```json
{
    "type": "object",
    "properties": {
        "city": {"type": "string"},
        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
    },
    "required": ["city"]
}
```

这个 schema 的意思是：

- 最外层是一个 `"object"`（即 JSON 中的 `{...}`）
- 这个对象有两个属性：`city`（类型为字符串）和 `unit`（类型为字符串，只能取两个值之一）
- `city` 是必填的（在 `required` 数组中），`unit` 是可选的（不在 `required` 数组中）

当你把这个 schema 放在工具定义的 `"parameters"` 字段中传给 LLM 时，LLM 理解了约束，在生成 `arguments` 时就会遵守。

**为什么 OpenAI 选择 JSON Schema**？三个原因：
1. **LLM 天然理解它**：JSON Schema 广泛用于 Web API 文档（OpenAPI/Swagger），LLM 的训练语料中包含大量 JSON Schema 实例
2. **跨语言无障碍**：JSON Schema 本身是 JSON，不依赖 Python/JS/Go 等任何特定语言的类型系统
3. **有成熟的校验生态**：你的代码可以用 `jsonschema` 库在服务端再次校验 LLM 的生成结果，双重保险

相比之下，Python type hints（`city: str`）LLM 没学过、Protobuf 太复杂且不是训练语料中的常见格式、纯自然语言描述没有结构化约束力。

#### 2.3.1 JSON Schema 基础关键字详解

JSON Schema 的核心就几个关键字。逐一理解后，任何工具的 parameters 你都能自己设计了。

**`type` — 类型约束**

```json
{"type": "string"}
```

这是最基础的约束——声明一个值"是什么类型"。JSON Schema 支持七种基本类型：

| type 值 | 对应 JSON 中的 | Function Calling 中常用？ | 示例参数 |
|---|---|---|---|
| `"string"` | 字符串 | 最常用 | 城市名、搜索词、文件名 |
| `"number"` | 浮点数 | 常用 | 金额、坐标、百分比 |
| `"integer"` | 整数 | 常用 | 年龄、数量、页码 |
| `"boolean"` | true/false | 偶尔 | 是否启用某选项 |
| `"object"` | `{...}` | 常用（嵌套结构） | 地址对象包含街道/城市/邮编 |
| `"array"` | `[...]` | 常用 | 多个搜索关键词、商品 ID 列表 |
| `"null"` | null | 几乎不用 | — |

**关键区分**：`"number"` 和 `"integer"` 是不同的。如果你用 `"number"` 约束年龄，LLM 可能传 `25.7`——这在数学上没错，但在业务上是错的。原则是：只要参数值在业务逻辑中是整数，就用 `"integer"`。

**`properties` — 定义对象的字段**

```json
{
    "type": "object",
    "properties": {
        "city": {"type": "string"},
        "unit": {"type": "string"}
    }
}
```

`properties` 只在 `"type": "object"` 时生效。它声明了"这个对象包含哪些字段，每个字段各自的 schema 是什么"。注意：`properties` 中列出的字段**不一定是必填的**——声明一个字段和标记它为必填是两件事（后者由 `required` 控制）。这个细微的区分经常被误解。

**`required` — 必填字段声明**

```json
{
    "type": "object",
    "properties": {
        "city": {"type": "string"},
        "unit": {"type": "string"}
    },
    "required": ["city"]
}
```

`required` 是一个**字符串数组**，列出哪些字段必须出现。在这里：
- `city` 在 required 中 → 必填。LLM 如果不传，API 会拒绝
- `unit` 不在 required 中 → 可选。LLM 可以传也可以不传。不传时你的代码用默认值

设计原则：**只标记真正必须的字段**。如果把所有字段都标记为 required，LLM 在选择调用这个工具时可能会因为缺少某个不必要的信息而放弃调用。

**`enum` — 限定取值范围**

```json
{"type": "string", "enum": ["celsius", "fahrenheit"]}
```

`enum` 声明"这个字段只能是以下值之一"。对于 Function Calling，`enum` 是最重要的约束之一——它直接消除了 LLM 生成自由文本导致的参数不确定性。不用 `enum` 时，LLM 可能传 `"摄氏度"`、`"C"`、`"degree"`、`"centigrade"` 来表示同一个意思——你的代码需要逐一处理这四种情况。用了 `enum`，LLM 的 output 被限制在 `["celsius", "fahrenheit"]` 中，你的代码只需要处理两个值。

**`additionalProperties` — 是否允许额外字段**

```json
{
    "type": "object",
    "properties": {"city": {"type": "string"}},
    "additionalProperties": false
}
```

`additionalProperties` 控制"LLM 能否传入你在 `properties` 中未定义的字段"。设为 `false` 意味着 LLM 不能凭空发明新字段——它只能传 `city`，不能额外传一个 `year` 或 `country`。这是防止 LLM 参数幻觉的关键约束。

**`description` — 在每个 property 级别也要写**

```json
"city": {
    "type": "string",
    "description": "City name in English, e.g. 'Beijing' or 'New York'"
}
```

`description` 在 parameter 级别的作用和在第 2.2 节讨论的工具级别 description 一样——它是 LLM 理解"这个字段应该填什么"的唯一依据。**永远给每个 property 加 description**。这是最低成本、最高回报的 schema 优化——一行文字可以让 LLM 的参数准确率从 80% 提升到 95%。

#### 2.3.2 嵌套 Schema：对象中的对象、数组中的对象

真实世界的工具参数往往比 `{"city": "string"}` 复杂。JSON Schema 支持嵌套。

**对象中的对象**。假设你的工具需要接收一个地址：

```json
"address": {
    "type": "object",
    "properties": {
        "street":  {"type": "string", "description": "Street name and number"},
        "city":    {"type": "string"},
        "zipcode": {"type": "string", "description": "5-digit postal code"}
    },
    "required": ["city"],
    "additionalProperties": false
}
```

注意：嵌套的对象也有自己的 `type`、`properties`、`required`、`additionalProperties`。约束是层层叠加的——外层的约束和外层属性自己的约束都要满足。

**数组中的对象**。假设 `get_weather` 需要同时查多个城市：

```json
"cities": {
    "type": "array",
    "description": "List of cities to query weather for",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "City name in English"},
            "country": {"type": "string", "description": "2-letter country code, e.g. 'CN'"}
        },
        "required": ["name"],
        "additionalProperties": false
    }
}
```

`"items"` 关键字定义了"数组中每个元素的 schema"。这里 `cities` 是一个数组，每个元素是一个包含 `name` 和可选 `country` 的对象。

**设计建议**：能不用嵌套就不用。每次往 schema 中加一层嵌套，LLM 出错概率增加一分。优先用扁平结构——宁可把 `address(street, city, zip)` 拆成三个平级的顶层参数，也不要用一个嵌套的 `address` 对象，除非语义上确实需要打包。

#### 2.3.3 好坏对比

把上面学的所有关键字放到一起，做一个完整的对比：

```python
# 好——精确、有约束、有说明
"parameters": {
    "type": "object",
    "properties": {
        "city": {
            "type": "string",
            "description": "City name in English, e.g. 'Beijing' or 'New York'"
        },
        "unit": {
            "type": "string",
            "enum": ["celsius", "fahrenheit"],
            "description": "Temperature unit. Default: celsius."
        }
    },
    "required": ["city"],
    "additionalProperties": False
}

# 坏——类型模糊、无约束、无说明
"parameters": {
    "type": "object",
    "properties": {
        "city": {"type": "string"},
        "unit": {"type": "string"}
    }
}
# 问题 1: "unit" 没有 enum——LLM 可能传 "摄氏度"、"C"、"degree"，你的代码无法处理
# 问题 2: 没有 required——LLM 可能不传 city，你收到的 args 中 city 为 None
# 问题 3: 没有 additionalProperties: False——LLM 可能幻觉出 "year": 2024
# 问题 4: 每个 property 没有 description——LLM 对字段的理解完全靠猜
```

#### 2.3.4 设计原则总结

| 原则 | 说明 | 反例 |
|---|---|---|
| **类型精确** | 整数用 `"integer"` 不用 `"number"` | `"age": {"type": "number"}` → LLM 可能传 `25.7` |
| **enum 约束** | 已知选项用 `enum` 锁死 | 不用 enum → LLM 可能生成你的代码无法处理的自由文本 |
| **required 最小但完整** | 只标记真正必须的字段，但一个都不能少 | 少了 required → 关键参数可能为 None |
| **每个 property 写 description** | 嵌套越深越需要 description 引导 LLM | 只有外层有 description → 内层字段 LLM 靠猜 |
| **`additionalProperties: False`** | 阻止 LLM 在参数中幻觉出新字段 | 不加 → LLM 可能传入你从未定义过的字段 |
| **能扁不平** | 优先用扁平参数结构，嵌套只在语义必需时使用 | 过深的嵌套 → LLM 出错概率倍增 |

### 2.4 设计演进：从"能用"到"好用"

用一个 `get_weather` 工具为例，展示 schema 设计的四次迭代：

**V1 — 勉强能用**：

```python
"parameters": {"type": "object", "properties": {"city": {"type": "string"}}}
```

问题：`city` 不是必填的（LLM 可能不传，导致执行时参数为空）。没有 `additionalProperties`（LLM 可能添加多余字段）。没有 description（LLM 只能靠猜 `city` 应该是什么值）。

**V2 — 加上约束**：

```python
"parameters": {
    "type": "object",
    "properties": {"city": {"type": "string"}},
    "required": ["city"],
    "additionalProperties": False
}
```

改进：`city` 必须存在。LLM 不能传入超出定义的字段。但仍缺少语义引导——LLM 知道要传 string，但不知道应该传 "Beijing" 还是 "北京市朝阳区"。

**V3 — 加上引导**：

```python
"parameters": {
    "type": "object",
    "properties": {
        "city": {
            "type": "string",
            "description": "City name in English, e.g. 'Beijing' or 'New York'"
        },
        "unit": {
            "type": "string",
            "enum": ["celsius", "fahrenheit"],
            "description": "Temperature unit. Default: celsius."
        }
    },
    "required": ["city"],
    "additionalProperties": False
}
```

改进：LLM 知道 `city` 应该是英文城市名（而非中文或邮政编码），`unit` 只能是 `"celsius"` 或 `"fahrenheit"`。可选字段 `unit` 不在 required 中——不传就用默认值。

**V4 — 生产就绪**：在 V3 的基础上，将整个 function 设为 `"strict": True`（详见下节）。此时 schema 本身还必须满足 strict 模式的额外约束——所有字段都在 required 中，或在 properties 中明确标记为可选。

### 2.5 strict: true

`strict` 是 OpenAI 在 2025 年引入的一个布尔字段（放在 function 层级，不是 parameters 层级）。

**为什么要有它**：2023-2024 年 Function Calling 有一个困扰所有开发者的痛点——即使用了 JSON Schema 约束，LLM 仍有约 5-10% 的概率生成不符合 schema 的参数。比如让你传 `{"city": "Beijing"}` 时多传了一个 `{"year": 2026}`，或者在 required 字段不出现的时候漏掉了。开发者的应对方式痛苦而低效：用 try/except 包住每次工具调用，解析失败就重试；或者先用 JSON Mode 生成 json，再用代码校验并修正。

2025 年的解决方案是 **`strict: true`**——它的工作原理不是在生成后校验，而是**在模型采样时就约束 token 的分布**。模型在生成工具调用的参数时，每个 token 的可选集合已经被 schema 裁剪过了——不会出现超出的字段、不会缺少 required 字段、不会传错类型。生成即符合。

**开启条件**：`strict: true` 要求你的 schema 满足更严格的条件：
1. 所有 `object` 必须有 `"additionalProperties": False`
2. `required` 中列出的字段必须在 `properties` 中有定义
3. 所有 `properties` 中的字段如果不全在 `required` 中，就说明有可选字段——这没问题，但需要确保语义清晰

**建议**：生产环境一律开启。调试阶段可以关掉快速迭代 schema（因为 strict 模式在 schema 不合规时会直接报错，你需要读懂错误信息来修正）。

---

## 3. tool_choice：控制 LLM 的调用行为

### 3.0 为什么需要 tool_choice

上面花了大量篇幅讲"怎么定义好一个工具"——确保 LLM 在合适的时机选择它。但还有一个前提问题：**LLM 在什么情况下可以不调用任何工具？**

看这个场景：你有一个 `extract_user_info` 工具，用来从用户输入中提取结构化信息（姓名、地址、偏好）。你希望这个工具在**每次请求**时都被强制调用——因为你的下游代码依赖它的输出。但如果你不设置 `tool_choice`，当你发送 `"你好"` 时，LLM 可能"礼貌地"用自然语言回复 `"你好！有什么可以帮你的？"`——它没有调用工具，你的结构化提取流程就断了。

这就是 `tool_choice` 要解决的问题：**LLM 的"最佳判断"不总是开发者想要的"行为模式"**。`tool_choice` 让开发者可以限定 LLM 在这一步的**决策自由度**——从"你随意"到"你必须调"到"你绝不能调"到"你只能调这个"。

### 3.1 四种模式详解

| 值 | 设计意图 | 适用场景 | **不可用**场景 |
|---|---|---|---|
| `"auto"`（默认） | 让 LLM 自由判断是否需要工具。最接近"自然智能体"的行为模式 | 常规对话、工具调用是可选的 | 你的下游代码**依赖**工具输出的场景 |
| `"required"` | 强制 LLM 必须调用至少一个工具。无论用户说了什么，response 中一定有 tool_calls | 工作流的每一拍都必须产生结构化输出（如"每个用户消息都提取意图→路由→执行"） | 用户可能在"纯聊天"的场景（如"你好""谢谢"）——LLM 被迫乱调工具 |
| `"none"` | 禁止 LLM 调用任何工具。即使 tools 参数中有工具定义，LLM 也不能用 | 只让 LLM 做纯文本处理：总结上一轮工具结果、解释某个概念、生成自由文本 | 需要 LLM 主动获取外部信息的场景 |
| `{"type": "function", "function": {"name": "xxx"}}` | 强制调用特定的一个工具。LLM 不能选择其他工具，也不能直接回答 | 工作流的固定步骤（如"入库阶段必须用 ingest_document"）、A/B 测试某个工具的调用质量 | 该步骤的输入为空或无法满足工具的参数要求 |

### 3.2 翻车场景与根因分析

**`auto` 翻车**：用户问"今天天气怎么样"→ LLM 自信地用训练数据里的旧天气信息直接回答，没有调 `get_weather`。

**根因**：不是 LLM"不想"调工具，而是在它看来"直接回答"和"调工具再回答"都是合理策略，它选了前者——因为它无法知道"这个信息必须是最新的"这一外部约束。**对策**：在工具 description 中加负面引导："Do NOT answer weather questions from training data——always call this tool for current weather."

**`required` 翻车**：用户说"你好"→ LLM 被强制调用工具，于是随机选一个工具，传了一组荒谬的参数。**根因**：`required` 把 LLM 逼到了一个它不想去的角落——它没有合适的工具可用，但必须调一个。**对策**：在 `required` 模式**之前**加一层意图判断——确认需要工具时才进入 `required` 分支。这恰好是 LangGraph Conditional Edge 的典型用法。

**指定工具名翻车**：某工作流节点强制调用 `search_documents(query)`，但上游传来的 query 为空字符串 → LLM 必须调但不知道该传什么 → 传了一个空 query 或随机字符串。**根因**：你强制了"必须调"，但没有检查"能不能调"。**对策**：在进入指定工具名节点前，验证工具的 required 参数是否非空。

#### 汇总：Agent 工作流各阶段推荐 tool_choice

| 工作流阶段 | 推荐 tool_choice | 理由 |
|---|---|---|
| 初始路由（判断意图） | `"auto"` | 让 LLM 灵活决定直接聊还是调工具 |
| 必须执行操作的步骤 | `"required"` | 确保这一步一定有结构化输出 |
| 汇总/解释工具结果 | `"none"` | 只需要自然语言表达，不需要再调工具 |
| 固定的流水线步骤 | 指定工具名 | 确定性行为，不依赖 LLM 的路由判断 |

---

## 4. 并行调用 vs 串行调用

### 4.0 为什么会有并行调用

LLM 生成 tool_calls 时，是在一次前向传播中逐 token 输出的。当 LLM 判断"用户同时问了天气和计算问题"，它可以在同一次 response 中生成多个 tool_calls——第一个 `get_weather` 结束，紧接着生成第二个 `calculate`。这一切发生在一轮 `client.chat.completions.create()` 调用中。

**如果 LLM 不分两次返回，而是一次只返回一个 tool_call，会怎样？**多一轮完整的 API 往返——额外的网络延迟（200ms-1s）+ 额外的 token 消耗。这对用户体验和成本都不利。

但并行不是万能的。看图：

```
用户："查北京和上海的天气，然后用两城市气温的平均值做计算"

Round 1: LLM 返回 [get_weather("Beijing"), get_weather("Shanghai")]
     ↓ 并行执行（互不依赖）—— 省一轮 API 调用
Round 2: LLM 拿到两个温度，返回 [calculate("(25 + 22) / 2")]
     ↓ 串行执行（依赖 Round 2 的结果才能做下一步）
Final:  LLM 回答 "平均气温 23.5 C"
```

第一轮两个 `get_weather` 之间没有依赖 → 并行。第二轮 `calculate` 依赖第一轮的结果 → 必须等第一轮完成，串行执行。

### 4.1 parallel_tool_calls 参数

| 属性 | 说明 |
|---|---|
| 位置 | `client.chat.completions.create()` 的**顶层参数**（不在 tools 定义中，在 create 调用的参数里） |
| 默认值 | `True`——允许 LLM 一次返回多个 tool_calls |
| 语义 | 设为 `False` 时，LLM 每次最多返回一个 tool_call |

**与 `tool_choice` 的关系**：

| 参数 | 控制的是什么 |
|---|---|
| `tool_choice` | LLM **要不要**调工具？调哪个？ |
| `parallel_tool_calls` | LLM **一次能不能调多个**？ |

两者是正交的：`tool_choice="required"` + `parallel_tool_calls=False` = 每轮必须调一个且只能调一个工具——适用于严格的流水线模式。

### 4.2 决策规则

**形式化判断标准**：对于 LLM 返回的 N 个 tool_calls，如果任意两个调用的输出互不构成对方的输入，则可以安全并行；否则必须串行。

用一个依赖图示例（用 ASCII 展示）：

```
用户 query: "查北京的天气，然后用那个温度做复杂运算，同时查上海天气"

tool_call_1: get_weather("Beijing")  ──→  输出: 25 C
                                              │
tool_call_2: get_weather("Shanghai")        依赖（25 C 是输入）
                                              ↓
                               tool_call_3: calculate("25 * 1.8 + 32")

并行组: {get_weather(Beijing), get_weather(Shanghai)} ← 两者无依赖
串行组: {并行组的结果} → {calculate(...)}
```

**决策流程**：
1. LLM 返回 tool_calls 列表
2. 遍历列表，构建依赖关系（B 的 arguments 中是否引用了 A 的输出字段）
3. 将列表划分为独立组——组内并行，组间串行
4. 如果组的划分太复杂（手动维护成本高），直接设 `parallel_tool_calls=False`，简化逻辑

### 4.3 多工具结果合并

并行执行后，LLM 同时收到了多条 `role: "tool"` 的消息。LLM 靠什么区分谁是谁？**`tool_call_id`**。这是 1.3 节讲的机制——每条 tool role 消息的 `tool_call_id` 必须精确匹配对应的 tool_call 的 `id`。

**一个容易出错的情况**：两个并行调用的结果互相矛盾。比如 `get_weather("Beijing")` 返回 "Sunny, 25 C"，`get_weather("Beijing")` 的另一个来源返回 "Rainy, 10 C"。LLM 会把两个结果都读进去，可能出现三种行为：(a) 选一个并忽略另一个，(b) 尝试"折中"（北京有点晴又有点雨），(c) 向用户说明两个来源的矛盾。目前没有任何 API 层面机制来处理这种情况——你需要在自己的 prompt 中告诉 LLM "如果两个来源结果矛盾，优先选择较新的那个"。

### 4.4 何时主动禁用并行

以下情况建议禁用并行（`parallel_tool_calls=False`）：

1. **工具间有因果依赖**：B 的输入从 A 的输出中提取，强行并行会导致 B 传错参数
2. **共享有状态资源**：两个工具写同一个文件或操作同一个数据库连接——产生竞态条件
3. **严格速率限制**：并行调 10 个外部 API 全被 429 限流，不如串行 + 背压控制
4. **调试阶段**：串行模式下 trace 更清晰，出问题时更容易定位是哪一步

---

## 5. 错误处理：让 LLM 从失败中恢复

### 5.0 错误发生在哪里

回到 1.2 节的五阶段闭环：

```
阶段 1 (定义工具) → 阶段 2 (LLM 决策) → 阶段 3 (解析调用) → 阶段 4 (执行工具) ← 错误发生在这里
                                                                         ↓
                                                      阶段 5 (返回结果给 LLM) → LLM 需要据此决策"下一步怎么办"
```

核心矛盾：**工具在你的代码中执行（阶段 4），但如果执行失败，做出"怎么办"决策的是 LLM（阶段 2 的下一次循环）**。LLM 只看到了你返回的字符串。如果这个字符串不能帮 LLM 做出聪明的决策——它就会乱猜。

### 5.1 失败类型分类

| 类型 | 典型原因 | 发生阶段 | LLM 应该怎么做 |
|---|---|---|---|
| **临时性故障** | API 超时、限流 (429)、网络抖动 | 阶段 4（工具执行超时） | 换参数重试、等待后重试 |
| **参数错误** | 城市名不存在、日期格式错误、数值越界 | 阶段 4（执行中参数校验失败） | 修正参数后重试（如 "Beijinggg" → "Beijing"） |
| **业务逻辑错误** | 余额不足、权限不够、数据不存在 | 阶段 4（业务校验拒绝） | 向用户解释原因，建议替代方案 |
| **致命错误** | 工具本身挂了、认证失败、依赖服务宕机 | 阶段 4（工具不可用） | 坦诚向用户说明能力不可用，不再重试 |

### 5.2 为什么纯文本错误信息不够

考虑三种错误返回，以及 LLM 对应的行为：

```python
# 情况 A：纯文本，无分类
return "Error"
# → LLM 行为：完全随机。可能放弃、可能重试同样参数、可能换一个无关工具。

# 情况 B：纯文本，有描述
return "Error: timeout"
# → LLM 行为：知道是超时，但不知道等了多久、需不需要换参数重试。

# 情况 C：结构化错误
return json.dumps({
    "error": True,
    "error_type": "temporary",
    "message": "Request timed out after 30s",
    "retry_after": 5,
    "suggested_action": "retry_with_same_params"
})
# → LLM 行为：明确知道这是临时错误，等 5 秒后用相同参数重试。
```

**核心原则**：你要让 LLM 不仅知道"失败了"，还要知道**"这是什么类型的失败""我该怎么做"**。结构化的字段就是 LLM 做"下一步决策"的依据。

### 5.3 结构化错误的设计

每个字段的设计意图：

| 字段 | 类型 | 设计意图 |
|---|---|---|
| `"error"` | `bool` | 标记——LLM 一看到这个就知道"这不是正常结果" |
| `"error_type"` | `str` | 分类——`"temporary"`（可以等一会儿重试）、`"invalid_input"`（需要修正参数）、`"business_logic"`（业务上不允许）、`"fatal"`（别再试了） |
| `"message"` | `str` | 人类可读的描述——LLM 可以用来向用户解释发生了什么 |
| `"retry_after"` | `int`（可选） | 明确的等待秒数——防止 LLM 进入"快速失败→快速重试"的死循环 |
| `"suggested_action"` | `str`（可选） | 直接告诉 LLM 怎么做——降低 LLM "自己想办法"时的不确定性 |

### 5.4 错误恢复在 ReAct 循环中的表现

用你下周要写的 ReAct 循环来模拟这个场景：

```
Scenario: 用户问 "Search for Python Agent frameworks"

Step 1: Thought: 我需要搜索 Python Agent 框架
        Action: search
        Action Input: Python Agent frameworks
        Observation: {"error":true, "error_type":"temporary", "message":"Rate limited",
                       "retry_after":3, "suggested_action":"retry_with_same_params"}

Step 2: Thought: 搜索被限流了，需要等 3 秒后用相同参数重试。
        [等待 3 秒]
        Action: search
        Action Input: Python Agent frameworks
        Observation: - LangGraph: ... - AutoGen: ... - CrewAI: ...

Step 3: Thought: 已获取搜索结果，可以列出三个框架并做简要介绍。
        Final Answer: 当前主要的 Python Agent 框架有...
```

**对比**：如果 Step 1 的 Observation 只是 `"Error"`，Step 2 的 Thought 会是什么？LLM 不知道发生了什么，它可能：(a) 放弃搜索试图用内部知识回答（幻觉），(b) 换成无关的搜索词，(c) 调用一个完全不相关的工具。结构化错误提供了 LLM 做出"再试一次"这个正确决策所需的所有信息。

### 5.5 致命错误与终止策略

**致命错误识别**：`authentication_failed`、`permission_denied`、`service_unavailable`（持续，非临时）、`tool_not_implemented`。这类错误意味着重试不会改变结果。

**终止策略**：设置硬性重试上限（如 3 次）。超过上限后，Agent 应该优雅降级——"抱歉，我目前无法完成这个操作，因为 [错误原因]。建议你 [替代方案]。"——而不是无限循环。

**预告（第 3 周）**：在 LangGraph 中，致命错误的处理不是靠"多试几次"——而是通过 `interrupt` 机制暂停整个 graph，等待人工介入。这和 Human-in-the-Loop 是同一种机制。下周你手写 Agent 时可以用 `max_steps` + 错误类型检查来手动模拟这个行为。

---

## 6. Function Calling vs 其他方案

### 6.1 vs ReAct 文本格式

| 维度 | Function Calling | ReAct 文本格式 |
|---|---|---|
| 可靠性 | 极高——结构化输出，解析 100% 可靠 | 中——正则解析有失败概率 |
| 灵活性 | 受 Schema 限制，不能自由发明调用格式 | 极高——LLM 可自由发明调用模式 |
| 推理可见性 | 无——跳过 Thought 直接调工具 | 有——每步 Action 前有 Thought，便于调试 |
| 并行调用 | 原生支持（一次返回多个 tool_calls） | 几乎不可能（文本格式没有并行通道） |
| 模型要求 | 需模型原生训练过 tool calling | 任何能生成文本的 LLM 都行 |
| 适用场景 | 工具多、需要可靠性、生产环境 | 需要显式推理链、原型阶段、弱模型 |

**不是"谁更好"的问题**。下周你手写 ReAct 时会亲身体验文本格式的痛苦——正则解析脆弱、格式约束冗长、并行调用做不到。但 Function Calling 也有代价——Thought 推理步骤消失了，你无法看到 LLM "为什么"选了这个工具。两者互补：LangGraph 允许在同一个 graph 的不同节点中混用这两者。

### 6.2 vs JSON Mode / Structured Outputs

OpenAI 提供了三种让模型输出结构化数据的方式，按使用场景区分：

| 方案 | API 参数 | 用途 | 何时用 |
|---|---|---|---|
| **Function Calling** | `tools=[...]` | 连接模型到外部工具/API | 需要模型"决定"调不调工具、调哪个工具 |
| **JSON Mode** | `response_format={"type": "json_object"}` | 让 LLM 输出 JSON 而非自然语言 | 需要结构化输出但不需要"工具调用"概念（如分类、情感分析） |
| **Structured Outputs** | `response_format={"type": "json_schema", "json_schema": {...}}` | 严格 Schema 约束的 JSON 输出 | 从响应中提取结构化数据，保证符合 schema |

**简单判断**：如果你需要 LLM 在"直接回答"和"调工具"之间做选择 → Function Calling。如果你只是想让 LLM 的输出是 JSON 格式而非自然语言 → JSON Mode 或 Structured Outputs。

### 6.3 vs MCP 协议

Function Calling 是**单模型 + 单工具列表**的调用机制——工具定义写在请求的 `tools` 参数里，每次请求时现传。MCP 是**跨模型、跨应用的标准化工具生态**——工具定义独立存在于 MCP Server 中，任何 LLM 通过 MCP Client 都能发现和调用。

你第 6-7 周学 MCP 时会重新审视这个关系：**Function Calling 解决的是"怎么调"（调用协议），MCP 解决的是"调到谁"和"怎么发现可用工具"（工具注册与发现）**。两者在 Agent 架构中是互补的：Function Calling 是底层调用机制，MCP 是上层工具管理标准。

### 6.4 决策表：何时选哪种

| 场景 | 推荐方案 |
|---|---|
| 原型 / 学习 / 需要推理链可见 | ReAct 文本格式 |
| 生产环境、多工具、需要可靠性 | Function Calling + `strict: true` |
| 只需要结构化数据输出（分类/提取） | Structured Outputs |
| 跨应用工具生态、第三方提供工具 | MCP 协议 |
| 复杂编排、多策略混用 | LangGraph + Function Calling / ReAct 混用 |

---

## 7. 安全性设计

（本节简化，详细设计在旗舰项目开发阶段展开。）

### 7.1 工具权限分级

```
Level 0 - 只读：查询信息，不产生副作用（搜索、计算、读文件）
Level 1 - 写入：创建新数据（写文件、新建数据库记录）
Level 2 - 修改：更新已有数据（编辑文件、更新数据库）
Level 3 - 删除/外部：不可逆操作或外部网络操作（删除文件、付款、发邮件）
```

### 7.2 最小权限原则

Agent 的 tools 列表中只包含它完成当前任务**必需的**工具。如果任务是"查天气"，不要给 `delete_file` 工具——即使 LLM 被 prompt injection 诱导去删除文件，它也没有这个能力。

### 7.3 Human-in-the-Loop

Level 2-3 级别的操作必须经过人类审批。LangGraph 的 `interrupt` 机制就是为此设计的——在关键节点暂停图执行，等待人工确认后继续。

---

## 8. 与 LangGraph 的关系（第3周预习）

### 8.1 ToolNode 的本质

你在 LangGraph 中不会手动处理 `tool_calls → 执行 → 追加 tool 消息` 的流程。LangGraph 的 `ToolNode` 类自动完成这些：

```python
# 手写版本（下周你要做的）：
for tc in msg.tool_calls:
    result = execute(tc.function.name, json.loads(tc.function.arguments))
    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

# LangGraph 版本（第3周学习）：
# ToolNode 自动解析 tool_calls，执行对应工具函数，生成 ToolMessage
# 你只需要把"工具函数"注册进去，剩下的都是自动的
```

### 8.2 自动化流程

```
LLM Node（生成 tool_calls）
       ↓
ToolNode（自动解析 + 执行 + 生成 ToolMessage）
       ↓
LLM Node（汇总结果，生成最终回答）
```

这本质上就是你第 1 节学习的五阶段闭环中阶段 3-5 的自动化封装。

### 8.3 混用 Function Calling 和文本格式 ReAct

LangGraph 的核心灵活性之一是：**不同节点可以使用不同的工具调用策略**：

- 需要可靠执行的关键步骤 → 使用 Function Calling 节点
- 需要显式推理的诊断/调试步骤 → 使用文本格式 ReAct 节点

Conditional Edge 可以根据任务类型在运行时动态路由到不同策略的节点。这是 LangGraph 区别于 LangChain 旧版 AgentExecutor 的关键设计。

---

## 9. 实战 Checklist

### 9.1 开发阶段

- [ ] 每个工具单独测试：验证 schema 正确 + LLM 能正确选择
- [ ] 多工具联合测试：验证 LLM 在多个工具可选时路由正确
- [ ] 边界情况测试：空输入、非法输入、工具不存在、超时、并发冲突
- [ ] 用 LangSmith / LangFuse 追踪：观察每次 tool call 的实际参数和返回

### 9.2 上线前检查

- [ ] Schema 校验通过（`strict: true` + `additionalProperties: False`）
- [ ] 所有工具都有超时设置（每个工具单独超时 + Agent 全局超时）
- [ ] 错误返回是结构化的（带 `error_type`、`message`、`suggested_action`）
- [ ] 日志记录完整：每次 tool call 的 input、output、duration、status
- [ ] 权限分级到位：Level 2+ 操作有 Human-in-the-Loop 审批

### 9.3 持续优化

根据三个指标迭代工具定义：

| 指标 | 含义 | 目标 |
|---|---|---|
| **Tool Selection Rate** | LLM 是否在正确时机选择了这个工具 | 误选率 < 5% |
| **Argument Validity** | LLM 传的参数是否合法 | 合法性 > 95% |
| **Recovery Rate** | 工具调用失败后 LLM 能否正确恢复 | 恢复率 > 80% |

如果某个指标持续不达标——**不是改 prompt，而是改工具 Schema**。description 的措辞调整有时带来显著改善。

---

## 附录 A：5 分钟速查表

### 最小完整示例

```python
from openai import OpenAI
client = OpenAI()

# 1. 定义工具
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "strict": True,
        "description": "Get current weather for a city. Use when user asks about weather/temperature.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name in English, e.g. 'Beijing'"
                }
            },
            "required": ["city"],
            "additionalProperties": False
        }
    }
}]

# 2. 第一次请求
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=tools,
    tool_choice="auto"
)
msg = response.choices[0].message

# 3. 处理 tool_calls
if msg.tool_calls:
    messages = [{"role": "user", "content": "What's the weather in Tokyo?"}]
    messages.append(msg)  # assistant role with tool_calls
    for tc in msg.tool_calls:
        result = your_execute_function(tc.function.name, json.loads(tc.function.arguments))
        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,         # 必须
            "content": str(result)          # 必须是字符串
        })

    # 4. 第二次请求——LLM 汇总
    final = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    print(final.choices[0].message.content)
```

### 最常用参数

| 参数 | 类型 | 说明 |
|---|---|---|
| `tools` | `list[dict]` | 工具定义列表 |
| `tool_choice` | `str` 或 `dict` | `"auto"` / `"required"` / `"none"` / 指定工具 |
| `parallel_tool_calls` | `bool` | 是否允许一次返回多个 tool_calls（默认 `True`） |
| `strict` | `bool` | 是否开启严格 Schema 校验（在 tool 的 function 层级） |

### 最容易犯的三个错误

1. **忘记 `tool_call_id`**：没有它，并行调用时 LLM 分不清哪个结果对应哪个调用
2. **tool role 消息的 content 不是字符串**：必须 `str(result)`，不能直接传 dict
3. **`strict: true` 但 schema 不兼容**：所有 object 必须有 `additionalProperties: False`，所有 property 必须在 `required` 中

---

## 附录 B：知识来源与参考链接

| 来源 | 类型 | 链接 |
|---|---|---|
| OpenAI Function Calling 官方文档 | 官方文档 | https://platform.openai.com/docs/guides/function-calling |
| OpenAI Function Calling Help Center | 官方 FAQ | https://help.openai.com/en/articles/8555517-function-calling-in-the-openai-api |
| OpenAI Structured Outputs 文档 | 官方文档 | https://platform.openai.com/docs/guides/structured-outputs |
| Machine Learning Mastery: Tool Calling Roadmap (2025) | 技术综述 | https://machinelearningmastery.com/the-roadmap-to-mastering-tool-calling-in-ai-agents/ |
| From Prompts to Production: Function Calling in 2026 | 行业实践 | https://dev.to/author_shivani_9c765c8db9/from-prompts-to-production-how-developers-are-building-smarter-ai-apps-with-function-calling-in-8md |
| AsyncFC: Asynchronous Function Calling (UC Berkeley, 2025) | 学术论文 | https://people.eecs.berkeley.edu/~kubitron/courses/cs262a-F25/projects/reports/project1009_paper_36116196665666091745.pdf |
| AWS Summit: Tool use & agents at the frontier (2025) | 行业演讲 | https://pages.awscloud.com/rs/112-TZM-766/images/GAI302-Amsterdam-English.pdf |
| ReAct 论文 (Yao et al., ICLR 2023) | 学术论文 | https://arxiv.org/abs/2210.03629 |
| MCP 官方文档 | 协议规范 | https://modelcontextprotocol.io/docs |
