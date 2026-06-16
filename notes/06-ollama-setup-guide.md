# Ollama 本地大模型部署指南（macOS）

> 日期：2026-06-09 | 硬件：MacBook Air M4 16GB 统一内存 + RTX 5070 Ti 16GB（eGPU，Mac 不支持）
> 目标：在 MacBook Air M4 上安装 Ollama，拉取并运行开源模型，作为 DeepSeek API 的本地备选
> 搜索数据截止：2026 年 6 月

---

## 目录

- [0. Ollama 是什么](#0-ollama-是什么)
- [1. 安装](#1-安装)
- [2. 模型选型与拉取（2026 年 6 月最新）](#2-模型选型与拉取2026-年-6-月最新)
- [3. 使用方式](#3-使用方式)
- [4. 在你的 Agent 代码中使用 Ollama](#4-在你的-agent-代码中使用-ollama)
- [5. 显存与性能](#5-显存与性能)
- [6. 注意事项](#6-注意事项)
- [7. 常用命令速查](#7-常用命令速查)
- [串讲：为什么是客户端-服务器架构？——三个设计问题](#串讲为什么是客户端-服务器架构三个设计问题)
- [Part 2：内部实现原理](#part-2内部实现原理)
  - [8. Ollama 本质：一个完整的本地推理运行时](#8-ollama-本质一个完整的本地推理运行时)
  - [9. 分层架构](#9-分层架构)
  - [10. 一次推理请求的完整生命周期](#10-一次推理请求的完整生命周期)
  - [11. 推理引擎：llama.cpp 与 Ollama Engine](#11-推理引擎llamacpp-与-ollama-engine)
    - [11.0 llama.cpp 是怎么到你电脑上的](#11.0-llamacpp-是怎么到你电脑上的以及它本质上是什么)
    - [11.0.1 权重量化 vs 运行时反量化 vs KV Cache 量化](#11.0.1-澄清权重量化-vs-运行时反量化-vs-kv-cache-量化)
    - [11.1 两种推理引擎](#11.1-两种推理引擎)
  - [12. 模型加载与显存管理](#12-模型加载与显存管理)
  - [13. KV Cache 管理](#13-kv-cache-管理)
  - [14. GGUF 格式与量化](#14-gguf-格式与量化)
  - [15. 请求调度](#15-请求调度)
  - [16. Ollama vs vLLM 定位差异](#16-ollama-vs-vllm-定位差异)
  - [17. 一句话总结](#17-一句话总结)
- [18. 参考来源](#18-参考来源)

---

## 0. Ollama 是什么

Ollama 是一个**本地 LLM 运行工具**——它把"下载模型、量化、加载到 GPU、提供 API 服务"这一整套流程封装成一个命令。类比：

| 你用过的                                                | Ollama 对应的                                              |
| --------------------------------------------------- | ------------------------------------------------------- |
| 调 DeepSeek API → `client.chat.completions.create()` | 调本地 Ollama API → 同样用 `client.chat.completions.create()` |
| DeepSeek 帮你管理模型                                     | 你自己管理模型文件                                               |
| 按 token 付费                                          | **免费**，但受限于你的 GPU 显存                                    |

核心价值：**离线可用、零 API 费用、数据不出本机**。代价：本地模型（7B-14B）的能力明显弱于 DeepSeek-V3 或 GPT-4o。

在你的学习计划中的定位：**DeepSeek API 主力 + Ollama 本地备选**。API 不可用时（断网、余额不足、深夜调试不想花钱）切到本地模型。

---

## 1. 安装

### 1.1 安装 Ollama

macOS 最简单的方式——Homebrew：

```bash
brew install ollama
```

如果没有 Homebrew，去 [ollama.com](https://ollama.com) 下载 macOS 安装包（.dmg），双击安装。

### 1.2 启动 Ollama 服务

安装完成后，Ollama 作为一个**后台服务**运行。有两种启动方式：

```bash
# 方式一：命令行启动（终端关闭后服务停止）
ollama serve

# 方式二：从 macOS 应用程序启动
# 在 Applications 中找到 Ollama 图标，双击。
# 菜单栏会出现一个羊驼图标 🦙，说明服务在后台运行
```

验证服务是否在运行：

```bash
curl http://localhost:11434/api/tags
# 返回 {"models": []} 表示服务正常，但还没拉取任何模型
```

### 1.3 Ollama 的端口

Ollama 默认监听 **`http://localhost:11434`**。这个地址就是你后续在代码中调用的 `OPENAI_BASE_URL`。

---

## 2. 模型选型与拉取（2026 年 6 月最新）

### 2.1 你的硬件画像

| 配置 | 数值 | 对 LLM 推理意味着什么 |
|---|---|---|
| 统一内存 | 16GB LPDDR5 | 系统 + 应用占用约 3-4GB。剩余约 **12GB** 供模型使用 |
| 芯片 | M4 (10 核 GPU) | Metal GPU 加速，Ollama 自动启用。无风扇，无噪音 |
| 存储 | 512GB SSD | 充足——一个 Q4 量化的 7B 模型约 4-5GB，多存几个没问题 |

**重要**：Apple Silicon Mac 的"统一内存"意味着 CPU 和 GPU **共享**这 16GB。模型加载到 GPU 推理时，占用的就是这同一块内存。这和 NVIDIA 独显（显存和系统内存分开）完全不同。

### 2.2 RTX 5070 Ti 能在 Mac 上用吗？

**不能。** Apple Silicon Mac 不支持 NVIDIA 外置 GPU（eGPU）——没有 NVIDIA 驱动。RTX 5070 Ti 16GB 只能在 Windows/Linux 上用。在 MacBook Air 上，Ollama 用的是内置 M4 芯片的 GPU（Metal）做推理。这对 7B-14B 模型来说完全够。5070 Ti 留到后续做 PyTorch/HuggingFace 微调时用。

### 2.3 你应该选哪些模型

以下基于 2026 年 6 月搜索结果，按你的硬件（M4 16GB）筛选。**Q4_K_M 量化**是 Ollama 默认格式，也是 sweet spot——质量和速度的平衡点。

#### 首选梯队（日常使用 + Agent 开发）

| 模型 | 参数量 | 显存占用 | 速度 | 中文 | Tool Calling | 推荐理由 |
|---|---|---|---|---|---|---|
| **Qwen3:8b** | 8B 稠密 | ~5GB | 25-35 tok/s | 优秀 | 较好 | **2026 年首选**——阿里最新开源，中文+Agent 双优 |
| **Qwen2.5:14b** | 14B 稠密 | ~9GB | 15-25 tok/s | 优秀 | 一般 | 中文推理天花板（16GB 下），Agent 原型够用 |
| **Qwen2.5-Coder:14b** | 14B 稠密 | ~9GB | 15-25 tok/s | 优秀 | 较好 | 代码生成最强本地模型（HumanEval 72.5%） |
| **DeepSeek-R1:8b** | 8B 稠密 | ~5GB | 25-35 tok/s | 优秀 | 不支持 | 推理链最长，适合多步推理任务。但输出冗长、慢 |
| **Phi-4:14b** | 14B 稠密 | ~9GB | 15-25 tok/s | 一般 | 一般 | 微软出品，数学/逻辑推理最强小模型（MATH 80.4%），MIT 协议 |

#### 备选梯队（特定场景）

| 模型 | 参数量 | 显存 | 特点 | 适用场景 |
|---|---|---|---|---|
| **Llama 3.3:8b** | 8B 稠密 | ~5GB | 128K 长上下文、生态最大、英文最优 | 需要长上下文 + 英文为主的场景 |
| **Gemma 3:12b** | 12B 稠密 | ~8GB | 多模态（文本+图像）、Google 出品 | 处理图片输入时 |
| **Qwen3-Coder:30b-A3B** | 30B MoE (仅 3B 激活) | ~8GB | MoE 架构——总参数大但激活参数少，推理快 | 极致 coding agent 体验（如果能拉下来） |
| **Mistral-Small:24b** | 24B 稠密 | ~14-16GB (Q4) | 128K 上下文、RAG 专用、**刚好塞进 16GB** | RAG 场景的最强本地模型 |

#### 不要选这些

| 模型 | 为什么不适合 |
|---|---|
| Qwen 72B / DeepSeek-V3 (非量化) | 40GB+，16GB 完全装不下 |
| Qwen3-235B (MoE) | 虽然只有 22B 激活，但总参数量巨大，需要 32GB+ |
| Llama 4 Scout | 10M 上下文但模型本身需要 32GB 内存 |

### 2.4 拉取命令

```bash
# 首选——中文 Agent 开发主力
ollama pull qwen3:8b

# 中文推理最强——16GB 刚好跑得动的天花板
ollama pull qwen2.5:14b

# 推理专用——数学/逻辑/多步任务
ollama pull deepseek-r1:8b

# 代码生成——如果你做 Coding Agent 项目
ollama pull qwen2.5-coder:14b

# 微软出品——逻辑推理最强小模型
ollama pull phi4:14b
```

**建议拉取顺序**：先 `qwen3:8b`（最稳妥、最常用），再按需拉 `qwen2.5:14b`（需要更强推理时）和 `deepseek-r1:8b`（需要长推理链时）。

### 2.5 验证

```bash
ollama list
# NAME                ID              SIZE      MODIFIED
# qwen3:8b            xxxxxxxxxxxx    4.9 GB    2 minutes ago
# qwen2.5:14b         xxxxxxxxxxxx    8.9 GB    1 hour ago
```

---

## 3. 使用方式

### 3.1 终端直接对话

```bash
# 最简单的交互——直接在终端里聊天
ollama run qwen2.5:7b

# 你会看到：
# >>> 你好
# 你好！有什么我可以帮你的吗？
#
# >>> 用 Python 写一个快速排序
# [输出代码...]
#
# >>> /bye    ← 退出对话
```

这是测试模型是否正常工作的最快方式。

### 3.2 单次问答（非交互）

```bash
ollama run qwen2.5:7b "用一句话解释什么是 Function Calling"
```

### 3.3 API 调用（与你调 DeepSeek 的方式完全一样）

Ollama 启动后，提供了**兼容 OpenAI SDK 的 API**。这意味着你之前写的所有代码只要改 `base_url` 和 `model` 参数，就能切到本地模型：

```bash
# 用 curl 测试
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

---

## 4. 在你的 Agent 代码中使用 Ollama

### 4.1 修改 .env 配置

```bash
# .env 中切换到本地 Ollama
OPENAI_API_KEY=ollama                      # Ollama 不验证 key，随便填
OPENAI_BASE_URL=http://localhost:11434/v1  # 注意末尾有 /v1
```

### 4.2 代码中的 model 名称

```python
# 调 DeepSeek API 时
MODEL = "deepseek-chat"

# 切换到本地 Ollama 时
MODEL = "qwen3:8b"        # 2026 年推荐——阿里最新开源，中文+Agent 双优
# MODEL = "qwen2.5:14b"   # 备选——需要更强推理能力时切换
# MODEL = "deepseek-r1:8b" # 备选——需要长推理链时切换
```

### 4.3 在你的 smoke_test.py 中测试

已经改好了一个常量——把 MODEL 改成 `"qwen2.5:7b"` 就能测试本地模型。但你当前的 `.env` 指向的是 DeepSeek API，所以需要切 `.env` 中的 `base_url`：

```bash
# .env 中注释掉 DeepSeek，启用 Ollama
# OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_BASE_URL=http://localhost:11434/v1
```

然后跑：

```bash
python smoke_test.py
# 输出中看到 model: qwen2.5:7b 就说明跑通了
```

### 4.4 注意：本地模型的 Function Calling 不可靠

7B 级别的模型对 Function Calling 的遵循度明显弱于 DeepSeek-V3 和 GPT-4o-mini。你在 Day 3 写的 `function_calling_demo.py` 如果用 Ollama 本地模型跑，可能出现：
- tool_choice 被忽略（LLM 直接用自然语言回答而不是调工具）
- 生成的 JSON 参数格式错误
- 多工具选择时选错工具

**建议**：Function Calling 练习用 DeepSeek API。Ollama 本地模型用于**纯文本对话**和**ReAct 文本格式**的场景——你下周手写 ReAct Agent 时，文本格式的工具调用不依赖模型的 tool calling 能力，本地模型一样能用。

---

## 5. 显存与性能

### 5.1 Apple Silicon 统一内存的特殊性

MacBook Air M4 使用**统一内存架构**——CPU 和 GPU 共享同一块 16GB 内存。这意味着：

- 系统 macOS + 日常应用占用约 3-4GB
- 留给模型的实际可用内存约 **12GB**
- 这 12GB 不是"显存"，CPU 和 GPU 同时用它。模型加载到 GPU 推理时，占用的就是这块

这与 NVIDIA 独立显卡（显存和系统内存分开）完全不同。Ollama 在 Apple Silicon 上自动使用 Metal GPU 加速——不需要额外配置。

### 5.2 M4 MacBook Air 16GB 实测性能

| 模型 | 量化 | 占用 | 速度 | 上下文限制 |
|---|---|---|---|---|
| Qwen3:8b / DeepSeek-R1:8b | Q4_K_M | ~5GB | **25-35 tok/s** | 4K-8K（常规）/ 50K（TurboQuant） |
| Qwen2.5:14b / Phi-4:14b | Q4_K_M | ~9GB | **15-25 tok/s** | 4K-8K |
| Mistral-Small:24b | Q4_K_M | ~14-16GB | **8-15 tok/s** | 4K（刚好塞进，系统会压缩内存） |

**关键数据**：
- M4 芯片运行 7B-8B 模型（Q4 量化）：25-35 tokens/秒——流畅可接受
- 无风扇设计，静默运行。温度约 50-55°C。长时间高负载可能触发降频（速度降到 ~15 tok/s）
- 续航影响：本地 LLM 推理下约 9-10 小时（vs 闲置 15-18 小时）

### 5.3 突破上下文限制：TurboQuant

常规情况下，16GB Mac 上 8B 模型的上下文窗口只能开到 4K-8K tokens。但 **Google TurboQuant (TQ)**——一种 KV Cache 实时压缩算法——可以把这个限制推到 **50,000 tokens**。

```text
常规：Qwen3 8B + 16GB → 上下文 ~4K tokens
TurboQuant：Qwen3 8B + 16GB → 上下文 ~50K tokens ← 3 倍速度，10 倍上下文
```

TurboQuant 已被集成到一些 Ollama 替代品中（Atomic Chat、oMLX、llama.cpp TQ 分支）。你目前用标准 Ollama 就够——Agent 原型开发通常不需要超长上下文。等旗舰项目（个人知识库 Agent）阶段需要处理长文档时再考虑切到支持 TQ 的工具。

### 5.4 Ollama 模型生命周期

```bash
# 查看当前加载到内存的模型
ollama ps
# NAME            ID              SIZE      PROCESSOR    UNTIL
# qwen3:8b        xxxxxxxx        5.1 GB    100% GPU    4 minutes from now
```

模型默认在内存中保留 **5 分钟**。5 分钟内没有新请求，自动卸载释放内存。下次请求重新加载（约 5-10 秒冷启动延迟）。调试期间建议拉长：

```bash
# 首次启动时设置保留 1 小时
ollama serve &
export OLLAMA_KEEP_ALIVE=1h
ollama run qwen3:8b "测试"
```

---

## 6. 注意事项

### 6.1 冷启动延迟

模型从磁盘加载到 GPU 需要 5-10 秒。如果 5 分钟内没有请求，模型自动卸载。第一次调 API 时等几秒是正常的——不是卡死了。

### 6.2 模型存储位置

模型文件默认存储在 `~/.ollama/models/`。几个 7B 模型轻松占 20-30GB 磁盘。空间不够时：

```bash
# 查看所有已下载的模型
ollama list

# 删除不用的模型
ollama rm llama3.1:8b

# 查看磁盘占用
du -sh ~/.ollama/models/
```

### 6.3 不要在生产环境用本地小模型

7B 模型在 Agent 场景下有明显短板——推理链容易断裂、复杂指令遵循度低、多工具协调混乱。它们适合**本地原型开发和调试**，不适合生产环境。你的生产环境用 DeepSeek API（便宜 + 能力强）。

### 6.4 API key 随便填

Ollama 不验证 API key。你 `.env` 中的 `OPENAI_API_KEY=ollama` 是合法的——填什么都可以，但不能为空（OpenAI SDK 要求这个字段非空）。

### 6.5 模型名包含冒号

Ollama 的模型命名格式是 `name:tag`，如 `qwen2.5:7b`。在代码的 `model=` 参数中必须写完整的含冒号名称，否则找不到模型。

### 6.6 DeepSeek-R1 推理慢是正常的

DeepSeek-R1 系列被训练为在回答前生成**长推理链**（`<think>...</think>` 标签内的内容）。一个简单问题可能产生 500-1000 tokens 的推理链。这意味着：

- 同样的一个问题，Qwen3:8b 可能在 3 秒内回答完毕
- DeepSeek-R1:8b 可能要 **15-30 秒**——大部分时间在生成你看不到的推理链

这不是模型卡了，是它的设计如此。在需要多步推理的任务中（数学证明、复杂逻辑题），R1 的准确率更高；在简单问答中，Qwen3 更快更直接。

### 6.7 M4 MacBook Air 特有提示

- **无风扇**：长时间推理（连续 10 分钟以上）可能触发被动降频。如果感觉变慢，休息 2-3 分钟让机身冷却
- **不要同时跑两个 14B**：一个 14B 模型占 9GB，两个同时驻留内存 = 18GB > 16GB → 系统用 swap 到 SSD，速度暴降
- **关闭不必要的浏览器标签和 IDE**：Chrome 吃内存，和 Ollama 抢同一块 16GB 统一内存
- **如果做长推理任务**：先用 DeepSeek API 验证思路是否正确，再用本地模型跑——省时间不是省钱的问题，是本地模型慢

---

## 7. 常用命令速查

```bash
# ---- 服务管理 ----
ollama serve                  # 启动服务（前台）
brew services start ollama    # 设为开机自启动

# ---- 模型管理 ----
ollama pull <model>           # 拉取模型
ollama list                   # 列出已下载的模型
ollama rm <model>             # 删除模型
ollama cp <src> <dst>         # 复制模型（用于备份自定义 Modelfile）
ollama show <model>           # 查看模型详细信息（参数量、量化方式、架构）

# ---- 使用 ----
ollama run <model>            # 交互式对话
ollama run <model> "prompt"   # 单次问答

# ---- 运行时 ----
ollama ps                     # 查看当前加载到内存的模型
```

---

> **下一步**：装好 Ollama、拉取 qwen2.5:7b、跑通 `smoke_test.py` 切到本地模型后，确认模型响应正常。然后回到 TASK-PLAN.md 继续 Day 4 的剩余任务（如果还没跑 Function Calling demo 的话）。
---

## 串讲：为什么是客户端-服务器架构？——三个设计问题

> Part 1 讲了"怎么用"，Part 2 要讲"内部怎么工作"。在进入内部原理之前，先回答一个承上启下的问题：**为什么 Ollama 选择 C/S 架构？** 这三个问题从你的 `new_agent.py` 直接引出。

### Q1: 为什么 Ollama 必须启动监听端口才能用？

表面回答是"它是一个服务"，真正原因有三个。

**1) 进程隔离：模型 crash 不炸应用**

```
┌──────────────────────┐     HTTP      ┌──────────────────────┐
│  你的 Python 脚本      │ ←----------→ │  Ollama Server (Go)   │
│  (Python 进程)        │   localhost   │  (独立 OS 进程)        │
│  ~50MB 内存           │              │  ~4-14GB GPU 显存      │
└──────────────────────┘              └──────────────────────┘
```

如果 Ollama 做成 `import ollama` 库：模型 4-14GB 权重直接加载在 Python 进程地址空间 → Python GC 与模型内存管理混在一起极易 OOM → 模型 crash（CUDA OOM、非法权重访问）则整个 Python 进程死掉。进程隔离意味着：**模型崩了，你的应用还活着，可以重试或降级。**

这与 Part 2 §9 中 Scheduler 和 Runner 分层的动机一致——Runner 运行在子进程里，llama.cpp 崩溃不会拖垮 Ollama 服务（详见 §11.1 子进程模式）。

**2) 模型生命周期管理：加载一次，常驻复用**

加载 7B 模型到 GPU 需 10-30 秒（磁盘读取 → 反量化 → 拷贝 VRAM → 初始化 KV Cache）。如果做成库，每次 `python agent.py` 都要重新加载——ReAct 循环跑 5 步可能只要 10 秒，但模型加载先等 30 秒冷启动。

Server 模式下**模型常驻 GPU 显存**（默认 keep-alive 5 分钟，配置详见 §5.4），启动时加载一次，后续所有请求直接复用。这正是推理服务器的核心价值。

**3) 多消费者共享同一份模型**

```
         ┌─────── agent.py (本学习项目)
Ollama ──┼─────── Open WebUI (聊天界面)
  Server ─┼─────── Continue.dev (IDE 补全插件)
         └─────── 其他开发工具
```

同一个加载好的模型被多个客户端复用，不需要每个工具各自加载一份——那会各自吃掉一份显存。§15 会详述调度器如何管理这些并发请求。

### Q2: 本地通信为什么还要走 HTTP + OpenAI SDK？

**1) HTTP 是进程间通信的"通用语"**

| 方案 | 问题 |
|------|------|
| 直接函数调用 (`import ollama`) | 见 Q1——无进程隔离，模型 crash 炸一切 |
| Unix Domain Socket | 仅 Unix，Windows 不支持；无现成生态工具 |
| gRPC | 需 proto 定义、代码生成、强类型耦合，生态重 |
| 共享内存 | 极复杂，需自行管理并发安全、序列化、内存布局 |

HTTP：全平台原生支持、生态成熟（curl/Postman/任何语言 HTTP 库）、人类可调试（文本协议可直接抓包）、原生流式支持（SSE / chunked transfer encoding，推理结果逐 token 推送）。

**2) OpenAI API 格式已成为事实标准——这是最关键的答案**

Ollama 选择兼容 OpenAI API schema，意味着：

```python
# 每行代码、每个参数对 DeepSeek API 和本地 Ollama 完全相同
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
response = client.chat.completions.create(
    model="qwen3.5:9b",
    messages=[...],
    temperature=0.0,
    tools=[...],          # Function calling — Ollama 也支持
    stream=True,          # 流式响应 — Ollama 也支持
)
```

**改一行 `base_url` 就能在云端模型和本地模型之间切换，不需要换 SDK、不需要改调用逻辑、不需要重新学习。** 这是 Ollama 能做大的关键设计决策——不是发明一个新协议，而是直接兼容已有生态。

**3) 不是"用 HTTP"，是"用了 HTTP 之后获得了整个生态"**

因为兼容 OpenAI API，这些工具全部零配置可用：
- LangChain / LangGraph / LlamaIndex
- Open WebUI、Chatbox、LobeChat 等聊天前端
- Continue.dev、Cursor 等 IDE 插件
- 所有语言的 OpenAI SDK（Python、JS、Go、Rust...）

### Q3: 能否把 Ollama 看作推理服务器，OpenAI SDK 看作客户端？

**完全可以——这个视角是理解整个 LLM 基础设施的钥匙。**

| 层 | Web 服务器类比 | LLM 推理类比 |
|----|-------------|------------|
| 服务器 | Nginx / Apache | **Ollama** — 管理模型生命周期、调度请求、返回结果 |
| 协议 | HTTP/1.1 | OpenAI-compatible HTTP API（REST + SSE 流式） |
| 客户端 | curl / 浏览器 / `requests` 库 | **OpenAI Python SDK** — 封装 HTTP 请求的客户端库 |
| 资源 | 静态文件 / 动态内容 | **模型权重 + KV Cache**（GPU 显存中的核心资产） |

关键洞察：**OpenAI SDK 本身不包含任何 AI 逻辑。** 它只是一个 HTTP 客户端库，负责：
1. 把你的 `messages` 序列化成 JSON
2. POST 到 `/v1/chat/completions`
3. 把返回的 JSON 反序列化成 Pydantic 对象（`response.choices[0].message.content`）
4. 处理重试、超时、streaming 的 SSE 解析

你完全可以不依赖它：

```python
# OpenAI SDK 的本质等价于这段 requests 代码
import requests, os
resp = requests.post(
    f"{os.getenv('OPENAI_BASE_URL')}/chat/completions",
    headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"},
    json={"model": "deepseek-chat", "messages": [{"role": "user", "content": "hi"}]},
)
print(resp.json()["choices"][0]["message"]["content"])
```

这和 `requests.get("https://api.github.com/repos/...")` 没有本质区别——都是 HTTP 客户端调用远程服务。区别只在于"服务端"恰好可以运行在同一台机器上。

**这个视角能解决的困惑**：

- "为什么 model 参数要填 deepseek-chat？" → 服务器端注册了哪些模型，客户端就请求哪个，就像 `GET /users/123` 里的 `123` 是服务端决定的
- "为什么 base_url 改一行就换模型？" → 你换的不是模型，是服务端地址，和换一个 API 网关没区别
- "为什么 Ollama 也能用 tool calling？" → Ollama 服务端实现了 OpenAI 的 tool calling 协议规范，客户端不需要知道服务端是 DeepSeek 还是 Ollama
- "LangChain 的 ChatOpenAI 为什么能同时对接 OpenAI 和 Ollama？" → 它只是一个更厚的 HTTP 客户端，只要服务端说同一种"方言"（OpenAI API schema），它就能调

### 架构全景

```
┌─────────────────────────────────────────────────────────────────┐
│                       你的 Agent 代码                             │
│  agent.run("What is 2+2?")                                       │
│    → llm.generate(messages)                                      │
│      → OpenAI SDK: serialize → HTTP POST → deserialize            │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/JSON (OpenAI API Schema)
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
   ┌──────────────────┐     ┌──────────────────────┐
   │  DeepSeek 云服务   │     │  Ollama (本地 Server)  │
   │  api.deepseek.com │     │  localhost:11434/v1   │
   │  模型: deepseek-v3 │     │  模型: qwen3.5:9b      │
   │  显存: 集群级       │     │  显存: M4 的统一内存     │
   └──────────────────┘     └──────────────────────┘
        按 token 付费              免费，本地运行

   ┌──────────────────────────────────────────────┐
   │  两者对 Agent 代码完全透明                     │
   │  改 base_url 一行，其余代码不变                │
   └──────────────────────────────────────────────┘
```

这个 C/S 架构不是 Ollama 的妥协，而是有意为之——它用 HTTP 进程边界换来了**隔离性、资源复用、生态兼容**，这三样是"直接把模型跑在进程里"永远做不到的。

> **下一步**：Part 2 将从 HTTP 请求到达开始，逐层拆解这个 Server 内部的完整链路——调度 → llama.cpp 子进程 forward → Metal GPU 执行 → 逐 token 返回。


---

## Part 2：内部实现原理

> 以下内容深入 Ollama 的工程架构和底层机制。理解这些不仅让你"会用"，更让你知道请求在整个软件栈中经历了什么——这对后续学 vLLM/SGLang 至关重要。

---

## 8. Ollama 本质：一个完整的本地推理运行时

前面 Part 1 用"本地 LLM 运行工具"来描述 Ollama。更精确的定义是：

> **Ollama 是一个本地推理运行时**——它封装了模型加载、量化、GPU 内存管理、KV Cache 管理、请求调度和 API 服务，对外暴露 OpenAI 兼容的 HTTP API。

它和 DeepSeek/OpenAI 的差别不是"有没有推理能力"——而是在**哪里推理**：

```
DeepSeek API：
  你的代码 → OpenAI SDK → HTTP → DeepSeek 数据中心 GPU → 返回

Ollama：
  你的代码 → OpenAI SDK → HTTP → localhost:11434 → 你 MacBook 的 GPU → 返回
                         ↑                    ↑
                    同样是 HTTP            同样是 GPU
                    但延迟=WAN             但延迟<1ms
```

Ollama **不是推理引擎本身**——它是对底层推理引擎的封装。真正执行 `forward()` 计算的是 llama.cpp 或 Apple MLX。Ollama 的角色是：管理模型文件、解析请求、编排推理、管理显存、提供 API。你可以把它理解为**本地版的"推理即服务"平台**——就像 DeepSeek 用 vLLM 管理他们的 GPU 集群，你用 Ollama 管理你的 M4 芯片。

**重要区分**：KV Cache 的分配、复用、量化、裁剪——这些操作的实际执行者是 **llama.cpp**（推理引擎），不是 Ollama。Ollama 只负责把 KV Cache 类型配置（f16/q8_0/q4_0）通过环境变量传给 llama.cpp 的启动参数，并在 Runner 卸载时回收显存。它没有一行代码操作 KV 张量本身。

### 8.1 推理引擎 vs 推理运行时/框架——概念辨析

你问"Ollama 算不算推理框架"——这个问题触及了一个精准的概念边界。理解它对你后续学 vLLM/SGLang 有直接帮助。

#### 核心区分标准

**谁写了 `forward()` 函数，谁就是推理引擎。** 推理引擎是实际执行 Transformer 前向传播的底层库——Attention、FFN、LayerNorm、层归一化、残差连接、token 采样。其余的所有东西——HTTP 服务、请求排队、Runner 生命周期管理、模型加载/卸载策略——都是推理运行时的职责。

```
推理运行时/框架 与 推理引擎 的责任边界

┌─────────────────────────────────────────────┐
│              推理运行时 / 框架                 │
│  ollama serve / vLLM API Server / SGLang     │
│  ┌───────────────────────────────────────┐   │
│  │ • HTTP API 服务                        │   │
│  │ • 请求排队与调度 (scheduler)            │   │
│  │ • Runner 生命周期管理 (启动/卸载/驱逐)  │   │
│  │ • 模型文件管理 (pull / list / rm)       │   │
│  │ • 并发控制 (parallel / queue)           │   │
│  │ • 显存预算估算 (GPU layer placement)    │   │
│  │ • 模型注册与发现 (Modelfile / GGUF)     │   │
│  └──────────────┬────────────────────────┘   │
│                 │ 子进程 / CGO / 内部调用       │
│  ┌──────────────▼────────────────────────┐   │
│  │           推理引擎                      │   │
│  │  llama.cpp / MLX / vLLM CUDA Kernels    │   │
│  │  ┌───────────────────────────────────┐ │   │
│  │  │ • Transformer forward() 计算        │ │   │
│  │  │ • KV Cache 分配/复用/量化/裁剪      │ │   │
│  │  │ • Tokenizer (tokenize/detokenize)   │ │   │
│  │  │ • 采样 (temperature/topK/topP)      │ │   │
│  │  │ • 量化反量化 (运行时精度转换)         │ │   │
│  │  │ • GPU 内核调用 (Metal/CUDA/ROCm)    │ │   │
│  │  └───────────────────────────────────┘ │   │
│  └────────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                    ↓ Metal / CUDA / ROCm API
┌─────────────────────────────────────────────┐
│               GPU 硬件                        │
│        M4 / H100 / MI300 / ...                │
└─────────────────────────────────────────────┘
```

#### 你的 Mac 上的实际情况

```
ollama run qwen3.5:9b "你好"

Ollama (推理运行时——Go 代码)
  ├── "qwen3.5:9b" → 查找 manifest → 定位 GGUF 文件
  ├── 检查 Runner 是否已加载 → 否 → 启动新 Runner
  ├── 构造子进程参数：
  │     --model ~/.ollama/models/blobs/sha256-xxx  (GGUF 路径)
  │     --ctx-size 4096          (上下文窗口)
  │     --n-gpu-layers 999       (全部放 GPU)
  │     --parallel 4             (并发数)
  │     --port 51234             (子进程监听端口)
  └── fork → llama-server 子进程启动
          ↓
llama.cpp (推理引擎——C++ 代码)
  ├── 解析 GGUF 格式 → 提取 metadata (架构、参数量、量化方式)
  ├── mmap 权重文件 → 虚拟地址映射，按需加载
  ├── 根据量化类型配置反量化内核 (Q4_K_M)
  ├── 根据 ctx-size 分配 KV Cache 内存块
  ├── 加载 tokenizer → tokenize("你好") → [108386, 105645, ...]
  ├── Prefill：15 个 token 并行 forward → 生成 KV Cache[0..14]
  ├── Decode loop：
  │     for each new token:
  │       Attention(Q_new, KV_Cache[0..N]) → logits → sample
  │       新 token 的 K,V 追加到 KV Cache 尾部
  │       if token == <EOS> or len >= max_tokens: break
  └── Detokenize → "你好！有什么可以帮你的吗？"
          ↓ HTTP SSE 逐 token 返回
Ollama (推理运行时)
  └── 收到 SSE chunk → 逐字打印到终端 (ollama run 模式)
      或 → 封装为 ChatCompletionChunk → 返回 HTTP 响应 (API 模式)
```

#### 各组件定位对照表

| 组件 | 定位 | 有无推理引擎 | 有无调度器 | 有无 API 服务 | 典型用户 |
|---|---|---|---|---|---|
| **llama.cpp** | 推理引擎 | **有**（C++ forward、KV Cache、采样） | 无（需要外部编排） | 无 | 框架开发者、HPC 团队 |
| **MLX** | 推理引擎 | **有**（Apple Silicon 原生 GPU 内核） | 无 | 无 | macOS/iOS 应用开发者 |
| **GGML** | 推理引擎 | **有**（纯 C 实现，无外部依赖） | 无 | 无 | 嵌入式部署 |
| **Ollama** | **推理运行时** | 无——委托给 llama.cpp 或 MLX | **有**（Go Scheduler：refCount + 驱逐 + 排队） | **有**（OpenAI 兼容） | 个人开发者、Agent 原型 |
| **vLLM** | **推理框架**（全栈） | **有**（自研 CUDA 内核 + PagedAttention） | **有**（Continuous Batching） | **有**（OpenAI 兼容） | 生产级推理服务 |
| **SGLang** | **推理框架**（全栈） | **有**（自研 CUDA 内核 + RadixAttention） | **有**（RadixCache 调度） | **有**（OpenAI 兼容） | 生产级推理服务 |
| **LM Studio** | 推理运行时（GUI 封装） | 无——委托给 llama.cpp | 有（基本的加载/卸载） | 有（OpenAI 兼容） | 非技术用户 |

#### KV Cache 管理的责任归属

这是你反复追问的问题——现在有一个精确的答案：

| KV Cache 操作 | 谁做的 | 说明 |
|---|---|---|
| **KV Cache 显存的分配与回收** | llama.cpp（推理引擎） | 根据 `--ctx-size` 和量化类型 (`OLLAMA_KV_CACHE_TYPE`) 在模型加载时分配固定大小的显存区域 |
| **Prefill 阶段的 KV 生成** | llama.cpp（推理引擎） | 所有输入 token 的 K、V 在 prefill 阶段被一次并行计算并存入 Cache |
| **Decode 阶段的 KV 追加** | llama.cpp（推理引擎） | 每个新生成 token 的 K、V 被计算后追加到 Cache 尾部 |
| **同对话内的前缀复用** | llama.cpp（推理引擎） | 同一 Runner 内，下一轮请求的前缀 token 的 KV 直接复用，不重算 |
| **KV Cache 量化** | llama.cpp（推理引擎） | 根据配置在内部使用 q8_0 或 q4_0 精度存储 K、V 张量 |
| **KV Cache 驱逐 / Swapping** | llama.cpp（推理引擎） | 当 Cache 用满时的 LRU 驱逐或换出到 CPU 内存 |
| **KV Cache 配置传递** | Ollama（推理运行时） | 将 `OLLAMA_KV_CACHE_TYPE`、`OLLAMA_FLASH_ATTENTION`、`--ctx-size` 等环境变量翻译为 llama.cpp 的启动参数 |
| **Runner 卸载时的显存回收** | Ollama（推理运行时） | 在 Runner 生命周期结束时发送 unload 信号，llama.cpp 进程退出后 OS 回收所有显存 |

**结论**：KV Cache 的 95% 的操作在 llama.cpp 内部完成。Ollama 的角色仅限于"告诉 llama.cpp 用什么参数"和"什么时候启动/停止 llama.cpp"。

#### 为什么 Ollama 可以和 vLLM 并列被称为"推理框架"

两者在架构抽象层次上并列——都位于应用层之下、推理引擎之上：

```
应用层      ← 你的 agent.py、ChatGPT 网页版
────────────────────────────────────
推理运行时   ← Ollama (轻量) / vLLM (重量) / SGLang
────────────────────────────────────
推理引擎     ← llama.cpp / MLX / vLLM CUDA Kernels
────────────────────────────────────
GPU 硬件     ← M4 / H100 / MI300
```

区别在于：Ollama 的运行时和引擎是**解耦**的（Go Scheduler + 外部 llama.cpp 子进程），vLLM 的运行时和引擎是**一体**的（Python Scheduler + 自研 CUDA Kernel，在同一个进程内）。这决定了：

- Ollama 更容易安装（一行 `brew install`，引擎随安装包自带）
- vLLM 更高效（引擎和运行时共享同一进程内存，无跨进程通信开销）
- Ollama 更灵活（换引擎只需换子进程二进制——比如 2026 年从 CGO 迁移到 llama-server）
- vLLM 更深（PagedAttention 需要运行时和引擎紧密配合——KV Cache Block Table 在引擎中，但调度在运行时中）

---

## 9. 分层架构

Ollama 的源码（Go 语言编写）分为四层：

```
┌──────────────────────────────────────┐
│  第 1 层：CLI / HTTP API             │  ← 你交互的入口
│  ollama run / ollama pull /          │
│  POST :11434/v1/chat/completions     │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│  第 2 层：Orchestration (调度层)     │  ← Go 代码，核心调度逻辑
│  Scheduler (server/sched.go)          │
│  - Runner 生命周期管理                │
│  - 并发请求排队                      │
│  - 模型加载/卸载/驱逐策略            │
│  - GPU 显存感知的调度决策            │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│  第 3 层：Runner (推理执行层)        │  ← 子进程或 CGO 绑定
│  ┌─────────────┐  ┌───────────────┐  │
│  │ llama.cpp   │  │ Ollama Engine │  │  ← 两种 Runner 实现
│  │ (GGUF)      │  │ (GGML-native) │  │
│  └─────────────┘  └───────────────┘  │
│  + MLX (Apple Silicon 专用)           │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│  第 4 层：Hardware Backend (硬件层)  │
│  CUDA / ROCm / Metal / CPU           │  ← 实际执行矩阵乘法的地方
└──────────────────────────────────────┘
```

**各层职责**：

| 层 | 组件 | 职责 |
|---|---|---|
| CLI/API | `ollama serve`, REST API | 接收请求，返回响应 |
| 调度层 | `server/sched.go` | Runner 生命周期、并发管理、驱逐策略 |
| Runner | llama.cpp 子进程 / Ollama Engine | 加载模型、执行 forward、管理 KV Cache |
| 硬件后端 | CUDA/Metal/CPU | 调用底层矩阵乘法 API 执行实际计算 |

**为什么要分 Runner 和 Scheduler 两层**：Runner 运行在子进程里——如果 llama.cpp 因为显存不够或模型 bug 而崩溃，只死掉一个 Runner 子进程，不会拖垮整个 Ollama 服务。进程隔离提供了容错性。

---

## 10. 一次推理请求的完整生命周期

从你键入 `ollama run qwen3.5:9b "你好"` 到终端打印回复，经历了以下完整链路：

**阶段 1：请求到达**

```text
ollama run qwen3.5:9b "你好"
    ↓ CLI 通过 Unix socket 发给 ollama daemon 进程
daemon 收到请求 → 创建 LlmRequest 对象
    ↓ 检查 model "qwen3.5:9b" 是否已在内存中
```

**阶段 2：调度决策**（`server/sched.go`）

调度器检查 `loaded` map 中是否有该模型的 Runner：

- **已在内存**（5 分钟内有请求命中）→ 直接复用，跳到阶段 3
- **不在内存** → 需要加载。检查是否需要驱逐旧模型（当 `OLLAMA_MAX_LOADED_MODELS` 达到上限时，选一个 `refCount==0` 的 Runner 卸载）
- **Runner 参数不匹配**（如上次用 4K 上下文，这次需要 8K）→ `needsReload()` 返回 true → 重新加载

**阶段 3：Runner 启动与模型加载**（见第 12 节详述）

```text
调度器为 Runner 分配一个随机端口
    ↓
构造 llama.cpp 启动参数：
  --model /path/to/gguf
  --n-gpu-layers 36       ← GPU 层数，根据可用显存自动计算
  --ctx-size 4096         ← 上下文窗口大小
  --parallel 1            ← 并发请求数
  --port <random>         ← 子进程监听端口
    ↓
fork 子进程 → llama.cpp 加载 GGUF → mmap 权重 → 分配 KV Cache → 启动 HTTP 服务
```

**(2026 年 3 月架构变更)**：Ollama 正在将推理引擎从 vendored CGO 代码迁移到标准 `llama-server` 子进程。GGUF 模型统一走 `llama-server`；Safetensor 模型走 MLX (Apple Silicon)。这个变更让你的 Ollama 在每次升级时能更快地获得 llama.cpp 上游的新特性。

**阶段 4：推理执行**

```text
"你好"（原始 UTF-8 字符串）
    ↓
Tokenizer（和模型同一个 GGUF 文件中的 tokenizer 配置）
    ↓
[101, 204, 302, ...]  ← token IDs，如 15 个 token
    ↓
预填充 (Prefill)：
  15 个 token 一次性送入 Transformer
  并行计算所有 15 个位置的 K、V → 存入 KV Cache
  生成第 1 个新 token
    ↓
逐 token 生成 (Decode)：
  while 新 token ≠ <EOS> and len < max_tokens:
      新 token → 只算 1 个位置的 K、V → 追加到 KV Cache
      Attention(Q_new, KV_Cache_all) → logits → sample → 下一个 token
    ↓
Detokenizer：token IDs → UTF-8 字符串 "你好！有什么可以帮你的吗？"
    ↓
通过 HTTP SSE 逐 token 返回给 ollama daemon → CLI 逐字打印
```

**阶段 5：等待与卸载**

```text
响应完成 → Runner 进程继续存活
    ↓
启动 keep-alive 计时器（默认 5 分钟）
    ↓
计时器到期 → 调度器发送 unload 信号 → Runner 进程退出 → KV Cache 释放 → 显存回收
```

---

## 11. 推理引擎：llama.cpp 与 Ollama Engine

### 11.0 llama.cpp 是怎么到你电脑上的——以及它本质上是什么

你只敲了 `brew install ollama`，但 Ollama 内部用 llama.cpp 做推理。那 llama.cpp 是怎么来的？**不是你单独装的——它是 Ollama 打包带进来的。**

```
brew install ollama
  → 下载 Ollama.app (macOS bundle)
    → bundle 内自带 llama-server 二进制 (llama.cpp 编译产物)
```

Ollama.app 的 Resources 目录里藏着一个 `llama-server` 可执行文件——这就是 llama.cpp 项目编译出来的推理引擎。Ollama 启动时 `fork` + `exec` 这个二进制作为子进程。你没装过 llama.cpp，也不需要单独装——它随 Ollama 更新而更新。

**llama.cpp 本质上是什么？** 它是一个纯 C/C++ 程序，没有 Python、没有 pip、没有外部依赖。编译出来就是一个独立的可执行文件——和你熟悉的 PyTorch/Transformers 是两条完全不同的技术路线：

| | PyTorch / Transformers | llama.cpp |
|---|---|---|
| **语言** | Python + C++ (libtorch) | 纯 C/C++ |
| **运行方式** | `python script.py` → Python 解释器 → C 扩展 | 编译成独立二进制 → 直接运行 |
| **依赖** | `pip install torch transformers` (几百 MB) | 零外部依赖（静态链接） |
| **GPU 后端** | CUDA (NVIDIA 专用) / MPS (macOS, 功能有限) | Metal (Apple Silicon 原生)、CUDA、ROCm、Vulkan、CPU |
| **模型格式** | PyTorch checkpoint (`.pt` / safetensors) | GGUF 单文件 |
| **定位** | 研究/训练框架（`autograd`、优化器、数据加载） | 纯推理引擎（只管 forward，不管训练） |

llama.cpp 不只是一个"量化推理库"——它是一个完整自包含的推理引擎：tokenizer（用 SentencePiece/BPE 子集重新实现）、模型加载（解析 GGUF）、forward 计算（手写 Metal/CUDA 内核）、KV Cache 管理（分配、复用、量化、驱逐）、采样（temperature/topK/topP）——全部在 C++ 里完成，不依赖 Python 生态的任何东西。

**为什么用 C++ 而不是 Python？** 因为推理是纯计算——`matmul`、`softmax`、`layernorm`，不需要 Python 的灵活性。C++ 编译成原生机器码，没有 Python 解释器开销，没有 GIL，可以在消费级硬件上榨出每一分性能。这就是为什么同样是 Q4_K_M 量化的 9B 模型，llama.cpp 在 M4 上能跑到 30-40 token/s，而 PyTorch + MPS 可能只有 10-15 token/s。

### 11.0.1 澄清：权重量化 vs 运行时反量化 vs KV Cache 量化

你的困惑很精准：下载的 GGUF 文件已经是 6.5GB（Q4_K_M 量化好的），那运行时 Ollama 还"量化"什么？

**答案是：运行时不做权重量化，做的是两件完全不同的事——反量化 + KV Cache 量化。** 这三者容易混在一起，但它们的时间点和对象完全不同：

```
       权重量化                 运行时反量化              KV Cache 量化
    (模型发布时)              (每次 forward)            (运行时，可选)
    
  f16 权重 → 4-bit          4-bit 权重 → f16          K,V 张量 → q8_0/q4_0
  存进 GGUF 文件            临时解压喂给 GPU           降低 KV Cache 显存
  
  只做一次                   每个 token 都做            推理过程中持续做
  你下载前就完成了            你感受不到                  你用 OLLAMA_KV_CACHE_TYPE 控制
```

**权重量化**：模型发布者（如 Qwen 团队或 Ollama 官方）用 Q4_K_M 算法把原始 f16 权重压缩到 4-bit，打包进 GGUF 文件。你 `ollama pull` 下载的就是这个已经量化好的文件。6.5GB = 9B × 4.5 bit/param（Q4_K_M 的平均位宽含 overhead）÷ 8 + tokenizer + metadata。**你的计算完全正确。**

**运行时反量化**：GPU 的矩阵乘法单元只能算 f16（或 bf16），不能直接算 4-bit。所以每次 forward 时，llama.cpp 会把当前层需要的权重从 4-bit **解压回 f16**，算完 Attention/FFN 立刻扔掉，再解压下一层。这个反量化用 Metal Shader 在 GPU 上做，额外开销极小（< 3% 推理时间）。**它是 Q4_K_M 块状量化的设计要点**——反量化只在 32 个权重的子块内做，这 32 个值共享一个 f16 scale，一条 GPU 指令就完成。

**KV Cache 量化**：这是 `OLLAMA_KV_CACHE_TYPE` 环境变量控制的东西，和模型权重毫无关系。KV Cache 存储的是你输入文本经过 forward 后产生的 K、V 张量——这是推理过程中**新生成**的数据，不在你下载的 GGUF 文件里。你可以选择用 f16（最高精度）、q8_0（推荐）或 q4_0（最省显存）来存这些 K、V 值。9B 模型 5000 token 对话：f16 KV Cache ≈ 3GB，q8_0 ≈ 1.5GB，q4_0 ≈ 0.75GB。

**三者总结**：

| | 对象 | 何时 | 谁做的 | 你控制 |
|---|---|---|---|---|
| **权重量化** | 模型权重（f16 → 4-bit） | 模型发布时 | 模型发布者 | 不能——你下载的就是量化好的 |
| **运行时反量化** | 模型权重（4-bit → f16） | 每次 forward | llama.cpp Metal Shader | 不能——自动发生 |
| **KV Cache 量化** | K,V 张量（f16 → q8_0/q4_0） | 推理时 | llama.cpp | 能——`OLLAMA_KV_CACHE_TYPE` |

### 11.1 两种推理引擎

| 引擎 | 语言 | 适用模型 | 如何接入 |
|---|---|---|---|
| **llama.cpp / llama-server** | C++ | 大多数 GGUF 模型（Qwen、Llama、DeepSeek-R1 等） | 子进程 + HTTP |
| **Ollama Engine (Go-native)** | Go + CGO | 新版架构模型 (GPT-OSS 等) | CGO 直接调用 GGML |
| **MLX** | C++/Python | Apple Silicon 专用 (Safetensor 格式) | MLX runtime |

### llama.cpp 子进程模式（当前主流）

llama.cpp 不是动态链接库——它编译成一个独立的可执行文件 `llama-server`。Ollama daemon 通过 `fork` + `exec` 启动它作为子进程，两者通过 HTTP 通信。

**为什么是子进程而不是链接库**：

1. **进程隔离**：llama.cpp 如果因为显存爆炸或模型 bug 而崩溃，不会拖垮 Ollama daemon——只有那个 Runner 进程死掉
2. **独立的 GPU 上下文**：每个 Runner 有自己的 CUDA/Metal 上下文，互不干扰
3. **便于升级**：Ollama 升级 llama.cpp 版本时，只需替换子进程二进制，不需要重新编译整个 Go 代码

### llama.cpp 内部 GPU 后端支持

| 后端 | 对应的硬件 | macOS 上能用吗 |
|---|---|---|
| **Metal** | Apple Silicon GPU (M1/M2/M3/M4) | 能——Ollama 自动使用 |
| **CUDA** | NVIDIA GPU | 不能——macOS 不支持 NVIDIA 驱动 |
| **ROCm** | AMD GPU | 能——但 Mac 上的 AMD eGPU 支持有限 |
| **CPU (GGML)** | 纯 CPU 回退 | 能——如果模型太大 GPU 放不下，部分层回退到 CPU |

### 你的 MacBook 上的实际情况

当你在 M4 MacBook Air 上运行 `ollama run qwen3.5:9b` 时：
- Ollama 检测到 Metal GPU → 启动 llama-server 子进程 → llama.cpp 使用 Metal 后端
- `-ngl 999` 或自动计算——所有 36 层 transformer 加载到 Metal GPU
- 如果显存不够放全部层（如 14B 模型），剩余的层自动回退到 CPU（性能明显下降）

---

## 12. 模型加载与显存管理

### 12.1 模型加载的三个阶段

**阶段 A：文件定位**。Ollama 解析 `qwen3.5:9b` → 在 `~/.ollama/models/manifests/` 中找到 manifest → 定位所有 GGUF blob 文件（权重 + tokenizer + 配置）

**阶段 B：显存分配**。`EstimateGPULayers()` 函数计算多少层应该放在 GPU 上：

```text
总 GPU 显存 - 运行时开销(0.5GB) - KV Cache 预留 = 可用于权重的显存

对于你的 M4 16GB：
  16GB - 4GB(系统) - 0.5GB(运行时) - 3GB(KV Cache, 8K 上下文) = 8.5GB
  qwen3.5:9b Q4_K_M 权重 ≈ 6.5GB → 8.5GB > 6.5GB → 全放 GPU ✅
  qwen2.5:14b Q4_K_M 权重 ≈ 9GB → 8.5GB < 9GB → 部分层回退 CPU ⚠️
```

**阶段 C：内存映射（mmap）**。Ollama 默认使用 `mmap` 加载模型文件，而不是把整个文件读进内存：

```text
传统方式：
  读 6.6GB GGUF 文件 → 磁盘 → 完整读入 RAM（6.6GB）→ 从 RAM 拷贝到 GPU 显存（再 6.6GB）
  → 峰值占用 13.2GB + 加载时间 30 秒

mmap 方式：
  GGUF 文件 → 操作系统建立虚拟地址映射
  → GPU 需要某段权重时 → OS 自动从磁盘按页加载到 RAM
  → 只有被访问的页进入物理内存
  → 加载时间 2-3 秒，RAM 占用减少 60-70%
```

环境变量控制：`OLLAMA_MMAP=1`（默认开启）。

### 12.2 GPU 层自动分配

你不需要手动指定多少层放 GPU。Ollama 的调度器在加载模型时自动调用 `CalculateLayerPlacement()`，基于：
- 当前可用显存（减去已加载的其他 Runner）
- 模型每层的参数大小
- KV Cache 的预期大小（根据上下文长度计算）
- Flash Attention 是否开启（影响显存预算）

如果你在加载 qwen3.5:9b 的同时还有一个 14B 模型驻留在内存中（假设你在做 A/B 对比），后者的 Runner 在 `keep-alive` 期内不会被卸载——调度器会基于剩余显存重新计算新的 Runner 能放多少层到 GPU。

---

## 13. KV Cache 管理

这是和你上一份笔记（[07-kv-cache-and-inference-frameworks.md](07-kv-cache-and-inference-frameworks.md)）直接连接的部分。

### 13.1 Ollama 的 KV Cache 实现

Ollama 通过 llama.cpp 的 KV Cache 实现，支持三种量化精度：

| KV Cache 类型 | 精度 | 显存节省 | 适用场景 |
|---|---|---|---|
| `f16`（默认） | 最高 | 基准 | 显存充足时的最优质量 |
| `q8_0` | 8-bit 量化 | ~50% | 长上下文对话 |
| `q4_0` | 4-bit 量化 | ~75% | 极限节省显存，质量略降 |

在你的 Mac 上，8K 上下文的 KV Cache 占用（qwen3.5:9b）：

```
f16:  2 × 36 层 × 32 头 × 128 头维度 × 8192 token × 2 bytes ≈ 4.5 GB
q8_0: 4.5 × 0.5 ≈ 2.3 GB
q4_0: 4.5 × 0.25 ≈ 1.1 GB
```

你可以通过环境变量切换：

```bash
export OLLAMA_KV_CACHE_TYPE=q8_0   # 长对话时节省 ~2GB 显存
```

### 13.2 Ollama 的 KV Cache 管理策略与局限

Ollama 当前的 KV Cache 管理采用 **Prefix Reuse + LRU** 策略，但**没有 PagedAttention 式的细粒度分页**。这意味着：

- **复用已有的前缀**：同一对话的后续请求中，与上轮完全相同的 token 前缀的 KV Cache 直接复用，不重算（这和你的直觉一致——避免重复计算）
- **LRU 驱逐**：当 KV Cache 用满时，最久未使用的 block 被驱逐
- **局限性**：Ollama 没有 PagedAttention 式的页表——KV Cache 仍是一段连续分配的内存区域。当上下文超过 ~32K token 时，性能退化明显。有测试显示 100K 上下文时内存占用飙升至 ~56GB，而支持 PagedAttention 的 MLC-LLM 在同样条件下能稳定处理

> 这意味着：Ollama 适合**短到中等上下文**（< 16K）的本地推理——这正是你 Agent 原型开发的典型场景。当你的个人知识库 Agent 需要处理超长文档时，你会需要用到支持 RadixCache 的 SGLang 或 PagedAttention 的 vLLM——这是第 8-9 周的内容。

### 13.3 Flash Attention

Ollama 支持可选的 Flash Attention（通过 llama.cpp），通过 tiling 和 streaming 减少 Attention 计算的中间结果显存占用：

```bash
export OLLAMA_FLASH_ATTENTION=1   # 开启 Flash Attention
```

开启后 KV Cache 的 q8_0/q4_0 量化才生效——因为 Flash Attention 的内核原生处理量化后的 K、V 张量。

---

## 14. GGUF 格式与量化

### 14.1 GGUF 是什么

**GGUF（GGML Universal Format）** 是 llama.cpp 生态的模型文件格式，取代了早期的 GGML 格式。它不是 PyTorch 的 `.pt` 或 HuggingFace 的 `safetensors`——它是专为**本地 CPU/GPU 推理**设计的自包含格式。

一个 GGUF 文件包含：

```
GGUF 文件结构：
┌──────────────────────┐
│ Magic Number         │  ← "GGUF" 标识
│ Version              │  ← 格式版本 (当前 v3)
│ Tensor Count         │  ← 有多少个张量
│ Metadata KV Pairs    │  ← 架构名、tokenizer、量化方式、上下文长度...
│   - "general.architecture": "qwen3"
│   - "tokenizer.ggml.model": "gpt2"
│   - "qwen3.context_length": "32768"
│   - ...
├──────────────────────┤
│ Tensor 1: model.embed_tokens.weight  │  ← 实际权重矩阵
│ Tensor 2: model.layers.0.self_attn.q_proj.weight │
│ ...                  │
│ Tensor N: lm_head.weight            │
└──────────────────────┘
```

关键特征：**一个文件包含所有东西**——权重 + tokenizer + 模型配置 + 量化参数。这就是你在 Finder 里看到的那一个 6.6GB 文件。

### 14.2 量化类型

Ollama 拉取模型时默认选择 Q4_K_M（sweet spot）。GGUF 支持的量化选项包括：

| 量化类型 | 每个参数 | 7B 模型的 GGUF 大小 | 质量 vs FP16 |
|---|---|---|---|
| F16（无量化） | 2 bytes | ~14 GB | 100%（基准） |
| Q8_0 | 1 byte | ~7 GB | ~99.9% |
| Q6_K | ~0.8 byte | ~5.8 GB | ~99.5% |
| **Q4_K_M**（默认） | ~0.55 byte | **~4.5 GB** | **~98%** |
| Q4_0 | 0.5 byte | ~4.0 GB | ~96% |
| Q2_K | ~0.3 byte | ~2.8 GB | ~92% |

**量化原理（直觉版）**：

```text
FP16 权重矩阵（原始精度）：
  [0.1234, -0.5678, 0.9012, -0.3456, ...]  ← 每个值 2 bytes

Q4_K_M 量化后：
  1. 把权重分成 block（如每 256 个值为一个 block）
  2. 每个 block 找出 min 和 max → 计算 scale factor
  3. 每个值按 scale factor 缩放为 4-bit 整数（0-15 共 16 个槽位）
  4. 存储时只存 4-bit 整数 + 每个 block 一个 scale factor

block_size=256 时：
  原始：256 × 2 bytes = 512 bytes
  Q4_K_M：256 × 0.5 bytes + 2 bytes (scale) ≈ 130 bytes
  压缩率 ≈ 4x
```

推理时，这些 4-bit 整数被**实时反量化**回 FP16，然后用 FP16 做实际的矩阵乘法。这个过程比你想象的快——反量化只需要一次乘法和一次加法，远小于矩阵乘法本身的 FLOPS。

### 14.3 量化敏感张量

不是所有权重都以相同的精度量化。Ollama 的 `quantize` 函数会升级某些对精度敏感的张量类型：

```go
// 伪代码——来自 server/quantization.go
func getTensorNewType(tensorName string) {
    if strings.Contains(tensorName, "attn_v") ||
       strings.Contains(tensorName, "output") {
        return Q8_0  // ← Attention Value 和输出层升级到 8-bit
    }
    return Q4_K_M    // ← 其他层用默认量化
}
```

这就是为什么你不能自己选任意量化模式——不是所有层对量化的敏感度一样。Ollama 的默认量化配置已经针对质量做了优化。

---

## 15. 请求调度

### 15.1 并发模型

Ollama 的调度器管理两类并发：

| 参数 | 默认值 | 含义 |
|---|---|---|
| `OLLAMA_NUM_PARALLEL` | 0 (自动) | 每个 Runner 同时处理的请求数。0 = 自动根据显存计算 |
| `OLLAMA_MAX_LOADED_MODELS` | 3×GPU 数量 | 同时驻留在内存中的模型数量上限 |
| `OLLAMA_MAX_QUEUE` | 512 | 最大排队请求数 |

当你同时向 `/v1/chat/completions` 发 5 个并发请求时：

```text
请求 1-4：OLLAMA_NUM_PARALLEL=4 → 同时进入 llama-server batch
请求 5：超出并发限制 → 进入 pendingReqCh 队列
    ↓ 其中一个请求完成
请求 5 出队 → 进入 llama-server
```

### 15.2 模型驱逐策略

当加载新模型而内存已满时，调度器选择一个 victim Runner：

1. 优先选 `refCount == 0`（没有活跃请求）的 Runner
2. 在多个零引用的 Runner 中，选最早到期的（`keep-alive` 剩余时间最短的）
3. 如果所有 Runner 的 `refCount > 0`（都有未完成的请求），不驱逐——新模型排队等待

### 15.3 双阶段批处理

Ollama Engine 使用双阶段批处理来最大化 GPU 利用率：

```text
阶段 A（CPU 侧——Go 代码）：
  收集待处理的序列 → 构建 batch（forwardBatch）
  准备输入张量、padding、position_ids
    ↓ 提交给底层引擎

阶段 B（GPU 侧——llama.cpp/CUDA/Metal）：
  执行 forward() → 每个序列生成 1 个 token
    ↓ token 返回给 Go 代码
    
阶段 A 和阶段 B 流水线重叠：
  当 B 在执行 GPU 计算时，A 同时在准备下一个 batch
```

---

## 16. Ollama vs vLLM 定位差异

两者都是"推理运行时/框架"，但处于完全不同的量级。理解它们的差异需要区分**推理引擎层**和**运行时层**的职责（详见第 8.1 节）。

| 维度 | Ollama | vLLM |
|---|---|---|
| **定位** | 个人本地推理 / 原型开发 | 生产级高吞吐推理服务 |
| **架构模式** | **解耦式**：Go 运行时 + 外部 llama.cpp 子进程 | **一体式**：Python 运行时 + 自研 CUDA Kernel，同一进程 |
| **推理引擎** | 无自研引擎——委托给 llama.cpp / MLX | 自研 CUDA 内核 + PagedAttention |
| **KV Cache 管理** | 委托给 llama.cpp：Prefix Reuse + LRU，无分页 | **PagedAttention**：自研 Block Table + Hash Cache，细粒度页表 |
| **跨请求前缀共享** | 同对话内复用（llama.cpp 管理） | **Automatic Prefix Caching**：跨请求、跨用户共享相同前缀 KV Cache |
| **并发调度** | 基础 round-robin（Go Scheduler refCount + 驱逐） | **Continuous Batching**：每 token 重新调度 |
| **分布式** | 不支持 | 张量并行 + 流水线并行 + 多节点 |
| **安装难度** | `brew install ollama`（一行） | 需要 CUDA 环境 + NVIDIA GPU + 编译或 Docker |
| **你的学习计划中** | 现在用（Day 3+）——本地原型开发 | **第 8-9 周学**——理解生产级推理优化 |
| **典型的帧** | 一个开发者 + 一个模型 + M4 MacBook | 数千并发用户 + 多模型 + H100 集群 |

---

## 17. 一句话总结

Ollama = **Go 调度器** + **llama.cpp 推理引擎 (子进程)** + **GGUF 文件格式** + **Metal GPU 后端**，封装成一条命令的本地推理运行时。它把从"字符串输入"到"逐 token 生成"的完整路径自动化了——但你敲 `ollama run` 时发生的远不止"调个 API"。

---

## 18. 参考来源

| 来源 | 类型 | 链接 |
|---|---|---|
| Ollama 官方 DeepWiki — 推理引擎架构 | 架构文档 | https://deepwiki.com/ollama/ollama/5-backend-system |
| Ollama 官方 DeepWiki — 请求调度与 Runner 管理 | 架构文档 | https://deepwiki.com/ollama/ollama/2.2-request-scheduling-and-runner-management |
| Ollama 官方 DeepWiki — 量化 | 技术文档 | https://deepwiki.com/ollama/ollama/4.6-quantization |
| Ollama 官方 DeepWiki — 模型文件格式 | 技术文档 | https://deepwiki.com/ollama/ollama/4.4-model-file-formats |
| PR #15122: 移除 CGO engines，统一到 llama-server | 源码变更 | https://github.com/ollama/ollama/pull/15122 |
| SitePoint: Ollama vs vLLM 扩展指南 (2026) | 行业对比 | https://www.sitepoint.com/ollama-vs-vllm-scaling-local-ai-stack/ |
| Markaicode: Ollama 内存映射优化教程 | 技术教程 | https://markaicode.com/ollama-memory-mapping-optimization-tutorial/ |
| Dev.to: From ollama run to Tokens (2026) | 技术博客 | https://dev.to/akshitzatakia/from-ollama-run-to-tokens-what-really-happens-when-you-run-an-llm-locally-9c0 |
| VMware Tanzu: Understanding the Ollama Provider | 技术文档 | https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/ai-services/10-3/ai/explanation-understand-ollama-config.html |
| Ollama 源码解析：用 Go 语言打造本地 LLM 运行框架 | 中文技术博客 | http://mp.weixin.qq.com/s?__biz=MzY5MTIzMTQ5Mw==&mid=2247483706&idx=1&sn=956e984e85fcd63922e2b6e504d5b445 |
| 前序笔记：07-kv-cache-and-inference-frameworks.md | 本项目的笔记 | 对 KV Cache 工程问题的系统性推导 |
