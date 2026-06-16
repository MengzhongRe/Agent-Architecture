# Agent 技术栈深度试水学习计划（3-4个月）

## 背景与定位

**已有基础**：Python/PyTorch、GPU基础知识、3个月 Transformer 核心组件理解 + PyTorch 手撕代码经验。中山大学逻辑学本硕在读。
**硬件**：MacBook Air M4 16GB（本地 Ollama qwen3.5:9b）+ RTX 5070 Ti 16GB（留做后续微调任务）。
**旗舰项目**：个人知识库 Agent（已选定）

**2026 年 6 月技术校准**：本计划基于 2026 年 6 月最新技术栈编写——LangGraph 1.2+（Command 动态路由、TimeoutPolicy、DeltaChannel）、MCP Stateless Spec (RC)（无状态协议、Tasks 长任务原语）。Agent 技术栈已从"探索期"进入"工业级生产"阶段，核心三角组合为 **LangGraph (编排) + MCP (工具/数据) + Pydantic (类型安全)**。

**目标定位**：以 **3-4 个月** 为周期，**深度优先**地系统性学习 Agent 技术栈：
- 验证这个方向是否适合自己（兴趣 + 能力匹配）
- 建立 Agent 技术的完整认知框架
- 产出 1-2 个有深度的可展示项目
- 达到"能独立设计和实现一个非平凡的 Agent 系统"的水平

**不做什么**：不追求就业就绪、不做后训练微调、不碰 CUDA/C++、不刷 LeetCode。

---

## 第1部分：Agent 理论基础（第1-2周）

**目标**：理解 Agent 为什么这样设计，建立概念框架。最重要的是——在接触任何框架之前，先用纯代码手写一个 ReAct Agent。

### 1.1 学习内容

- LLM-based Agent 的形式化定义：Agent = LLM + Planning + Memory + Tool Use
- ReAct 推理模式：Thought → Action → Observation → Thought 循环
- Plan-and-Execute vs ReAct 的适用场景
- Tool Use / Function Calling 的设计原理
- 逻辑学连接：Agent 规划的搜索空间与自动证明搜索的形式相似性

### 1.2 核心资源

**必读（按顺序）**：

| 序号  | 资源                                                                                                           | 类型  | 为什么好                                                                                               |
| :-: | ------------------------------------------------------------------------------------------------------------ | --- | -------------------------------------------------------------------------------------------------- |
|  1  | [Lilian Weng: "LLM Powered Autonomous Agents"](https://lilianweng.github.io/posts/2023-06-23-agent/)         | 博客  | **Agent 入门最好的单篇文章，没有之一**。OpenAI 研究员写，把 Agent = Planning + Memory + Tool Use 的框架讲得极其清晰。全篇约 40 分钟读完。 |
|  2  | [ReAct 论文](https://arxiv.org/abs/2210.03629) (Yao et al., 2023)                                              | 论文  | Agent 推理策略的奠基论文。不需要从头读到尾，重点读 Section 2-4 的 ReAct 方法论和实验设计。                                         |
|  3  | ["The Rise and Potential of LLM-Based Agents: A Survey"](https://arxiv.org/abs/2309.07864) (Xi et al., 2023) | 综述  | 100+ 页的 Agent 综述。**不需要全读**。重点读 Section 3（Agent 架构）和 Section 4（Agent 应用），作为知识地图使用。                  |

**选读**：
- [Toolformer 论文](https://arxiv.org/abs/2302.04761) (Schick et al., 2023) — 如果有余力，理解 LLM 如何自主学习使用工具
- [Simon Willison: "Things we learned about LLMs in 2024"](https://simonwillison.net/2024/Dec/31/llms-in-2024/) — 实战派视角，理解 LLM 的实际能力和局限性

### 1.3 动手：从零实现 ReAct Agent（本周的核心产出）

**任务**：不依赖任何 Agent 框架（不用 LangChain/LangGraph），只用 `openai` Python SDK 或本地模型 API，手写一个 ReAct Agent。

**要求**：
- 手动实现 Thought → Action → Observation 循环
- 支持至少 3 个工具：计算器、搜索（Tavily API 或 DuckDuckGo）、文件读写
- 设计合理的停止条件（避免死循环）
- 处理工具调用失败的情况

**参考代码结构**：
```python
# 核心循环（伪代码思路）
system_prompt = """You are an agent. Respond in the format:
Thought: <your reasoning>
Action: <tool_name>
Action Input: <parameters>
... (after observation):
Thought: <your reasoning>
Final Answer: <your response>
"""

while not finished and steps < max_steps:
    response = llm.generate(system_prompt + history)
    thought, action, action_input = parse(response)
    observation = execute_tool(action, action_input)
    history.append(observation)
```

**为什么这个练习重要**：做完你会理解 LangChain/LangGraph 到底帮你解决了什么问题——State 管理、工具路由、循环控制、错误恢复。这些框架不是魔法，而是工程抽象。

### 第1部分产出
- 一个可运行的纯手写 ReAct Agent（GitHub repo）
- 3 篇论文/博客的阅读笔记
- 对 Agent 架构的直觉理解（不是调包经验）

---

## 第2部分：LangGraph 1.2+ 深度学习（第3-5周）

**目标**：掌握 LangGraph 1.2 的最新 API——不做"调包侠"，理解工业级 Agent 编排框架的核心设计。

> **2026 年技术校准**：LangGraph 1.0（2025 年底发布）和 1.2（2026 年 5 月发布）带来了几个关键变化。Conditional Edge（条件边）的大量样板代码已被 **Command 模式**替代；**TimeoutPolicy** 和 Per-Node Error Handler 原生支持重试和 Saga 补偿；**DeltaChannel** 默认启用增量 Checkpointing。Pregel 源码阅读的优先级降低——你更需要理解新 API 的设计范式和最佳实践。

### 2.1 学习内容

- StateGraph 核心概念：State（Pydantic v2 类型校验）、Node（含 TimeoutPolicy 和 Error Handler 配置）、Command 动态路由（替代大部分 Conditional Edge）
- Checkpointing 与 DeltaChannel：增量状态存储——只在 Checkpoint 中保存每次交互的 Diff，而非整个 messages 列表的完整拷贝。长对话场景下内存占用大幅降低
- Human-in-the-Loop：`interrupt` 机制 + Command 模式的 resume 流程
- Subgraph 与 Agent 层级嵌套
- ~~Pregel 源码精读~~ → 降级为选读。LangGraph 1.2 的 API 抽象层已经足够成熟，直接理解 Command/Node/Edge 的语义即可

### 2.2 核心资源

| 序号 | 资源 | 类型 | 为什么好 |
|:---:|------|------|------|
| 1 | [LangGraph 官方文档 - Quick Start](https://langchain-ai.github.io/langgraph/tutorials/introduction/) | 文档 | 官方 tutorial 质量很高。2026 年版本的示例已默认使用 Command 模式和 Pydantic State。 |
| 2 | [DeepLearning.AI: "AI Agents in LangGraph"](https://www.deeplearning.ai/short-courses/ai-agents-in-langgraph/) | 课程 | Harrison Chase 亲讲，免费短课程，1-2 小时。 |
| 3 | [LangGraph: Command 模式文档](https://langchain-ai.github.io/langgraph/how-tos/command/) | 文档 | **2026 年新增**。节点内 `Command(goto=..., update=...)` 替代繁琐的 Conditional Edge——这是 1.2 最重要的 API 变化 |
| 4 | [LangGraph: TimeoutPolicy 文档](https://langchain-ai.github.io/langgraph/how-tos/timeout/) | 文档 | **2026 年新增**。在 `add_node` 时配置超时策略和 Per-Node 错误处理器——工具调用超时后自动流转到回滚或重试节点 |
| 5 | [LangGraph Concept Guide - DeltaChannel](https://langchain-ai.github.io/langgraph/concepts/low_level/#channels) | 文档 | 理解增量 Checkpointing——LangGraph 1.2 默认使用 DeltaChannel，只保存增量 Diff |
| 6 | [LangGraph 官方示例: "Agent Supervisor"](https://github.com/langchain-ai/langgraph/tree/main/examples/multi_agent/agent_supervisor) | 代码 | Multi-Agent 的官方参考实现，Supervisor-Worker 模式的典范 |

### 2.3 动手实战

**实战#1（第3-4周）**：用 LangGraph 1.2 重写手写 ReAct Agent
- 用 **Pydantic v2** 定义 AgentState（类型安全——减少工具调用幻觉的最有效手段）
- 用 **Command 模式**替代大部分 Conditional Edge——对比手写版的条件分支，体会 1.2 API 简化了多少
- 使用 Checkpointing + DeltaChannel 实现对话历史持久化
- 写一篇对比分析（手写 vs LangGraph 1.2 的取舍）

**实战#2（第5周）**：Human-in-the-Loop 审批工作流 + TimeoutPolicy
- 构建"文档审批 Agent"：撰写→审核（interrupt）→修改→发布
- 在工具调用节点配置 **TimeoutPolicy**——模拟工具超时后的自动重试
- 使用 LangGraph Studio 可视化调试

### 第2部分产出
- LangGraph 1.2 版 ReAct Agent（Pydantic State + Command 路由）
- Human-in-the-Loop 审批工作流（含 TimeoutPolicy）
- 手写 vs LangGraph 1.2 对比分析博客

---

## 第3部分：MCP 2026 Stateless 协议 + Multi-Agent（第6-7周）

**目标**：掌握 MCP 协议的最新标准（Stateless Spec RC），开发无状态 MCP Server，理解 Multi-Agent 协作模式。

> **2026 年技术校准**：MCP 协议于 2025 年底正式捐赠给 Linux 基金会旗下的 Agentic AI Foundation，成为 OpenAI、Anthropic、Google、Microsoft 共同遵守的行业标准。2026 年 5/6 月发布了 **MCP Stateless Spec (Release Candidate)**——最重要的变化是协议彻底无状态化，不再需要 Session ID 绑定。同时引入了 **Tasks 原语**用于长耗时操作的异步事件通知。编写 MCP Server 时请直接采用最新 SDK，避免已废弃的旧版 Session 握手逻辑。

### 3.1 MCP 协议学习内容

- 协议架构：Client-Server 模型、**Stateless Transport**（无 Session ID 绑定，Server 可在普通负载均衡器后水平扩展）
- 三大原语：Tools、Resources、Prompts
- **Tasks 原语（新增）**：长耗时操作（如知识库的"关联发现""每周整理"）不应阻塞 HTTP 请求——使用 Tasks 异步机制进行事件通知
- MCP Server 开发（新版 Python SDK——避免旧版 Session 握手逻辑）
- 在 LangGraph Agent 中集成 MCP Client（LangChain MCP Adapter）

### 3.2 核心资源

| 序号  | 资源                                                                                                               | 类型  | 为什么好                                                                |
| :-: | ---------------------------------------------------------------------------------------------------------------- | --- | ------------------------------------------------------------------- |
|  1  | [MCP 官方文档](https://modelcontextprotocol.io/docs)                                                                 | 文档  | 协议规范。重点看 **Stateless Transport** 和 **Tasks Primitives**（2026 新增）。15 分钟了解全貌 |
|  2  | [MCP Python SDK - Quick Start](https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#quickstart) | 代码  | 使用**最新版 SDK**（避免旧版 Session 握手）。最简 Stateless Server 模板 |
|  3  | [MCP Python SDK 示例](https://github.com/modelcontextprotocol/python-sdk/tree/main/examples)                       | 代码  | 官方示例集。重点看 `simple_tool`、`sqlite`、`filesystem` 三个示例 |
|  4  | [LangChain MCP Adapter 文档](https://python.langchain.com/docs/integrations/tools/mcp/)                            | 文档  | 如何在 LangGraph Agent 中集成 MCP Client |
|  5  | [MCP Specification (Full)](https://spec.modelcontextprotocol.io/)                                                | 协议  | **不需要通读**。开发遇到协议细节问题时查阅 Stateless Transport 和 Tasks 章节 |

### 3.3 Multi-Agent 学习内容

- Agent 间通信模式：顺序传递、并行执行、层级委派（Supervisor-Worker）
- LangGraph 实现 Multi-Agent：多个 StateGraph 的嵌套与通信，使用 Command 模式跨 Agent 路由
- 快速了解 AutoGen / CrewAI 的设计理念（半天即可）

### 3.4 核心资源

| 序号 | 资源 | 类型 | 为什么好 |
|:---:|------|------|------|
| 1 | [LangGraph Multi-Agent 官方教程](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/) | 教程 | Supervisor-Worker 模式的官方教程，带完整代码 |
| 2 | [AutoGen 官方文档 - Core Concepts](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/index.html) | 文档 | 半天快速过一遍，了解对话驱动 vs 图驱动两种 Multi-Agent 范式 |
| 3 | [CrewAI 官方文档](https://docs.crewai.com/introduction) | 文档 | 角色驱动的 Multi-Agent 框架。快速浏览其角色定义和任务分配方式即可 |

**逻辑学连接**：Multi-Agent 系统中，Agent A 向 Agent B 委派任务时，隐含了认知逻辑中的"信念传递"假设——A 相信 B 有完成任务的能力。这跟模态逻辑中的 K(B) 算符直接对应。

### 3.5 动手实战

**MCP 实战（第6周）**：开发 3 个 Stateless MCP Server + Agent 集成
1. 文件系统 Server（读取/写入/搜索目录）——使用新版无状态 SDK
2. SQLite 数据库 Server（查询/建表/插入）
3. 自定义 Web API Server（封装公开 API）
4. 在 LangGraph Agent 中通过 MCP Adapter 集成上述工具

**Multi-Agent 实战（第7周）**：Multi-Agent 代码审查系统
- Coder Agent + Reviewer Agent，使用 LangGraph Supervisor-Worker + Command 路由编排
- 输出：一轮"生成→审查→修改→再审查"的完整工作流

### 第3部分产出
- 3 个 Stateless MCP Server（新版 SDK，无 Session 绑定）
- MCP + LangGraph 集成 Agent
- Multi-Agent 代码审查系统

---

## 第4部分：Agent 记忆系统（第8-9周）

**目标**：让 Agent 拥有"记性"，从单次对话变为持续交互的智能体。

### 4.1 学习内容

- 短期记忆：Conversation Buffer / Summary Memory / Sliding Window
- 长期记忆：向量数据库（Chroma/FAISS）+ 语义检索 + 时间衰减
- LangGraph 的 Store API（长期记忆）
- 记忆检索策略：相关性排序、重要性加权

### 4.2 核心资源

| 序号 | 资源 | 类型 | 为什么好 |
|:---:|------|------|------|
| 1 | [LangGraph: "Memory" 概念文档](https://langchain-ai.github.io/langgraph/concepts/memory/) | 文档 | LangGraph 对 Memory 的设计哲学：Short-term（Checkpointing）vs Long-term（Store）。清晰地区分了两种记忆。 |
| 2 | [LangGraph Store API How-to](https://langchain-ai.github.io/langgraph/how-tos/cross-thread-persistence/) | 文档 | 跨会话持久化的实战指南。Store API 的核心用法。 |
| 3 | [MemGPT 论文](https://arxiv.org/abs/2310.08560) (Packer et al., 2023) | 论文 | 把 LLM 的上下文管理类比为操作系统的虚拟内存管理。理解记忆分层的思想：主存（context window）↔ 磁盘（external storage）。读 Section 2-3。 |
| 4 | [Chroma 官方文档](https://docs.trychroma.com/docs/overview/introduction) | 文档 | 轻量级向量数据库，适合本地开发和实验。API 简洁直观。 |
| 5 | [Generative Agents 论文](https://arxiv.org/abs/2304.03442) (Park et al., 2023) | 论文 | Stanford 小镇实验的论文。Agent 记忆系统的经典：记忆流 → 检索 → 反思。回看 Section 3（记忆架构）即可。 |

### 4.3 动手实战

**实战（第8-9周）**：构建一个有"长期记性"的 Agent
- 使用 LangGraph Checkpointing 实现短期记忆（单次对话内）
- 使用 LangGraph Store + Chroma 实现长期记忆（跨对话）
- 设计记忆检索策略：语义相似度 + 时间衰减 + 重要性评分
- 验证：与 Agent 对话→关闭会话→新会话中 Agent 能回忆起上次对话的关键信息

### 第4部分产出
- 带持久化记忆的 Agent
- 记忆系统的设计文档（解释你的检索权重设计）

---

## 第5部分：Agentic RAG（第10-11周）

**目标**：从"静态 RAG"升级到"Agent 驱动的自适应 RAG"。

### 5.1 学习内容

- 静态 RAG vs Agentic RAG 的本质区别
- 自适应检索策略：Agent 自主判断是否需要检索、检索什么、怎么用检索结果
- RAG 基础组件：Embedding 选型、Chunking 策略、Re-ranking
- 了解 GraphRAG 概念（不深入实现）

### 5.2 核心资源

| 序号 | 资源 | 类型 | 为什么好 |
|:---:|------|------|------|
| 1 | [LlamaIndex: "Building an Agentic RAG Pipeline"](https://docs.llamaindex.ai/en/stable/understanding/agentic_rag/) | 文档 | LlamaIndex 对 Agentic RAG 的系统介绍。讲清楚了 Agent 在 RAG 中的三种角色：Router、Planner、Multi-hop Reasoner。 |
| 2 | [Pinecone: "RAG Chunking Strategies"](https://www.pinecone.io/learn/chunking-strategies/) | 博客 | 分块策略的最佳综述。Fixed-size、Semantic、Recursive、Agentic 四种方式各有优劣，这篇文章的对比表格值得截图保存。 |
| 3 | [Self-RAG 论文](https://arxiv.org/abs/2310.11511) (Asai et al., 2023) | 论文 | 让 LLM 自己决定什么时候检索、检索结果好不好、需不需要重新检索。核心思想：在每个生成步骤引入 Reflection Token。读 Section 3 方法论。 |
| 4 | [BGE Embedding 模型](https://huggingface.co/BAAI/bge-base-en-v1.5) + [BGE-M3](https://huggingface.co/BAAI/bge-m3) | 模型 | 中文 RAG 场景下最推荐的开源 Embedding 模型。BGE-M3 支持多语言 + 稠密+稀疏混合检索。 |
| 5 | [Ragas 文档](https://docs.ragas.io/en/stable/) | 工具 | RAG 系统的评估框架。Context Precision、Faithfulness、Answer Relevancy 三维指标设计得很好。 |

### 5.3 动手实战

**实战（第10-11周）**：构建 Agentic RAG 知识问答系统
- 首先搭建一个"静态 RAG"作为 baseline（固定检索→生成）
- 然后升级为 Agentic RAG：Agent 自主决定检索策略
  - 简单问题直接回答（不检索）
  - 事实性问题单轮检索
  - 需要多跳推理的问题多轮动态检索
- 使用 Ragas 对两个版本做对比评估
- 输出：静态 vs Agentic 的性能对比报告

### 第5部分产出
- Agentic RAG 知识问答系统
- 静态 vs Agentic 对比评估报告
- Chunking + Embedding 选型实验笔记

---

## 第6部分：Agent 评测与调试（第12周）

**目标**：学会评估和调试 Agent，让 Agent 从"能跑"到"可靠"。

### 6.1 学习内容

- 评测维度：任务成功率、工具选择准确率、执行效率、输出一致性
- 使用 LangSmith / LangFuse 进行 Agent Trace 追踪与调试
- Agent 常见失效模式与对策：死循环、幻觉工具调用、上下文溢出

### 6.2 核心资源

| 序号 | 资源 | 类型 | 为什么好 |
|:---:|------|------|------|
| 1 | [LangSmith: "Tracing" 文档](https://docs.smith.langchain.com/tracing) | 文档 | LangSmith 的核心功能。学会看 Trace 是调试 Agent 最重要的技能——你能看到每个 Node 的输入输出和执行时间。 |
| 2 | [LangFuse 开源项目](https://github.com/langfuse/langfuse) | 工具 | LangSmith 的开源替代品。如果你不想用 LangSmith 的付费 SaaS，自部署 LangFuse。 |
| 3 | [Lilian Weng: "Evaluating LLM-Powered Applications"](https://lilianweng.github.io/posts/2024-04-19-llm-evaluation/) | 博客 | 评测体系的系统梳理。重点读"Agent Evaluation"部分，讲清楚了为什么 Agent 评测比普通 LLM 评测难一个量级。 |

### 6.3 动手实战

- 为你之前构建的 Agent 搭建 LangSmith/LangFuse Trace 追踪
- 设计 10 个测试用例，覆盖正常路径和边界情况
- 写一份 Agent 评测报告：总体成功率、典型失败模式、改进建议

### 第6部分产出
- Agent 评测 + 调试 Pipeline
- 评测报告（含失败案例分析与改进方向）

---

## 第7部分：旗舰项目 — 个人知识库 Agent + 逻辑验证（贯穿+第13-14周集中收尾）

**目标**：构建一个完整、有深度的项目。这是 3-4 个月学习的最终答卷。

你日常积累的笔记、论文 PDF、书签、代码片段散落在各处。这个 Agent 将它们汇集为一个可对话的知识系统。

### 核心能力

- **入库**：拖入任意格式文件（Markdown/PDF/网页/代码）→ 自动解析、分块、向量化存储
- **问答**：用自然语言查询"我之前关于 XX 的笔记说了什么？"→ 检索+生成回答，标注来源
- **关联发现**：Agent 主动发现"你关于 A 的笔记和关于 B 的论文其实在讨论同一个问题"
- **定期整理**：每周自动生成"本周知识摘要"，帮你回顾学了什么、遗漏了什么
- **逻辑冲突检测（杀手级特性）**：半年前写的"观点 A 成立"和新论文里的"非 A 成立"——静态 RAG 察觉不到这种语义矛盾。你的 Agent 能：
  1. **冲突检测**（Inconsistency Detection）：在知识入库或问答时，"逻辑审判 Agent"（Verifier Node）自动介入
  2. **形式化转换**：LLM 将检索出的上下文转化为命题逻辑公式
  3. **相容性验证**（Consistency Check）：调用 Python `z3-solver` 做 SAT 求解——验证知识库中是否存在逻辑矛盾
  4. **前端告警**："系统发现：你今天的笔记与 3 个月前的笔记存在逻辑冲突，冲突点在于..."

### 技术栈整合

- LangGraph 1.2 做编排（Command 路由 + TimeoutPolicy + DeltaChannel）
- **Pydantic v2** 全量类型校验 State（类型安全——减少工具调用幻觉）
- MCP Stateless Server 提供工具（文件系统、PDF 解析、网页抓取）
- Chroma/FAISS 做向量存储与检索
- BGE-M3 做中文 Embedding
- Agentic RAG：Agent 自主决定检索策略
- Store API 做长期记忆
- **`z3-solver`**（Python SAT Solver）：逻辑一致性验证引擎
- 轻量知识图谱（可选）：NetworkX 构建概念关联

### 为什么这个项目辨识度极高

- 你自己就是用户，有真实的痛点和持续的改进动力
- **逻辑冲突检测是 GitHub 上的稀有特性**——它不仅展示了你对 LangGraph 复杂多 Agent 控制流的掌控，更完美彰显了你的逻辑学学术背景。任何一个面试官看到"用 SAT Solver 验证知识库一致性"都会记住你
- 跟你的学术身份（中山大学逻辑学硕士）契合，面试时讲起来真实、有说服力
- 可以逐渐演进为你整个研究生涯的工具链

### 项目开发节奏

- 第10-11周：设计架构 + 搭建骨架（入库/检索/问答基础闭环）
- 第12-13周：完善核心功能 + **集成 Verifier Node（逻辑冲突检测）**+ 使用 LangSmith Fleet 做端到端延迟和成本分析
- 第14周：打磨 README + 录 Demo + 写技术博客（逻辑学+大模型交叉主题）

### 产出

- GitHub Repo（含清晰 README、架构图、使用文档）
- 技术博客一篇（逻辑学+大模型交叉主题——学术工程双背景的最佳展示）
- 演示视频或 GIF

**项目管理建议**：第1周就建好 GitHub repo，每个学习阶段的产出都提交进去。第14周不是从零开始，而是把分散实现的模块整合为一个完整应用。

---

## 总体时间线（2026 年 6 月校准）

| 周次 | 模块 | 核心产出 | 2026 年技术重点 | 精力占比 |
|:---:|------|------|------|:---:|
| 1-2 | Agent 理论 + 手写 ReAct | 纯手写 ReAct Agent | 体会正则解析的痛苦——理解框架为什么存在 | 15% |
| 3-5 | LangGraph 1.2 深度学习 | LangGraph 版 Agent + HITL 审批流 | **Command 路由**、**TimeoutPolicy**、DeltaChannel、Pydantic State | 25% |
| 6-7 | MCP Stateless + Multi-Agent | 3 个 Stateless MCP Server + Multi-Agent 系统 | **无状态 SDK**（避免旧 Session 握手）、Tasks 原语 | 20% |
| 8-9 | 记忆系统 | 带长期记忆的 Agent | LangGraph Store + Chroma、记忆检索权重设计 | 15% |
| 10-11 | Agentic RAG | Agentic RAG + 静态对比评估 | Self-RAG 自适应检索 + **Pydantic 结构化输出** | 15% |
| 12-14 | 旗舰项目 + 评测 | GitHub Repo + 技术博客 | **逻辑冲突检测（Verifier Node + z3-solver）**、LangSmith Fleet 端到端分析 | 10% |

每周投入 **20-25 小时**（兼顾硕士学业）。

**2026 年核心技术三角**：**LangGraph 1.2 (编排) + MCP Stateless (工具/数据) + Pydantic v2 (类型安全)**。Dify/Coze 等低代码平台只做快速了解——不做主线。

---

## 选做模块（时间充裕时）

- **逻辑学延伸**：用 LangGraph 实现简单定理证明助手（自然语言→形式化命题→证明搜索→验证）。资源：[Lean 4 入门](https://leanprover.github.io/theorem_proving_in_lean4/) + [LeanDojo](https://leandojo.org/)（LLM + 定理证明的开源项目）
- **Dify/Coze 快速体验**：花 2-3 天用低代码平台搭一个应用，体会它们"能做什么"和"不能做什么"的边界
- **Agent 微调入门**：了解 Agent 训练数据格式（ReAct-style multiturn traces），用 [Unsloth](https://github.com/unslothai/unsloth)（最易用的 LoRA 微调工具）跑一次 Qwen2.5-7B 的工具调用微调
