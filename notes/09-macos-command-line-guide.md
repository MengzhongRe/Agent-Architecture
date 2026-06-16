# macOS 终端与命令行系统学习指南

> 日期：2026-06-14 | 系统：macOS / Apple Silicon M4 | Shell：zsh 5.9
> 定位：原理接触——理解命令行是什么、为什么这样设计、敲下回车后到底发生了什么
> 场景：本地 LLM 推理、Python 开发、Git 版本管理、Ollama 管理、远程连接 Linux

---

## 目录

- [0. 你敲下回车后到底发生了什么——终端、Shell、PTY、内核](#0-你敲下回车后到底发生了什么终端shellpty内核)
  - [0.1 完整的层次架构](#0.1-完整的层次架构用户终端shell内核硬件)
  - [0.2 内核到底是什么](#0.2-内核到底是什么)
    - [0.2.1 macOS 到底是什么](#0.2.1-macos-到底是什么)
    - [0.2.2 OS Kernel vs CUDA Kernel](#0.2.2-os-kernel-vs-cuda-kernel同一个词两种截然不同的意思)
    - [0.2.3 OS Kernel 可以类比 GPU 驱动吗](#0.2.3-os-kernel-可以类比-gpu-驱动吗)
  - [0.3 Shell 到底是什么](#0.3-shell-到底是什么)
  - [0.4 zsh vs bash](#0.4-zsh-vs-bash它们都是-shell有什么不同)
  - [0.5 CLI vs GUI](#0.5-cli-vs-gui同一个底层不同的入口)
  - [0.6 四个概念的精确区分](#0.6-四个概念的精确区分)
  - [0.7 PTY——GUI 应用和 CLI 进程怎么通话的](#0.7-ptygui-应用和-cli-进程怎么通话的)
  - [0.8 终端驱动器里的 line discipline](#0.8-终端驱动器里的-line-discipline)
  - [0.9 完整链路](#0.9-完整链路)
- [1. Shell 怎么找到你的命令——PATH、可执行文件与 Mach-O](#1-shell-怎么找到你的命令path可执行文件与-mach-o)
  - [1.1 PATH——谁写的、从哪来、怎么排的序](#1.1-path谁写的从哪来怎么排的序)
  - [1.2 找命令的三个工具](#1.2-找命令的三个工具)
  - [1.3 什么是"可执行文件"——从源码到机器码](#1.3-什么是可执行文件从源码到机器码)
  - [1.4 Mach-O——macOS 可执行文件的内部结构](#1.4-mach-omacos-可执行文件的内部结构)
  - [1.5 Shebang——让文本脚本也能被 execve](#1.5-shebang--让文本脚本也能被-execve)
  - [1.6 conda 怎么接管了你的 Python](#1.6-conda-怎么接管了你的-python)
  - [1.7 为什么 pip install 有时候装错地方](#1.7-为什么-pip-install-有时候装错地方)
- [2. 文件系统——从 inode 到目录树](#2-文件系统从-inode-到目录树)
  - [2.1 磁盘上的数据怎么组织的](#2.1-磁盘上的数据怎么组织的块inode目录项)
  - [2.2 inode——文件名的背后是什么](#2.2-inode文件名的背后是什么)
  - [2.3 目录到底是什么](#2.3-目录到底是什么)
  - [2.4 路径的两种写法](#2.4-路径的两种写法)
  - [2.5 硬链接——一个 inode，多个名字](#2.5-硬链接一个-inode多个名字)
  - [2.6 符号链接——独立的"指路牌"](#2.6-符号链接软链接独立的指路牌)
  - [2.7 动手验证 inode](#2.7-动手验证-inode在终端里直接看发生了什么)
  - [2.8 根目录 / 下放了什么](#2.8-根目录--下放了什么)
  - [2.9 为什么点开头的文件是隐藏的](#2.9-为什么点开头的文件是隐藏的)
  - [2.10 ls 详解](#2.10-ls-详解每个-flag-对应什么信息)
  - [2.11 常用文件操作命令](#2.11-常用文件操作命令每个背后都是系统调用)
  - [2.12 查看文件内容](#2.12-查看文件内容catlessheadtail)
  - [2.13 查找文件和内容](#2.13-查找文件和内容find-和-grep)
- [3. 权限模型——rwx、sudo、SIP](#3-权限模型rwxsudosip)
- [4. 进程管理——fork、exec、信号、前后台](#4-进程管理forkexec信号前后台)
- [5. 管道、重定向与文件描述符——Unix 最核心的组合哲学](#5-管道重定向与文件描述符unix-最核心的组合哲学)
- [6. 文本处理命令——管道的另一半价值](#6-文本处理命令管道的另一半价值)
- [7. 压缩与归档——tar、gzip、zip](#7-压缩与归档targzipzip)
- [8. Shell 变量、环境变量与配置文件](#8-shell-变量环境变量与配置文件)
- [9. 网络诊断基础——curl、ping、lsof、netstat](#9-网络诊断基础curlpinglsofnetstat)
- [10. SSH 与远程连接](#10-ssh-与远程连接)
- [11. 包管理——pip、brew、conda 三张清单](#11-包管理pipbrewconda-三张清单)
- [12. macOS 特有——launchd、brew services、系统诊断](#12-macos-特有launchdbrew-services系统诊断)
- [13. Shell 脚本基础——当你需要重复做某件事](#13-shell-脚本基础当你需要重复做某件事)
- [14. 速查索引——按"我想干什么"查](#14-速查索引按我想干什么查)

---

## 0. 你敲下回车后到底发生了什么——终端、Shell、PTY、内核

大多数人第一次打开终端，看到的是黑底白字窗口和一个闪烁的光标。他们被告知"在这里敲命令"。但他们不知道的是——**终端不是一个独立的世界，它和触控板、Finder 共享同一个操作系统，调的是同一套系统调用。**

此节是整个指南最重要的基础——理解了它，后面的所有命令不必靠背。

### 0.1 完整的层次架构——用户、终端、Shell、内核、硬件

计算机是一个洋葱。从你敲键盘到芯片执行，数据经过五层：

```
┌──────────────────────────────────────────────────────┐
│  第 1 层：你（用户）                                   │
│  敲键盘 "ls" 回车                                     │
├──────────────────────────────────────────────────────┤
│  第 2 层：终端仿真器 (Terminal.app / iTerm2)           │
│  GUI 应用。接收键盘事件，把字符画到屏幕上。               │
│  **它不知道 ls 是什么——它只管显示像素。**                │
├──────────────────────────────────────────────────────┤
│  第 3 层：Shell (zsh / bash / fish)                   │
│  命令解释器。一个普通的用户程序，和 python 同级。         │
│  你敲 ls → shell 解析字符串 → 去 PATH 里找 /bin/ls     │
│  → fork 子进程 → exec("/bin/ls")                     │
│  **Shell 自己不干活——它是指挥，找到并启动真正干活的程序。** │
├──────────────────────────────────────────────────────┤
│  第 4 层：内核 (Kernel) — XNU (macOS) / Linux         │
│  操作系统的本体。管理 CPU、内存、文件系统、进程、硬件。     │
│  fork()、exec()、open()、read()、write() —             │
│  **所有程序最终都通过内核来操作硬件。**                    │
├──────────────────────────────────────────────────────┤
│  第 5 层：硬件 (CPU / GPU / 内存 / 磁盘 / 网卡)         │
│  真正做计算和存储的硅片。                                │
└──────────────────────────────────────────────────────┘
```

**这五层的关系**：每一层只和相邻的层交互。Shell 不知道你用的是 Terminal.app 还是 iTerm2（它只知道有 stdin/stdout）。内核不知道敲键盘的是人还是脚本（它只知道有进程调了 `exec`）。硬件不知道上面跑的是 macOS 还是 Linux（它只知道有指令要执行）。

这个分层的核心含义：**Shell 的地位并不比 Python 高。** 内核眼里，zsh 和 python 和 ollama 都是同一种东西——用户空间进程。区别只在于：zsh 的活儿是"找到别的程序并启动它们"，python 的活儿是"执行 py 脚本"，ollama 的活儿是"管理本地模型推理"。

### 0.2 内核到底是什么

内核是操作系统的**本体**。它不是"一个程序"——它是唯一一个不受任何限制、可以直接操作硬件的软件。

```
用户空间 (User Space)         内核空间 (Kernel Space)
─────────────────────         ─────────────────────
Terminal.app                    进程调度 (谁用 CPU、用多久)
zsh / bash                      内存管理 (谁用哪块内存、swap)
python                          文件系统 (inode、权限检查)
ollama                          设备驱动 (GPU、网卡、键盘)
Safari                          网络协议栈 (TCP/IP)
...                             ...

用户程序不能直接碰硬件。         内核是唯一可以直接操作硬件的。
想读文件？→ 调 open() → 进入内核 → 内核读磁盘 → 返回数据。
想用网络？→ 调 socket() → 进入内核 → 内核发 TCP 包 → 返回。
想启动进程？→ 调 fork() → 进入内核 → 内核创建新进程 → 返回 PID。
```

**用户程序和内核的交互只有一种方式：系统调用（syscall）。** 系统调用是内核对外暴露的 API——`fork()`、`exec()`、`open()`、`read()`、`write()`、`mmap()`、`kill()`——全部是 C 函数，在底层编译为一条 `syscall` CPU 指令，让 CPU 从用户模式切换到内核模式。

macOS 的内核叫 **XNU**（X is Not Unix），由两部分组成：**Mach**（进程管理、内存管理、IPC）+ **BSD 层**（文件系统、网络、POSIX API）。Linux 内核是单独的 Linux（monolithic kernel）。但对外暴露的系统调用几乎一样——这就是为什么同样是 `fork()` + `exec()`，在 macOS 和 Linux 上都能跑。

**内核和 Shell 的区别**：内核在内存的特权区（ring 0），用户程序在非特权区（ring 3）。Shell 是 ring 3 里的一个普通程序——它没有特权，不能直接操作硬件。它能做的只是：解析你敲的字、在 PATH 里找到可执行文件路径、然后调 `fork()` + `exec()` **委托内核去启动那个程序**。Shell 自己是"指挥"，内核才是"动手的那个"。

### 0.2.1 macOS 到底是什么

macOS 不只是内核。内核只是最底下那一层——上面还有好几层，Apple 把它们打包在一起，统称为"macOS"：

```
macOS = 一块完整的软件栈

┌──────────────────────────────────────────────┐
│  GUI 应用层                                   │
│  Finder / Safari / 照片 / Terminal.app         │  ← 普通用户进程，你每天点的
├──────────────────────────────────────────────┤
│  Frameworks 框架层                             │
│  AppKit / Metal / Core ML / Foundation        │  ← Apple 提供的库，开发者调用
├──────────────────────────────────────────────┤
│  System Services 守护进程                      │
│  WindowServer (画屏幕) / launchd (启进程)       │  ← 后台服务，随系统启动
│  CoreAudio (声音) / mDNSResponder (网络发现)    │
├──────────────────────────────────────────────┤
│  内核 (XNU)                                   │
│  Mach (进程+内存) + BSD (文件系统+网络)          │  ← 特权层，直接操作硬件
├──────────────────────────────────────────────┤
│  硬件 (M4 芯片 + 内存 + 磁盘 + 屏幕...)         │
└──────────────────────────────────────────────┘
```

内核只是地基——上面还有系统服务、框架、GUI 应用，这些加起来才是完整的"macOS 操作系统"。

### 0.2.2 OS Kernel vs CUDA Kernel——同一个词，两种截然不同的意思

你在 ML 开发中常听到"kernel"——学习 CUDA 时叫 CUDA Kernel（GPU 核函数），这里又讲 OS Kernel（操作系统内核）。它们是同一个英文单词，但完全不是一回事：

| | OS Kernel（操作系统内核） | CUDA Kernel（GPU 计算核函数） |
|---|---|---|
| **是什么** | 操作系统的**独一特权程序**，管理所有硬件和进程 | GPU 上并行运行的**普通函数**，一个程序可以有几百个 |
| **运行在哪** | 内核空间（CPU ring 0），CPU 执行 | 用户空间，GPU 执行 |
| **权限** | 最高——可直接操作任意硬件 | 零特权——和你的 Python 代码同级，不能碰硬件 |
| **数量** | 一个系统只有一个（XNU） | 一个 CUDA 程序可能有几百个 |
| **类比** | 操作系统的脑干——没它系统起不来 | 一个并行 for 循环的函数体 |
| **谁写的** | Apple / Linus Torvalds / Microsoft | 你、PyTorch 团队、任何 CUDA 开发者 |

"kernel"这个词在计算机科学里最早的用法是指"核心"——操作系统的核心。CUDA 借用这个词是因为在 GPU 编程里，一段在设备端并行执行的代码也是那个计算任务的"核心"。词源相同，但语境和对象完全不同。

### 0.2.3 OS Kernel 可以类比 GPU 驱动吗

可以，但两者不是平级——驱动是内核的**组成部分**：

```
        OS 内核 (XNU)                  GPU 驱动 (Metal Driver)
        ─────────────                  ─────────────────────
        管所有硬件                       只管 GPU 这一种硬件
        (CPU + 内存 + 磁盘 + 网络 + ...)
        系统启动的核心第一步                内核启动后，作为内核模块加载
        没了它系统起不来                   没了它 GPU 不能用，但系统照跑

            GPU 驱动是内核的"插件"——
            它作为内核模块 (kext) 插进内核，
            扩展了内核的能力，让它能跟 GPU 对话。
```

所以精确的类比：

| 层次 | 类比的角色 |
|---|---|
| OS Kernel = **总指挥** | 管理所有硬件资源（CPU、内存、磁盘、网络...），所有用户程序唯一的"硬件访问入口" |
| GPU Driver = **专职翻译** | 内核的一个扩展模块，专管 GPU 这块硬件——把 Metal Shader / CUDA Kernel 翻译成 GPU 能懂的指令，管理显存分配 |

`/bin/ls` 要读磁盘 → 走 OS Kernel 的文件系统层。Ollama 的 Metal Shader 要跑在 GPU 上 → 走 OS Kernel 里插着的 Metal Driver。同一个内核，不同的模块。

**为什么 macOS 没有 NVIDIA GPU 驱动**：驱动必须由厂商为特定操作系统写。macOS 不认 NVIDIA 的驱动——Apple 要，NVIDIA 也愿意写，但 Apple 不签。不是技术问题，是商业关系。这就是你 RTX 5070 Ti 在 Mac 上完全用不了的根因——不是性能不够，是 macOS 不识别。

### 0.3 Shell 到底是什么

Shell 是一个**交互式的命令解释器**。展开：

- **交互式**：你敲一行 → 它执行 → 显示结果 → 等你敲下一行。这个循环叫 REPL（Read → Evaluate → Print → Loop），和 Python 交互模式一样。
- **命令解释器**：它把你敲的字符串（"ls -la"）解析成结构化意图（要启动的程序 = "ls"，参数 = "-la"），然后调系统调用去执行。

Shell 的核心职责就三件事：

1. **解析输入**：把 `ls -la /tmp` 拆成"命令"和"参数"；把 `|` 识别为管道；把 `>` 识别为重定向；把 `$PATH` 展开为环境变量的值
2. **找到程序**：在 PATH 列出的目录中搜索叫这个名字的可执行文件
3. **启动进程**：`fork()` 创建子进程 → 在子进程里设置好重定向/管道 → `exec()` 把子进程替换成目标程序 → `wait()` 等它跑完

除此之外的事——文件读写、网络通信、内存分配、CPU 调度——Shell **全部不管**。都是内核和具体程序的事。

Shell 代码你可以直接看到：

```bash
file /bin/zsh           # → Mach-O 可执行文件，1.3MB
file /bin/bash          # → Mach-O 可执行文件，1.4MB
```

zsh 和 bash 和 python 一样，都是写好的 C 代码编译出来的二进制文件。没有神秘成分。

### 0.4 zsh vs bash——它们都是 Shell，有什么不同

macOS 从 2019 年 macOS Catalina (10.15) 开始默认 Shell 从 bash 换成了 zsh。这不是因为 bash "不好"——是因为 bash 的许可证从 GPLv2 升级到了 GPLv3，Apple 不愿意接受 GPLv3 的专利条款。zsh 用的是 MIT 许可证，Apple 可以自由使用。

**对你来说，zsh 和 bash 的区别很具体**：

| | bash | zsh（你用的） |
|---|---|---|
| **许可证** | GPLv3 | MIT |
| **命令自动补全** | 基本（Tab 补全文件名） | **更好**——Tab 可补全命令选项、支持模糊匹配、大小写不敏感 |
| **通配符** | 基本（`*` 匹配文件名） | **更强**——`**/*.py` 递归匹配所有子目录、`ls *(.)` 只列普通文件 |
| **变量数组** | 索引从 0 开始 | **索引从 1 开始**（更接近人类直觉） |
| **主题/插件** | 需要额外装 bash-it | **Oh My Zsh**（最流行的 Shell 美化框架）原生支持 |
| **兼容性** | POSIX 标准，Linux 默认 | POSIX 兼容，但有些扩展语法不同 |
| **配置文件名** | `.bashrc` / `.bash_profile` | `.zshrc` / `.zprofile` |

日常使用中，99% 的命令在两者里完全一样（`cd`、`ls`、`python`、`git`、`pip` 这些和 shell 本身无关——它们只是可执行文件的名字）。区别只出现在**写 Shell 脚本**的时候——bash 脚本里的一些语法（比如数组下标从 0 开始）在 zsh 里表现不同。你的项目里没有需要手动写的 Shell 脚本，所以这个区别对你目前基本透明。

**你可以随时切到 bash 体验一下**：

```bash
bash            # 在 zsh 里启动 bash（新进程，exit 退出回到 zsh）
echo $SHELL     # 看你默认 shell 是哪个：/bin/zsh
```

### 0.5 CLI vs GUI——同一个底层，不同的入口

**CLI** = Command Line Interface（命令行接口）。你在终端里敲命令、看文字输出，就是在用 CLI。和它对应的是 **GUI**（Graphical User Interface）——Finder、浏览器、VS Code 的菜单栏。两者做的事可以完全一样（比如创建一个文件夹），只是交互方式不同——一个用键盘敲字，一个用鼠标点。底层调的是同一套系统调用。

### 0.6 四个概念的精确区分

以下四个概念是 CLI 世界的四大角色——它们被装在同一个终端窗口里，但它们是独立的东西：

| 概念 | 是什么 | macOS 上你的实例 |
|---|---|---|
| **终端仿真器** | GUI 应用，画窗口 + 接收键盘 + 显示输出 | Terminal.app / iTerm2 / Warp |
| **Shell** | 命令解释器，解析你敲的字符串，找到对应程序，启动它 | zsh（你用的）/ bash / fish |
| **内核** | 操作系统的本体，管理硬件和进程的唯一特权软件 | XNU (macOS) / Linux (你的虚拟机) |
| **命令** | 实际干活的独立可执行文件 | `/bin/ls`、`/opt/anaconda3/envs/deep_learning/bin/python` |

四者是**完全独立**的：你可以在 Terminal.app 里跑 zsh，也可以在 iTerm2 里跑 zsh（同样的 zsh，不同的终端窗口）；你可以在 zsh 里敲 `bash` 进入 bash（同一个终端窗口，不同的 shell）；你可以在任何一个 shell 里敲 `ls`（shell 变但命令不变）；内核一直都在，不管你用哪个 shell 或终端——它是地基，其余都是地基上的建筑。

### 0.7 PTY——GUI 应用和 CLI 进程怎么通话的

终端仿真器（GUI 应用）和 zsh（CLI 进程）怎么通信？靠的是内核提供的 **PTY（Pseudo Terminal，伪终端）**：

```
你的手指 → 键盘 → IOKit (macOS 驱动层)
                    ↓
              Terminal.app (GUI 应用)
                    ↓ write("ls\n", PTY master fd)
              ╔══════════════════════════════╗
              ║       内核 PTY 设备          ║
              ║  ┌───────────────────────┐  ║
              ║  │    字节流缓冲区        │  ║
              ║  │  双向：master↔slave   │  ║
              ║  │  内核负责复制转发     │  ║
              ║  └───────────────────────┘  ║
              ║   ↑ master                 ║
              ║   ↓ slave (从设备)          ║
              ╚══════════════════════════════╝
                    ↓ read(PTY slave fd) → "ls\n"
              zsh (CLI 进程，作为子进程)
                    ↓ 解析 → fork → exec /bin/ls
              /bin/ls
                    ↓ write("agent.py  ...", PTY slave fd)
              ╔══════════════════════════════╗
              ║       内核 PTY 设备          ║
              ╚══════════════════════════════╝
                    ↓ read(PTY master fd) → "agent.py  ..."
              Terminal.app → 画像素到屏幕
```

PTY 是一个**双向字节通道**——Terminal.app 把键盘输入写入 master 端，zsh 从 slave 端读到。zsh 启动的 `/bin/ls` 的输出写到 slave 端，Terminal.app 从 master 端读到后画到屏幕上。

PTY 的关键设计：zsh（以及它的子进程 `/bin/ls`）**根本不知道自己在终端里运行**。它以为自己连着真实的 VT100 硬件——它只管向 stdin/stdout 文件描述符读写。是不是 GUI、窗口多大、有没有视网膜屏幕——它一概不知。程序的这种"无知"是 Unix 哲学的核心：**程序只处理字节流，界面交给别的东西。**

### 0.8 终端驱动器里的 line discipline

你敲的每个键，在到达 zsh 之前要经过内核的 *line discipline* 层——这是 PTY 子系统里的一段内核代码：

```
你的键盘 → Terminal.app → PTY master
                              ↓
                    内核 line discipline 层
                    (对特殊字符做特殊处理)
                              ↓
                          PTY slave → zsh 的 stdin
```

Line discipline 负责把**击键**转成**信号**和**行编辑**。这是为什么：

- `Ctrl+C` 在终端里不是"复制"，而是**发 SIGINT 信号给前台进程**
- `Ctrl+D` 不是"书签"，而是**向 stdin 发送 EOF**
- `Ctrl+Z` 不是"撤销"，而是**发 SIGTSTP 信号暂停前台进程**
- 你按 Backspace 删除时，line discipline 帮你从缓冲区删掉那个字符
- 你按回车前可以随意修改输入（line discipline 在缓冲——这叫做 "cooked mode"）

这些键的行为都**不是 zsh 规定的，而是内核 line discipline 规定的**。它在从 PTY master 到 slave 的路径中间截获特殊字符，翻译成信号或编辑操作。zsh 只收到"净文本"（或者被信号打断）。

### 0.9 完整链路

```
你敲 ls 然后回车：

  1. 键盘中断 → macOS IOKit 驱动
  2. IOKit 把按键事件发给活跃窗口 Terminal.app
  3. Terminal.app 把字符 "l" "s" "\n" 写入 PTY master fd
  4. 内核 PTY 传输：master buffer → slave buffer
  5. zsh 从 PTY slave fd 逐字符读出
     "\n" 被 line discipline 处理：此行结束
  6. zsh 解析：这是个简单命令 "ls"
  7. zsh 在 PATH 里找 ls → /bin/ls
  8. zsh 调用 fork()，创建子进程（子进程继承 PTY slave fd 作为 stdin/stdout/stderr）
  9. 子进程调用 exec("/bin/ls")，操作系统把当前进程映像替换成 ls 的代码
  10. /bin/ls 执行：
      调用 getdents() 系统调用读当前目录的目录项
      把结果 write(stdout) → PTY slave fd
  11. 内核 PTY 传输：slave buffer → master buffer
  12. Terminal.app 从 PTY master fd 读出数据
  13. Terminal.app 把文本画到窗口
  14. ls 进程退出 → zsh 收到 SIGCHLD → zsh 重新打印提示符
```

**关键教训**：`ls` 不是 Shell 的功能。Shell 只负责找到它并启动它。macOS 系统下 `/bin`、`/usr/bin` 目录里几百个可执行文件——这些才是真正干活的。Shell 的角色是"指挥"——找到、启动、连接它们。

同样的链路适用于你敲 `python agent.py`、`ollama pull qwen3.5:9b`、`git status`——Python 解释器、Ollama、Git 都是一个普通的可执行文件，zsh 找到它们，fork+exec 它们。

---

## 1. Shell 怎么找到你的命令——PATH、可执行文件与 Mach-O

这是命令行最核心的机制：你敲 `python` 回车，zsh 怎么知道该跑 `/opt/anaconda3/envs/deep_learning/bin/python` 而不是 `/usr/bin/python3`？

答案有三步：(1) PATH 告诉 zsh 去哪找，(2) 可执行文件是编译好的机器码，(3) 内核加载文件并运行它。

### 1.1 PATH——谁写的、从哪来、怎么排的序

PATH 是一个**环境变量**（回顾第 8 章：环境变量是 fork 时被子进程继承的键值对）。它的值是一串目录，用 `:` 分开：

```bash
echo $PATH
# → /opt/anaconda3/envs/deep_learning/bin:/Users/.../LADR.../bin:/opt/homebrew/bin:...
```

zsh 找命令的算法：拿到你敲的名字（如 `python`），按 PATH 中的顺序逐个目录查找。在目录里找有没有一个叫 `python` 的文件，且这个文件的执行权限位（`x`）对当前用户为 1。找到了 → `fork + exec` 启动它。找遍了所有目录都没找到 → 打印 `command not found: python`。

这个 PATH 不是你手动写的——它是在不同阶段被一段段拼出来的：

```
① 系统基础 PATH：/usr/bin:/bin:/usr/sbin:/sbin
                   由 launchd 在创建 login session 时设定

② 你的 .zshrc（第 8 章讲过）：
   export PATH="/Users/mengzhong__ren/Downloads/LADR-2009-11A/bin:$PATH"
                                                          ↑
                                          把 LADR 的 bin 插到最前面

③ conda init 注入的 hook：
   你每次 conda activate deep_learning 时，conda 动态把
   /opt/anaconda3/envs/deep_learning/bin 插到 PATH 最前面
   你 deactivate 时，conda 把它从前面摘掉

④ brew 的路径：
   /opt/homebrew/bin 和 /opt/homebrew/sbin 是 brew 安装时
   自动写入 PATH 的（通过 /etc/paths.d/ 或 shell 配置）
```

所以你的完整 PATH 是这四股来源从上到下叠起来的——排在最前面的优先级最高。当一个目录被插到 PATH 最前面时，它里面的可执行文件就"遮蔽"了后面所有同名文件。

**为什么是这个顺序？** 因为 conda 环境的 `bin` 必须排第一：你想用虚拟环境里的 `python` 和 `pip`，而不是系统自带的。如果 `/usr/bin` 排在前面，你的 `python` 永远指向系统 Python 3.9（过时的），而 conda 环境里的 Python 3.13 不被调用——这就是 PATH 顺序的工程意义。

### 1.2 找命令的三个工具

```
which python         # 快速查：PATH 里哪个 python 先被找到
type python          # 区分外部文件 vs shell 内置 vs alias
command -v python    # POSIX 标准写法，跨 shell 兼容
```

`type` 比 `which` 更全面——`which` 是一个外部命令（`/usr/bin/which`），只查 PATH 里的可执行文件。`type` 是 shell 内置的，它知道你定义的 alias 和函数：

```
type cd    # → cd is a shell builtin    ← 内置命令，无对应文件
type ls    # → ls is /bin/ls             ← 外部可执行文件
type ll    # → ll is an alias for ls -la ← 你自己定义的别名
type echo  # → echo is a shell builtin   （但同时存在 /bin/echo）
```

Shell 内置命令（`cd`、`export`、`alias`、`source`、`fg`、`bg`、`jobs`、`echo`）不是独立的可执行文件——它们是 zsh 编译进自己二进制代码里的 C 函数。你找不到 `/bin/cd`，因为没有——`cd` 改变当前进程的工作目录，而这个操作**必须发生在当前进程里**。如果 `cd` 是一个外部命令，它在 `fork` 出的子进程里改了工作目录，子进程退出后父进程的工作目录不变——白改了。所以 `cd` 被迫做成内置命令。

### 1.3 什么是"可执行文件"——从源码到机器码

一个文件要有两样东西才能被 zsh 启动：

1. **执行权限位（`x`）为 1**——文件系统层面允许执行
2. **内容格式是内核认识的**——不是 JPEG 不是 PDF，是 Mach-O（或带 shebang 的文本）

但"内核认识"到底什么意思？这需要退一步看源文件是怎么变成可执行文件的。

**编译的过程**：

```
你写的 C 代码 (hello.c)：                  编译器生成的机器码 (hello.o)：
#include <stdio.h>                          55 48 89 E5 48 83 EC 10    ← x86 机器指令
int main() {                                C7 45 FC 00 00 00 00
    printf("Hello\n");                      48 8D 3D 1E 00 00 00
    return 0;                               E8 00 00 00 00 ...
}                                           这些十六进制字节就是 CPU 能直接
                                             执行的"机器语言"
  ↓ gcc/clang 编译
  ↓ 编译器把 C 语句翻译成
    CPU 原生指令（机器码）                       链接 (linker) 把 hello.o 和 printf 的
                                             库代码拼接 → 最终可执行文件 hello
```

**机器码**：CPU 只认二进制——每条指令是一个或多个字节，CPU 读一个字节序列，译码成"把寄存器 A 的值加上寄存器 B 的值，结果存回寄存器 A"，执行，再读下一条。x86 的机器码是变长的（1-15 字节），ARM (你的 M4) 是定长 4 字节。编译器的工作就是把 `printf("Hello\n")` 翻译成一串 CPU 能懂的字节。

**从源码到可执行文件的完整链**：

```
预处理 (preprocess)：展开 #include、替换 #define
    ↓
编译 (compile)：C 代码 → 汇编代码
    ↓
汇编 (assemble)：汇编代码 → 机器码 (.o 目标文件)
    ↓
链接 (link)：多个 .o 文件 + 系统库 (libc 等) → 一个完整的可执行文件 (Mach-O)
```

`/bin/ls` 就是这条链的产物——Apple 的工程师写了 ls.c，用 clang 编译成 Mach-O，打包进 macOS 安装镜像。你的 Python 虚拟环境里的 `python` 也是同样链路产出的——只是编译它的人不同（Python 社区），编译它的时候用的配置选项不同。

**可执行文件 vs 文本脚本**：

| | 可执行文件 (Mach-O) | 文本脚本 (.py / .sh) |
|---|---|---|
| 内容 | 二进制机器码（CPU 直接执行） | 纯文本（需要解释器翻译） |
| 能不能被 cat 看 | 能但乱码（字节不是字符） | 能，就是文字 |
| 如何被执行 | 内核 `execve` 直接加载到内存，CPU 从入口点开始执行 | 内核读到 `#!` → 启动 shebang 指定的解释器 → 解释器读脚本逐行执行 |
| 例子 | `/bin/ls`、`/opt/homebrew/bin/ollama`、编译好的 `.app` | `agent.py`（shebang → python3）、`script.sh`（shebang → zsh） |

### 1.4 Mach-O——macOS 可执行文件的内部结构

Mach-O 是 macOS（和 iOS）上的可执行文件格式。Linux 上对应的是 ELF，Windows 上是 PE。它们解决的都是同一个问题：**内核需要一个规范化的方式去读取和加载可执行文件**。

```bash
file /bin/ls
# → /bin/ls: Mach-O universal binary with 2 architectures: [x86_64] [arm64e]
```

Universal Binary 意思是同一个文件里包含两份机器码——一份 for Intel Mac (x86_64)，一份 for Apple Silicon (arm64e)。你的 M4 跑的是 arm64e 那份。Rosetta 2 转译旧版 x86 应用时用的是 x86_64 那份。

Mach-O 的内部结构——内核加载时逐段解析：

```
┌──────────────────────────────┐
│  Mach-O Header               │
│  魔数: 0xFEEDFACE (64-bit)    │  ← "魔数"是什么：文件头几个字节的硬编码签名。
│  或 0xFEEDFACF (32-bit)      │     内核先读这里，确认"这确实是 Mach-O 文件"。
│  CPU 类型: ARM64             │     如果魔数不对，execve 直接返回错误。
│  文件类型: EXECUTE           │     JPEG 的魔数是 0xFFD8FF，PDF 是 0x25504446。
├──────────────────────────────┤
│  Load Commands               │
│  "把 __TEXT 段映射到地址      │  ← 内核的加载指令清单——告诉内核：
│   0x100000000"               │     "这个段文件偏移 X，大小 Y，映射到虚拟地址 Z，
│  "把 __DATA 段映射到地址      │     权限是 r-x（只读+执行）"
│   0x100005000"               │
│  "需要链接 /usr/lib/libSystem"│
│  "入口点在 0x100003F00"      │
├──────────────────────────────┤
│  __TEXT 段 (代码段)           │
│  B8 01 00 00 00             │  ← 实际机器码。标记为 r-x (只读+可执行)——
│  C7 45 FC 00 00 00 00       │     你不能在执行时修改自己的代码。
│  ... (几十 KB 二进制)         │     这是安全机制——防止缓冲区溢出注入恶意代码。
├──────────────────────────────┤
│  __DATA 段 (数据段)           │
│  全局变量、静态变量            │  ← 程序运行时数据的初始值。标记为 rw- (可读写)。
│  "Hello, World!\0"           │     这些数据在程序启动前被内核从文件拷贝到内存。
├──────────────────────────────┤
│  __LINKEDIT 段 (链接信息)     │
│  符号表：函数名↔地址映射       │  ← 动态链接器 (dyld) 用的"索引"——
│  字符串表                    │     告诉 dyld "printf 这个符号在 libSystem 里，
│  重定位信息                  │     地址是 ..."
└──────────────────────────────┘
```

**魔数 (Magic Number)**：文件格式的"身份证"。每种二进制格式的头几个字节都是固定值——Mach-O 是 `0xFEEDFACE`，ELF 是 `0x7F 0x45 0x4C 0x46`（即 `.ELF` 的 ASCII），JPEG 是 `0xFF 0xD8`。内核在加载文件前先读魔数——如果不对，拒绝执行并返回错误。这不是加密，是格式标识——防止把一个 MP3 文件当机器码执行。

**段 (Segment) vs 节 (Section)**：段是虚拟内存层面的区域（有独立的读写执行权限），节是链接层面的分类（一个段可以包含多个节）。`__TEXT` 是段（权限 r-x），里面放了 `__text` 节（实际的机器码）和 `__stubs` 节（外部函数跳板）。`__DATA` 是段（权限 rw-），里面放了全局变量的初始值。代码和数据分开，是安全需求——代码不可写（防止注入），数据不可执行（防止恶意数据被当成代码跑）。

**动态链接**：`/bin/ls` 很小（~135KB），但它里面没有 `printf` 的完整实现。`printf` 在 `/usr/lib/libSystem.dylib` 里——所有程序共享这一份。这是动态链接：你的可执行文件不包含所有依赖库的代码，只记录了"我需要 libSystem"（写在 Load Commands 里）。程序启动时，macOS 的动态链接器（`/usr/lib/dyld`）在 `execve` 过程中自动把需要的动态库映射进进程地址空间，然后把 `ls` 代码里的 `printf` 调用连接到库里的真实 `printf` 地址。你在 Mach-O 的 `__stubs` 节里看到的跳板就是为此而存在的。

**当你敲 `ls` 回车时，内核做了**：
1. 打开 `/bin/ls`，读 Mach-O Header，校验魔数
2. 解析 Load Commands，按指令把 __TEXT 映射到进程地址空间（只读+执行），把 __DATA 映射进去（可读写）
3. 启动 dyld（动态链接器），dyld 读 __LINKEDIT，把 ls 依赖的所有 .dylib 也映射进来
4. dyld 解析符号表，把 `printf`、`malloc` 等外部符号的地址填进 `ls` 的跳板——这叫"符号绑定"
5. 内核把 CPU 的指令指针（PC）设为 Load Commands 里记录的入口点地址
6. CPU 从入口点开始执行机器码 → ls 开始跑

**小结**：zsh 找命令的三步——PATH 告诉它去哪找、可执行文件权限位（`x`）告诉它能不能跑、Mach-O 格式让内核知道怎么加载。

### 1.5 Shebang (`#!`)——让文本脚本也能被 execve

上面讲了二进制可执行文件（Mach-O）。但文本脚本——`agent.py`、`script.sh`——是怎么跑起来的？内核打开它，发现头两个字节是 `#!`（不是魔数 `0xFEEDFACE`），就知道这不是二进制。

**Shebang 的原理**：内核 `execve` 读到文件以 `#!` 开头 → 不把它当二进制执行 → 读第一行剩余内容（如 Blast 是 `/usr/bin/env python3`）→ 启动那个程序（`/usr/bin/env`），把原脚本路径作为参数传进去。所以如下脚本：

```python
#!/usr/bin/env python3
import sys
print(f"Python: {sys.executable}")
```

内核实际执行的是：

```
/usr/bin/env python3 ./agent.py
```

`env` 的作用是去 PATH 里找 `python3`——这样你的 conda 虚拟环境里的 Python 会被优先找到（因为它在 PATH 第一位）。如果直接写 `#!/usr/bin/python3`，就绑死了 macOS 系统自带的 Python 3.9（版本过时），无论你怎么切 conda 环境都改不了。Shebang 用 `#!/usr/bin/env <解释器名>`，是让脚本继承当前 PATH 的灵活性。

然后加执行权限即可直接跑：

```bash
chmod +x agent.py    # 给文件加上执行权限位
./agent.py           # 现在可以直接跑了——内核读 shebang → 启动 python3 → python3 执行脚本
```

### 1.6 conda 怎么接管了你的 Python

这是你的 `~/.zshrc` 里最关键的一段代码：

```bash
# >>> conda initialize >>>
__conda_setup="$('/opt/anaconda3/bin/conda' 'shell.zsh' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/opt/anaconda3/etc/profile.d/conda.sh" ]; then
        . "/opt/anaconda3/etc/profile.d/conda.sh"
    else
        export PATH="/opt/anaconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<
```

每次新开终端，这段代码被执行。它调用 `conda shell.zsh hook`，conda 返回一段 zsh 函数代码（包含 `conda` 和 `conda activate/deactivate` 函数定义），`eval` 把它们注入当前 shell session。

**关键结果**：`conda activate deep_learning` 不只是设一个变量——它动态修改 PATH，把 `/opt/anaconda3/envs/deep_learning/bin` 插到最前面，同时设定 `CONDA_DEFAULT_ENV`、`CONDA_PREFIX` 等环境变量。`conda deactivate` 把这些还原。所以：
- 终端刚打开：PATH 第一位是 `/opt/anaconda3/bin`（base 环境）
- `conda activate deep_learning`：第一位变成 `/opt/anaconda3/envs/deep_learning/bin`
- 同一个 `python` 命令，不同环境里对应完全不同的可执行文件

**为什么 conda 必须做成 shell 函数而不是独立可执行文件？** 因为修改 PATH 必须发生在当前 shell 进程里。如果 conda 是一个独立的外部程序，它在子进程里修改了 PATH，子进程退出后 PATH 恢复原样——白改了（子进程改不了父进程的环境变量）。Shell 函数在当前进程的上下文中执行——可以直接修改当前 shell 的环境，不需要 fork。这就是你笔记里之前提过的"conda init 的本质是注入一个 zsh 函数"。

### 1.7 为什么 `pip install` 有时候装错地方

```bash
which pip
# → /opt/anaconda3/envs/deep_learning/bin/pip

pip show openai | grep Location
# → Location: /opt/anaconda3/envs/deep_learning/lib/python3.13/site-packages
```

**原理**：pip 本身是一个 Python 脚本——`cat $(which pip)` 你能看到它的 shebang 和源码。当你敲 `pip install` 时，zsh 在 PATH 里找到了哪个 pip，那个 pip 就把包装进**它自己的** `site-packages`。没有全局配置，完全由"哪个 pip 先被 PATH 找到"决定。

```bash
/opt/homebrew/bin/pip install xxx     # 强制用 brew 的 pip，绕过 PATH 顺序
```

## 2. 文件系统——从 inode 到目录树

前面讲了可执行文件是什么——编译好的机器码。但文件系统关心的不是文件的内容，而是**文件放在磁盘上的什么位置、叫什么名字、谁有权限碰它**。这层抽象的核心是一个叫 inode 的东西。

### 2.1 磁盘上的数据怎么组织的——块、inode、目录项

一块 SSD 或 HDD 在物理上是连续的存储单元。文件系统（你的 Mac 用的是 **APFS**，Apple File System）在这之上建了三层抽象：

```
磁盘物理层：                         文件系统抽象：
┌──────────────────────┐            ┌──────────────────────────┐
│ Block 0              │            │  超级块 (Superblock)       │
│ Block 1              │            │  文件系统总量信息：         │
│ Block 2              │            │  块大小、inode 总数、      │
│ ...                  │            │  空闲块位图、挂载状态       │
│ Block 1048576  ←──┐  │            ├──────────────────────────┤
│   "hello\n"       │  │            │  inode 表 (Inode Table)    │
│ Block 1048577     │  │            │  inode #0: (保留)         │
│ Block 1048578  ───┘  │            │  inode #1: (保留)         │
│ ...                  │            │  inode #285740:           │
│ Block 2097152        │            │    大小=18204, 权限=rw-r--│
└──────────────────────┘            │    数据块=[1048576, ...]  │
                                    ├──────────────────────────┤
                                    │  目录项 (Directory Entries)│
                                    │  目录本质是一张表：        │
                                    │  "agent.py" → inode 285740│
                                    │  ".env"     → inode 285741│
                                    └──────────────────────────┘
```

**块（Block）**：磁盘不是按字节读的——一次最少读一个"块"。APFS 默认块大小 4096 字节（4KB）。即使一个文件只有 12 字节（`"hello world\n"`），它也会占用一个完整的 4KB 块。更大的文件跨多个块存储——inode 记录着"这些块分布在磁盘上的哪些位置"。

**超级块（Superblock）**：整个文件系统的"户口本首页"——记录了这个文件系统有多少个 inode、多少空闲块、块大小多少、最后一次挂载是什么时候。内核挂载磁盘时先读超级块，拿到容量信息后才能继续操作。

**为什么需要这个三层结构？** 因为文件系统面对两个矛盾的需求：(1) 文件大小差异极大——1 字节的 `.env` 和 6.5GB 的 GGUF 模型；(2) 文件创建和删除极其频繁——编译一次项目可能创建几百个临时 .o 文件再秒删。用 inode + 块指针 把"文件叫什么"和"文件的数据库存放在哪"解耦——名字归目录管，数据位归 inode 管。

### 2.2 inode——文件名的背后是什么

**inode（Index Node，索引节点）** 是"文件"这个抽象在磁盘上的实际代表。inode 是一个固定大小的数据结构（APFS 里约 256 字节），每个 inode 有一个唯一的整数编号——inode 号。

一个 inode 里存了什么：

```
inode #285740 (假设这是你的 agent.py)

  ┌─ 文件类型 (普通文件 / 目录 / 符号链接 / 设备文件 / ...)
  ├─ 权限位 (rw-r--r-- = 0644)
  ├─ 所有者 uid (501 = mengzhong__ren)
  ├─ 所属组 gid (20 = staff)
  ├─ 文件大小 (18204 字节)
  ├─ 硬链接计数 (1)
  │
  ├─ 数据块指针表 (这文件占用了哪些 Block):
  │   直接指针 [0]: Block #1048576
  │   直接指针 [1]: Block #1048577
  │   直接指针 [2]: Block #1048578
  │   直接指针 [3]: Block #1048579
  │   直接指针 [4]: 0 (未使用)
  │   ...
  │   一级间接指针: 0 (超大文件才需要)
  │
  ├─ 时间戳:
  │   atime: 2026-06-14 10:30:00  (最后访问时间)
  │   mtime: 2026-06-14 09:15:22  (最后修改时间——改文件内容)
  │   ctime: 2026-06-14 09:15:22  (最后状态变更——改名/改权限)
  │   btime: 2026-06-09 14:22:00  (诞生时间——何时创建，APFS 专有)
  │
  └─ 扩展属性 (APFS/XFS/Btrfs 的额外元数据)

特别重要的：inode 里没有文件名。
文件名不在 inode 里。文件名是目录的内容。
```

**inode 不存文件名**——这是理解文件系统最关键的一点。文件名是一条"目录记录"，和你认为的"文件本身"是完全分开的两样东西。这让一个 inode 被多个文件名引用成为可能——这就是硬链接。

**stat 命令直接看 inode 内容**：

```bash
stat agent.py          # 人类可读格式
stat -f "%i %p %l" agent.py  # -f 自定义格式：inode号 权限(八进制) 链接计数
ls -li agent.py        # -i 显示 inode 号
```

**inode 号是每个文件系统内部唯一的**。不同磁盘上的文件可以有相同的 inode 号——内核用"设备号 + inode 号"的组合唯一确定一个文件。

### 2.3 目录到底是什么

目录是一个特殊的文件——它的"数据块"里存的不是文本，而是一张表：

```
(文件名, inode号) 的数组

"ls /Users/mengzhong__ren/Developer/" 背后的内核操作：
  1. 找到 Developer 这个目录的 inode
  2. 读它的数据块——这些数据块的内容就是文件名→inode号的表
  3. 对表中每个文件名，去对应 inode 里取文件类型、权限、大小
  4. 打印出来
```

这就是为什么 `ls` 可以看到文件名但看不到 inode 号——inode 号是内部编号，ls 默认不显。`ls -i` 才显。

### 2.4 路径的两种写法

```
绝对路径：从根 / 开始，唯一确定一个文件
  /Users/mengzhong__ren/Developer/agent/agent-learning-journey/LEARNING-PLAN.md

相对路径：从当前工作目录开始
  ../venv/bin/activate      → 上级目录/venv/bin/activate
  ./agent.py                → 当前目录下的 agent.py（./ 通常可省略）
  ~/Developer               → 等价于 /Users/mengzhong__ren/Developer
```

`.` = 当前目录的 inode。`..` = 父目录的 inode。`~` = 你的 HOME 目录（`$HOME` 环境变量的值）。这三个符号在任何地方都通用——`ls`、`cd`、`python`、`git`、文本编辑器的文件路径框里。

**内核怎么解析 `/Users/mengzhong__ren/agent.py`**：
1. 找到根目录 `/` 的 inode（inode #2，Unix 约定）
2. 在 `/` 的数据块里找 `Users` → inode #15
3. 在 inode #15 的数据块里找 `mengzhong__ren` → inode #501
4. 在 inode #501 的数据块里找 `agent.py` → inode #285740
5. 返回 inode #285740——这就是目标文件

绝对路径和相对路径的区别只在第一步——绝对路径从 `/` 的 inode 开始，相对路径从当前进程的 CWD（Current Working Directory）inode 开始。其余步骤完全一样。

### 2.5 硬链接——一个 inode，多个名字

理解了 inode 和目录的关系后，硬链接就自然懂了：**在某个目录里加一条记录，指向一个已经存在的 inode**。

```bash
ln original.py alias.py

# 操作前：
#   目录里只有: "original.py" → inode #285740 (inode 引用计数 = 1)
#
# ln 做的事：
#   在同一个目录里加一条: "alias.py" → inode #285740 (inode 引用计数变为 2)
#
# 现在 original.py 和 alias.py 是同一个文件的两个名字。
# 这不是"复制"——没有任何数据被复制。两块"目录记录"指向着同一个 inode。
```

验证：

```bash
touch original.py
echo "hello" > original.py

ln original.py alias.py

ls -li original.py alias.py
# → 285740 -rw-r--r--  2  mengzhong  staff  6  Jun 14 10:30  alias.py
# → 285740 -rw-r--r--  2  mengzhong  staff  6  Jun 14 10:30  original.py
#       ↑                                                      ↑
#    同一个 inode 号                                      引用计数=2
```

现在改内容：

```bash
echo "world" >> alias.py
cat original.py
# → hello
# → world
# 通过 alias.py 改了内容，original.py 也看到了——
# 因为它们指向同一个 inode、同一个数据块。
```

**硬链接的关键限制**：

1. **不能跨文件系统**：硬链接是关于 inode 的操作。两个不同的磁盘（或两个 APFS 卷）有各自独立的 inode 表，inode #285740 在 Disk A 上指的是一组数据块，在 Disk B 上完全可能是另一个东西。所以 `ln /Volumes/DiskA/file.txt /Volumes/DiskB/alias.txt` 会报错 `Invalid cross-device link`。
2. **不能给目录做硬链接**：内核禁止——防止循环引用导致 `find` 和备份工具无限递归。唯一的例外是 `.` 和 `..`（内核在 `mkdir` 时自动创建）。
3. **同一个文件系统内的所有硬链接完全等价**——没有"原文件"和"别名"之分。inode 的引用计数降到 0 时，块才被回收。先创建的那个文件名和后创建的没有任何区别。

**删除原文件名后**：

```bash
rm original.py
ls -li alias.py
# → 285740 -rw-r--r--  1  mengzhong  staff  12  Jun 14 10:35  alias.py
#                                                ↑ 引用计数降回 1
# 文件完好无损。original.py 这个"名字"被删了，但 inode 还在，
# 数据块还在——通过 alias.py 照样访问。
```

### 2.6 符号链接（软链接）——独立的"指路牌"

符号链接和硬链接完全不同。它不指向 inode——它**是一个独立的文件，内容是目标路径的字符串**。

```bash
ln -s /usr/bin/python3 mypython
```

内核做的事：创建一个新 inode，标记为"符号链接"类型→在这个 inode 的数据块里写进字符串 `/usr/bin/python3`。

```bash
ls -li mypython
# → 285745 lrwxr-xr-x  1  mengzhong  staff  16  Jun 14 10:40  mypython -> /usr/bin/python3
#       ↑                                                       ↑
#   不同的 inode 号（新文件）                                     l 开头 = 符号链接
#   引用计数=1（独立文件）
```

**符号链接的本质**：它自己是一个 16 字节的"指路牌"。内核在解析路径时，看到符号链接 → 不返回连接本身，而是**自动跳转到**目标路径，继续解析。这个过程对用户透明——你敲 `cat mypython`，内核在路径解析中遇到 `mypython` 时发现它是符号链接，自动替你换成 `/usr/bin/python3`，继续解析。

**硬链接 vs 符号链接**：

| | 硬链接 | 符号链接 |
|---|---|---|
| **指向什么** | 同一个 inode | 目标路径的字符串 |
| **底层原理** | 目录里加一条记录指向已有 inode → 引用计数 +1 | 创建新 inode（类型=符号链接）→ 数据块存路径字符串 |
| **跨越文件系统** | **不能**——inode 是每个文件系统独立的 | **能**——存的是字符串，任何路径都可以 |
| **删原文件后** | **还有效**——inode 引用计数 > 0 所以还在 | **变成死链接**——存着的路径指向一个不存在的 inode |
| **目录** | **不能**（内核禁止） | **能**——存路径字符串，指向任何东西 |
| **展示** | `ls` 显示为普通文件，看不出是链接 | `ls` 显示 `->` 箭头和目标的路径 |
| **stat** 看到的大小 | 原文件大小 | 目标路径的字节数（~16 字节） |

**死链接（dangling symlink）**：删了原文件后，符号链接还在——但它指着的路径变成了空。`cat mypython` 会报 `No such file or directory`。内核路径解析到 `mypython` → 替换为 `/usr/bin/python3` → 去找 `/usr/bin/python3` 这个 inode → 不存在 → 报错。不是"符号链接坏了"——是符号链接指向的目标不存在了。

```bash
ln -s /nonexistent/file dead_link
ls -l dead_link
# → lrwxr-xr-x ... dead_link -> /nonexistent/file   ← 这个符号链接能正常创建
cat dead_link
# → cat: dead_link: No such file or directory      ← 但读的时候目标不存在，报错
```

### 2.7 动手验证 inode——在终端里直接看发生了什么

```bash
# 创建一个测试目录
mkdir /tmp/inode_test && cd /tmp/inode_test

# 创建文件，看 inode 号
echo "hello" > test.txt
ls -li
# → 123456 -rw-r--r--  1  user  wheel  6  ... test.txt
#   ↑                          ↑
# inode 号                 引用计数=1

# 硬链接
ln test.txt hardlink.txt
ls -li
# → 123456 -rw-r--r--  2  user  wheel  6  ... hardlink.txt   ← 同一 inode！
# → 123456 -rw-r--r--  2  user  wheel  6  ... test.txt        ← 同一 inode！
# 引用计数变成 2

# 符号链接
ln -s test.txt softlink.txt
ls -li
# → 123456 -rw-r--r--  2  user  wheel  6  ... hardlink.txt
# → 123457 lrwxr-xr-x  1  user  wheel  8  ... softlink.txt -> test.txt
# → 123456 -rw-r--r--  2  user  wheel  6  ... test.txt
# softlink.txt 有独立的 inode，引用计数=1

# 删原文件——看硬链接和符号链接的差异
rm test.txt
ls -li
# → 123456 -rw-r--r--  1  user  wheel  6  ... hardlink.txt    ← 还在！引用计数降为 1
# → 123457 lrwxr-xr-x  1  user  wheel  8  ... softlink.txt -> test.txt  ← 死链接

cat hardlink.txt   # → hello（数据完好）
cat softlink.txt   # → cat: softlink.txt: No such file or directory（目标没了）

# 清理
rm hardlink.txt softlink.txt
cd .. && rmdir /tmp/inode_test
```

### 2.8 根目录 `/` 下放了什么

```bash
ls /        # 看看你系统的根目录长什么样
```

| 路径 | 放什么 | 你能改吗 |
|---|---|---|
| `/bin` | Unix 核心命令：`ls`、`cp`、`mv`、`rm`、`bash` | 不能（SIP 保护） |
| `/usr/bin` | macOS 系统命令：`python3`、`perl`、`curl`、`ssh`、`vim` | 不能（SIP 保护） |
| `/opt` | 第三方软件：`/opt/anaconda3`、`/opt/homebrew` | 能——你的 conda 和 brew 都在这里 |
| `/Applications` | GUI 应用 (.app bundle)：Chrome、VS Code、Ollama | 能 |
| `/Users` | 所有用户的家目录（你的在 `/Users/mengzhong__ren`） | 只能改你自己的 |
| `/tmp` | 临时文件，重启清空 | 能 |
| `/System` | macOS 核心系统文件，绝对不要碰 | 绝对不能 |
| `~` | 即 `/Users/mengzhong__ren`——你所有工作文件都在这里 | 你的地盘 |
| `/Library` | 系统级配置、LaunchDaemons/LaunchAgents（launchd 服务定义） | 部分需要 sudo |
| `/private/etc` | 配置文件（相当于 Linux 的 `/etc`） | 大多需要 sudo |
| `/dev` | 设备文件——不是存数据的，是通向内核驱动或硬件的接口 | 不能（由内核自动管理） |

你装的所有命令行工具几乎都在 `/opt` 或 `/usr/local`——macOS 通过 SIP 把 `/bin`、`/usr/bin` 锁死，保证你不小心 `sudo rm` 也破坏不了系统。

### 2.9 为什么点开头的文件是隐藏的

`.env`、`.zshrc`、`.gitignore`——文件名以 `.` 开头。这是 Unix 至少 50 年的约定：**ls 默认不显示以 `.` 开头的文件**。不是加密、不是特殊权限、不是文件系统特性——就是 `ls` 的源代码里写了一句 `if (name[0] == '.') continue;`。

### 2.10 `ls` 详解——每个 flag 对应什么信息

```bash
ls                  # 只显示文件名
ls -l               # 长格式——显示大小、权限、所有者、时间
ls -a               # 显示隐藏文件（-a = all）
ls -A               # 显示隐藏文件，但不包括 . 和 ..
ls -h               # 人类可读的大小（1K、234M、3.4G 而非 1428576）
ls -t               # 按修改时间排序（最新的在最上面）
ls -tr              # -t + -r 逆序 = 最旧的在最上面
ls -R               # 递归列出所有子目录
ls -S               # 按文件大小排序

# 常用组合
ls -lah             # -l 长格式 + -a 全显示 + -h 可读大小
ls -ltr             # -l + -t 按时间排序 + -r 逆序 = 最近修改的在最下面
```

**`ls -la` 输出逐列解读**：

```
drwxr-xr-x  12 mengzhong__ren  staff  384  Jun 14 10:30  agent-learning-journey
-rw-r--r--   1 mengzhong__ren  staff  2048 Jun 14 09:15  .env
│││││││││   │  │              │      │    │             │
│││││││││   │  │              │      │    │             └── 文件名
│││││││││   │  │              │      │    └── 最后修改时间 (mtime)
│││││││││   │  │              │      └── 文件大小 (字节)
│││││││││   │  │              └── 所属的组 (staff = gid 20)
│││││││││   │  └── 所属的用户 (mengzhong__ren = uid 501)
│││││││││   └── 硬链接数（= inode 引用计数）
││││││││└───── others 的 execute (x)
│││││││└────── others 的 write (w)
││││││└─────── others 的 read (r)
│││││└──────── group 的 execute
││││└───────── group 的 write
│││└────────── group 的 read
││└─────────── owner 的 execute
│└──────────── owner 的 write
└───────────── owner 的 read    d = directory, - = regular file, l = symlink
```

第一个字符表示文件类型：`-` 普通文件、`d` 目录、`l` 符号链接、`p` 命名管道、`c` 字符设备、`b` 块设备、`s` 套接字。不是只有普通文件和目录——`/dev` 下面全是设备文件（`c` 和 `b`），它们不是存数据的，是内核向用户空间暴露的硬件接口。

### 2.11 常用文件操作命令——每个背后都是系统调用

```bash
# 创建
touch newfile.txt            # 更新文件时间戳到"现在"；文件不存在则创建空文件
                             # 底层：utimes() 系统调用。如果 inode 不存在 → open(O_CREAT)
mkdir newdir                 # 创建目录
mkdir -p a/b/c               # 递归创建所有父目录（-p: 父目录不存在则自动创建，已存在不报错）

# 复制
cp file.txt copy.txt         # 复制文件——内核 open() 源文件读 → write() 新文件
                             # 新文件有独立的 inode，和原文件无关系
cp -r project/ backup/       # 递归复制整个目录（-r = recursive）
cp -a project/ backup/       # 归档模式——保留权限、时间戳、符号链接（比 -r 更完整）

# 移动 / 重命名（mv 既是移动也是重命名——在 Unix 里它们是同一个系统调用）
mv oldname.txt newname.txt   # 重命名：rename() 系统调用，只改目录项里的名字
mv file.txt ~/Documents/     # 同一个文件系统内：只改目录项
                             # 跨文件系统：先 cp 再 rm（因为 inode 不通用）

# 删除
rm file.txt                  # unlink() 系统调用——删目录项，inode 引用计数 -1
rm -r project/               # 递归删
rm -rf project/              # -f: 不询问、不报不存在的文件、silent
rmdir emptydir/              # 只删空目录——目录非空时拒绝，比 rm -r 安全

# 查看 inode 信息
stat file.txt                # 完整 inode 信息（大小、权限、所有时间戳、块信息）
stat -f "%i %Sp %l %N" *     # -f 自定义格式：inode号 权限(字符串) 引用计数 文件名
ls -li                       # 快速看 inode 号 + 引用计数
```

**`mv` 的底层**：在同一个文件系统内，`mv` 只调 `rename()` 系统调用——改一条目录项。不读不写文件数据本身。一个 6GB 的 GGUF 模型在同磁盘的移动是瞬间完成的。跨文件系统时（比如从 SSD 移到 U 盘），`mv` 只能走 `cp + rm`——6GB 数据必须完整复制。

**`rm` 的底层**：`rm` 不擦除数据——它调 `unlink()`，删目录项 + inode 引用计数 -1。计数归零时，inode 和数据块被标记为空闲。数据还在磁盘上——被标记为"可覆盖"，但还未被覆盖。安全删除需要手动覆写（`rm -P` 在 BSD/macOS 上可以覆写后再删，但 APFS 的写时复制让这不再可靠——需要 FileVault 全盘加密来保证删除的安全性）。

**`rm -rf` 的注意事项**：永远不要在 `-rf` 中嵌套通配符——`rm -rf / tmp/*` 中间的空格会把 `/` 当作目标目录（删除整个系统）。养成习惯：敲 `rm -rf` 前先 `ls <同样的路径>` 确认。

### 2.12 查看文件内容——cat、less、head、tail

```bash
cat file.py              # 整个文件一次打印到 stdout。小文件（<几 KB）用
less file.py             # 分页查看。空格=下一页，b=上一页，q=退出，/=搜索
                         # less 不一次加载整个文件——它按需读块，大文件秒开
head -20 file.py         # 前 20 行。默认前 10 行
tail -20 file.py         # 后 20 行。默认后 10 行
tail -f server.log       # -f = follow：新行写入立刻显示（实时追日志）
tail -F server.log       # -F = follow + 文件被删/轮转后重新打开（比 -f 更稳）
```

**为什么 `tail -f` 能实时追？** 不是循环 `cat + sleep`。macOS 上它用 `kqueue`（Linux 上用 `inotify`）——内核在文件被修改时主动通知 `tail` 进程："这个 inode 的某个数据块被写入了新内容"。`tail` 收到通知后 `read()` 新字节，打印，继续等下一个通知。没有轮询开销。

```bash
tail -f ~/.ollama/logs/server.log           # 追 Ollama 日志
tail -f log.txt | grep "error"              # 追日志但只显示含 "error" 的行
```

### 2.13 查找文件和内容——find 和 grep

```bash
# find：按名称/类型/大小/时间搜索
find . -name "*.py"                        # 当前目录及所有子目录中的 .py 文件
find . -name "*.py" -type f                # 只要普通文件（排除恰好叫 xxx.py 的目录）
find . -name "*.gguf" -size +1G            # 大于 1GB 的模型文件
find . -mtime -7                           # 最近 7 天修改过的文件
find . -mtime +30                          # 30 天前修改的文件（+ = 大于，- = 小于）
find . -type f -name "*" | wc -l           # 所有文件的个数
find . -size +100M -exec ls -lh {} \;      # 大于 100MB 的文件，列详细信息
find . -name "__pycache__" -type d -exec rm -rf {} \;  # 找到并删除

# find + -exec：对每个找到的文件执行一个命令
# {} 是占位符——代表找到的每个文件路径
# \; 是 -exec 的结束符（\ 转义 ;，防止 shell 把 ; 当命令分隔符）
# 每个文件都单独 fork+exec 一次命令——效率低但安全

# 更快的方式：用 xargs 一次性传参（见第 6 章）

# grep：按文件内容搜索
grep "pattern" file.txt                    # 在单个文件中搜索
grep -r "pattern" .                        # -r 递归搜索整个目录树
grep -rn "class Tool" .                    # -n 显示行号
grep -rc "TODO" .                          # -c 仅计数，不打印匹配行
grep -rl "OPENAI_API_KEY" .                # -l 仅打印文件名
grep -i "ERROR" log.txt                    # -i 忽略大小写
grep -v "DEBUG" log.txt                    # -v 排除匹配行（仅打印不匹配的）
grep -E "error|warning|fatal" log.txt      # -E 扩展正则，支持 | (或)
grep -A 3 "Error" log.txt                  # 匹配行 + 后 3 行 (-A = After)
grep -B 2 "Error" log.txt                  # 匹配行 + 前 2 行 (-B = Before)
grep -C 5 "Error" log.txt                  # 匹配行 + 前后各 5 行 (-C = Context)
grep -w "def" file.py                      # -w 仅匹配整个词（不会匹配 "define" 里的 "def"）
```

`grep` 名字的来历：1974 年，Unix 的 `ed` 文本编辑器。命令 `g/re/p` = 全局（g）搜索正则表达式（/re/）并打印（p）。这个功能后来独立出来成了一个命令。

---

## 3. 权限模型——rwx、sudo、SIP

### 3.1 Unix rwx 三位制

Unix 把所有用户分成三个圈层，每种操作可独立授予：

```
owner  (u) ──→ read (r=4) + write (w=2) + execute (x=1)
group  (g) ──→ read (r=4) + write (w=2) + execute (x=1)
others (o) ──→ read (r=4) + write (w=2) + execute (x=1)
```

`chmod 755 file` 的数字是八进制——每组 3 个二进制位：

```
7 = 111 = rwx    (owner 全权限)
5 = 101 = r-x    (group 可读不可写可执行)
5 = 101 = r-x    (others 可读不可写可执行)
```

常见的组合：

| chmod | 含义 | 什么时候用 |
|---|---|---|
| `755` | owner 全权限，别人只读/执行 | 目录、普通可执行文件 |
| `644` | owner 可读写，别人只读 | 普通文件、源代码 |
| `700` | 只有 owner 全权限，别人全禁 | SSH 私钥 (`~/.ssh/id_ed25519`) |
| `600` | owner 可读写，别人全禁 | 敏感配置文件 |
| `777` | **所有人全权限——不要用** | 几乎永远不应该出现 |

用符号方式更直观（初学者推荐）：

```bash
chmod +x script.sh          # 全角色加执行权限
chmod u+x script.sh         # 只给 owner 加执行
chmod g-w file.txt          # 去掉 group 的写权限
chmod o-rwx secret.key      # 去掉 others 的所有权限
```

### 3.2 权限检查的内核流程

当进程调用 `open("/tmp/test.txt", O_RDONLY)` 时，内核做以下检查：

1. 进程有 uid（用户 ID）和 gid（组 ID）——来自 fork 时继承的凭据
2. 文件 inode 有 owner uid、group gid、mode bits
3. 内核比对：
   - 进程的 uid == 文件的 owner uid？ → 用 owner 权限位 (rwx 的前三位)
   - 不相等 → 进程的 gid == 文件的 group gid？ → 用 group 权限位 (中间三位)
   - 都不等 → 用 others 权限位 (后三位)
   - 进程的 uid == 0？ → 是 root，直接放行（root 跳过权限检查）
4. 权限位匹配 → 允许打开；不匹配 → 返回 EACCES (Permission denied)

### 3.3 sudo 在做什么

```bash
sudo rm /System/some_file    # 以 root 身份执行 rm
```

`sudo` = "superuser do"。它是一个 setuid 程序——文件本身的 owner 是 root，并且设置了 setuid 位（`chmod u+s`）。当任何用户运行它时，内核把进程的 effective uid 设置为文件 owner 的 uid（即 root = 0）。root 不受权限限制。

但 `sudo` 不是无条件的——它先检查 `/etc/sudoers`（由 `sudo visudo` 编辑），确认你在白名单里，然后要你输入自己的密码（不是 root 的密码）。这是为了让：知道你的密码的人才能以 root 身份执行命令，而不知道你密码的人即使坐在你解锁的 Mac 前也不能 `sudo rm -rf /`。

为什么 `brew install` 不需要 sudo 但 `pip install` 有时候需要？brew 装在 `/opt/homebrew/`，这个目录的所有者是你（mengzhong__ren）。所有 brew 管理的文件都在你的名下，你有写权限。pip 如果装包到系统 Python 的 `site-packages`（`/usr/lib/python3.9/site-packages/`，所有者 root），就必须 sudo。你的 conda Python 装在 `/opt/anaconda3/`，所有者是你，不需要 sudo。

### 3.4 chown——改变文件所有者

```bash
chown mengzhong__ren file.txt          # 把文件所有者改为 mengzhong__ren
chown -R mengzhong__ren project/       # 递归改整个目录
```

普通用户不能把文件所有者改成别人（安全限制——如果你能把自己的恶意文件改成 root 属主然后 setuid，系统就被破了）。只有 root 可以自由 `chown`。

### 3.5 SIP——为什么你改不了 /usr/bin 下的东西

macOS 从 10.11 El Capitan (2015) 引入了 **SIP (System Integrity Protection)**——即使你用 `sudo`（即使你以 root 身份），也不能修改 `/usr/bin`、`/bin`、`/System`、`/sbin` 下的文件。

SIP 不是文件权限——文件权限在 inode 里，SIP 是**内核的强制访问控制 (Mandatory Access Control, MAC)**，在 inode 权限检查之外、更底层。内核在执行 `write()` 系统调用之前额外检查：这个操作的进程是不是被 Apple 签名的？目标文件路径是不是在 SIP 保护区？如果是，即使 uid=0 也拒绝。

SIP 的存在解释了为什么 macOS 自带的 `/usr/bin/python3` 你碰不了——不是你没权限，是系统不让你碰。你要用 Python 必须自己装（brew / conda / 官网下载），装到 `/opt` 或 `/usr/local`（这些路径不在 SIP 保护范围）。

---

## 4. 进程管理——fork、exec、信号、前后台

### 4.1 什么是进程

进程 = 一个运行中的程序的实例。它在内存里有一块自己的地址空间（代码 + 数据 + 堆 + 栈），在内核里有一个任务结构体（存着 PID、PPID、状态、打开的文件描述符表、信号处理器表）。

```
PID   进程 ID（内核为每个进程分配的唯一标识符）
PPID  父进程 ID（谁 fork 了我）
UID   执行这个进程的用户 ID
GID   组 ID
State 运行中 / 睡眠 / 停止 / 僵尸
```

**进程树**：所有进程都是 PID=1 的**子子孙孙**。macOS 的 PID=1 是 `launchd`（Linux 是 `systemd` 或 `init`）。你在终端敲的任何命令，都是 zsh 的子进程，zsh 的子进程也可以再 fork 子进程（比如 shell 脚本里调了 python）。

### 4.2 fork + exec——每个命令背后的系统调用

这是 Unix 最核心的设计。零例外——你敲的每一条命令都走这条路：

```
fork():
  内核创建当前进程的一份精确副本（"子进程"）。
  子进程拥有父进程的：
    - 内存的完整复制 (copy-on-write: 不立即拷贝，只在有写入时拷贝对应页)
    - 文件描述符表 (子进程继承父进程打开的所有 fd，包括 PTY slave)
    - 环境变量
    - 当前工作目录
    - 信号处理器表
  唯一不同：fork() 的返回值。父进程得到子进程的 PID；子进程得到 0。

  为什么叫 fork（叉子）？因为一个进程在这一点分叉成两个——
  同样代码、同样数据、同样状态。通过检查 fork() 返回值来决定走不同分支。

exec():
  子进程调用 exec("/bin/ls")。
  内核把子进程的地址空间清空，加载 ls 的 Mach-O 代码和数据，
  把 CPU 指令指针设为 ls 的入口点。
  子进程"变成" ls——不再是原来那个程序的副本。
  PID 不变（还是子进程的 PID），但运行的是 ls 的代码。
```

**组合在一起**：

```
zsh (PID 100) 敲了 ls
  → fork() → 子进程 (PID 101, zsh 的副本)
  → 子进程 exec("/bin/ls") → 现在是 PID 101 在跑 ls
  → ls 完成任务 → exit(0) → 内核回收 PID 101
  → 内核向 zsh (PID 100) 发 SIGCHLD: "你的子进程 101 已退出"
  → zsh 的 SIGCHLD 处理器: waitpid(101) 获取退出状态 → 打印提示符
```

**为什么 Ollama 启动 llama.cpp 用子进程？** Ollama daemon fork 一个子进程，子进程 exec("llama-server")。如果 llama.cpp 因为显存爆炸或模型 bug 崩溃，只有那个子进程死掉——Ollama daemon 本身不受影响。这就是你的 06-ollama 笔记里讲的"进程隔离"。

### 4.3 前台 vs 后台 & 作业控制

```bash
ollama serve              # 前台运行——zsh 调用 waitpid，不显示新提示符
ollama serve &            # 后台运行——zsh 不 wait，立刻打印新提示符
                          # 打印: [1] 51234（[作业号] PID）
```

Shell 的作业控制命令：

```bash
jobs              # 列出当前 shell session 的所有后台作业
    [1]  - running    ollama serve
    [2]  + suspended  python train.py

fg %1             # 把作业 1 拉回前台
bg %2             # 让暂停的作业 2 在后台继续跑
kill %1           # 杀掉作业 1
```

`Ctrl+Z`：发送 SIGTSTP 给前台进程，暂停它（不是终止）。进程状态变为 Stopped（T），不消耗 CPU。
`bg`：给暂停的进程发 SIGCONT，让它在后台继续跑。
`fg`：把后台进程拉回前台——shell 重新 wait 它。

**`&` 放到后台的进程在终端关闭后会怎样？** 终端关闭 → PTY master 被释放 → 内核向所有把该 PTY slave 作为控制终端的进程发 SIGHUP。进程中默认行为是收到 SIGHUP 后自杀。

如果你想让进程在终端关了以后继续跑：

```bash
nohup ollama serve &          # nohup 忽略 SIGHUP，终端关了也不死
ollama serve & disown         # disown 把进程从 shell 的作业列表中移除——之后发 SIGHUP 时 shell 不会管它
```

`nohup` 的输出默认写入 `~/nohup.out`（如果 stdout 是终端的话）。

### 4.4 信号——不是你杀进程，是给它发"通知"

信号是内核发给进程的整数——一种进程间异步通知机制。进程可以注册"信号处理器"来决定收到信号后做什么。

| 信号 | 编号 | 谁发 | 默认行为 | 进程能忽略吗 | 进程能捕获吗 |
|---|---|---|---|---|---|
| **SIGINT** | 2 | 内核（你按 Ctrl+C） | 终止进程 | 能 | 能——Python 可以 `try/except KeyboardInterrupt` |
| **SIGTERM** | 15 | kill 命令（默认） | 终止进程 | 能 | 能——可以注册 cleanup 函数，保存状态后自杀 |
| **SIGKILL** | 9 | kill -9 命令 | 强制终止 | **不能** | **不能**——内核直接清除 |
| **SIGTSTP** | 20 | 内核（你按 Ctrl+Z） | 暂停进程 | 能 | 能 |
| **SIGCONT** | 19 | fg / bg 命令 | 恢复暂停的进程 | 不能 | 能 |
| **SIGHUP** | 1 | 终端关闭时 | 终止进程 | 能 | 能——很多服务器用 SIGHUP 来实现"重载配置" |
| **SIGCHLD** | 20 | 内核（子进程退出时） | 忽略 | 能 | 能——shell 用它感知子进程退出 |

**`Ctrl+C` 为什么在终端里不是"复制"而在浏览器里是？** 因为终端是老东西，GUI 是后来者。在终端仿真器里，`Ctrl+C`（ASCII 码 0x03, ETX）被 line discipline 截获，翻译成 SIGINT。在 GUI 应用里，快捷键由应用的 key binding 系统决定——浏览器把 `Cmd+C` 定义为复制，`Ctrl+C` 通常不生效。

**`kill -9` 为什么是最后手段？** `kill PID`（不发 -9）给进程一个清理的机会——它可以在 SIGTERM 处理器里关闭文件描述符、写日志、保存状态。`kill -9` 直接让内核清除进程，没有机会做任何清理——文件可能只写了一半、共享内存可能还锁着。永远先试 `kill PID`（SIGTERM），不行再 `kill -9 PID`（SIGKILL）。

### 4.5 找到并操作进程

```bash
# 找进程
ps aux                          # 所有进程的快照
ps aux | grep ollama            # 只显示含 ollama 的
pgrep -l ollama                 # 按进程名查找，打印 PID + 进程名
pgrep -f "llama-server"         # 全命令行匹配（-f = full）

# 杀进程
kill 51234                      # SIGTERM——请退出
kill -9 51234                   # SIGKILL——强制杀
killall ollama                  # 杀掉所有名为 ollama 的进程（等于 pgrep ollama | xargs kill）
pkill -f "python train.py"      # 按完整命令行匹配并杀
```

**`ps aux` 输出解读**：

```
USER     PID  %CPU %MEM     VSZ    RSS   TT  STAT  STARTED     TIME COMMAND
mengzhong 51234 95.2 42.1 4151200 6745600 ??  R    10:30AM  2:15.34 llama-server --model ...

%CPU  95.2  → 单核 100%，说明 GPU 推理中（CPU 在等 GPU 完成内存传输），实际计算在 GPU 上
%MEM  42.1  → 总内存 16GB × 42.1% ≈ 6.7GB —— 模型权重 + KV Cache 的总占用
VSZ         → 虚拟内存大小（地址空间——由 mmap 的 GGUF 文件大小决定）
RSS         → 实际占用的物理内存（驻留集大小）
STAT R      → Running（正在运行或在运行队列里等着）
TT ??       → 没有绑定终端（后台 daemon）
```

### 4.6 进程查看的三种层次

| 命令 | 显示什么 | 适合 |
|---|---|---|
| `ps aux` | 进程快照（瞬间） | 脚本化、快速查 PID |
| `btop` / `htop` | 实时 TUI 仪表盘（CPU/内存/磁盘/进程树） | 日常监控，直观 |
| `sudo powermetrics` | Apple Silicon 硬件计数器（GPU 频率、功耗、内存带宽） | LLM 推理性能分析 |

---

## 5. 管道、重定向与文件描述符——Unix 最核心的组合哲学

这是 Unix 区别于其他操作系统的核心特性。Windows 也有命令行，但它不具备"把一个小程序的输出无缝喂给另一个小程序"的管道哲学。

### 5.1 文件描述符——一个整数代表"打开的文件"

每个进程在内核里有一个"打开文件表"——文件描述符是这张表的索引，一个非负整数：

```
进程的打开文件描述符表：
  fd 0 → PTY slave (作为 stdin——键盘输入)
  fd 1 → PTY slave (作为 stdout——正常输出)
  fd 2 → PTY slave (作为 stderr——错误输出)
  fd 3 → 未使用
  fd 4 → /tmp/data.json (被你 open() 打开的文件)
  ...
```

新打开的文件总是用**最小的未使用 fd**。这就是为什么 `2>&1` 可行——它让 fd 2 指向与 fd 1 相同的东西。

### 5.2 重定向操作符全表

```bash
# 输出重定向
command > file.txt          # stdout 写到文件（覆盖原内容）
command >> file.txt         # stdout 追加到文件末尾
command 2> errors.txt       # stderr 写到文件
command > out.txt 2>&1      # stdout 和 stderr 都写到同一个文件

# 关键：2>&1 必须写在 > 后面！
# 为什么？因为 shell 从左到右执行重定向：
#   > out.txt   → 打开 out.txt，fd 1 指向它
#   2>&1        → fd 2 指向 fd 1 当前指向的东西（out.txt）
# 如果反过来写 2>&1 > out.txt：
#   2>&1        → fd 2 指向 fd 1 当前指向的东西（终端）
#   > out.txt   → fd 1 指向 out.txt
#   结果：stdout 进文件，stderr 仍在终端——不是你想要的

# 输入重定向
command < input.txt         # 从文件读取 stdin
command <<< "hello world"   # Here String：直接把后面的字符串传给 stdin
command << EOF              # Here Document：多行输入，直到遇到 EOF
line1
line2
EOF

# 全部重定向
command &> all.txt          # stdout + stderr 都写同一个文件（等效 > file 2>&1）
command &>/dev/null         # 丢弃所有输出
```

### 5.3 /dev/null 和 /dev/zero——不是真文件

```bash
command > /dev/null         # 丢弃 stdout
command 2> /dev/null        # 丢弃 stderr
command &>/dev/null         # 丢弃一切
```

`/dev/null` 不是一个存数据的文件——它是内核提供的特殊字符设备。写入 `/dev/null` 的所有数据被内核直接丢弃（不占任何磁盘空间）；读取 `/dev/null` 立即返回 EOF。它是一个无限的"数据黑洞"。

`/dev/zero` 返回无限个 `\0`（空字节）——常用于创建填零文件。

### 5.4 管道的完整原理——pipe() 系统调用

```bash
command1 | command2 | command3
```

管道是进程间通信（IPC），和重定向（进程↔文件）本质不同：

```
shell 执行 ls | wc -l 时的操作序列：

1. shell 调用 pipe() 系统调用
   内核创建一对 fd：fd[0] (读端) 和 fd[1] (写端)
   它们之间是一个内核缓冲区——写在 fd[1] 的数据可以从 fd[0] 读出来

2. shell fork() 第一个子进程 (将来跑 ls)
   子进程继承 fd[0] 和 fd[1]

3. 在第一个子进程中：
   close(fd[0])              ← 关掉读端（用不上）
   dup2(fd[1], STDOUT_FILENO) ← 把 fd[1] 复制到 fd 1 (stdout)
   close(fd[1])              ← 关掉原始的 fd[1]
   exec(ls)                  ← ls 写 stdout → 写进管道

4. shell fork() 第二个子进程 (将来跑 wc)
   子进程继承 fd[0] 和 fd[1]

5. 在第二个子进程中：
   close(fd[1])              ← 关掉写端（用不上）
   dup2(fd[0], STDIN_FILENO)  ← 把 fd[0] 复制到 fd 0 (stdin)
   close(fd[0])              ← 关掉原始的 fd[0]
   exec(wc)                  ← wc 读 stdin → 从管道读

6. shell 关闭自己手里的 fd[0] 和 fd[1]（不管了）
7. shell wait() 两个子进程都结束
```

**关键设计**：
- 所有子进程同时运行（shell fork 后不等——两个子进程并发）
- `ls` 往管道写了多少数据 `wc` 就立刻读多少（流水线并发，不需要中间文件）
- 管道有容量上限（通常 64KB）——如果 `ls` 写得比 `wc` 读得快，写操作会阻塞，等 `wc` 消费一些后再继续写。这是内核流量控制

**管道 vs 重定向**：

| | 管道 `\|` | 重定向 `>` |
|---|---|---|
| 数据流向 | 进程→进程（IPC） | 进程→文件 |
| 中间存储 | 无（内核缓冲区，不落盘） | 文件（落盘） |
| 并发 | 两个进程同时跑 | 不需要并发 |
| 适用场景 | "把 A 的结果喂给 B 做后续处理" | "保存输出到文件" |

### 5.5 命名管道（FIFO）和进程替换

普通管道只在父子进程间通信（需要共享 fd）。不相关的进程怎么用管道？**命名管道（FIFO）**——有名字，出现在文件系统里：

```bash
mkfifo mypipe                # 创建命名管道
ls > mypipe &                # 启动 ls，输出到命名管道（阻塞直到有人读）
cat mypipe                   # 从命名管道读取
```

两个不相关的进程——`ls` 和 `cat`——通过 `mypipe` 这个文件系统入口通信。但 `mypipe` 不是文件——它不存数据，只是一个内核缓冲区的"接头点"。

**进程替换**（zsh/bash 特性）：

```bash
diff <(ls dir1) <(ls dir2)   # 把两个命令的输出伪装成"文件路径"传给 diff
                              # <(cmd) 创建命名管道，返回路径如 /dev/fd/11
```

---

## 6. 文本处理命令——管道的另一半价值

管道如果只是连接两个命令，好用但有限。产生真正的威力的是**你可以把通用的文本处理程序插入管道的任何位置**——不是为每个任务写专用程序，而是组合通用工具。

### 6.1 grep——搜索文本

```bash
grep "pattern" file.txt                  # 基本搜索
grep -i "ERROR" log.txt                  # 不区分大小写
grep -v "DEBUG" log.txt                  # 排除（-v）匹配行
grep -r "class Tool" .                   # 递归搜索当前目录
grep -rn "TODO" .                        # 加行号（-n）
grep -c "error" log.txt                  # 只输出匹配行数（-c）
grep -l "OPENAI_API" *.py                # 只输出文件名（-l），不输出匹配行
grep -A 3 "Error" log.txt                # 匹配行 + 后 3 行（-A=After）
grep -B 2 "Error" log.txt                # 匹配行 + 前 2 行（-B=Before）
grep -C 5 "Error" log.txt                # 匹配行 + 前后各 5 行（-C=Context）
grep -E "error|warning|fatal" log.txt    # 扩展正则（-E），\| 表示 OR
```

**正则表达式元字符速览**（grep 默认用基本正则，`-E` 开启扩展正则）：

```
.      任意单个字符
*      前一个字符重复 0 次或任意多次
+      前一个字符重复 1 次或任意多次（需要 -E）
?      前一个字符重复 0 次或 1 次（需要 -E）
^      行首
$      行尾
[abc]  字符类：a、b 或 c 中的任意一个
[^abc] 否定字符类：不是 a、b、c 的任意字符
\d     数字 [0-9]（需要 -P Perl 正则）
\s     空白字符（需要 -P）
|      OR：左边或右边（需要 -E）
()     分组（需要 -E）
```

grep 名字的来历：**g**lobally search a **r**egular **e**xpression and **p**rint。来自 1974 年 `ed` 文本编辑器的命令 `g/re/p`。

### 6.2 sort——排序

```bash
sort file.txt                     # 按字母序排序
sort -n file.txt                  # 按数值排序（否则 "10" < "2" 按字符串序）
sort -r file.txt                  # 逆序
sort -k 2 file.txt                # 按第 2 列排序（-k = key）
sort -k 2 -n -t ',' data.csv      # 按逗号分隔的第 2 列数值排序
sort -u file.txt                  # 去重（只保留每组的第一个）
```

### 6.3 uniq——去重

```bash
uniq file.txt                   # 删除相邻重复行（必须先 sort！）
sort file.txt | uniq            # 真正的去重：先排序，再删相邻重复
sort file.txt | uniq -c         # 去重并统计每行出现次数
sort file.txt | uniq -d         # 只显示重复的行（-d = duplicates）
```

**为什么 uniq 只删相邻重复？** 因为它是为流式数据设计的——一行一行读，比较"当前行和上一行是否一样"。如果先排序，所有相同的行就会聚集在一起，uniqu 就能正确去重。不排序直接用 uniq 只会在每段重复的头一次去重。

### 6.4 wc——计数

```bash
wc file.txt              # 打印：行数 词数 字节数 文件名
wc -l file.txt           # 只计行数
wc -w file.txt           # 只计词数
wc -c file.txt           # 只计字节数
wc -m file.txt           # 只计字符数（-c 和 -m 对中文不一样：一个中文字 = 3 字节 = 1 字符）

ls *.py | wc -l          # 当前目录有几个 .py 文件
```

### 6.5 cut——按列切分

```bash
cut -d ',' -f 1,3 data.csv       # 按逗号分隔，取第 1 和第 3 列
cut -c 1-10 file.txt             # 取每行的第 1-10 个字符
cut -d ':' -f 1 /etc/passwd      # 取 passwd 文件的用户名（第 1 列）
```

### 6.6 sed——流编辑器

sed 的完整语法能写一本书。你只需要知道它 80% 的场景都是一种操作：

```bash
sed 's/old/new/' file.txt            # 替换每行的第一个 old
sed 's/old/new/g' file.txt           # 替换每行的所有 old（g = global）
sed 's/old/new/g' file.txt           # 打印到 stdout（不改原文件）
sed -i '' 's/old/new/g' file.txt     # 直接改文件（macOS 语法）
sed -i 's/old/new/g' file.txt        # 直接改文件（Linux 语法，不需要 ''）

sed -n '5,10p' file.txt              # 只打印第 5-10 行
sed '/error/d' log.txt               # 删除含 error 的行
```

**sed -i 在 macOS 和 Linux 上的不同**：macOS 的 sed 是 BSD 版本，`-i` 后面**必须**跟备份后缀（空字符串 `''` 表示不备份）。Linux 的 sed 是 GNU 版本，`-i` 不需要后缀。这就是为什么从 Linux 教程抄的命令在 Mac 上经常报错。

### 6.7 awk——按列处理文本

awk 是一个完整的编程语言。你只需要记住这一种用法就覆盖大部分需求：

```bash
awk '{print $1, $3}' file.txt        # 打印第 1 和第 3 列（默认按空白分隔）
awk -F ',' '{print $1}' data.csv     # 指定逗号为分隔符
awk '{sum += $2} END {print sum}'    # 第 2 列求和
```

### 6.8 xargs——把 stdin 变成参数

```bash
find . -name "*.py" | xargs wc -l           # 对每个 .py 文件跑 wc -l
find . -name "__pycache__" -type d | xargs rm -rf  # 找到并删除
git diff --name-only | xargs grep "TODO"         # 只搜改过的文件
```

**xargs 为什么存在**：很多命令不是从 stdin 读参数的——它们要求参数写在命令行上。`wc -l file1 file2` 是合法的，但 `wc -l < file1` 只有 stdin 被重定向，wc 不知道文件名。xargs 把 stdin 的每一行转成下一个命令的命令行参数。

`find ... -exec` 和 `find ... | xargs` 的区别：`-exec` 为每个找到的文件启动一次命令（找到 1000 个文件就 fork+exec 1000 次），xargs 默认把多个参数拼在一次命令里（找到 1000 个文件可能只跑 1 次 `rm file1 file2 ... file1000`）——效率高很多。

---

## 7. 压缩与归档——tar、gzip、zip

### 7.1 压缩和归档是两个操作

```
归档 (Archive)：把多个文件和目录打包成一个文件。
                不改变大小。tar = Tape ARchive。

压缩 (Compress)：用算法把数据变小。
                只对单个文件有效。gzip (LZ77 + Huffman)。
```

这就是为什么 `tar.gz` 是两个后缀：先用 `tar` 把多个文件捆成一个 `.tar`，再用 `gzip` 把这个 `.tar` 压缩成 `.tar.gz`。

### 7.2 tar

```bash
# 创建
tar -czf archive.tar.gz project/       # 打包 + gzip 压缩
    -c  create（创建归档）
    -z  通过 gzip 压缩
    -f  指定文件名（必须放在最后，后面跟文件名）

tar -cjf archive.tar.bz2 project/      # 打包 + bzip2 压缩（更小但更慢）
tar -cf archive.tar project/           # 只打包不压缩

# 解压
tar -xzf archive.tar.gz                # 解压 + 拆包
    -x  extract（提取）
tar -xzf archive.tar.gz -C /tmp/       # 解压到指定目录（-C）
tar -xvf archive.tar.gz                # 加 -v 显示解压的文件列表（verbose）

# 查看（不解压）
tar -tzf archive.tar.gz                # 列出压缩包中的所有文件
```

**tar 为什么没 `-`？** 它是 Unix 最老的命令之一（1979 年）。当时很多命令的选项不需要 `-`——tar 一直保持着这个传统。`tar czf` 和 `tar -czf` 效果一样。现在约定：新手都写 `-`，不写谁看得懂。

### 7.3 gzip / gunzip

```bash
gzip file.txt           # 压缩 → file.txt.gz（原文件被删除！）
gunzip file.txt.gz      # 解压
gzip -k file.txt        # 压缩但保留原文件（-k = keep）
gzip -d file.txt.gz     # 解压（同 gunzip）
```

### 7.4 zip / unzip

zip 是跨平台的——Windows 原生支持，tar.gz 是 Unix 世界的格式：

```bash
zip -r archive.zip project/        # 打包+压缩（-r = recursive）
unzip archive.zip                  # 解压
unzip -l archive.zip               # 只看内容不解压
```

---

## 8. Shell 变量、环境变量与配置文件

### 8.1 Shell 变量 vs 环境变量

```bash
MY_NAME=mengzhong              # 普通 shell 变量——只在当前 shell 存活
echo $MY_NAME                  # 打印变量值（$ 前缀：取变量的值）
echo "Hello, $MY_NAME"         # 双引号内变量展开
echo 'Hello, $MY_NAME'         # 单引号内不展开——原样打印 $MY_NAME

export MY_NAME                 # 把 shell 变量"导出"——子进程也能读到
```

**`export` 到底做了什么？** 每个进程有一块"环境变量"内存区域，和 shell 变量是分离的。`export MY_NAME` 把 `MY_NAME` 从 shell 变量表复制到环境变量表。fork 时子进程继承父进程的环境变量表（但不继承 shell 变量）。所以：
- Shell 变量：当前 shell 进程自己用，子进程看不到
- 环境变量：随 fork 传递给子进程，子进程的代码通过 `os.getenv()` 读取

```python
import os
os.getenv("MY_NAME")  # 能读到——因为被 export 了
```

### 8.2 子 shell vs 子进程

```bash
(cd /tmp && ls)       # 括号启动子 shell——共享当前 shell 变量
pwd                   # 仍是原目录——子 shell 的 cd 不影响父 shell
```

子 shell 是 fork 后不 exec——还在运行 zsh 的代码。它共享普通 shell 变量（因为 fork 复制了 shell 进程的内存空间）。而外部命令（如 python、ls）是 fork 后 exec——子进程只继承环境变量，不继承 shell 变量。

这就是为什么 `conda activate` 必须写成 shell 函数而不是独立可执行文件——如果 conda 是一个独立程序，它在子进程里修改 PATH 和环境变量，子进程退出后修改全部丢失（子进程改不了父进程的环境）。conda 是 shell 函数——它在当前 shell 进程的上下文中运行，直接修改当前 shell 的环境。

### 8.3 .zshrc 是什么

每次新开终端窗口时，zsh 自动执行 `~/.zshrc` 里的所有代码。

```
新开终端窗口
  → 内核启动 login 进程 → 认证 → 启动 zsh 作为 login shell
  → zsh 按顺序读取这些文件（存在哪个就读哪个）：
      1. /etc/zprofile  (系统级，所有用户共享)
      2. ~/.zprofile    (个人 login shell 配置)
      3. /etc/zshrc     (系统级 zsh 配置)
      4. ~/.zshrc       (你的 zsh 配置 ← 最重要)
  → 逐行执行 → 显示提示符 → 等你敲命令
```

你的 `.zshrc` 里实际有三类东西：

```bash
# ① conda 注入 (让 conda 环境切换机制生效)
# >>> conda initialize >>>
... (前文 1.5 节已解释过)
# <<< conda initialize <<<

# ② 环境变量 (API Key——所有从终端启动的程序能读到)
export DEEPSEEK_API_KEY="sk-eb0c9a7b27c94222aceb5aa6a326d998"
export GOOGLE_API_KEY="AIzaSyC8957..."
export DASHSCOPE_API_KEY="sk-87e7792..."

# ③ PATH 扩充
export PATH="/Users/mengzhong__ren/Downloads/LADR-2009-11A/bin:$PATH"
```

### 8.4 alias——给长命令起短名

```bash
alias ll='ls -la'                       # 经典 alias
alias gs='git status'                   # git status 的快捷
alias gd='git diff'
alias gp='git push'
alias activate='conda activate deep_learning'
alias ollama-log='tail -f ~/.ollama/logs/server.log'
```

alias 是 zsh 的一个内置机制——**在解析你输入的命令之前做纯文本替换**。敲 `ll` → zsh 发现它是 alias → 替换为 `ls -la` → 继续按正常流程处理。所以 alias 不能带参数（`alias mycd='cd $1'` 是无效的）——需要参数时用 shell 函数。

把这些 alias 加到 `.zshrc` 里，以后每次新开终端都能用：

```bash
# 编辑 .zshrc
vim ~/.zshrc  # 或 code ~/.zshrc

# 加上你的 alias
alias ll='ls -la'
alias gs='git status'

# 加了之后立刻生效（不用关终端）
source ~/.zshrc
```

`source`（缩写为 `.`）在当前 shell 里执行指定文件中的命令——不是 fork 子进程执行，是直接在当前进程里跑。

### 8.5 Shell 配置排错

```bash
source ~/.zshrc             # 改了 .zshrc 后手动重新加载

# 排错：开启命令回显——让你看到每一行被执行的代码
set -x
source ~/.zshrc
set +x                      # 关掉回显

# 检查 PATH 是否有问题
echo $PATH | tr ':' '\n'
```

`set -x` 让 zsh 在执行每条命令之前先打印它（以 `+` 开头）。当 `.zshrc` 中的某行报错但你不知道是哪行时——`set -x` 开回显后 `source ~/.zshrc`，zsh 每执行一行就打印一行。

---

## 9. 网络诊断基础——curl、ping、lsof、netstat

### 9.1 curl——命令行的 HTTP 客户端

```bash
curl http://localhost:11434/api/tags              # GET 请求，打印响应体
curl -X POST http://localhost:11434/api/generate \  # POST 请求
     -H "Content-Type: application/json" \          # 自定义 Header
     -d '{"model":"qwen3.5:9b","prompt":"Hello"}'   # JSON body

curl -v http://localhost:11434/api/tags             # verbose——显示请求/响应头
curl -s http://localhost:11434/api/tags | python -m json.tool  # 静默（-s）+ 格式化 JSON
curl -o output.json http://example.com/data.json    # 保存到文件（-o output）
curl -O http://example.com/data.json                # 保存为原始文件名（-O）
curl -L http://example.com                          # 跟随重定向（-L）
curl -I http://example.com                          # 只显示响应头（-I，HEAD 请求）
```

你每天都用到：不用 Python 调 Ollama API，一行 curl 就能确认 Ollama 是否活着。`curl` 本身不依赖任何东西——它直接用 socket 发 HTTP 请求，和 Python 的 `httpx` 库做的是同一件事。

### 9.2 ping——主机可达性

```bash
ping google.com                          # 一直 ping，Ctrl+C 停止
ping -c 4 google.com                     # 只 ping 4 次（-c = count）
ping -i 0.5 google.com                   # 间隔 0.5 秒（默认 1 秒，需要 sudo）
```

`ping` 发的是 ICMP Echo Request 包——它不是 TCP/UDP，是 IP 层的独立协议。如果目标主机禁了 ICMP（很多云服务器这么做），ping 不通但不代表 HTTP/TCP 不能连——只说明 ICMP 被过滤了。

### 9.3 端口与连接

```bash
# lsof——列出打开的文件（包括网络 socket）
lsof -i :11434                           # 哪个进程在用 11434 端口
# → ollama  51234  mengzhong  7u  IPv4  0x...  0t0  TCP localhost:11434 (LISTEN)

lsof -i                                   # 所有网络连接
lsof -i TCP                               # 只看 TCP

# netstat——网络连接状态
netstat -an | grep 11434                  # 端口 11434 的连接状态
netstat -an | grep LISTEN                 # 所有正在监听的端口
```

`lsof -i` 的原理：Unix 一切皆文件，网络 socket 也不例外。进程打开一个 socket 监听某个端口时，这个 socket 在进程的文件描述符表中占一个条目（fd 7 之类的）。lsof 遍历所有进程的打开文件表，找出 fd 对应的网络连接信息。

### 9.4 下载文件——curl 和 wget

```bash
curl -O https://example.com/file.tar.gz           # 下载到当前目录
curl -L -o model.gguf https://hf.co/.../model.gguf  # 跟随重定向保存

wget https://example.com/file.tar.gz              # wget 更简洁但 macOS 默认没装
brew install wget                                 # 需要时再装
```

---

## 10. SSH 与远程连接

### 10.1 SSH 的原理（一句话版）

**SSH = 加密的远程终端。** 你在 Mac 上敲命令，加密后通过网络发到 Linux 虚拟机，虚拟机解密后执行，结果加密返回。中间的网络设备（路由器、交换机、你的校园网管理后台）看到的是加密字节流，不知道你发了什么。

```
你的 Mac Terminal → /usr/bin/ssh → 加密的 TCP 连接 → sshd (Linux 虚拟机) → bash
    ↑                                                              ↓
    └──────────── 返回的执行结果（加密） ←─────────────────────────┘
```

### 10.2 基本用法

```bash
ssh username@192.168.1.100           # 连到指定 IP
ssh username@hostname.local          # 连到主机名（局域网 mDNS）
ssh -p 2222 user@host               # 指定端口（默认 22）
ssh -v user@host                    # 详细模式——连接过程的所有调试信息
```

### 10.3 免密码登录——SSH Key 认证

```
你的 Mac                        Linux 虚拟机
─────────                       ─────────────
~/.ssh/id_ed25519 (私钥)         ~/.ssh/authorized_keys (存着你的公钥)
   ↑ 绝不离开本机                    ↑ 公钥可安全分发
```

**认证过程**：
1. 你运行 `ssh user@host`
2. 服务器发一条随机消息（challenge）
3. 你的 Mac 用私钥签名这条消息
4. 服务器用你预先存放的公钥验证签名
5. 签名有效 → 登录成功（不需要密码）

私钥永远不离开你的 Mac——服务器只有公钥。即使服务器被黑、公钥被偷，攻击者无法冒充你（因为没有私钥）。

```bash
# 生成密钥对（只做一次）
ssh-keygen -t ed25519 -C "your@email.com"
# → ~/.ssh/id_ed25519 (私钥，绝不给任何人)
# → ~/.ssh/id_ed25519.pub (公钥，放服务器上)

# 公钥放到服务器上（方法 1——自动）
ssh-copy-id user@192.168.1.100

# 公钥放到服务器上（方法 2——手动）
cat ~/.ssh/id_ed25519.pub | ssh user@host "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

# 验证——这次不用输密码了
ssh user@192.168.1.100
```

### 10.4 ~/.ssh/config——给 IP 起别名

```bash
# 编辑 ~/.ssh/config（没有就创建）
Host linuxml
    HostName 192.168.1.100
    User mengzhong
    Port 22
    IdentityFile ~/.ssh/id_ed25519

Host myserver
    HostName myserver.example.com
    User root
    Port 2222
    IdentityFile ~/.ssh/my_custom_key

# 然后只需要：
ssh linuxml          # 等价于 ssh -i ~/.ssh/id_ed25519 -p 22 mengzhong@192.168.1.100
ssh myserver
```

### 10.5 本地端口转发——把远程服务映射到本地

这是你在 Mac 上跑 VS Code 调远程 GPU 机器上 Jupyter Notebook 的关键：

```bash
# 远程的 Jupyter 在 localhost:8888，映射到本地 8080
ssh -L 8080:localhost:8888 user@remote-gpu

# 本地浏览器打开 http://localhost:8080
# 实际上在访问远程的 localhost:8888
# 流量通过 SSH 隧道加密转发
```

`-L 8080:localhost:8888` = 本地（Local）8080 端口 → 通过 SSH 隧道 → 远程的 localhost:8888。

### 10.6 后台隧道

```bash
ssh -N -f -L 8080:localhost:8888 user@remote
# -N: 不执行远程命令（只做端口转发，不打开 shell）
# -f: 认证完成后放到后台
# 你需要的是：隧道建好后本地能连，但不想在终端里留一个 ssh 登录窗口
```

### 10.7 文件传输

```bash
scp model.gguf linuxml:~/models/            # Mac → Linux
scp linuxml:~/logs/output.log ./            # Linux → Mac
scp -r project/ linuxml:~/                  # 拷贝整个目录（-r = recursive）
```

---

## 11. 包管理——pip、brew、conda 三张清单

你的 macOS 上用着三套独立的包管理器。这不是混乱——它们各自管不同层面的东西。

| 包管理器 | 管什么 | 清单在哪 | 你的实际例子 |
|---|---|---|---|
| **brew** | 系统级 CLI 工具 | `brew list` | ollama, git, btop, wget |
| **conda** | Python 版本 + 虚拟环境 | `conda list` | deep_learning 环境里的一切 |
| **pip** | 当前 Python 环境的 Python 包 | `pip list` | openai, torch, pydantic, ddgs |

```bash
# brew
brew install <pkg>          # 安装系统工具
brew list                   # 已安装的所有包
brew update && brew upgrade # 更新 brew 本身和所有包
brew info <pkg>             # 包详情（版本、依赖、安装路径）
brew uninstall <pkg>        # 卸载

# pip
pip install <pkg>           # 装包
pip list                    # 已装包列表
pip show <pkg>              # 某包的详细信息（位置、版本、依赖）
pip uninstall <pkg>         # 卸载
pip install -r requirements.txt  # 按清单批量安装

# conda
conda info --envs           # 列出所有虚拟环境
conda create -n myenv python=3.13  # 创建新环境
conda activate myenv        # 激活
conda deactivate            # 退出当前环境
conda list                  # 当前环境所有包
conda remove -n myenv --all # 删除整个环境
```

**为什么不用 brew 装 Python 包**：brew 管的是系统层——ollama、git、wget 是独立可执行文件，不依赖特定 Python 解释器。Python 包（openai、torch）必须依赖某个 Python 版本和 conda 环境——brew 感知不到你的 conda 环境树，装进去也找不到。

**pip 和 conda 的冲突**：不要在 conda 环境里混用 `conda install` 和 `pip install` 装同一个包——conda 和 pip 各自维护自己的依赖树，互相不知道对方装了啥。优先用 conda 装（它感知 Python 版本兼容性），conda 没有的再用 pip。

---

## 12. macOS 特有——launchd、brew services、系统诊断

### 12.1 launchd——macOS 的一号进程

macOS 的 PID=1 是 **launchd**（Linux 上是 systemd 或 init）。它的职责：

- 系统启动时按顺序启动所有系统服务
- 守护进程挂了自动重启
- 按时间计划运行定时任务（替代 Linux 的 cron）

launchd 的配置以 `.plist`（Property List）XML 文件存在以下目录：

```
~/Library/LaunchAgents/         # 你的用户级后台服务（brew 的 service 放这里）
/Library/LaunchDaemons/         # 系统级守护进程（需要 sudo）
/System/Library/LaunchDaemons/  # macOS 核心守护进程（SIP 保护）
```

### 12.2 brew services——用 launchd 管理后台服务

```bash
brew services list                # 所有 brew 管理的后台服务
brew services start ollama        # 启动 Ollama 守护进程（放到 LaunchAgents）
brew services stop ollama         # 停止
brew services restart ollama      # 重启（配置改了或服务卡住时用）
brew services info ollama         # 服务详情（PID、plist 位置、状态）
```

`brew services start ollama` 实际做的事：在 `~/Library/LaunchAgents/` 创建一个 `homebrew.mxcl.ollama.plist` 文件，然后让 launchd 加载它。从此之后每次开机，launchd 自动启动 Ollama——你不需要手动跑 `ollama serve`。

Ollama 有两种启动方式：
- `ollama serve`：前台运行，终端阻塞，`Ctrl+C` 退出（调试时用）
- `brew services start ollama`：后台 daemon，随开机自启（日常用）

你多数时候用的是第二种——所以打开终端、`python agent.py --local` 就能调，不需要另开窗口跑 `ollama serve`。

### 12.3 系统更新与信息

```bash
softwareupdate --list                        # 列出可用的 macOS 更新
softwareupdate --install -a                  # 安装所有更新
softwareupdate --install 'macOS Sequoia 15.6'   # 安装指定更新

system_profiler SPHardwareDataType           # 硬件信息（型号、芯片、内存、序列号）
sw_vers                                      # macOS 版本号
uname -a                                     # 内核版本（Darwin = macOS 内核）
```

### 12.4 电源与性能

```bash
pmset -g                             # 电源管理设置和当前状态
pmset -g therm                       # 热管理状态（CPU/GPU 节流情况）
```

---

## 13. Shell 脚本基础——当你需要重复做某件事

Shell 脚本就是把你在终端里敲的命令写进一个文件，一次执行。

### 13.1 基本结构

```bash
#!/bin/zsh
# 这是一个 shell 脚本——它里面的命令一行一行被 zsh 执行

set -e    # 任何命令返回非零退出码 → 脚本立刻退出
set -u    # 用了未定义的变量 → 立刻报错
set -x    # 打印每条执行的命令（调试用）

echo "=== 开始 Agent 测试 ==="

cd ~/Developer/agent/agent-learning-journey/01-handwritten-react
source ../../venv/bin/activate

python agent.py --local "Calculate 3600 divided by 24"
python agent.py --local "Write hello to test.txt and read it back"

echo "=== 测试完成 ==="
```

### 13.2 变量与传参

```bash
#!/bin/zsh

NAME="Mengzhong"
echo "Hello, $NAME"

echo "第一个参数: $1"
echo "第二个参数: $2"
echo "所有参数: $@"
echo "参数个数: $#"

# 运行: ./script.sh arg1 arg2
```

### 13.3 条件判断

```bash
#!/bin/zsh

if [ -f ".env" ]; then
    echo ".env 文件存在，开始测试"
    python agent.py --local "$1"
else
    echo ".env 文件不存在，请先配置 API Key"
    exit 1
fi
```

`[ -f ".env" ]` = 测试文件是否存在且为普通文件。常用判断：

```
[ -f file ]  文件存在且为普通文件
[ -d dir  ]  目录存在
[ -z str  ]  字符串为空
[ -n str  ]  字符串非空
[ "$a" = "$b" ]  两字符串相等
```

### 13.4 循环

```bash
#!/bin/zsh

# 对每个 .py 文件做语法检查
for file in *.py; do
    echo "Checking $file..."
    python -m py_compile "$file" && echo "  OK" || echo "  FAILED"
done

# 也可以从命令输出逐行循环
for model in $(ollama list | tail -n +2 | awk '{print $1}'); do
    echo "Model: $model"
done
```

### 13.5 一个你实际能用的示例——一键测试 Agent

```bash
#!/bin/zsh
# 保存为 ~/Developer/agent/test_agent.sh

set -e

cd ~/Developer/agent/agent-learning-journey/01-handwritten-react

# 检查虚拟环境
if [ ! -f "../../venv/bin/activate" ]; then
    echo "Error: 虚拟环境不存在"
    exit 1
fi

source ../../venv/bin/activate

QUERY="${1:-Calculate 3600 divided by 24}"
MODEL="${2:---local}"

echo "============================================"
echo "  Agent Test: $QUERY"
echo "  Model Flag: $MODEL"
echo "============================================"

python agent.py "$MODEL" "$QUERY"

# 使用方法：
#   chmod +x test_agent.sh
#   ./test_agent.sh "What is 2+2" --local
#   ./test_agent.sh                      # 用默认值
```

`${1:-default}` 的意思是：如果 `$1` 已设置，用 `$1`；否则用 `default`。

---

## 14. 速查索引——按"我想干什么"查

### 文件操作

| 我想干什么 | 命令 |
|---|---|
| 创建空文件 | `touch file.txt` |
| 创建多层目录 | `mkdir -p a/b/c` |
| 复制文件 | `cp src.txt dst.txt` |
| 复制整个目录 | `cp -r src/ dst/` |
| 移动/重命名 | `mv old.txt new.txt` |
| 删除文件 | `rm file.txt` |
| 删除目录及其内容 | `rm -rf dir/`（三思！） |
| 查找文件 | `find . -name "*.py"` |
| 查找含特定内容的文件 | `grep -r "pattern" .` |
| 查看文件（小） | `cat file.txt` |
| 查看文件（大，分页） | `less file.txt` |
| 看文件前 20 行 | `head -20 file.txt` |
| 看文件后 20 行 | `tail -20 file.txt` |
| 实时追日志 | `tail -f server.log` |
| 改变文件权限 | `chmod +x script.sh` |
| 创建符号链接 | `ln -s /usr/bin/python3 mypython` |

### 进程管理

| 我想干什么 | 命令 |
|---|---|
| 查看所有进程 | `ps aux` |
| 找特定进程 | `ps aux \| grep ollama` 或 `pgrep -l ollama` |
| 优雅终止进程 | `kill PID` |
| 强制杀掉进程 | `kill -9 PID` |
| 按名字杀进程 | `killall ollama` 或 `pkill ollama` |
| 后台运行命令 | `command &` |
| 终端关了也继续跑 | `nohup command &` 或 `command & disown` |
| 动态进程监控 | `btop` |
| GPU/功耗/带宽分析 | `sudo powermetrics --samplers gpu_power -i 2000` |

### 管道与文本处理

| 我想干什么 | 命令 |
|---|---|
| 搜索含 pattern 的行 | `grep "pattern" file.txt` |
| 递归搜索目录 | `grep -r "pattern" .` |
| 排序 | `sort file.txt` |
| 数值排序 | `sort -n file.txt` |
| 去重 | `sort \| uniq` |
| 统计行数 | `wc -l` |
| 按逗号取第 1、3 列 | `cut -d ',' -f 1,3` |
| 替换文本 | `sed 's/old/new/g'` |
| 把 stdin 变成参数 | `xargs command` |

### 网络与远程

| 我想干什么 | 命令 |
|---|---|
| 测试 Ollama API | `curl http://localhost:11434/api/tags` |
| 发 POST 请求 | `curl -X POST -H "Content-Type: application/json" -d '{...}' URL` |
| 查端口被谁占 | `lsof -i :11434` |
| 测试网络通断 | `ping -c 4 google.com` |
| SSH 连远程 | `ssh user@host` |
| 拷文件到远程 | `scp file user@host:~/` |
| 从远程拷文件 | `scp user@host:~/file ./` |
| 免密登录 | `ssh-keygen -t ed25519` + `ssh-copy-id user@host` |
| 把远程端口映射到本地 | `ssh -L 8080:localhost:8888 user@host` |

### 包管理

| 我想干什么 | 命令 |
|---|---|
| 装系统工具 | `brew install <pkg>` |
| 已装 brew 包 | `brew list` |
| 装 Python 包 | `pip install <pkg>` |
| 已装 pip 包 | `pip list` |
| 查看包详细信息 | `pip show <pkg>` |
| 创建 conda 环境 | `conda create -n name python=3.13` |
| 激活环境 | `conda activate name` |
| 查看所有环境 | `conda info --envs` |

### Shell 配置

| 我想干什么 | 命令 |
|---|---|
| 看当前用的哪个 python | `which python` |
| 看 PATH 搜索顺序 | `echo $PATH \| tr ':' '\n'` |
| 给长命令起短名 | `alias name='long command'` 写到 `.zshrc` |
| 加载 .zshrc 改动 | `source ~/.zshrc` |
| 查历史命令 | `history \| grep "keyword"` |
| 查磁盘空间 | `df -h` |
| 查当前目录各文件夹大小 | `du -sh *` |

### Ollama 诊断

| 我想干什么 | 命令 |
|---|---|
| 查看本地模型 | `ollama list` |
| 查看已加载模型 | `ollama ps` |
| 卸载模型（释放内存） | `ollama stop qwen3.5:9b` |
| 删除模型 | `ollama rm qwen3.5:9b` |
| 拉取模型 | `ollama pull qwen3.5:9b` |
| 查看后台服务状态 | `brew services list` |
| 重启 Ollama 后台 | `brew services restart ollama` |
| 测试 API | `curl http://localhost:11434/api/tags` |
| 追 Ollama 日志 | `tail -f ~/.ollama/logs/server.log` |
| 看谁占了 11434 端口 | `lsof -i :11434` |
