# 从无状态 API 到推理框架 —— KV Cache 管理的工程问题

> 日期：2026-06-09 | 触发：你对"每次请求都拼完整 history 是资源浪费"的直觉完全正确
> 定位：理解 vLLM/SGLang 等推理框架为什么存在——不只是"加速"，而是解决 KV Cache 的生命周期管理

---

## 目录

- [0. 你的直觉是对的](#0-你的直觉是对的)
- [1. 预填充 vs 逐 token 生成——一次推理的两个阶段](#1-预填充-vs-逐-token-生成一次推理的两个阶段)
- [2. KV Cache 是什么——每次 Attention 的"草稿纸"](#2-kv-cache-是什么每次-attention-的草稿纸)
- [3. 无状态 API 的浪费——扔掉草稿纸重新算](#3-无状态-api-的浪费扔掉草稿纸重新算)
- [4. 保留 KV Cache 的困境——显存管理的两难](#4-保留-kv-cache-的困境显存管理的两难)
- [5. 推理框架的解决方案](#5-推理框架的解决方案)
- [6. 为什么你现在用不上但有价值理解](#6-为什么你现在用不上但有价值理解)

---

## 0. 你的直觉是对的

你问了两个极其精准的问题：

1. "每次请求拼完整 history，前面已经计算过的 token 的 KV Cache 不是白算了吗？"——**对，确实白算了。无状态 HTTP API 的资源浪费是结构性的。**

2. "但如果一直保留 KV Cache 在显存里等用户发消息，用户可能不发，或者发的不是同一个对话——不也是浪费？"——**也对。KV Cache 的生命周期管理是推理框架的核心工程问题。**

你靠自己推理出了推理框架存在的两个根本动机。下面把这条逻辑链拆开。

---

## 1. 预填充 vs 逐 token 生成——一次推理的两个阶段

LLM 在一次 `POST /chat/completions` 中做的事，分成两个阶段：

```
阶段 1: 预填充 (Prefill / Prompt Processing)
──────────────────────────────────────────────
输入：完整 messages（所有历史 + 新问题）
      "你好" "我叫小明" "今天天气怎么样" ... 共 1000 个 token
LLM 做的事：
  - 把 1000 个 token 一次性送入模型
  - 并行计算所有 1000 个位置的 Attention Key 和 Value
  - 生成第一个新 token："今"
时间：~0.5 秒
计算量：O(N²)——每个 token 要 attend 到所有之前的 token

阶段 2: 逐 token 生成 (Decoding / Auto-regressive Generation)
──────────────────────────────────────────────────────────────
输入：前一步生成的 token
LLM 做的事：
  - 每次只处理 1 个新 token
  - 计算这个 token 的 Key 和 Value，追加到 KV Cache
  - 用 KV Cache 中已有的所有 K、V 做 Attention
  - 生成下一个 token
时间：每个 token ~10ms。生成 200 个 token 约 2 秒
计算量：O(N)——只算新 token 的 Attention
```

**关键洞察**：阶段 1 算出的 KV Cache（1000 个 token 的 Key 和 Value）在阶段 2 中被**反复使用**——每生成一个新 token 都要 attend 到前面所有 token 的 K、V。这些 K、V 不是临时变量——它们是整个生成过程的共享基础设施。

---

## 2. KV Cache 是什么——每次 Attention 的"草稿纸"

回忆你手撕过 Transformer 的 Attention 计算（你在 Day 1 提到有 3 个月的 Transformer 手撕经验，这段你应该很熟）：

对于序列中的每个位置 i：
```
Query_i  = X_i × W_Q    ← 当前 token 的"我要找什么"
Key_i    = X_i × W_K    ← 当前 token 的"我是什么，供其他 token 检索"
Value_i  = X_i × W_V    ← 当前 token 的"如果被 attend 到，我返回什么信息"

Attention(Q_i, K_all, V_all) = softmax(Q_i · K_all^T / √d) · V_all
```

在阶段 1（预填充）中，所有 1000 个输入 token 的 X_i 已经确定了——所以它们的 K_i 和 V_i 也被**一次性全部算出来了**。这些 K 和 V 就是 KV Cache。

在阶段 2（逐 token 生成）中，每生成一个新的 token j：
- `X_j` → 算出 `K_j`、`V_j` → **追加**到 KV Cache 尾部
- 新的 Attention = `softmax(Q_j × [K_0, K_1, ..., K_1000, ..., K_j] / √d) × [V_0, V_1, ..., V_1000, ..., V_j]`
- 不需要重算 K_0 到 K_999——它们已经在 Cache 中

KV Cache 就是 Attention 的草稿纸——把已经算过的东西记下来，下次不用重新算。

---

## 3. 无状态 API 的浪费——扔掉草稿纸重新算

你的疑问就在这里。当你做第二轮 API 调用时：

```
第 1 轮调用：
  messages = [user:"你好" | assistant:"你好！" | user:"我叫小明" | assistant:"好的小明！"]
  → 预填充 25 个 token → 生成 KV Cache(25) → 逐 token 生成 → 返回
  → HTTP 响应结束 → 服务器丢弃 KV Cache ❌

第 2 轮调用：
  messages = [user:"你好" | assistant:"你好！" | user:"我叫小明" | assistant:"好的小明！" |
              user:"我今天做了什么？"]
  → 预填充 32 个 token（前面 25 个和上一轮完全一样！）
  → 重新生成 KV Cache(32)——其中前 25 个 token 的 K、V 和第 1 轮一模一样
  → 这 25 个 token 的预填充是**纯重复计算**
```

**浪费了多少**：假设你的 Agent 和用户对话了 10 轮，累计 5000 个 token。第 11 轮 API 调用时：
- 前面 5000 个 token 的 KV Cache 全部重算一遍
- 只有最后的新消息是"新信息"
- 预填充的 O(N²) 计算量中，99% 是重复上一次已经做过的事

这就是你说的"做了无用功"。而这是 OpenAI / DeepSeek HTTP API 的**结构性缺陷**——不是因为工程师偷懒，而是 HTTP 协议本身是无状态的。服务器无法知道"这个请求和 3 秒前的那个请求是不是同一个人、是不是同一个对话"。

---

## 4. 保留 KV Cache 的困境——显存管理的两难

那直接把 KV Cache 留在显存里不删，等用户发下一条消息直接用——不行吗？

你也想到了这一层的矛盾。能，但有代价：

### 4.1 显存不是无限的

一次对话的 KV Cache 占用：

```
KV Cache 大小 = 2 × 层数 × 头数 × 头维度 × token数 × 每个参数的字节数

以 Qwen3.5:9b 为例（在 M4 16GB 上跑）：
- 层数 36、头数 32、头维度 128
- 每个 token 的 KV Cache ≈ 2 × 36 × 32 × 128 × 2 bytes ≈ 0.6 MB
- 5000 token 的对话 ≈ 3 GB 的 KV Cache（单独一项，不含模型权重）
```

**5000 token 对话的 KV Cache 已经占了 3GB**——你的 16GB Mac 上模型权重占了 7GB、系统占了 3GB，剩下 6GB。一场长对话的 KV Cache 直接吃掉一半。

### 4.2 更严重的问题——如果同时有 100 个用户在对话

这是推理框架面对的真实场景。100 个并发用户，每个对话 5000 token。

```
100 × 3GB = 300GB KV Cache
→ 需要 5 块 H100 (80GB) 只存 KV Cache
→ 这还没算模型权重
```

保留所有 KV Cache = 显存爆炸。不保留 = CPU 重复计算。

### 4.3 用户行为不可预测——闲置 Cache 也是浪费

你指出的另一个矛盾：用户可能在对话中途去接了杯水，5 分钟没发消息。这 5 分钟内，3GB 的 KV Cache 占着显存什么都不做——而这块显存本可以用来服务另一个正在活跃对话的用户。

---

## 5. 推理框架的解决方案

这四个困境正是 vLLM、SGLang 等推理框架设计时面对的核心问题。它们的解决方案：

### 5.1 PagedAttention（vLLM 的核心贡献）

**思想**：KV Cache 不再存成一个连续的大块——而是切成小块（Page），每页固定大小（比如 16 个 token）。就像操作系统管理虚拟内存一样——用的时候加载，不用的时候可以换出。

```
传统方式（无状态 API）：
  KV Cache = [████████████████████████████████]  ← 一整块连续显存。请求结束全丢弃
                       ↑
                  浪费：前面算过的全扔了

PagedAttention：
  KV Cache = [Page0][Page1][Page2][Page3][Page4][Page5]...  ← 小块，非连续
               ↑       ↑       ↑       ↑       ↑       ↑
            "你好" "小明" "天气" "好吗" "不错" "再见"
            
  第 2 轮请求：前 4 页已经算过 → 直接复用。只算新 token 的 Page5、Page6
```

当用户发来第 2 轮消息时，PagedAttention 只预填充**新的 token**。已经存在的 Page 直接指向之前保留的 KV Cache——零重复计算。

### 5.2 Prefix Caching / RadixCache（SGLang 的方案）

SGLang 更进一步。它注意到——不同用户之间也可能共享相同的前缀：

```
用户 A：system_prompt + "北京天气怎么样？"
用户 B：system_prompt + "上海天气怎么样？"
用户 C：system_prompt + "今天星期几？"

system_prompt = "你是一个有帮助的助手。请用中文回答。" ← 完全相同！
```

system_prompt 的 15 个 token 在 A、B、C 三个用户之间一模一样。SGLang 的 RadixCache 用一棵**字典树**来存 KV Cache：

```
system_prompt（根节点，三用户共享）
├── "北京天气怎么样？"（用户 A）
├── "上海天气怎么样？"（用户 B）
└── "今天星期几？"（用户 C）
```

当一个新用户 D 发来请求时，SGLang 检查它的 system_prompt 的 token 序列是否在树中。如果在——直接用，不重算。**跨用户共享 KV Cache。**

### 5.3 KV Cache 换出与换入（Swapping / Offloading）

当显存不够时，推理框架不会丢弃 KV Cache——它会把它从 GPU 显存**换出到 CPU 内存**（甚至 SSD），等需要时再换回来。

```
GPU HBM（显存，快但小）
  ↕ swap out / swap in
CPU RAM（系统内存，大但慢）
  ↕ offload
SSD（超大但很慢）
```

这和操作系统的虚拟内存管理一模一样——只是管理对象从"内存页"变成了"KV Cache Block"。

当用户 5 分钟没发消息时，推理框架自动把它的 KV Cache swap 到 CPU 内存（甚至 SSD）——释放 GPU 显存给活跃用户。当用户回来发新消息时，再 swap 回来。

### 5.4 Continuous Batching（连续批处理）

无状态 API 的问题不止于 KV Cache 复用——另一个问题是调度粒度。

传统批处理：等一批请求全部处理完，才处理下一批。问题——当这 3 个请求中有一个生成了 500 个 token（耗时 5 秒），其他两个各自只需要 20 个 token（0.2 秒），那两个就会被卡住。

Continuous Batching：推理框架**不再以"请求"为单位调度**——而是以"迭代"为单位。每生成一个 token 就重新决策：

```
迭代 1：批处理 [req_A, req_B, req_C] → 各生成 1 个 token
迭代 2：req_B 已经完成 → 退出。加入新请求 req_D → [req_A, req_C, req_D]
迭代 3：req_C 完成 → 退出。加入 req_E → [req_A, req_D, req_E]
...
```

每一轮迭代都重新选择哪些请求参与计算。不再有任何请求被长请求阻塞——这就是 Continuous Batching。

---

## 6. 为什么你现在用不上但有价值理解

你的学习计划（LEARNING-PLAN.md）把这个内容放在第 8-9 周。现在理解它的价值不在于"现在就能用上"——而在于：

### 6.1 你现在调 DeepSeek API 时，意识到"每一轮都在重复计算"
这个认知让你在写 Agent 循环时更清醒——你每调一次 `llm.generate(messages)`，DeepSeek 那边都在重算整个 messages 历史。这不是你的代码有问题，是 HTTP API 的结构性开销。知道这一点，你就不会在 Agent 循环已走过 15 步时还随手把完整 history 塞进去——你会开始想怎么压缩 messages。

### 6.2 理解了 KV Cache 是什么
以后学 PagedAttention 和 RadixCache 时，不是从零开始学一个新概念——而是"哦，这就是我猜到的那个问题的解决方案"。这个"先有问题、再见答案"的学习顺序比"先看答案、再倒推问题"有效得多。

### 6.3 这个知识链条帮你串起整个 Agent 领域
```
你的直觉：HTTP API 的无状态在浪费 KV Cache
  ↓
推理框架的核心问题：KV Cache 的生命周期管理
  ↓
PagedAttention / RadixCache / Continuous Batching
  ↓
vLLM / SGLang / TensorRT-LLM（第 8-9 周学习）
  ↓
你的 Agent 部署方案：LangGraph (编排) + vLLM (推理)
```

你刚才靠自己的推理串联了前两步——后面两条是第 8-9 周的事。
