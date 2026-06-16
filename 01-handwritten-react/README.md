# 01-handwritten-react — 第1-2周：Agent 理论基础 + 手写 ReAct Agent

> **主任务计划**：[TASK-PLAN.md](TASK-PLAN.md) — 10 天的日级任务分解，先看这个
> **上级计划**：[../LEARNING-PLAN.md](../LEARNING-PLAN.md) 第1部分

---

## 本阶段目标

在接触任何框架之前，先理解 Agent 的设计原理，并用纯 Python 从零实现一个 ReAct Agent。**知道框架帮你做了什么，你才知道框架的价值在哪。**

## 文件清单

| 文件                             | 说明                                                        |
| ------------------------------ | --------------------------------------------------------- |
| [TASK-PLAN.md](TASK-PLAN.md)   | **主入口** — 10 天日级任务，每个任务的 checklist、目标、完成标准                |
| [agent.py](agent.py)           | ReAct Agent 完整实现（5 层：Tool → Prompt → Agent → LLM → Entry） |
| [smoke_test.py](smoke_test.py) | API 环境测试（Day 4 用）                                         |
| [.env.example](.env.example)   | API 密钥模板 → `cp .env.example .env` 填入真实 key                |

## 产出物（两周完成后应有）

```
01-handwritten-react/
├── agent.py              ✅ 可运行的 ReAct Agent
├── smoke_test.py         ✅ API 冒烟测试通过
└── .env                  ✅ API 密钥配置

notes/
├── 01-lilian-weng-agent.md   ✅ Lilian Weng 文章笔记
├── 02-react-paper.md         ✅ ReAct 论文笔记
├── 03-agent-survey-map.md    ✅ Agent 综述概念地图
├── 04-failure-modes.md       ✅ 压力测试失败模式清单
└── 05-week1-2-reflection.md  ✅ 两周反思 + 自评
```

## 运行

```bash
source venv/bin/activate
cd 01-handwritten-react

# 冒烟测试
python smoke_test.py

# 运行 Agent
python agent.py "What is 15% of 250?"

# 三个压力测试
python agent.py "Search for the top 3 programming languages and save them to a file"
python agent.py "Send an email to test@example.com"           # 没有 email 工具
python agent.py "Calculate the meaning of life"               # 死循环测试
```
