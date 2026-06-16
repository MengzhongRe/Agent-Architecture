# 10 — Agent 主循环的工程细节

> 几个在实现 `new_agent.py` 过程中暴露出来的关键设计决策，涉及对话管理、token 追踪和 SDK 使用方式。

---

## 1. 为什么 Observation 放在 `{"role": "user"}` 中？

这是手写 ReAct Agent 中最容易被忽视但最重要的设计决策。对应代码 [new_agent.py:352-353](../01-handwritten-react/new_agent.py#L352-L353)：

```python
messages.append({'role': 'assistant', 'content': response})        # 模型输出
messages.append({'role': 'user', 'content': f'Observation: {observation}'})  # 工具结果
```

### 1.1 角色交替规则（API 约束）

OpenAI Chat Completions API 要求消息严格交替：`user → assistant → user → assistant → ...`。模型输出 `assistant` 后，下一条必须是 `user`（或 `tool`），不能连续两条 `assistant`。

```
合法:  system → user → assistant → user → assistant → ...
非法:  system → user → assistant → assistant → ...    ← API 拒绝
```

Observation 必须插在 `assistant` 之后，所以它只能是 `user`。

### 1.2 语义归属：谁"说"了这句话？

这是更深层的原因。把对话想象成两个人交谈：

| 角色 | 谁在说话 | 内容 |
|------|---------|------|
| `user` | 外部世界 | 用户问题、工具返回结果、环境反馈 |
| `assistant` | 模型自身 | 推理过程、行动决策、最终答案 |

**Observation 是工具/环境返回的，不是模型生成的。** 模型只负责"思考与决策"，它不产生工具结果。把 Observation 塞进 `assistant` 会让模型误以为"这是我之前说过的话"，从而混淆自己的推理链。

`user` 角色的本质含义：**来自模型外部的信息输入**。原始用户问题是外部输入，工具执行结果同样是外部输入——它们都来自"模型之外的世界"。

### 1.3 与原生 Function Calling 的对应

OpenAI 后来引入了专用的 `tool` 角色来解决这个问题：

```python
# 原生 function calling — 专用 tool 角色
messages.append({'role': 'assistant', 'tool_calls': [...]})
messages.append({'role': 'tool', 'tool_call_id': tc.id, 'content': observation})

# 手写 ReAct 文本协议 — 复用 user 角色
messages.append({'role': 'assistant', 'content': 'Action: calculator\nAction Input: 2+2'})
messages.append({'role': 'user', 'content': 'Observation: Result: 4'})
```

手写 Agent 用文本协议（Thought/Action/Action Input/Observation）来模拟工具调用，没有 `tool` 角色可用，`user` 就是唯一的"外部输入通道"。

### 1.4 一图总结

```
对话轮次:

  [user]      "1+1 等于几？"              ← 用户问题（外部输入）
  [assistant] "Thought: 需要计算           ← 模型决策（模型输出）
               Action: calculator
               Action Input: 1+1"
  [user]      "Observation: Result: 2"     ← 工具结果（外部输入）★ 关键
  [assistant] "Thought: 我有答案了          ← 模型推理（模型输出）
               Final Answer: 等于 2"
```

**分界线**：`user` = 一切来自模型外部的信息；`assistant` = 一切模型自己产生的内容。

---

## 2. Token 追踪：从字符估算到 `response.usage`

### 2.1 第一版：字符数 / 4 启发式估算

最初实现 [new_agent.py:219-228](../01-handwritten-react/new_agent.py#L219-L228)：

```python
def estimate_tokens(messages: List[dict]) -> int:
    total_chars = sum(len(msg.get('content', '')) for msg in messages)
    return total_chars // 4
```

英文 ~4 chars/token，足够看趋势，但有两个问题：
- 不精确（中文 ~1 char/token，代码差异更大）
- 看不到 `completion_tokens`，只知道输入侧

### 2.2 改进版：直接用 API 返回的 usage

OpenAI API 每次响应自带精确 token 计数：

```json
{
    "usage": {
        "prompt_tokens": 342,
        "completion_tokens": 85,
        "total_tokens": 427
    }
}
```

改 `generate()` 签名为 `-> tuple[str, dict]`，同时返回文本和 usage：

```python
def generate(self, messages: List[dict]) -> tuple[str, dict]:
    response = self.client.chat.completions.create(...)
    text = response.choices[0].message.content
    usage = {
        'prompt_tokens': response.usage.prompt_tokens,
        'completion_tokens': response.usage.completion_tokens,
        'total_tokens': response.usage.total_tokens,
    }
    return text, usage
```

主循环中打印：

```python
response, usage = self.llm.generate(messages)
print(f'[Context]: {usage["prompt_tokens"]} prompt tokens '
      f'(+{usage["completion_tokens"]} completion '
      f'= {usage["total_tokens"]} total) [{len(messages)} msgs]')
```

### 2.3 运行时你能观察到什么

```
Step 1/8
[Context]: 342 prompt (+85 completion = 427 total) [2 msgs]

Step 2/8
[Context]: 618 prompt (+112 completion = 730 total) [4 msgs]

Step 3/8
[Context]: 901 prompt (+95 completion = 996 total) [6 msgs]
```

每轮工具调用追加 2 条消息（assistant + user/Observation），prompt 膨胀约 250-300 tokens/步。这就是 context window 被逐步填满的过程——也是为什么生产环境中需要对话摘要、滑动窗口等 context 管理策略。

---

## 3. OpenAI SDK 属性访问 vs 字典访问

### 3.1 SDK 返回的是 Pydantic 模型，不是 dict

```python
# ✅ 正确 —— Pydantic 模型用属性访问
response.choices[0].message.content
response.usage.prompt_tokens

# ❌ 错误 —— 会抛 TypeError: 'ChatCompletion' object is not subscriptable
response["choices"][0]["message"]["content"]
```

这是因为 OpenAI Python SDK 的返回对象是 Pydantic `BaseModel`，不是普通 dict。`pydantic` 模型只支持属性访问（`.`），不支持下标访问（`[]`）。

### 3.2 唯一的例外：`Usage` 对象同时支持两种方式

```python
response.usage.prompt_tokens  # ✅ 属性访问
response.usage["prompt_tokens"]  # ✅ 也能用，但风格不统一，不推荐
```

### 3.3 对后续学习的影响

LangChain/LangGraph 等框架在封装 SDK 时，有些地方会帮你转成 dict，有些保留 Pydantic 对象。混用的边界是排查 bug 的常见坑——当你看到一个对象时，先确认它是 `dict` 还是 Pydantic `model`，再决定用 `[]` 还是 `.`。
