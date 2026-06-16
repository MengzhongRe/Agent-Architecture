# Agent 技术栈学习之旅

> 2026年6月启动 | 目标：3-4个月深度掌握 Agent 技术栈
> 硬件：RTX 5070 Ti 16GB
> 旗舰项目：个人知识库 Agent

---

## 长期指南

**所有学习内容、资源、产出标准请参见 [LEARNING-PLAN.md](LEARNING-PLAN.md)**——这份文档是你整个学习周期的主导航。每进入一个新模块前，先回头读一下对应部分的计划。

---

## 学习进度追踪

| 周次    | 日期   | 模块                |   状态   | 产出        |
| ----- | ---- | ----------------- | :----: | --------- |
| 1     | 6/6- | Agent 理论 + 环境搭建   | 🔄 进行中 | 文章笔记、代码骨架 |
| 2     | -    | 手写 ReAct Agent    |   ⬜    | -         |
| 3-5   | -    | LangGraph 深度学习    |   ⬜    | -         |
| 6-7   | -    | MCP + Multi-Agent |   ⬜    | -         |
| 8-9   | -    | 记忆系统              |   ⬜    | -         |
| 10-11 | -    | Agentic RAG       |   ⬜    | -         |
| 12    | -    | 评测与调试             |   ⬜    | -         |
| 13-14 | -    | 旗舰项目收尾            |   ⬜    | -         |

---

## 项目目录

```
agent-learning-journey/
├── LEARNING-PLAN.md          # 主计划文档（长期指南）
├── 01-handwritten-react/     # 手写 ReAct Agent
├── 02-langgraph/             # LangGraph 学习
├── 03-mcp-servers/           # MCP Server 开发
├── 04-multi-agent/           # Multi-Agent 系统
├── 05-memory/                # 记忆系统
├── 06-agentic-rag/           # Agentic RAG
├── 07-evaluation/            # 评测与调试
├── knowledge-vault/          # 旗舰项目：个人知识库 Agent
├── notes/                    # 阅读笔记
│   └── 01-lilian-weng-agent.md
└── venv/                     # Python 虚拟环境
```

---

## 快速启动

```bash
cd agent-learning-journey
source venv/bin/activate

# 第1-2周：运行手写 ReAct Agent
cd 01-handwritten-react
cp .env.example .env    # 编辑 .env 填入 API key
python agent.py "What is 15% of 250?"
```
