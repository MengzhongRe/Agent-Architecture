# 第1部分：Agent 理论基础 — 详细任务计划（第1-2周）

> **属于**：[LEARNING-PLAN.md](../LEARNING-PLAN.md) 第1部分
> **目录**：`01-handwritten-react/`
> **目标**：理解 Agent 设计原理 + 从零手写 ReAct Agent（不借助任何框架）

---

## 两周总览

```
第1周：理论建立（读 → 理解 → 设计）
第2周：动手实现（写 → 跑 → 搞坏 → 修 → 反思）
```

|   天   | 日期      | 主题                                         |   类型   |  预计时间  |    状态    |
| :---: | ------- | ------------------------------------------ | :----: | :----: | :------: |
|   1   | 6/7     | 阅读 Lilian Weng 文章 + 建立 Agent 概念框架          |   阅读   |   3h   |    ✅     |
|   2   | 6/8     | 精读 ReAct 论文 Section 2-4                    |   阅读   |   3h   |    ✅     |
|   3   | 6/8-9   | 综述速览 + API 环境搭建（DeepSeek + Ollama 本地）      | 阅读+环境  |   3h   |    ✅     |
|   4   | 6/9     | Function Calling 系统学习 + 跑通 demo            | 阅读+编码  |  2.5h  |    ✅     |
| **5** | **6/9** | **设计工具系统 + 阅读 agent.py + 实现 DateTimeTool** | **编码** | **3h** | **← 今天** |
|   6   | —       | 实现 Prompt 模板 + ReAct 主循环                   |   编码   |  3.5h  |    ⬜     |
|   7   | —       | 实现 Search / FileRead / FileWrite 工具        |   编码   |   3h   |    ⬜     |
|   8   | —       | 集成测试 + 跑通完整 ReAct 流程                       |   测试   |   3h   |    ⬜     |
|   9   | —       | 压力测试：故意搞坏 Agent + 观察边界行为                   |   实验   |   3h   |    ⬜     |
|  10   | —       | 写反思笔记 + 标记 LangGraph 对比要点                  |   写作   |  2.5h  |    ⬜     |

---

## 第1周：理论建立

### Day 1 — 阅读 Lilian Weng + 建立 Agent 概念框架

**目标**：建立 Agent 系统的完整心智模型。

**任务清单**：

- [x] **阅读** [Lilian Weng: "LLM Powered Autonomous Agents"](https://lilianweng.github.io/posts/2023-06-23-agent/)（约 40 分钟）
  - 阅读时重点关注三个模块的分工与边界：
    - **Planning**：Task Decomposition 怎么做？Self-Reflection 的几种方法有何不同？
    - **Memory**：Sensory / Short-term / Long-term 三层各解决什么问题？
    - **Tool Use**：LLM 怎么知道什么时候用哪个工具？
  - 边读边标注，不追求全记住——建立概念索引即可

- [x] **输出**：在 `notes/01-lilian-weng-agent.md` 中写一篇 300-500 字的结构化笔记（已创建模板）
  - 用你自己的话重述 Agent = LLM + Planning + Memory + Tool Use 框架
  - 写下你印象最深的 2 个案例（如 ChemCrow、Generative Agents）
  - 写下 1 个你不理解或想深入的点：agent如何知道什么时候应该调用什么外部工具?

- [x] **思考题**（不要求写下来，但要认真想）：
  - 如果 LLM 是大脑，Planning 是前额叶，Memory 是海马体，Tool Use 是手——这个类比哪里对、哪里不对？
  - ReAct 论文提出 Thought-Action-Observation 循环，和人类的"思考→行动→观察→调整"有什么本质区别？

**完成标准**：能脱稿画出 Agent = LLM + Planning + Memory + Tool Use 的四象限图，并解释每个部分的职责。

---

### Day 2 — 精读 ReAct 论文

**目标**：深入理解 ReAct 为什么这样设计，而不只是记住它的输出格式。

**任务清单**：

- [x] **阅读** [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629) (Yao et al., ICLR 2023)
  - **Section 1 (Introduction)**：为什么要用 ReAct？它解决了什么之前方法没解决的问题？
  - **Section 2 (ReAct Methodology)**：Thought-Action-Observation 循环的形式化定义。注意：Action space 是离散动作 + 自由文本语言的组合空间
  - **Section 3 (Experiments)**：重点看 Table 1-3。ReAct 在哪些任务上显著优于纯 CoT 或纯 Act？
  - **Section 4 (Analysis)**：重点——为什么 ReAct 在推理任务上比 Act-only 好？为什么在决策任务上比 CoT-only 好？（这解释了"推理+行动"互补的必要性）
  - 跳过 Section 5-6（Related Work 和 Conclusion，快速浏览即可）

- [x] **输出**：在 `notes/02-react-paper.md` 中写笔记，回答以下问题：
  1. ReAct 的 Thought 和 CoT 的 intermediate reasoning step 有什么本质区别？（提示：CoT 只推理不行动；ReAct 的 Thought 指导下一步 Action）
  2. 为什么 ReAct 结合了推理和行动后，比单独使用某一侧更好？
  3. ReAct 的 Action space 设计有什么巧妙之处？（提示：离散动作负责结构化操作，语言空间负责灵活表达）
  4. 图 1 中的那个 HotpotQA 例子——Trace 了 6 步，每一步 Thought/Action/Observation 分别做了什么？

- [x] **关键理解**：ReAct 不等于"调 API 时让 LLM 多想一步"。它是一个**推理-行动交替的决策循环**，每一步的 Observation 来自外部环境反馈（搜索结果、计算结果、文件内容），而不是 LLM 自己的内部知识。

**完成标准**：能用自然语言向一个没读过论文的同学解释清楚"ReAct 和 CoT 的区别、ReAct 的核心循环、以及为什么它有效"。

---

### Day 3 — 综述速览 + API 环境搭建（DeepSeek + Ollama 本地）

**目标**：快速收尾综述的 5% 有用内容。配置两套 LLM 环境——DeepSeek API（主力）和 Ollama 本地（备选）。跑通冒烟测试。为 Day 4 Function Calling 和 Day 5+ 编码做准备。

**预计时间**：3 小时（综述 5min + DeepSeek 配置 30min + Ollama 安装 1.5h + smoke test 25min）

---

**任务清单**：

#### 第一步：综述速览（5 分钟）

- [x] 用 AI 提取 Section 4 的应用分类表格，不超过 200 字
- [x] 在 `notes/03-agent-survey-map.md` 中完成：Agent 应用分类树 + 旗舰项目定位
- [x] 其余章节全部跳过。Section 6.2（Evaluation）标记为"第 12 周回看"

#### 第二步：DeepSeek API 配置（约 30 分钟）

- [x] **注册 DeepSeek API key**，配置 `.env`：
  ```bash
  # 01-handwritten-react/.env
  OPENAI_API_KEY=sk-your-deepseek-key
  OPENAI_BASE_URL=https://api.deepseek.com
  ```
- [x] **创建 `.env.example`** 作为模板（只含占位符 `your_key_here`，可提交 Git）
- [x] **理解 .env vs .env.example 的区别**（参考 `notes/04-function-calling.md` 第 0.5 节）

#### 第三步：Ollama 本地模型部署（约 1.5 小时）

- [x] **安装**：`brew install ollama`（或从 ollama.com 下载 .dmg）
- [x] **启动服务**：`ollama serve`（或双击 Applications 中的 Ollama 图标）
- [x] **拉取模型**：`ollama pull qwen3.5:9b`（MacBook Air M4 16GB 最优选择）
- [x] **验证**：`ollama run qwen3.5:9b "你好"` 确认对话正常
- [x] **了解关键概念**：模型文件大小 ≠ 运行时内存占用（+KV Cache + 运行时开销）；Q4_K_M 量化是 sweet spot
- [x] **理解 RTX 5070 Ti 不能在 Mac 上用**——Apple Silicon 不支持 NVIDIA eGPU。5070 Ti 留到后续微调任务
- [x] **参考**：`notes/06-ollama-setup-guide.md` 完整部署指南

#### 第四步：冒烟测试两套环境（约 25 分钟）

- [x] **DeepSeek 环境**：`.env` 中用 DeepSeek 配置，`smoke_test.py` 设 `MODEL="deepseek-chat"`，跑通
- [x] **Ollama 环境**：`.env` 中切到 `OPENAI_BASE_URL=http://localhost:11434/v1`，`MODEL="qwen3.5:9b"`，跑通
- [x] **确认**：两套环境均可独立工作，后续开发 DeepSeek 主力 + Ollama 本地备选

**完成标准**：
- `.env` 和 `.env.example` 正确配置（真实 key 在 `.env` 中、占位符在 `.env.example` 中）
- `smoke_test.py` 在两套环境下均打印 "Environment OK!"
- Ollama 本地模型能正常对话

---

### Day 4 — Function Calling 系统学习 + 跑通 demo

**目标**：深入理解 Function Calling——结构化工具调用的"正确答案"。先建立系统认知（阅读笔记），再动手验证（跑 demo）。为 Day 5 手写工具时提供参照系——知道 FC 帮你省了什么，才知道 ReAct 文本格式的取舍在哪。

**预计时间**：2.5 小时（阅读笔记 1.5h + 跑 demo 1h）

**注意**：Function Calling demo **必须用 DeepSeek API 跑**。本地 Ollama 7B/9B 模型的 tool calling 能力不可靠——tool_choice 可能被忽略、JSON 参数可能格式错误。

---

**任务清单**：

#### 第一步：阅读 Function Calling 系统性笔记（约 1.5 小时）

- [x] **阅读 `notes/04-function-calling.md`**，按以下优先级：

  **第一遍——建立概念框架（30min）**：
  - 第 0 节：Function Calling 是什么、为什么存在——LLM 的天然局限 → Tool Use 层的三种实现方式
  - 第 0.5 节：环境变量与 .env 文件——理解你刚配置好的 .env/.env.example 的工作原理

  **第二遍——理解核心机制（40min）**：
  - 第 1 节：完整生命周期——五阶段闭环 + messages 结构演变 + content/tool_calls 互斥规则
  - 第 1.4 节：与 ReAct 文本格式的逐阶段对比——**这是 Day 5-9 最重要的参照表**

  **第三遍——工程能力（20min）**：
  - 第 2 节：Tool Schema 设计——name/description/parameters 怎么写。**Day 5 你写 DateTimeTool 时直接套用这里的原则**

- [x] **其余章节（第 3-5 节 tool_choice/并行/错误处理）按需查阅**——Day 6-9 编码时遇到问题再回头翻

#### 第二步：跑通 function_calling_demo.py 四个实验（约 1 小时）

- [x] **切换到 DeepSeek API**（本地 Ollama 不可靠）：
  ```bash
  # .env 中取消注释 DeepSeek，注释掉 Ollama
  OPENAI_API_KEY=sk-bb5fc4b8c39545308071ab9e8b811213
  OPENAI_BASE_URL=https://api.deepseek.com
  ```

- [x] **跑四个实验**：
  ```bash
  cd agent-learning-journey/01-handwritten-react
  source ../venv/bin/activate
  python function_calling_demo.py
  ```

- [x] **观察关键现象并对照笔记**：
  - 实验一 → 对照笔记第 2 节（工具定义 = `type: "function"` 外层 + `function` 内层三要素）
  - 实验二 → 对照笔记第 1.1 节（`content` 为 None 时 `tool_calls` 非空——互斥规则）
  - 实验三 → 对照笔记第 1.2 节（五阶段闭环：定义→决策→解析→执行→返回）
  - 实验四 → 对照笔记第 1.4 节（FC 省掉了正则解析、格式 prompt、参数校验；丢了 Thought 推理）

- [x] **验证理解**——能脱稿回答：
  1. Function Calling 帮我们省掉了什么？（正则解析、格式 prompt、参数校验）
  2. 为什么不能替代 ReAct 的 Thought？（Thought 是工作记忆 + 规划推理——FC 跳过了这个，直接调工具）
  3. 什么场景选 ReAct 文本格式？（需要显式推理链、模型不支持 FC、原型快速验证）

**完成标准**：
- function_calling_demo.py 四个实验全部跑通
- 能说出 FC 和 ReAct 的三个核心差异
- 能解释"为什么 Day 5-9 用文本格式而不是 Function Calling"——不是技术限制，是为了理解框架抽象

---

### Day 5 — 设计工具系统 + 阅读 agent.py Tool 层 + 实现 DateTimeTool

**目标**：理解 Tool 抽象层的设计原理。精读 agent.py 的 Tool 基类和 Calculator 实现。亲手写一个完整的新工具（DateTimeTool）并集成到 agent.py。今天不止是读代码——是写代码。

**预计时间**：3 小时（阅读 agent.py 50min + 编码 DateTimeTool 80min + 思考 20min ）

**你的当前状态**：
- DeepSeek API + Ollama 本地（qwen3.5:9b）两套环境均已就绪，smoke_test 通过
- 已完成 Function Calling 系统性学习——理解了结构化工具调用的"正确答案"
- agent.py 骨架代码已写好（Tool 基类 + Calculator + LLM 适配 + ReAct 循环），但还没仔细读过

---

**任务清单**：
#### 第一步：阅读 agent.py 的 Tool 层（约 50 分钟）

- [x] **打开 `agent.py`**，定位到第 1 层（Tool 基类，第 22-34 行）和第 2 层（CalculatorTool，第 37-61 行）

- [x] **带着三个问题读**：

  1. **为什么 Tool 只需要 `name`、`description`、`execute` 三个接口？**
     对照你刚跑的 Function Calling——`name`=FC 的 `"name"`、`description`=FC 的 `"description"`、`execute`=你的函数体。FC 用 JSON Schema 描述工具，ReAct 用 Python 类描述工具——**形式不同，本质都是"名称+描述+执行"三段式**
     - `name`：LLM 在 `Action: calculator` 中引用它 → 你的 `parse_response` 拿这个名字去 `self.tools` 字典查找
     - `description`：被拼到 SYSTEM_PROMPT 的 `{tool_descriptions}` 占位符里 → LLM 就靠这段文字判断"该不该用这个工具"
     - `execute`：LLM 只生成文本——真正做事的是你的代码。FC 和 ReAct 在这一点没区别

  2. **Calculator 的白名单过滤为什么必要？**
     ```python
     allowed = set("0123456789+-*/().,%^eE sqrtincopah ")
     ```
     `eval(user_input)` 不加白名单 = LLM 可以注入任意 Python 代码。如果 LLM 幻觉出 `Action Input: __import__('os').system('rm -rf /')`，不加过滤就真执行了。白名单是工具安全的第一道防线——和你笔记第 7 节的"最小权限原则"是同一件事

  3. **为什么这里用正则解析而不是 Function Calling？**
     因为你要先理解框架帮你做了什么。LangChain 的 AgentExecutor、LangGraph 的 ToolNode——它们底层做的事就是你下周要手写的正则解析+工具调度。你先手写一遍才知道框架的价值

- [x] **对照总结**：FC vs ReAct 工具定义的全链路对比（一行对照表，你已经懂了不需要写下来）

#### 第三步：亲手实现 DateTimeTool（约 80 分钟）

LLM 自己不知道现在是几点。这是 Agent 最基础也最容易被忽略的工具——没有它，Agent 永远活在训练数据的时间戳里。

- [x] **创建 `01-handwritten-react/datetime_tool.py`**：

  ```python
  """DateTimeTool——让 Agent 知道现在是几点了"""
  from agent import Tool       # 从你的 agent.py 导入基类
  from datetime import datetime

  class DateTimeTool(Tool):
      def __init__(self):
          super().__init__(
              name="datetime",
              description=(
                  "Get the current date, time, and day of week. "
                  "Use when the user asks about today's date, current time, "
                  "or what day it is. "
                  "Returns: formatted datetime string like '2026-06-09, Monday, 15:30:45 CST'. "
                  "Note: does NOT accept parameters. For tomorrow/yesterday/next week, "
                  "call this tool first to get today, then calculate manually."
              ),
          )

      def execute(self, input_str: str) -> str:
          now = datetime.now()
          return now.strftime("%Y-%m-%d, %A, %H:%M:%S") + " (local time)"
  ```

- [x] **单独测试**：在文件底部加 `if __name__ == "__main__":` → `python datetime_tool.py` 确认输出

- [x] **集成到 agent.py**：
  1. 顶部加 `from datetime_tool import DateTimeTool`
  2. 在 `create_agent()` 的 tools 列表中加入 `DateTimeTool()`
  3. 用 DeepSeek API 跑 agent，测试 LLM 能否在正确时机调用它

- [x] **思考题**（不要求写代码，但 Day 6 之前想清楚）：
  如果 LLM 需要明天的日期，当前 DateTimeTool 做不到（没参数）。你怎么改造它？给 execute 加一个 `days_offset` 参数？但 execute 只接受一个字符串——你怎么把多个参数塞进一个字符串里？**这就是 Function Calling 用结构化 JSON 传参而不是纯字符串的原因**。

**完成标准**：
- function_calling_demo.py 四个实验跑通，理解"FC 省掉了 parse_response 的脏活"
- DateTimeTool 从零写完、通过单独测试、集成到 agent.py 中可被 LLM 调用
- 能说出 Tool 基类的三个接口与 Function Calling JSON Schema 字段的对应关系

---

## 第2周：动手实现

### Day 6 — Prompt 模板 + ReAct 主循环

**目标**：理解并实现 Agent 的最核心——ReAct 循环。

**任务清单**：

- [x] **精读 `agent.py` 中的 `SYSTEM_PROMPT` 和 `SimpleReActAgent` 类**（约 130 行）
  - 带着以下问题读：
    1. 为什么 prompt 中要明确 `{tool_descriptions}` 和 `{max_steps}`？（提示：LLM 需要知道它能用什么工具、有多少步预算）
    2. `parse_response` 中 `re.search(r"Thought:\s*(.+)", ...)` 的正则为什么用 `(.+)` 而不是 `(.*)`？如果 LLM 输出了空 Thought 会怎样？
    3. 当 LLM 解析失败（"No action found"）时，代码做了什么？这个 fallback 为什么重要？
    4. 主循环中的 `messages.append(Observation...)` 为什么放在 `{"role": "user"}` 中？（这是理解 Agent 对话管理的关键设计决策）

- [x] **动手修改**（在理解基础上做一个小改动）：
  - 在 `run()` 方法中添加"连续 3 次解析失败则提前终止"的逻辑

- [x] **日志增强**：在每一步循环中增加打印当前 `messages` 列表的 token 估算（粗略方法：len(str(messages))/4），观察随着对话进行，context window 如何被一步步填满。

**完成标准**：能画出 ReAct 主循环的流程图（Thought→Action→Observation 循环 + Final Answer 出口 + 异常处理分支），并向自己解释每一步的输入输出。

---

### Day 7 — 完整工具链实现

**目标**：实现 Search / FileRead / FileWrite 三个工具并理解其设计约束。

**任务清单**：

- [x] **SearchTool 测试**：
  - 单独测试 `SearchTool().execute("Python Agent framework 2026")`，观察返回结果的格式和信息量
  - 为什么只返回 3 条结果、每条截断 200 字符？（提示：context window 预算有限）
  - 思考：如果 Agent 觉得搜索结果不够好，它的 ReAct 循环应该怎么做？

- [x] **FileReadTool / FileWriteTool 测试**：
  - 为什么 FileReadTool 限制了 2000 字符？（提示：非截断的大文件会直接撑爆 context window）
  - FileWriteTool 的 input 格式 `"filename|content"` 用 `|` 做分隔符——如果文件内容本身包含 `|`，这个设计有什么问题？你能想出一个更好的解决方案吗？
  - 创建一个测试文件，让 Agent 读取它并用计算器处理其中的数据

- [x] **新增一个工具（必做）**：
  - 实现一个 `DateTimeTool`：返回当前日期/时间/星期。这是 Agent 最基础但最容易被忽略的工具（LLM 自己不知道"现在是什么时间"）
  - 要求：`name`、`description`、`execute` 三要素完整，description 能让 LLM 正确决策

**完成标准**：4 个工具（Calculator + Search + FileRead/Write + DateTime）全部通过单独测试。

---

### Day 8 — 集成测试：跑通完整 ReAct 流程

**目标**：让 Agent 用多工具完成一个需要 3+ 步的复杂任务。

**任务清单**：

- [ ] **测试用例1（简单）**：
  ```bash
  python agent.py "What is the current time? Then calculate 3600 divided by 24."
  ```
  Agent 需要：DateTimeTool → CalculatorTool。验证多工具协同。

- [ ] **测试用例2（中等）**：
  ```bash
  python agent.py "Search for the population of Tokyo in 2024, then calculate what 15% of that number is."
  ```
  Agent 需要：SearchTool → CalculatorTool。验证"搜索结果→下游计算"的信息流动。

- [ ] **测试用例3（困难）**：
  ```bash
  python agent.py "Search for the top 3 programming languages in 2026. Write them to a file called languages.txt. Then read the file back and tell me which one you'd recommend for an AI engineer."
  ```
  Agent 需要：SearchTool → FileWriteTool → FileReadTool。验证 3+ 步完整工作流。

- [ ] **每个测试用例做完后记录**：
  - Agent 走了几步？
  - 哪一步的 Thought 最准确？哪一步明显瞎猜？
  - 如果有失败，失败的根本原因是什么？（格式解析？工具选错？上下文过长？）

- [ ] **尝试用不同模型跑同样的测试用例**（如果你配置了多个 API）：
  - DeepSeek-V3 vs GPT-4o-mini vs 本地 Qwen2.5-7B
  - 哪个模型的 Thought 最有洞察力？哪个模型的格式遵循最稳定？

**完成标准**：3 个测试用例全部通过（Agent 给出合理答案），并记录了每个用例的 Trace 日志。

---

### Day 9 — 压力测试：故意搞坏 Agent

**目标**：理解 Agent 的失败模式——这比成功运行更重要。

**任务清单**：

- [ ] **破坏性测试1 — 格式破坏**：
  - 临时修改 SYSTEM_PROMPT，去掉格式约束的那一段。观察 LLM 的输出变成什么样？为什么没有格式约束的 Agent 会"发疯"？
  - 将 temperature 从 0.0 调成 1.0，跑同样的测试用例。输出有没有出现之前没有的格式错误？

- [ ] **破坏性测试2 — 工具幻觉**：
  ```bash
  python agent.py "Send an email to john@example.com with the subject 'Hello'."
  ```
  Agent 没有 email 工具——它会怎么做？
  - 幻觉一个不存在的 Action？
  - 承认自己做不到？
  - 尝试用 FileWriteTool 代替？
  - 记录它的行为，思考：生产环境中如何防止这种情况？

- [ ] **破坏性测试3 — 死循环**：
  ```bash
  python agent.py "Calculate the meaning of life."
  ```
  Agent 大概率会陷入循环——观察它在哪一步开始重复、为什么跳不出来。
  思考：除了 max_steps，还有哪些方法可以检测和终止死循环？
  （提示：连续相同 Action 检测、Observation 相似度检测、步骤时长超限...）

- [ ] **破坏性测试4 — 上下文溢出**：
  ```bash
  python agent.py "Search for 10 different facts about artificial intelligence and calculate something with each one."
  ```
  这个任务会快速消耗 context window。观察 Agent 在第几步开始"忘记"之前的搜索结果？
  思考：生产环境中，如果 Agent 需要处理长任务，你需要设计什么样的记忆管理策略？

- [ ] **输出**：在 `notes/04-failure-modes.md` 中整理一份"Agent 失败模式清单"：
  | 失败模式 | 触发条件 | 生产环境对策 |
  |---------|---------|------------|
  | 格式解析失败 | temperature 过高/prompt 模糊 | 降低 temperature+强化格式约束 |
  | 工具幻觉 | 需要的工具不存在 | 预定义工具列表+Fallback 机制 |
  | 死循环 | LLM 卡在无效策略 | 连续相同 Action 检测 |
  | 上下文溢出 | 步数过多/content 过长 | 自动摘要+滑动窗口 |
  | ... | ... | ... |

**完成标准**：4 种失败模式全部复现，并能解释每种模式在生产环境中的对策。

---

### Day 10 — 反思笔记 + LangGraph 对比预告

**目标**：把两周的学习内化为自己的理解，并为下一阶段埋下伏笔。

**任务清单**：

- [ ] **写一篇反思笔记** `notes/05-week1-2-reflection.md`，包含：

  1. **我学到了什么**（3-5 条最关键的理解）：
     - 例："ReAct 不是魔法——它就是一个带工具调用的 while 循环，配上合适的 prompt 格式"
     - 例："工具的 description 是 LLM 决定用不用它的唯一信息来源——写得不好，Agent 就不会用"

  2. **我遇到了什么问题**（2-3 条真实的困惑）：
     - 例："为什么 parse_response 用正则而不是 JSON 解析？JSON Schema 不是更结构化吗？"
     - 把这些问题记下来——学 LangGraph 时你会得到答案

  3. **LangGraph 对比预告**（为第3周做准备）：
     - 目前的手写 Agent 有什么痛点？列出至少 5 个让你觉得"麻烦"的地方：
       - 手动管理 messages 列表（每次 append 很容易出错）
       - parse_response 用正则匹配，脆弱且不支持复杂格式
       - 一旦出错没有恢复机制（只能 retry 或放弃）
       - 流程只有顺序循环，无法表达"先做 A 再做 B 如果 C 则回 A"
       - 没有持久化（程序退出后对话历史全丢）
     - 这 5 个痛点，恰好是 LangGraph 要解决的核心问题。等第3周开始学时，拿这个清单出来对照。

  4. **给自己打分**（1-5 分，诚实评估）：
     | 能力维度 | 自评分 | 证据/理由 |
     |---------|:---:|------|
     | 能解释 ReAct 循环原理 | — | |
     | 能从零手写一个 Agent | — | |
     | 能独立实现一个新工具 | — | |
     | 能诊断 Agent 的失败原因 | — | |
     | 理解 Agent 设计的工程取舍 | — | |

- [ ] **清理和整理代码**：
  - 确保 `agent.py` 代码整洁，注释清晰
  - 确保所有笔记文件已写入 `notes/` 目录

**完成标准**：反思笔记完成 + 代码整洁可读。可以自信地回答："我知道 Agent 是什么、它为什么要这样设计、我自己能写一个。"

---

## 每日节奏建议

每天的学习流程：

```
Reading (1h)  →  Coding (1-1.5h)  →  Reflection (0.5h)
    ↓                  ↓                    ↓
 带着问题读        动手验证理解         写笔记内化
```

- **不要跳过的环节**：Reflection（0.5h 写笔记）。这是你从"看懂了"到"会了"的质变步骤。
- **遇到卡住的地方**：先自己 Debug 15 分钟 → 再看代码中的注释 → 再看官方文档 → 最后问 Claude/Google。先自己挣扎，框架的坑你踩过一次就永远不会忘。

---

## 本文档与其他文件的关系

```
01-handwritten-react/
├── TASK-PLAN.md          ← 你正在读的文件（日级任务计划）
├── README.md             ← 目录说明和设计概览
├── agent.py              ← ReAct Agent 完整代码（已写好骨架）
├── smoke_test.py         ← API 冒烟测试（Day 4 自己创建）
└── .env                  ← API 密钥（从 .env.example 复制后填入）
```

每完成一天的任务，在 TASK-PLAN.md 对应的 checklist 中打勾。两周后，这份文档就是你第1部分的学习档案。
