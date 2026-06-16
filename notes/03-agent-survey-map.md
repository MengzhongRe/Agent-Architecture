# Day 3 笔记：Agent 综述 — 应用分类与知识地图

> 日期：2026-06-08 | 文献：Xi et al. "The Rise and Potential of LLM-Based Agents: A Survey" (2023)
> 定位：将 Agent 应用全景收束为一张地图，定位个人知识库 Agent 的位置

---

## 目录

- [1. Section 4 应用分类总表](#1-section-4-应用分类总表)
- [2. 分类详解](#2-分类详解)
  - [2.1 Single-Agent：单智能体部署](#21-single-agent单智能体部署)
  - [2.2 Multi-Agent：多智能体交互](#22-multi-agent多智能体交互)
  - [2.3 Human-Agent：人机交互](#23-human-agent人机交互)
- [3. Agent 知识地图](#3-agent-知识地图)
- [4. 个人知识库 Agent 定位](#4-个人知识库-agent-定位)

---

## 1. Section 4 应用分类总表

| 一级类别 | 二级类别 | 核心目标 | 典型特征 | 论文中举例 |
|---|---|---|---|---|
| **Single Agent** | **Task-oriented** | 帮用户完成明确任务 | 指令理解、任务分解、环境交互、执行子任务 | WebAgent, Mind2Web, WebGum, WebArena, WebShop, WebGPT, PET |
| | **Innovation-oriented** | 辅助科研、创造、专业分析 | 借助领域工具、文档分析、代码/科学推理、实验辅助 | ChemCrow, ChatMOF, Boiko et al., Feldt et al. |
| | **Lifecycle-oriented** | 长期探索、持续学习、生存与技能积累 | open-world、生存任务、skill library、lifelong learning | Voyager, GITM, DEPS, Plan4MC |
| **Multi-Agent** | **Cooperative** | 通过分工合作提升效率和质量 | 多角色、信息共享、顺序/无序协作 | CAMEL, MetaGPT, ChatDev, AutoGen, AgentVerse |
| | **Adversarial** | 通过争论/竞争提升推理与决策质量 | debate、tit-for-tat、互相纠错 | ChatEval, Du et al., Xiong et al., Liang et al. |
| **Human-Agent** | **Instructor-Executor** | 人下指令/反馈，Agent 执行 | 人类监督、迭代修正、任务辅助 | Dona, Math Agents, HuatuoGPT, Zhongjing, LISSA, AssistGPT |
| | **Equal Partnership** | Agent 作为"近人类合作者"参与任务或交流 | 共情交流、平等协作、谈判/策略参与 | SAPIEN, FAIR Diplomacy, Liu et al., Lin et al. |

---

## 2. 分类详解

### 2.1 Single-Agent：单智能体部署

单个 LLM Agent 独立完成任务，是当前最常见的部署形态。

**Task-oriented（任务导向）**：用户给一个明确目标，Agent 通过指令理解 → 任务分解 → 工具调用 → 结果汇总完成。这是你下周手写的 ReAct Agent 和旗舰项目（个人知识库 Agent）同属的类别。典型系统包括 WebAgent（网页操作）、WebShop（在线购物）、WebGPT（搜索增强问答）。

**Innovation-oriented（创新导向）**：Agent 辅助科研和专业分析——不是替代研究者，而是放大研究者的能力。例如 ChemCrow（化学实验设计与分析）和 ChatMOF（材料科学文献挖掘）。这类 Agent 通常配备领域专用工具（分子模拟器、谱图分析 API 等）。**与你关联**：你作为逻辑学硕士，如果未来做形式化验证 Agent，就属于此类。

**Lifecycle-oriented（生命周期导向）**：Agent 在开放世界中长期自主运行——探索、学习新技能、积累经验。典型代表 Voyager（Minecraft 中的终身学习 Agent），它在游戏中自主探索、学会建造、不断积累技能库 (skill library)。这类 Agent 的核心技术挑战是"如何不遗忘已学技能的同时持续获取新能力"。

### 2.2 Multi-Agent：多智能体交互

多个 Agent 协作或对抗完成单个 Agent 难以独立处理的任务。

**Cooperative（协作式）**：多个 Agent 各司其职，通过信息共享和分工提升效率。典型系统：MetaGPT（软件公司模拟——产品经理 Agent、架构师 Agent、工程师 Agent 各司其职）、AutoGen（Microsoft 的多 Agent 对话框架）、ChatDev（通过 Agent 间对话生成软件项目）。**这是你第 7 周要深入学习的方向**——LangGraph 的 Supervisor-Worker 模式就是此类协作的工程实现。

**Adversarial（对抗式）**：Agent 之间互相辩论、质疑、纠错，通过对抗提升输出质量。例如 ChatEval（多个 LLM 互评对方的回答质量）、Du et al. 的辩论框架（两方辩论直到达成共识）。这类模式目前更多在研究阶段，生产场景中较少单独使用。

### 2.3 Human-Agent：人机交互

人类参与 Agent 执行循环的模式。

**Instructor-Executor（指令-执行范式）**：人类是"指挥者"，Agent 是"执行者"。人类下达指令、提供反馈、修正错误，Agent 执行操作。**这是你下周手写的 ReAct Agent 以及当前大多数 Agent 系统的范式**。在你第 2 周的 Human-in-the-Loop 审批工作流中，人类"审核"就是此类交互的体现。

**Equal Partnership（平等协作范式）**：Agent 作为"接近人类的合作者"参与任务——共情交流、策略协商、共同决策。这是更长期的研究方向，当前在实际生产中的应用较少。你的野心不必到这一步——先让 Agent 做好执行者。

---

## 3. Agent 知识地图

```
LLM Agent
├── Single-Agent
│   ├── Task-oriented (WebAgent, WebShop, WebGPT)
│   │   └── ← 你的 ReAct Agent (第2周) + 个人知识库 Agent (旗舰项目)
│   ├── Innovation-oriented (ChemCrow, ChatMOF)
│   │   └── ← 逻辑学延伸方向：形式化验证 Agent
│   └── Lifecycle-oriented (Voyager, GITM)
│       └── ← 你的旗舰项目也涉及（长期记忆 + 持续对话）
│
├── Multi-Agent
│   ├── Cooperative (MetaGPT, AutoGen, ChatDev, CAMEL)
│   │   └── ← 你的第7周：LangGraph Supervisor-Worker
│   └── Adversarial (ChatEval, Debate Framework)
│       └── ← 了解即可，当前不涉及
│
└── Human-Agent Interaction
    ├── Instructor-Executor (Math Agents, AssistGPT)
    │   └── ← 你的第2周：Human-in-the-Loop 审批工作流
    └── Equal Partnership (SAPIEN, FAIR Diplomacy)
        └── ← 长期研究，暂不涉及
```

---

## 4. 个人知识库 Agent 定位

你的旗舰项目在这张地图上的位置：

- **主类别**：Single-Agent / Task-oriented —— 用户给出知识管理任务（导入笔记、查询信息、关联发现），Agent 分解并执行
- **交叉类别**：涉及 Lifecycle-oriented 的长期记忆和持续对话特性——Agent 记住用户的偏好和知识演变
- **交互范式**：Instructor-Executor —— 你下指令，Agent 执行；同时在关键节点（删除笔记、修改知识关联）需要 Human-in-the-Loop 确认

未来可能的扩展方向：
- **Multi-Agent 扩展**：知识库 Agent 拆分为"入库 Agent"和"检索 Agent"，通过 Cooperative Multi-Agent 模式协作
- **Innovation-oriented 扩展**：集成逻辑推理引擎（如 Lean 4），从知识库 Agent 演进为辅助研究的推理 Agent

---

> **后续回看标记**：Section 6.2（Evaluation）— 第 12 周评测模块回看；Section 6.3（Security）— 旗舰项目开发时参考
