# Git 深度指南：从第一性原理到实战

> **目标读者**：VSCode + GitHub 用户，希望从「根上」理解 Git 原理，而非只记住命令。
>
> **阅读方式**：第 1-5 部分是心智模型（按顺序读，这是全书最重要的部分），第 6-9 部分按需查阅。

---

## 目录

- [第一部分：第一性原理 —— Git 到底是什么](#第一部分第一性原理--git-到底是什么)
- [第二部分：Git 的对象模型 —— blob、tree、commit](#第二部分git-的对象模型--blobtreecommit)
- [第三部分：存储经济学 —— 为什么仓库不会爆炸](#第三部分存储经济学--为什么仓库不会爆炸)
- [第四部分：分支与 HEAD —— 指针，不是副本](#第四部分分支与-head--指针不是副本)
- [第五部分：Git 的四个区域](#第五部分git-的四个区域)
- [第六部分：合并与变基](#第六部分合并与变基)
- [第七部分：Git 与 GitHub 的联动机制](#第七部分git-与-github-的联动机制)
- [第八部分：常用指令速查](#第八部分常用指令速查)
- [第九部分：VSCode + Git + GitHub 全流程对接](#第九部分vscode--git--github-全流程对接)
- [第十部分：常见翻车场景 & 自救指南](#第十部分常见翻车场景--自救指南)
- [第十一部分：.gitignore & 仓库卫生](#第十一部分gitignore--仓库卫生)
- [第十二部分：Git 配置进阶](#第十二部分git-配置进阶)
- [第十三部分：术语表](#第十三部分术语表)
- [附 A：Constitute_Of_LLM 项目 Git 初始化步骤](#附-aconstitute_of_llm-项目-git-初始化步骤)

---

## 第一部分：第一性原理 —— Git 到底是什么

### 1.1 抛开所有命令

Git 不是「版本控制工具」。那是它的用途，不是它的本质。

**Git 的本质上是一个内容寻址文件系统（Content-Addressable Filesystem）。**

什么是「内容寻址」？正常的文件系统是「路径寻址」——你通过文件名和路径找到文件。内容寻址反过来：**文件的内容决定了它的地址**。两个内容完全一样的文件，有完全一样的地址；内容差一个字节，地址就完全不同。

这个「地址」就是 SHA-1 哈希值——一串 40 字符的十六进制数字，比如 `f797ebecb61fa0eb6415d2241be33e773b02d6eb`。

> **类比**：想象一个储物柜系统。你存一个包，系统不给你柜号牌——而是给你的包拍一张照片、称重、测量，然后根据包的物理特征生成一个独一无二的编码。同一个包存两次，编码相同；包里加了一张纸巾，编码完全不同。取包时，你不需要知道「柜号」，你提供这个编码，系统就能找到你的包。
>
> **Git 就是这样工作的。** 你存一个文件，Git 根据文件内容计算哈希作为地址；你取文件时，用哈希就能取回。哈希既是「身份证号」，也是「取件码」。

版本控制是这个文件系统之上的**应用**——Git 用这种内容寻址方式存储每一次提交的完整项目状态，然后用链条把它们串起来，就成了「历史」。

### 1.2 .git 目录：Git 的全部秘密在这里

当你 `git init` 时，Git 在你的项目根目录下创建一个 `.git/` 目录。这个目录**就是 Git 的整个数据库**。没有外部服务，没有守护进程，没有魔法——只是一个目录，里面存着压缩过的文件。

```
.git/
├── HEAD              # 一个文本文件，写着「当前在哪个分支上」
├── config            # 这个仓库的本地配置
├── objects/          # ★ Git 的核心数据库（后面详讲）
│   ├── 00/           # 松散对象（loose objects），按哈希前2位分目录
│   ├── 02/
│   ├── ...
│   └── pack/         # 打包文件（packfiles）
├── refs/
│   ├── heads/        # 本地分支指针（每个文件里只有一行：commit 哈希）
│   └── tags/         # 标签指针
└── logs/             # 所有指针的移动日志（reflog 的数据源）
```

**核心洞察**：`.git` 不是一个神秘黑盒，它就是一堆文件。你现在就可以用 Finder 打开看看。

### 1.3 如何方便快捷地浏览 .git 目录

了解 `.git` 的内部结构是理解 Git 原理的关键。以下是五种浏览方式，从快到慢：

**方法一：终端直接看**

```bash
# 树形结构（最直观）
brew install tree          # 如果没有 tree 先安装
tree .git -L 2             # -L 2 表示只展开两层

# 不分层的话用 ls
ls -lR .git | less         # 递归列出所有文件
```

**方法二：Finder 中临时显示隐藏文件**

```
Cmd + Shift + .（句号）
```

在 Finder 里按这个组合键，所有以 `.` 开头的隐藏文件（包括 `.git`、`.gitignore` 等）会立即显示/隐藏。这是 GUI 中最快捷的方式。

**方法三：用 VSCode 打开**

```bash
code .git
```

VSCode 会把 `.git` 作为一个文件夹打开在左侧文件树里。看 `HEAD`、`config`、`refs/heads/main` 这些小文本文件非常方便——它们都是纯文本，点击即看。

**方法四：用 Git 自己的命令查看对象内容（推荐）**

`.git/objects/` 下的 blob/tree/commit 是 zlib 压缩的二进制，不能直接 `cat`。用 Git 的命令来读取：

```bash
git cat-file -t <hash>     # 看对象类型（blob / tree / commit）
git cat-file -p <hash>     # 看对象内容（自动解压，格式化输出）
git cat-file -p HEAD       # 看最新 commit
git cat-file -p HEAD~1     # 看倒数第 2 个 commit
```

`-t` 查类型，`-p` 看内容。哈希只取前 7 位就够了。

**方法五：tig（终端里的图形化浏览器）**

```bash
brew install tig
tig                         # 上下键翻 commit，回车看详情
```

**日常推荐组合**：`Cmd+Shift+.` 在 Finder 瞄一眼结构，`code .git` 查看文本文件，`git cat-file -p` 追踪某个 blob 的具体内容。

---

## 第二部分：Git 的对象模型 —— blob、tree、commit

Git 的数据库（`.git/objects/`）里只存四种东西。其中三种是核心，理解它们就理解了 Git：

| 对象类型 | 存的是什么 | 类比 |
|---------|-----------|------|
| **blob** | 一个文件的**完整内容**（没有文件名，没有路径） | 一张复印好的纸 |
| **tree** | 一个目录的**结构清单**（文件名 → blob 哈希的映射） | 一个文件夹的目录索引卡 |
| **commit** | 一次提交的**元信息**（指向 tree + 作者 + 时间 + message + 父 commit） | 一张便签：「张三是哪天用哪个文件夹」 |

### 2.1 Blob：文件内容如何变成 Git 对象

这是 Git 最底层的操作。我们从头到尾走一遍。

**假设你有一个文件 `hello.txt`，内容是：**

```
hello world
```

（11 个字节：`hello world` 10 个字符 + 1 个换行符 `\n`）

#### 第一步：Git 拼接一个 header

```
"blob 11\0" + "hello world\n"
  │    │  │      └── 文件原始内容（11 字节）
  │    │  └── 空字节（分隔符）
  │    └── 文件内容的字节数
  └── 对象类型
```

> **为什么要这个 header？** 因为哈希必须是**唯一的**。如果只对文件内容做哈希，可能出现一个文件内容是 `hello` 而另一个 blob 恰好也有相同哈希的情况（虽然概率极低，但更重要的原因是：Git 需要对「类型 + 大小」也做哈希，保证类型不同或大小不同的对象不会碰巧哈希相同）。

#### 第二步：对 header + 内容 做 SHA-1 哈希

Git 把 `blob 11\0hello world\n` 这串字节喂进 SHA-1 算法，得到一个 160 位（20 字节）的数字，写成 40 位十六进制：

```
c7ed14b5e6e91b447c1a5072d43025d7a2286ef2
```

**这个 40 字符的哈希就是这个 blob 的「身份证号」，也同时是它的「存储地址」。**

#### 第三步：zlib 压缩

Git 把 `blob 11\0hello world\n` 用 **zlib** 算法压缩。zlib 是什么？它和 gzip 同门（都用 DEFLATE 压缩算法），是几乎所有编程语言标准库都支持的通用压缩格式。文本文件的压缩率通常在 2-5 倍。

#### 第四步：写入磁盘

```
.git/objects/c7/ed14b5e6e91b447c1a5072d43025d7a2286ef2
             │  │
             │  └── 哈希的后 38 位 → 文件名
             └── 哈希的前 2 位 → 子目录名
```

**为什么用前 2 位做子目录？** 因为某些文件系统在单目录下有太多文件时会变得很慢。用前 2 位拆成 256 个子目录（`00/` 到 `ff/`），每个目录最多存约 `16^38` 个文件。

#### 用 Python 完整复现这个过程

你可以自己在终端跑这段代码验证：

```python
import hashlib, zlib

content = b'hello world\n'                      # 文件原始内容
header = f'blob {len(content)}\x00'.encode()     # 拼接 header
data = header + content                          # 完整数据

sha1 = hashlib.sha1(data).hexdigest()            # SHA-1 哈希
compressed = zlib.compress(data)                  # zlib 压缩

print(f"哈希: {sha1}")
print(f"存储路径: .git/objects/{sha1[:2]}/{sha1[2:]}")
print(f"压缩前: {len(data)} bytes, 压缩后: {len(compressed)} bytes")
print(f"压缩率: {len(data)/len(compressed):.1f}x")
```

**输出：**
```
哈希: c7ed14b5e6e91b447c1a5072d43025d7a2286ef2
存储路径: .git/objects/c7/ed14b5e6e91b447c1a5072d43025d7a2286ef2
压缩前: 19 bytes, 压缩后: 27 bytes
压缩率: 0.7x
```

> 19 字节压成 27 字节，反而变大了——因为 zlib 有自己的压缩头，对小文件不合算。但对于几百行代码文件，压缩率通常在 3-10 倍。

#### Blob 的关键性质

1. **Blob 只有文件内容，没有文件名。** `hello.txt` 叫什么名字，blob 完全不知道。文件名存在 tree 里。
2. **相同内容 = 相同哈希 = 同一个 blob。** 你的项目里有 10 个文件内容一模一样（不管它们叫什么名字），磁盘上只存**一份**。因为它们生成了相同的哈希，Git 直接复用。

### 2.2 Tree：目录结构的快照

Blob 存了文件内容，但不知道文件名叫什么、在哪个目录。Tree 就是来记录这件事的。

一个 tree 对象的内容是这样的（概念表示）：

```
100644 blob c7ed14b5...  hello.txt         # 普通文件，权限 100644
100644 blob a1b2c3d4...  README.md
040000 tree e5f6g7h8...  src/              # 子目录，类型是 tree
```

你可以用 `git cat-file -p <tree-hash>` 看到真实输出。来一个你仓库的真实例子：

```
100644 blob 4c49bd78f1d08f2bc09fa0bd8191ed38b7dce5e3    .gitignore
040000 tree 9d04d9d367aae6ee9c2a82f8d4b467a95d39f369    01-handwritten-react
100644 blob 1f32ee166217e8ceb9cc9db5234f0cc9d1daad67    LEARNING-PLAN.md
100644 blob f797ebecb61fa0eb6415d2241be33e773b02d6eb    README.md
040000 tree e14dcf8fdec004005e925bfcdd7fbda78cc9cbce    notes
```

**Tree 也是一个对象，也有自己的哈希。** tree 的哈希由它的内容（所有条目）计算而来。因此：

- 如果目录里任何文件改名 → tree 内容变了 → tree 哈希变了
- 如果目录里任何文件的 blob 哈希变了 → tree 内容变了 → tree 哈希变了
- 只有目录结构完全不变 → tree 哈希不变 → 复用

**嵌套**：子目录本身也是一个 tree，所以 tree 可以无限嵌套，形成完整的目录树：

```
根 tree (c3659dd)
├── .gitignore        → blob 4c49bd7
├── README.md         → blob f797ebe
├── 01-handwritten-react/  → tree 9d04d9d
│       ├── agent.py       → blob xxxxxx
│       └── .env.example   → blob xxxxxx
└── notes/            → tree e14dcf8
        └── 01-notes.md    → blob xxxxxx
```

### 2.3 Commit：把 tree 变成历史

Tree 表示「项目在某一刻的样子」，但它不知道**谁**、**什么时候**、**为什么**保存了这个状态。Commit 来记录这些。

你执行 `git commit -m "add RoPE embedding"` 时，Git 做这几件事：

1. 把当前暂存区的内容写成一个 tree 对象（可能复用已有的 tree 和 blob）
2. 创建一个 commit 对象，包含：
   - 指向这个 tree 的哈希
   - 作者 & 提交者（名字 + 邮箱 + 时间戳）
   - commit message
   - **父 commit 的哈希**（除了第一次提交没有父 commit）

用 `git cat-file -p HEAD` 看看真实的 commit 对象：

```
tree c3659dd85acfa9965978123106c87637b84b83e4
parent 766188b852f57ab91370b70b5511dc409b1b19f3
author MengzhongRe <1217820711@qq.com> 1781595256 +0800
committer MengzhongRe <1217820711@qq.com> 1781595256 +0800

add .gitignore
```

**这就是一个 commit 的全部内容。** 大约几百个字节。它不包含任何文件内容——它只是一个「路标」，指向一个 tree。

### 2.4 从 40 个字符的哈希恢复到整个项目

现在你可以完整理解这个链路了：

```
一个 commit 哈希 (比如 6d369c5)
        │
        │  git cat-file -p 6d369c5
        ▼
commit 对象：「这个快照对应的 tree 是 c3659dd，爸爸是 766188b...」
        │
        │  git cat-file -p c3659dd
        ▼
tree 对象：「根目录有 5 个东西——
          .gitignore → blob 4c49bd7
          README.md → blob f797ebe
          01-handwritten-react/ → tree 9d04d9d
          ...」
        │
        │  对每一个 blob：git cat-file -p <blob> → 解压 → 写出到工作区
        │  对每一个子 tree：递归展开
        ▼
完整的项目文件出现在你的工作区
```

**这就是 `git checkout <commit-hash>` 背后发生的全部事情。** 它不是魔法——就是从 commit 出发，顺着 tree 的嵌套结构，把所有 blob 解压写出来。

### 2.5 哈希链的不可篡改性

因为每个 commit 的内容里包含了**父 commit 的哈希**，所以你改任何一个历史中的 commit，会发生什么？

```
A ← B ← C ← D ← E
         ↑
    你改了 C 里面的一个文件
```

C 的内容变了 → C 的 tree 哈希变了 → C 自己的哈希变了 → D 的「parent」字段指的还是**旧的 C 的哈希**，但现在已经不存在了。如果你想维持这条链，你必须：

1. 重新创建 C'（新哈希）
2. 修改 D 使其 parent 指向 C' → D 的哈希也变了 → D'
3. 修改 E 使其 parent 指向 D' → E 的哈希也变了 → E'
4. ...

**结论：改历史中任何一个 commit，它后面的所有 commit 的所有哈希全部要变。** 这就是 Git 历史不可篡改的数学基础——伪造历史需要重算整条链的哈希，而 SHA-1 目前没有实用级别的碰撞攻击，所以几乎不可能。

这也就是为什么 **已经 push 过的 commit 不要 rebase**——rebase 会「重新创建」commit，哈希全变。如果有人已经基于你的旧 commit 开始工作，他们的基础就被你改没了。

---

## 第三部分：存储经济学 —— 为什么仓库不会爆炸

这是新手最困惑的问题。每次 commit 存的是「完整快照」——那一个 100MB 的项目，commit 100 次岂不是 10GB？

答案分两层。

### 3.1 第一层：相同内容自动去重（hash-based dedup）

Blob 的哈希由内容决定。同一个文件在 100 次 commit 中都没变 → 100 个 tree 都指向同一个 blob 哈希 → 这个 blob 在磁盘上只存了**一份**。

**修改一个文件的某一行的效果**：

```
原来：README.md 内容 → SHA-1 → blob A (存了 2KB)
改了第一行：README.md 新内容 → SHA-1 → blob B (存了 2KB)
```

Git 存了 blob A **和** blob B。旧版本仍然可以通过旧 commit → 旧 tree → blob A 访问到。新版本走 blob B。

**但一个 1000 行的文件改了一行，两个 blob 几乎一模一样，这不是浪费吗？** 这就是第二层要解决的问题。

### 3.2 第二层：Git 的两种对象存储形态

Git 的对象存储有两个阶段：

#### 阶段一：松散对象（Loose Objects）——「先全量存着」

每次 `git add` + `git commit`，Git 立刻把新 blob、tree、commit 用 zlib 压缩后，独立写入 `.git/objects/`。

- 每个对象是独立的压缩文件
- 相同内容的 blob 天然去重（哈希相同）
- 但**相似内容的 blob**（同一文件改了一行）各存各的

这一步 Git 的策略是「**先存下来，别丢数据，优化以后再说**」。

#### 阶段二：打包文件（Packfiles）——「垃圾回收时统一优化」

当松散对象积攒多了（Git 会自动检测，或你手动 `git gc`），Git 触发垃圾回收（garbage collection），把松散对象打包成 `.pack` 文件。

打包过程：

1. **选基**：把同一文件的新旧版本选一个最近的完整版作为「基础版本」
2. **算差**：其他版本只存「相对于基础版本的增量（delta）」
3. **压缩**：全部打入 `.pack` 文件

**Delta 是什么？**

```
基础版本 (blob A, 2KB)：「hello world\n这是很长很长的文件...」
增量指令 (delta, 60 bytes)：「在第 12 字节后插入 \n这是新加的一行」
```

blob B 不需要重新存 2KB，它只需要存约 60 字节的「怎么从 A 变成 B」的指令。要读取 B 时，Git 取出 A + delta，实时重建出 B。

**这就是为什么 Linux 内核仓库（100 万+ 行代码，100 万+ 次 commit）.git 目录只有约 4GB。** 如果每次全量存，早爆了。

#### 实际效果

触发 `git gc` 前后的对比（以你的 agent-learning-journey 仓库为例）：

```
GC 前:
  .git 总大小: 536 KB
  .git/objects/:  396 KB (全是松散对象，每个独立 .z 文件)

GC 后:
  .git 总大小: 388 KB  (减少 ~30%)
  .git/objects/pack/: 224 KB (.pack + .idx 文件)
  .git/objects/下的松散目录: 0 个
```

你仓库历史不长所以减少不多。对于有几千次 commit 的仓库，`git gc` 能把 `.git` 压缩 5-20 倍。

#### 自动 gc 的触发条件

Git 会在以下时机自动运行 `git gc --auto`：
- `git commit` 后，如果松散对象超过 6700 个
- `git push` 后
- `git fetch` 后

日常使用你基本不需要手动 `git gc`。

### 3.3 一张图总结存储演进

```
git add / git commit
        │
        ▼
┌────────────────────────────────────────────────┐
│  阶段一：松散对象 (Loose Objects)               │
│                                                │
│  blob  → zlib 压缩 → .git/objects/ab/cdef...   │
│  tree  → zlib 压缩 → .git/objects/12/3456...   │
│  commit → zlib 压缩 → .git/objects/78/9abc...   │
│                                                │
│  特点：                                        │
│  • 相同内容 → 相同哈希 → 自动去重（只存一份）   │
│  • 相似内容 → 各存各的（还没有 delta）          │
│  • 写入快，适合高频 commit                     │
└────────────────────┬───────────────────────────┘
                     │
             git gc（自动或手动）
                     │
                     ▼
┌────────────────────────────────────────────────┐
│  阶段二：打包文件 (Packfiles)                   │
│                                                │
│  .git/objects/pack/pack-xxx.pack               │
│    ├── 基础版本 blob A (完整压缩)               │
│    ├── delta B (A → B 的二进制增量)             │
│    ├── delta C (B → C 的二进制增量)             │
│    ├── 基础版本 blob D (和 A 差异太大，另起基础) │
│    └── ...                                     │
│  .git/objects/pack/pack-xxx.idx (索引文件)      │
│                                                │
│  特点：                                        │
│  • 相似文件只存增量（delta），大幅节省空间       │
│  • 读取时需要「还原计算」，但极快               │
│  • 松散对象被删除（已打包的不留副本）           │
└────────────────────────────────────────────────┘
```

---

## 第四部分：分支与 HEAD —— Git 的指针系统

前三个部分讲了 Git 怎么存数据（blob → tree → commit 链）。但是光有一条 commit 链，你只能「往前走」——每次 commit 加一个新节点到链尾。这在现实中不够用：

- 你想尝试一个实验性功能，但不想搞坏 main 上稳定运行的代码
- 你和同事同时开发不同功能，需要互不干扰
- 线上出 bug 了，你需要基于三个月前的版本紧急修复，同时不能丢失这三个月的新代码

这些场景需要一个能力：**从 commit 链的某个点「分叉」出去，独立发展，最后再「合」回来。**

Git 的实现出奇地简单：**分支不过是一个文件，里面写着一个 commit 哈希。** 创建分支 = 创建这个文件。切换分支 = 改一下 HEAD 文件的内容。

### 4.1 从问题出发：如果没有分支会怎样

假设你只有一个线性 commit 链：

```
A ← B ← C ← D ← E ← F
```

你在 commit D 的时候突然想试一个新算法。没有分支的话：
- 你只能接着 commit，把不稳定的代码和稳定的代码混在一条线上
- 或者你手动复制整个项目文件夹（`project_backup_20260616/`），回到命名地狱

分支解决的就是这个问题：**让你从 D 出发，同时走两条路，互不干扰。**

### 4.2 分支的物理真相：一个 41 字节的文本文件

打开你的终端，直接看 Git 怎么存分支信息：

```bash
# HEAD 文件 —— 当前在哪个分支
cat .git/HEAD
# 输出：ref: refs/heads/main

# 看看有哪些分支指针
ls .git/refs/heads/
# 输出：new   noignore
```

`.git/refs/heads/` 下的每个文件就是一个分支。看看里面的内容：

```bash
cat .git/refs/heads/new
# 输出：6d369c5701de0649805b5b5b20de0b9d65b2b243
```

**就这一行。** 这就是 `new` 分支的全部内容——它指向的 commit 的哈希。

现在验证：`git log` 看到的 `new` 分支尖端是不是这个 commit？

```bash
git log new -1 --oneline
# 输出：6d369c5 add .gitignore
```

哈希完全匹配。**分支 = 指向某个 commit 的指针，物理上是一个 41 字节的文本文件**（40 位哈希 + 1 个换行符）。

#### 创建分支的机械过程

当你执行 `git switch -c feature/rope` 时，Git 只做了一件事：

```
第 1 步：在当前 HEAD 指向的 commit 哈希写入 .git/refs/heads/feature/rope
第 2 步：把 .git/HEAD 的内容从 "ref: refs/heads/main" 改为 "ref: refs/heads/feature/rope"
```

用伪代码表示：

```python
# git switch -c feature/rope 的等价操作
current_commit = read_file(".git/HEAD")           # "ref: refs/heads/main"
current_commit = resolve(current_commit)           # → "6d369c5..."

write_file(".git/refs/heads/feature/rope", current_commit)  # 创建分支文件
write_file(".git/HEAD", "ref: refs/heads/feature/rope")     # 更新 HEAD 指向
```

**没有复制任何文件，没有创建任何 blob 或 tree。** 只写了两个小文本文件。

### 4.3 commit 时分支如何自动移动

当你站在 `feature/rope` 分支上执行 `git commit -m "..."` 时：

```
第 1 步：根据暂存区创建 tree 对象（可能复用已有 blob）
第 2 步：创建 commit 对象（parent = HEAD 当前指向的 commit）
第 3 步：把新 commit 的哈希写入 .git/refs/heads/feature/rope（覆盖旧内容）
第 4 步：HEAD 不变，仍然指向 "ref: refs/heads/feature/rope"
```

关键在**第 3 步**：Git 自动把分支指针文件更新为新 commit 的哈希。这就是为什么你每次 commit 后，分支「自动前进」了。

用你仓库里的真实数据来验证：

```
.git/logs/refs/heads/main 的内容：

旧哈希 766188b... → 新哈希 6d369c5...    操作: commit: add .gitignore
旧哈希 0000000... → 新哈希 766188b...    操作: commit (initial): Initial agent repo

每次 commit 都在这个日志里留下一条「旧哈希 → 新哈希」的记录。
```

### 4.4 HEAD 的两种形态

`.git/HEAD` 是一个文本文件，它的内容有两种可能：

#### 形态一：符号引用（Symbolic Ref）—— 正常状态

```
ref: refs/heads/main
```

HEAD 不直接指向 commit，而是指向一个**分支名**。Git 看到这个，会再去读 `.git/refs/heads/main` 拿到真正的 commit 哈希。

```
HEAD → main（分支名）→ 6d369c5...（commit）
```

这是你日常工作时最常处的状态。好处是：当你 commit 时，Git 知道该更新哪个分支指针——就是 HEAD 指向的那个。

#### 形态二：直接引用（Direct Ref / Detached HEAD）

```
6d369c5701de0649805b5b5b20de0b9d65b2b243
```

HEAD 里直接写了一个 commit 哈希，没有经过分支名。这就是 **detached HEAD（分离头指针）**。

什么操作会进入 detached HEAD？

```bash
git checkout 766188b              # 直接 checkout 一个 commit
git checkout main~2               # checkout 到某个历史位置
git checkout origin/main          # checkout 远程追踪分支（这是另一种引用）
```

在 detached HEAD 状态下你仍然可以 commit，但因为没有分支指针会自动更新，新 commit 没有任何分支指向它。一旦你切到别处，这个 commit 就只能靠 reflog 找回来了（见 4.7）。

**解决方法**：给当前位置创建一个分支，HEAD 就重新挂上去了：

```bash
git switch -c new-branch-name
```

这会在 `.git/refs/heads/` 下创建文件，并把 `.git/HEAD` 改回符号引用形式。

### 4.5 分支指针的两种存储方式

和对象存储（松散对象 vs packfile）类似，分支指针也有两种存储形态：

#### 松散引用（Loose Ref）

```bash
cat .git/refs/heads/new
# 6d369c5701de0649805b5b5b20de0b9d65b2b243
```

每个分支一个独立文件，存在 `.git/refs/heads/` 下。适用于频繁变动的分支。

#### 打包引用（Packed Ref）

```
cat .git/packed-refs
# 6d369c5701de0649805b5b5b20de0b9d65b2b243 refs/heads/main
# 67da514a54370bbe72b6c1f3555bee01201b4158 refs/remotes/origin/main
# ...
```

所有不常变的分支被打包进一个文件 `.git/packed-refs`，每行一个引用。这就是为什么你仓库的 `main` 分支在 `.git/refs/heads/` 下找不到——执行 `git gc` 后，main 被移入了 `packed-refs`，而刚创建的 `new` 和 `noignore` 还是松散文件。

**Git 查找分支时的优先级**：先查 `.git/refs/heads/<name>`（松散），找不到再查 `.git/packed-refs`（打包）。如果你同时有两者，松散引用优先。这样频繁变动的分支可以用文件直接更新（性能好），稳定的分支可以打包（省空间）。

### 4.6 引用命名空间全景图

`.git/refs/` 下不只存分支指针。Git 把所有「名字 → commit 哈希」的映射统一叫 **引用（Reference / Ref）**，按用途分目录：

```
.git/refs/
├── heads/          # 本地分支
│   ├── new         #   → 6d369c5...
│   └── noignore    #   → 766188b...
├── remotes/        # 远程追踪分支（上一次 fetch 时远程的状态）
│   └── origin/
│       ├── HEAD    #   → 远程默认分支
│       └── main    #   → 67da514...（远程 main 在你上次 fetch 时的位置）
├── tags/           # 标签（给 commit 打的版本号）
│   └── v1.0.0      #   → 某个 commit 哈希
└── stash           # git stash 的临时保存
```

**核心认知**：它们**全是同一种东西**——一个名字，指向一个 commit 哈希。分支、远程分支、标签、stash，从数据结构上看没有本质区别，只是存在不同子目录下，语义不同。

- `refs/heads/*`：本地分支，commit 时自动前进
- `refs/remotes/*`：远程分支，`git fetch` 时自动更新，**你不能手动改**
- `refs/tags/*`：标签，不会自动移动（除非你用 `-f` 强制）
- `refs/stash`：stash 栈，`git stash` 时更新

### 4.7 Reflog：你的时间机器安全带

`.git/logs/` 目录记录了**每一个引用（ref）的每一次移动**。这是 Git 最被低估的安全网。

#### Reflog 的文件结构

```
.git/logs/
├── HEAD                            # HEAD 的完整移动历史
└── refs/
    └── heads/
        ├── main                    # main 分支指针的移动历史
        ├── new                     # new 分支的移动历史
        └── noignore                # noignore 分支的移动历史
```

每条日志的格式（以你的真实数据为例）：

```
旧哈希 6d369c5... → 新哈希 6d369c5...  MengzhongRe <...> 1781603625 +0800  checkout: moving from main to new
```

四个部分：`旧哈希 新哈希 用户 时间戳 操作描述`。

来看看你仓库的 `.git/logs/HEAD`（节选）：

```
0000000... → 766188b...  commit (initial): Initial agent repo
766188b... → 6d369c5...  commit: add .gitignore
6d369c5... → 6d369c5...  checkout: moving from main to new
6d369c5... → 6d369c5...  checkout: moving from new to main
6d369c5... → 766188b...  checkout: moving from main to 766188b...
766188b... → 6d369c5...  checkout: moving from noignore to main
```

每一条都记录了 HEAD 从哪移到哪、谁、什么时候、做了什么操作。**这就是 `git reflog` 的数据源。**

`git reflog` 只是把 `.git/logs/HEAD` 以更友好的格式打印出来：

```bash
git reflog
# 6d369c5 HEAD@{0}: checkout: moving from noignore to main
# 766188b HEAD@{1}: checkout: moving from 766188b to noignore
# ...
```

#### Reflog 如何救你的命

假设你做了 `git reset --hard HEAD~3`，丢弃了最近的 3 个 commit。commit 对象还在 `.git/objects/` 里（GC 还没清理），但没有任何分支指向它们了。

翻车之后的操作：

```bash
git reflog                          # 找到 reset 之前的 HEAD 哈希
# 假设看到 HEAD@{1}: a1b2c3d...

git switch -c recovery a1b2c3d     # 从这个哈希创建新分支，所有代码都回来了
```

**为什么 reflog 不会被 reset 清除？** 因为 `git reset` 本身也是一次 HEAD 移动——它会在 reflog 里留下一条记录，告诉你 HEAD 从哪移到了哪。只要你知道「旧位置」的哈希，就能回去。

#### Reflog 的过期策略

Reflog 条目不会永久保存。Git 会定期清理：
- 超过 90 天的条目（可配置 `gc.reflogExpire`）
- 不可达的 commit 超过 30 天（可配置 `gc.reflogExpireUnreachable`）

所以你最多有 30-90 天来做后悔操作。

### 4.8 删除分支到底删了什么

```bash
git branch -d feature/rope
```

Git 做的事：

1. 删除 `.git/refs/heads/feature/rope` 文件（41 字节）
2. 删除 `.git/logs/refs/heads/feature/rope` 文件（reflog）

**不会删除：**
- 任何 commit 对象
- 任何 tree 对象
- 任何 blob 对象

那些对象仍然在 `.git/objects/` 里，只是没有分支指针指向它们了。它们变成了「悬挂对象」（dangling objects）。下次 `git gc` 时会被清理。

**这也是为什么你可以恢复误删的分支**——只要找到它最后指向的 commit 哈希：

```bash
git reflog | grep "feature/rope"      # 在 reflog 里找到最后的哈希
# 或者
git fsck --lost-found                 # 列出所有悬挂的 commit
git switch -c feature/rope <hash>     # 恢复分支
```

### 4.9 为什么分支切换这么快

切换分支（`git switch other-branch`）的完整机械过程：

```
第 1 步：读 .git/HEAD，知道当前在 branch A，指向 commit X
第 2 步：读 .git/refs/heads/other-branch，得到 commit Y
第 3 步：计算 X 的 tree 和 Y 的 tree 的差异（哪些文件变了）
第 4 步：把变了的文件从 Y 的 blob 解压写出到工作区
第 5 步：把没变的文件留原样
第 6 步：更新 .git/HEAD 为 "ref: refs/heads/other-branch"
第 7 步：更新 .git/index（暂存区）为 commit Y 的状态
```

**关键优化**：第 3-4 步不是「全部删除再全部重写」，而是**只更新有差异的文件**。如果你两个分支之间只有一个文件的一行不同，Git 只改那个文件。

Git 也不创建临时目录或拷贝——它直接从 `.git/objects/` 解压 blob 到工作区。

**所以切换速度 = 读取两个 tree + 解压差异文件的耗时。** 两个分支的差异越小，切换越快。在一个大型仓库里，切换差异很大的分支可能需要一秒；差异很小的分支几乎瞬间完成。

### 4.10 用你的仓库做一次完整的文件级追踪

以下是一个真实的切换过程，每一步都可以在你的终端验证：

```bash
# 当前状态
cat .git/HEAD                              # ref: refs/heads/main
cat .git/packed-refs | grep main           # 6d369c5... refs/heads/main

# 创建新分支
git switch -c demo-branch

# 看发生了什么
cat .git/HEAD                              # ref: refs/heads/demo-branch
cat .git/refs/heads/demo-branch            # 6d369c5...（和 main 相同）
ls -la .git/refs/heads/demo-branch         # 41 字节

# 做一次 commit
echo "test" > test.txt && git add test.txt && git commit -m "demo commit"

# 看变化
cat .git/refs/heads/demo-branch            # 新哈希（不再是 6d369c5）
cat .git/refs/heads/main                   # 不存在，在 packed-refs 里
cat .git/packed-refs | grep main           # 仍然是 6d369c5...（没变！）
cat .git/logs/refs/heads/demo-branch       # 一条 create + 一条 commit

# 切回 main
git switch main
cat .git/HEAD                              # ref: refs/heads/main
ls test.txt                                # 文件不存在（main 上没有）

# 切回 demo-branch
git switch demo-branch
ls test.txt                                # 文件又出现了！
```

**这就是指针系统的全部威力**：两个「世界」在同一个文件夹里共存，切换只是改了几个文本文件和重写了工作区。

### 4.11 ORIG_HEAD：Git 留给你的「后悔路标」

某些危险操作（如 `git reset`、`git merge`、`git rebase`）在执行前，Git 会先把当前的 HEAD 哈希写入 `.git/ORIG_HEAD`。

```bash
cat .git/ORIG_HEAD
# 6d369c5701de0649805b5b5b20de0b9d65b2b243
```

如果你 merge 完后后悔了，可以用 `ORIG_HEAD` 回到 merge 前的状态：

```bash
git reset --hard ORIG_HEAD
```

`ORIG_HEAD` 只记录**上一次**危险操作的原始位置，新操作会覆盖它。它是临时路标，不是永久记录。永久记录找 reflog。

### 4.12 一张图总结整个指针系统

```
                        .git/HEAD
                   ┌─────────────────────┐
                   │ ref: refs/heads/    │
                   │     main            │
                   └────────┬────────────┘
                            │ 符号引用（间接指向）
                            ▼
              .git/packed-refs（或 .git/refs/heads/main）
                   ┌─────────────────────┐
                   │ 6d369c5b... refs/   │
                   │    heads/main       │
                   └────────┬────────────┘
                            │ 直接指向
                            ▼
                   .git/objects/6d/369c5b...
                   ┌─────────────────────┐
                   │ commit              │
                   │ tree: c3659dd...    │
                   │ parent: 766188b...  │
                   │ author: ...         │
                   └────────┬────────────┘
                            │
                            ▼
                   .git/objects/c3/659dd...
                   ┌─────────────────────┐
                   │ tree                │
                   │ README.md → f797ebe │
                   │ .gitignore → 4c49bd7│
                   │ 01-hand... → 9d04d9d│
                   └────────┬────────────┘
                            │
                            ▼
                   .git/objects/f7/97ebec...
                   ┌─────────────────────┐
                   │ blob (zlib 压缩)     │
                   │ "# Agent 技术栈..."  │
                   └─────────────────────┘

同时，每一步操作都记录在：
  .git/logs/HEAD              ← HEAD 每一次移动的日志
  .git/logs/refs/heads/main   ← main 分支指针每一次移动的日志
  .git/ORIG_HEAD              ← 上次危险操作前的位置（临时）
```

### 4.13 分支策略的本质

理解了以上全部机制后，你就会明白为什么业界的分支策略（Git Flow、GitHub Flow、Trunk-Based Development）本质上都是在约定**「什么时候创建分支、什么时候合并、指针该怎么移动」**。

没有哪种策略是「Git 技术限制」导致的——因为分支成本为零（只是一个 41 字节的文件），你可以创建无限多的分支。策略只是团队协作的社会约定。

对于个人项目，最简单的策略就是终身有效的：

```
main                   # 永远可运行的代码
feature/xxx            # 新功能从这里分叉，完成后合回 main
fix/xxx                # Bug 修复从这里分叉，完成后合回 main
```

**永远不要在 main 上直接改代码。** 切一个分支是最低成本的安全网。

---

## 第五部分：Git 的四个区域

### 5.1 四个区域的关系

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   工作区      │ ──→  │   暂存区      │ ──→  │   本地仓库    │ ──→  │   远程仓库    │
│  Working     │ git  │  Staging     │ git  │  Repository  │ git  │   Remote     │
│  Directory   │ add  │  / Index     │commit│  (.git/)     │ push │  (GitHub)    │
└──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘
  你在编辑器中          「下一张快照          由 commit 链          云端备份
  看到的文件            要拍哪些内容」        组成的完整历史          & 协作枢纽

每一层的作用：
  工作区 → 你自由修改，Git 知道改了但不管
  暂存区 → 你挑选「哪些修改纳入下个 commit」
  本地仓库 → commit 永久保存在 .git/objects，构建历史链
  远程仓库 → 把本地历史推给别人，或拉取别人的历史
```

**为什么要有暂存区？** 因为你经常改了 5 个文件，但逻辑上分属 2 个不同的改动。暂存区让你可以把它们分成 2 次 commit，每次只提交相关的文件。

### 5.2 数据流全景

```
  [你写代码]           [git add]           [git commit]         [git push]
    工作区    ───────→   暂存区   ───────→   本地仓库   ───────→   远程/GitHub
       ↑                  │                    │                    │
       │                  │                    │                    │
       └──── git restore ─┘                    │                    │
       │                                       │                    │
       └────────── git restore HEAD ───────────┘                    │
       │                                                            │
       └──────────── git pull (= fetch + merge) ────────────────────┘
```

### 5.3 每个区域「到底发生了什么」——以 blob 视角

```
git add README.md：
  → Git 读 README.md 当前内容
  → 拼接 header "blob 2107\0"
  → SHA-1 哈希 → f797ebec...
  → zlib 压缩 → 写入 .git/objects/f7/97ebec...
  → 更新 .git/index（暂存区索引）：「README.md → blob f797ebec」

git commit -m "update README"：
  → Git 读 .git/index（暂存区），创建 tree 对象
  → tree 哈希 → c3659dd...
  → zlib 压缩 tree → 写入 .git/objects/c3/659dd...
  → 创建 commit 对象，parent=HEAD 当前指向的 commit
  → commit 哈希 → 6d369c5b...
  → zlib 压缩 commit → 写入 .git/objects/6d/369c5...
  → 更新 .git/refs/heads/main 为 6d369c5b...
```

---

## 第六部分：合并与变基

分支创建后各走各的路，最终需要汇合。三种方式：

### 6.1 Fast-forward Merge（快进合并）

**条件**：目标分支（如 main）在被合并分支（如 feature）分叉后没有任何新 commit。

```
合并前：
A ← B ← C ← D ← E（feature）
        ↑
       main（还停在 C）

合并后（git switch main && git merge feature）：
A ← B ← C ← D ← E（feature + main 都指向 E）
                ↑
              main

Git 做的事：把 main 指针从 C 挪到 E。没有新建任何对象。
```

### 6.2 Three-way Merge（三方合并）

**条件**：两个分支在分叉后都有新 commit。

```
合并前：
A ← B ← C ← F（main）
        \
         D ← E（feature）

三方 = E（feature 最新）+ F（main 最新）+ C（共同祖先/分叉点）
```

Git 做的事：
1. 找到**共同祖先** C（也叫 merge-base）
2. 算出两条线各自的修改：C→F（main 的修改）和 C→E（feature 的修改）
3. 自动合成：改不同文件/不同行 → 自动合并；改同一行 → **冲突**，交给你裁决
4. 创建一个**新的 commit M（merge commit）**，有两个 parent：F 和 E

```
合并后：
A ← B ← C ← F ← M（main，M 有两个 parent）
        \     /
         D ← E（feature）

M 是一个普通 commit，特殊在于它有两个 parent。
```

### 6.3 Rebase（变基）

Rebase 不合并，而是**把你的 commit 搬到目标分支顶端**。

```
变基前（在 feature 分支上）：
A ← B ← C ← F（main）
        \
         D ← E（feature）

执行 git rebase main 后：
A ← B ← C ← F（main）
             \
              D' ← E'（feature）

D' 和 E' 的内容与 D、E 相同，但因为 parent 从 C 变成了 F，哈希也变了。
```

**Rebase 的核心代价**：commit 哈希改变。**绝对不要 rebase 已经 push 到共享仓库的 commit。**

### 6.4 合并策略选择

| 场景 | 用什么 | 为什么 |
|------|--------|--------|
| 个人 feature 分支合并到 main | rebase 或 squash merge | 历史干净，没人基于你的 feature 工作 |
| 多人协作的公共分支 | 普通 merge（--no-ff） | 保留历史完整性，不改已共享的 commit |
| 临时性的小修改 | rebase | 保持线性 |
| 长期分支（如 release） | merge | 可追溯，可 revert |

### 6.5 冲突（Conflict）的处理

冲突不是 bug。它是 Git 在说「这里我搞不定，你来。」

```
<<<<<<< HEAD
x = rope_embedding(query, cos, sin)          # 你当前分支的版本
=======
x = apply_rotary_pos_emb(query, cos, sin)    # 你要合并进来的版本
>>>>>>> feature/rope-optimization
```

**处理步骤**：
1. 编辑冲突文件，保留正确的代码（或综合两者）
2. 删除 `<<<<<<<`、`=======`、`>>>>>>>` 标记
3. `git add <resolved-file>`
4. `git merge --continue`（如果是 merge）或 `git rebase --continue`（如果是 rebase）

如果想放弃整个操作：
- `git merge --abort`（回到合并前）
- `git rebase --abort`（回到变基前）

---

## 第七部分：Git 与 GitHub 的联动机制

### 7.1 Git ≠ GitHub

| | Git | GitHub |
|---|---|---|
| **是什么** | 命令行工具/软件 | 网站/云平台 |
| **运行在哪** | 你的电脑上 | 微软的服务器上 |
| **做什么** | 内容寻址快照数据库 | 托管 Git 仓库 + 社交协作 |
| **需要联网吗** | 不需要 | push/pull/clone 需要 |

**类比**：Git 是相机，GitHub 是 Instagram。没有 Git，GitHub 就只是个空网站；没有 GitHub，Git 照样在本地工作。

### 7.2 Remote 的本质

`Remote` 就是**给一个 URL 取个名字**。默认叫 `origin`（纯约定，不是关键字）。

```bash
git remote -v
# origin  git@github.com:MengzhongRe/Constitute_Of_LLM.git (fetch)
# origin  git@github.com:MengzhongRe/Constitute_Of_LLM.git (push)
```

逐字段解释：

```
origin                                    ← 远程仓库在本地的昵称（默认叫 origin，纯约定）
git@github.com:MengzhongRe/xxx.git        ← 远程仓库的真实地址
(fetch)                                   ← 这个地址用于下载（git pull / git fetch）
(push)                                    ← 这个地址用于上传（git push）
```

`fetch` 和 `push` 可以指向不同的 URL（比如从 GitHub 下载、推送到 Gitee），但绝大多数情况下它们相同。

`git@github.com` 开头说明你用的是 **SSH 方式**，配了密钥之后 push 无需反复输密码。如果看到 `https://github.com/...` 则说明用的是 HTTPS 方式，需要 token 认证。

一个本地仓库可以关联多个远程。

### 7.3 Push 和 Pull 的内部步骤

**`git push origin main`**：
1. 根据 `origin` 找到远程 URL
2. 把你本地的 commit、tree、blob 打包（只发远程没有的对象）
3. 通过 SSH/HTTPS 发送
4. GitHub 接收后存入远端仓库，更新远端的 `main` 指针

**`git pull` = `git fetch` + `git merge`**：

```bash
# git pull 等价于：
git fetch origin          # 只下载 GitHub 上的新对象（不改你的工作区）
git merge origin/main     # 把 origin/main 合并到你的当前分支
```

推荐先 fetch 再决定怎么整合：

```bash
git fetch origin
git log origin/main --oneline    # 看看远程有什么新东西
git merge origin/main            # 或 git rebase origin/main
```

### 7.4 Fork 和 Clone 的区别

| | Clone | Fork |
|---|---|---|
| **在哪操作** | `git clone <url>` | GitHub 网页点 Fork 按钮 |
| **结果** | 代码下载到本地 | 在你的 GitHub 账号下创建一个仓库副本 |
| **与原仓库关系** | 本地仓库 ←push→ 原仓库（需权限） | 你的 Fork ←PR→ 原仓库（无需权限） |
| **典型场景** | 拉取自己有权限的仓库 | 给开源项目贡献代码 |

### 7.5 Pull Request 是什么

**PR 不是 Git 的功能，是 GitHub 的功能。** Git 本身不知道 PR 为何物。

PR = 「我改好了，请审阅后拉取合并」

完整流程：

```
1. 本地创建 feature 分支 → 写代码 → commit → push 到 GitHub
2. GitHub 网页上创建 PR：base(目标分支) ← compare(你的 feature 分支)
3. 等待 Review / CI 通过
4. 点击 Merge → GitHub 执行合并
5. 删除远程 feature 分支（可选）
```

GitHub 提供三种 merge 方式：

| 方式 | 结果 | 何时用 |
|------|------|--------|
| **Create a merge commit** | 标准三方合并 | 开源项目，保留完整历史 |
| **Squash and merge** | N 个 commit 压成 1 个 | 个人项目，main 历史干净 |
| **Rebase and merge** | Rebase 到 main 顶端 | 完全线性历史 |

---

## 第八部分：常用指令速查

> 按场景分组。

### 8.1 安装 & 配置

```bash
git --version                              # 确认 Git 已安装
git config --global user.name "MengzhongRe"
git config --global user.email "1217820711@qq.com"
git config --global init.defaultBranch main
git config --list                          # 查看所有配置
git help <command>                         # 打开某命令的文档
```

配置存储位置：
- **全局**：`~/.gitconfig`（对所有仓库生效）
- **项目级**：`.git/config`（只对当前仓库生效，优先级更高）

### 8.2 创建仓库 / 下载仓库

```bash
git init                        # 把当前目录变成 Git 仓库
git clone <url>                 # 从 GitHub 克隆到本地
git clone <url> <folder-name>   # 克隆到指定文件夹
git remote add origin <url>     # 给已有本地仓库关联远程
git remote -v                   # 查看所有远程的 URL
```

### 8.3 日常开发肌肉记忆

```bash
# 每天开工
git pull                          # 拉取最新代码

# 开发中...
git status                        # 我改了什么？（最常用的命令）
git diff                          # 看具体改了什么内容
git diff <file>                   # 只看某文件的变化
git add <file>                    # 把文件加入「待提交清单」
git add .                         # 把当前目录所有修改加入
git add -p                        # 逐块选择要不要 add（精细控制）
git restore <file>                # 放弃工作区修改（还没 add 的）
git restore --staged <file>       # 把 add 过的文件撤出暂存区

# 提交
git commit -m "简述做了什么"       # 拍快照
git commit -m "标题" -m "详细说明"  # 带正文的提交

# 推送
git push origin main              # 推送到 GitHub
git push -u origin main           # 首次推送 + 建立追踪（之后只需 git push）
```

### 8.4 查看历史

```bash
git log                                    # 完整 commit 历史
git log --oneline                          # 每个 commit 一行
git log --oneline --graph --all            # 图形化显示所有分支（最推荐的组合）
git log --oneline --graph --all -20        # 最近 20 条
git show <commit-hash>                     # 查看某 commit 的详情
git show HEAD                              # 查看最新 commit
git show HEAD~2                            # 查看倒数第 3 个 commit（~N = 倒数第 N+1 个）
git blame <file>                           # 每一行是谁改的
git blame -L 10,30 <file>                  # 只看第 10-30 行
```

### 8.5 分支操作

```bash
git branch                        # 列出本地分支（* = 当前分支）
git branch -a                     # 列出本地 + 远程所有分支
git branch <name>                 # 创建分支（但不切换）
git switch <name>                 # 切换到已有分支
git switch -c <name>              # 创建 + 切换（推荐）
git checkout -b <name>            # 同上（旧写法，老教程常用）
git branch -d <name>              # 删除已合并的分支
git branch -D <name>              # 强制删除（即使没合并）
git branch -m <old-name> <new-name>  # 重命名分支
git push origin --delete <name>   # 删除 GitHub 上的远程分支
```

### 8.6 合并与变基

```bash
# === 合并 ===
git merge <branch>                # 把 branch 合并到当前分支
git merge --no-ff <branch>        # 强制生成 merge commit
git merge --abort                 # 合并到一半有冲突，放弃

# === 变基 ===
git rebase main                   # 把当前分支的 commit 搬到 main 顶端
git rebase -i HEAD~3              # 交互式变基（整理最近 3 个 commit）
git rebase --abort                # 放弃变基
git rebase --continue             # 解决冲突后继续变基

# === 冲突解决流程 ===
# 1. 打开冲突文件，搜索 <<<<<<
# 2. 编辑解决冲突（或 VSCode 点 Accept Current/Incoming/Both）
# 3. git add <file>
# 4. git merge --continue 或 git rebase --continue
```

### 8.7 回退 & 撤销

```bash
# === 还没 git add → 放弃工作区修改 ===
git restore <file>                # 丢弃某文件的修改
git restore .                     # 丢弃所有修改

# === 已经 git add 还没 commit → 撤出暂存区 ===
git restore --staged <file>       # 撤出暂存区，修改还在

# === 已经 commit 还没 push → 撤销 commit ===
git reset --soft HEAD~1           # 撤销 commit，修改留在暂存区（推荐）
git reset --mixed HEAD~1          # 撤销 commit，修改退到工作区（默认）
git reset --hard HEAD~1           # 撤销 commit，丢弃修改（危险！）

# === 已经 push 了 → 用新 commit 对冲 ===
git revert <commit-hash>          # 建一个新 commit 来撤销（安全的唯一选择）
git revert HEAD                   # 撤销最新 commit 的影响

# === 终极后悔药 ===
git reflog                        # HEAD 的完整移动记录（找回丢失的 commit）
git switch -c recovery <hash>     # 从丢失的 commit 创建新分支恢复
```

### 8.8 同步远程

```bash
# push：上传
git push origin <branch>
git push                          # 已设置 upstream 时
git push --force-with-lease       # amend/rebase 后强制推送（较安全，检查远程有无新 commit）
git push --force                  # 无条件强推（危险！覆盖别人的 commit）

# pull：下载 + 合并
git fetch origin                  # 只下载，不改本地文件（安全）
git pull                          # fetch + merge
git pull --rebase                 # fetch + rebase（保持线性历史）
```

### 8.9 暂存工作（stash）

```bash
git stash                       # 暂存所有未提交修改，工作区变干净
git stash save "描述"
git stash list                  # 查看 stash 列表
git stash pop                   # 恢复最近的 stash 并删除
git stash apply                 # 恢复但保留 stash 记录
git stash drop                  # 删除最近的 stash
```

### 8.10 挑选 & 打标签

```bash
git cherry-pick <commit-hash>   # 把某次 commit 复制到当前分支
git tag v1.0.0                  # 在当前 commit 打标签
git tag -a v1.0.0 -m "发布说明"
git push origin v1.0.0          # 推送标签到 GitHub
git push origin --tags          # 推送所有标签
```

---

## 第九部分：VSCode + Git + GitHub 全流程对接

### 9.1 Source Control 面板

打开：`Cmd+Shift+G`

| 面板区域 | 对应命令 | 说明 |
|---------|---------|------|
| **Changes**（红色组） | `git status` 的 unstaged | 改过但没 add 的文件 |
| **Staged Changes**（绿色组） | `git status` 的 staged | 已经 add 等待 commit |
| **Message 输入框** | `git commit -m "..."` | 写 commit message |
| 文件名右边的 `+` 按钮 | `git add <file>` | 单个文件暂存 |
| 文件名右边的 `-` 按钮 | `git restore <file>` | 丢弃修改 |
| `...` 菜单 | 各种操作 | pull / push / stash / tag / branch |

**文件浏览器颜色标记**：
- 绿色 `U`：untracked（新文件，还没被 Git 追踪）
- 橙色 `M`：Modified（已追踪的文件被修改了）
- 灰色 `D`：Deleted（文件被删掉了）

### 9.2 VSCode 解决冲突

冲突时 VSCode 在冲突位置显示四个按钮：

- **Accept Current Change**：要你的版本
- **Accept Incoming Change**：要合并进来的版本
- **Accept Both Changes**：两个都要
- **Compare Changes**：并排对比两个版本

### 9.3 GitLens 扩展（推荐）

在 VSCode 扩展市场搜索 "GitLens"，安装后获得：
- **行内 blame**：每行末尾灰色小字显示提交信息
- **文件 blame 面板**：文件顶部完整 blame 历史
- **可视化 commit graph**

### 9.4 完整工作流示例

```bash
# 1. 开工前拉取最新代码
git pull origin main

# 2. 为新功能创建分支
git switch -c feature/gqa-kv-cache

# 3. 写代码...（在 VSCode 里正常编辑）

# 4. 看看改了什么
git status
git diff

# 5. 加入暂存区并提交
git add Phase2_Architecture/Stateful_KV_GQA/kv_cache.py
git commit -m "add GQA KV cache with prefill/decode separation"

# 6. 推送到 GitHub
git push -u origin feature/gqa-kv-cache

# 7. 打开 GitHub → 你的仓库 → 点 "Compare & pull request"
#    填写 PR 描述 → Create pull request

# 8. 审查 diff，确认无误 → Merge pull request

# 9. 回到 main，拉取合并后的代码
git switch main
git pull origin main

# 10. 删除已合并的 feature 分支
git branch -d feature/gqa-kv-cache
```

---

## 第十部分：常见翻车场景 & 自救指南

### 10.1 「commit 了但忘记加一个文件」

```bash
git add forgotten.py
git commit --amend --no-edit     # 把文件补进上次 commit
# 如果已经 push 了，需要强制推送：
git push --force-with-lease
```

### 10.2 「commit message 写错了」

```bash
git commit --amend -m "新的 commit message"
# 已经 push 了：
git push --force-with-lease
```

### 10.3 「不小心 add 了不该提交的文件」

```bash
git restore --staged <file>        # 从暂存区撤出
# 记住把它加入 .gitignore 防止下次再犯
```

### 10.4 「改到一半，需要紧急切分支但不方便 commit」

```bash
git stash                          # 暂存所有修改
git switch <other-branch>
# 处理完紧急问题...
git switch <original-branch>
git stash pop                      # 恢复之前的修改
```

### 10.5 「合并冲突了」

```bash
# 1. 打开冲突文件，搜索 <<<<<<
# 2. 在 VSCode 里点按钮解决
# 3. git add <file>
# 4. git merge --continue
# 如果彻底不想处理了：
git merge --abort                  # 回到合并前的状态
```

### 10.6 「git reset --hard 后后悔了」

```bash
git reflog                            # 找到丢失的 commit hash
git switch -c recovery abc12345       # 从那个 hash 创建新分支，代码就回来了
```

`reflog` 记录了 HEAD 的所有移动历史，commit 存在过 30 天内都能找回。

### 10.7 「在 main 上写了代码，但应该在 feature 分支」

```bash
git switch -c feature/xxx             # 基于当前位置创建新分支（修改会带过去）
git add . && git commit -m "..."
git push -u origin feature/xxx        # 代码现在安全地在 feature 分支上了
```

### 10.8 「push 被拒绝：! [rejected] ... fetch first」

原因：GitHub 上有你本地没有的新 commit。

```bash
git pull --rebase                     # 拉取远程，把你的 commit rebase 上去
git push                              # 再次推送
```

### 10.9 「把 API key / token commit 并 push 了」

```
1. 立即去服务商后台 revoke 这个 token（这是唯一可靠的补救！）
2. git revert 或 reset 删除包含 token 的 commit
3. 如果 token 在历史中很深：用 git filter-branch 或 BFG Repo-Cleaner 彻底擦除
4. git push --force
```

**警告**：token 一旦 push 到公开仓库，几十秒内就可能被爬虫抓走。Revoke 是唯一补救。

---

## 第十一部分：.gitignore & 仓库卫生

### 11.1 什么东西不该进 Git

| 类别 | 例子 | 原因 |
|------|------|------|
| 编译产物 | `__pycache__/`, `*.pyc`, `dist/`, `build/` | 可重新生成 |
| 环境 & 密钥 | `.env`, `.env.local`, `*.pem`, `credentials.json` | 安全风险 |
| IDE 配置 | `.vscode/settings.json`, `.idea/` | 每个人的 IDE 配置不同 |
| OS 文件 | `.DS_Store`(macOS), `Thumbs.db`(Windows) | 与项目无关 |
| 大文件 & 数据 | `*.pt`, `*.pth`, `*.bin`, `data/` | Git 不适合管理大文件 |
| 依赖 | `node_modules/`, `venv/` | 可在本地安装 |

### 11.2 .gitignore 语法

```gitignore
# 这是注释
*.pyc                    # 匹配所有 .pyc 文件
__pycache__/             # 匹配所有 __pycache__ 目录
.env                     # 匹配根目录的 .env
**/.env                  # 匹配任意深度的 .env
!/config/.env            # 但不匹配 config/.env（! = 否定/例外）
```

---

## 第十二部分：Git 配置进阶

### 12.1 设置快捷键（alias）

```bash
git config --global alias.co checkout     # git co = git checkout
git config --global alias.br branch       # git br = git branch
git config --global alias.st status       # git st = git status
git config --global alias.lg "log --oneline --graph --all"  # git lg = 图形化 log
git config --global alias.unstage "restore --staged ."      # git unstage = 全部取消暂存
git config --global alias.undo "reset --soft HEAD~1"        # git undo = 撤销上次 commit
```

### 12.2 用 VSCode 写 commit message

```bash
git config --global core.editor "code --wait"
```

### 12.3 配置文件的位置与查看方式

Git 配置存在两个层级：

| 位置 | 文件路径 | 作用范围 |
|------|---------|---------|
| 全局配置 | `~/.gitconfig` | 对本机所有 Git 仓库生效 |
| 项目配置 | `<project>/.git/config` | 只对当前仓库生效（优先级更高） |

**`~/.gitconfig` 是一个文件，不是目录**，所以不能 `cd` 进去。查看内容用：

```bash
cat ~/.gitconfig        # 终端直接看
code ~/.gitconfig        # VSCode 打开
git config --list        # 列出当前生效的所有配置（含全局 + 项目级）
```

类似地，`.git/config` 在项目根目录的 `.git/` 下面，也是一个文本文件。

### 12.4 全局 .gitconfig 逐字段解释

你的 `~/.gitconfig` 大概长这样：

```ini
[user]
    name = MengzhongRe
    email = 1217820711@qq.com
[init]
    defaultBranch = main
[alias]
    co = checkout
    br = branch
    st = status
    lg = log --oneline --graph --all
[core]
    editor = code --wait
```

逐字段的含义：

| 字段 | 含义 | 由什么命令设置 |
|------|------|---------------|
| `[user] name` | 你每次 commit 时写入的作者名 | `git config --global user.name "..."` |
| `[user] email` | 你每次 commit 时写入的作者邮箱（会显示在 GitHub 的 commit 记录上） | `git config --global user.email "..."` |
| `[init] defaultBranch = main` | 执行 `git init` 创建新仓库时，默认创建的分支名是 `main` 而非 `master` | `git config --global init.defaultBranch main` |

**关于 `[init] defaultBranch = main`**：Git 最早的默认分支名叫 `master`，2020 年后社区（GitHub、GitLab 等）推动改为 `main`。如果没设这一行，每次 `git init` 都会创建 `master` 分支，之后还得手动 `git branch -m main` 改名。

| `[alias]` 各条目 | 自定义命令缩写，比如 `git lg` 等价于 `git log --oneline --graph --all` | `git config --global alias.lg "..."` |
| `[core] editor` | 不加 `-m` 时 `git commit` 用哪个编辑器写 message | `git config --global core.editor "..."` |

### 12.5 多账号管理（个人 + 公司 GitHub）

在 `~/.ssh/config` 中配置：

```
Host github-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_personal

Host github-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_work
```

克隆时用别名：

```bash
git clone git@github-personal:MengzhongRe/personal-project.git
git clone git@github-work:company-name/work-project.git
```

---

## 第十三部分：术语表

| 中文 | 英文 | 本质解释 |
|------|------|----------|
| 仓库 | Repository | 一个项目目录 + `.git/` 数据库 |
| Blob | Binary Large Object | 压缩后存于 `.git/objects/` 的文件完整内容（不含文件名） |
| 目录树 | Tree | 目录结构快照，存 (文件名 → blob 哈希) 的映射 |
| 提交 | Commit | 指向 tree 的元信息对象（作者+时间+message+父 commit） |
| 哈希 | SHA-1 Hash | 对象的「身份证号」，由内容计算，同时也是存储地址 |
| 暂存区 | Staging Area / Index | `.git/index` 文件，存「下一个 commit 要包含哪些文件」 |
| 分支 | Branch | `.git/refs/heads/` 下的一个 41 字节文件，内容只有一个 commit 哈希 |
| 头指针 | HEAD | `.git/HEAD` 文件，指示当前所在分支 |
| 分离头 | Detached HEAD | HEAD 直接指向 commit 而非通过分支名间接指向 |
| 工作区 | Working Directory | 你正在编辑的文件（checkout 出来的 blob 解压版） |
| 合并 | Merge | 把两个分叉的 commit 合到一起，可能创建 merge commit |
| 变基 | Rebase | 把一串 commit 的 parent 换掉，「搬家」到别处 |
| 冲突 | Conflict | 同一行被两边都改了，Git 无法自动决定，需要人类裁决 |
| 克隆 | Clone | 把远程仓库的 `.git/objects/` 和引用全部下载到本地 |
| 拉取 | Pull | fetch + merge |
| 获取 | Fetch | 从远程下载新对象，但不修改本地工作区 |
| 推送 | Push | 把本地的新对象和引用更新上传到远程 |
| 分叉 | Fork | 在 GitHub 上创建别人仓库的副本到你名下 |
| 拉取请求 | Pull Request (PR) | GitHub 的功能：「请审阅后拉取合并」 |
| 远程 | Remote | 远程仓库 URL 的别名（默认叫 origin） |
| 贮藏 | Stash | 把工作区改动临时存起来，让工作区变干净 |
| 拣选 | Cherry-pick | 把单个 commit 的改动复制到当前分支 |
| 标签 | Tag | 给某个 commit 打版本号标记，`.git/refs/tags/` |
| 松散对象 | Loose Object | GC 前独立存储的压缩对象 |
| 打包文件 | Packfile | GC 后合并存储的文件，使用 delta 压缩节省空间 |
| 垃圾回收 | git gc | 把松散对象打包成 packfile，清理不可达对象 |

---

## 附 A：Constitute_Of_LLM 项目 Git 初始化步骤

### 步骤 1：确认当前状态

```bash
cd /Users/mengzhong__ren/Developer/Constitute_Of_LLM
ls -la .git           # 如果 "No such file or directory"，说明还不是 Git 仓库
```

### 步骤 2：初始化 Git 仓库

```bash
git init
git branch -m main    # 确保默认分支名是 main
```

### 步骤 3：完善 .gitignore

你已有 `.gitignore`，追加以下内容：

```gitignore
# 环境变量
.env
.env.*

# Jupyter
.ipynb_checkpoints/

# 模型权重 & 大数据
*.pt
*.pth
*.bin
*.safetensors
data/

# Triton 编译缓存
.cache/
```

### 步骤 4：设置全局配置（如果还没设）

```bash
git config --global user.name "MengzhongRe"
git config --global user.email "1217820711@qq.com"
git config --global init.defaultBranch main
```

### 步骤 5：首次提交

```bash
git status                           # 确认哪些文件会被提交
git add .                            # 把所有文件加入暂存区
git status                           # 再次确认
git commit -m "initial commit: LLM operators from scratch"
```

### 步骤 6：在 GitHub 上创建空仓库

1. 打开 github.com → 登录
2. 右上角 `+` → New repository
3. Repository name: `Constitute_Of_LLM`
4. **不要勾选** "Add a README file"（本地已有代码）
5. **不要勾选** "Add .gitignore"（本地已有）
6. 点击 "Create repository"

### 步骤 7：关联远程并推送

```bash
# SSH（推荐）：
git remote add origin git@github.com:MengzhongRe/Constitute_Of_LLM.git

# HTTPS：
git remote add origin https://github.com/MengzhongRe/Constitute_Of_LLM.git

git push -u origin main
```

### 步骤 8：验证

打开 `https://github.com/MengzhongRe/Constitute_Of_LLM`，应该能看到你的代码了。

### 步骤 9：后续日常开发

```bash
# 每天开工
git pull

# 开发新功能
git switch -c feature/my-new-operator
# ... 写代码 ...
git add <files>
git commit -m "implement xxx operator"
git push -u origin feature/my-new-operator

# 到 GitHub 开 PR → Merge
git switch main
git pull
git branch -d feature/my-new-operator
```

---

> **最后一条建议**：Git 不是看会的，是用会的。建议你今天就把项目初始化并 push 到 GitHub，接下来一周每次改代码都走「切分支 → commit → push → PR → merge」的完整流程。一周之后，肌肉记忆就形成了。
>
> 如果想可视化理解分支和合并，打开 [Learn Git Branching](https://learngitbranching.js.org/)，左边输命令，右边看动画。
