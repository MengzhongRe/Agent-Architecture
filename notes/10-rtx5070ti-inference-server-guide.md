# RTX 5070 Ti 本地推理服务器部署指南

> 日期：2026-06 | 硬件：NVIDIA RTX 5070 Ti 16GB GDDR7
> 目标：部署为长期运行的局域网推理服务器，Mac/手机/其他设备均可调用
> 前置阅读：[06-ollama-setup-guide.md](06-ollama-setup-guide.md)、[08-nsfw-local-llm-guide.md](08-nsfw-local-llm-guide.md)

---

## 目录

- [1. 总体架构](#1-总体架构)
- [2. 操作系统选择](#2-操作系统选择)
- [3. 推理框架选型](#3-推理框架选型)
- [4. 安装与配置](#4-安装与配置)
  - [4.1 系统环境准备](#41-系统环境准备)
  - [4.2 安装 Ollama](#42-安装-ollama)
  - [4.3 GPU 验证与调优](#43-gpu-验证与调优)
  - [4.4 设为开机自启](#44-设为开机自启)
- [5. 模型部署策略](#5-模型部署策略)
  - [5.1 5070 Ti 16GB 的模型矩阵](#51-5070-ti-16gb-的模型矩阵)
  - [5.2 模型驻留策略](#52-模型驻留策略)
- [6. 局域网配置与安全](#6-局域网配置与安全)
  - [6.1 绑定局域网地址](#61-绑定局域网地址)
  - [6.2 防火墙规则](#62-防火墙规则)
  - [6.3 Nginx 反向代理 + API Key 认证（推荐）](#63-nginx-反向代理--api-key-认证推荐)
  - [6.4 SSH 隧道方案（最简单，单用户）](#64-ssh-隧道方案最简单单用户)
- [7. 前端部署](#7-前端部署)
  - [7.1 Open WebUI（主力界面）](#71-open-webui主力界面)
  - [7.2 SillyTavern（角色扮演专用）](#72-sillytavern角色扮演专用)
  - [7.3 移动端访问](#73-移动端访问)
- [8. 日常运维](#8-日常运维)
  - [8.1 监控命令](#81-监控命令)
  - [8.2 磁盘清理](#82-磁盘清理)
  - [8.3 更新升级](#83-更新升级)
- [9. 性能调优](#9-性能调优)
- [10. 客户端接入指南](#10-客户端接入指南)

---

## 1. 总体架构

```
┌──────────────────────────────────────────────────┐
│                你的局域网 (192.168.x.x)             │
│                                                   │
│  ┌─────────────────────────┐                      │
│  │   RTX 5070 Ti 推理服务器  │                      │
│  │                         │                      │
│  │  Ollama :11434          │── Nginx :21434 (认证) │
│  │  Open WebUI :3000       │                      │
│  │  SillyTavern :8000      │                      │
│  └─────────────────────────┘                      │
│           │           │           │                │
│           ▼           ▼           ▼                │
│    ┌─────────┐ ┌─────────┐ ┌──────────┐           │
│    │ Mac M4  │ │ 手机/平板 │ │ 其他电脑  │           │
│    │ 浏览器   │ │ 浏览器   │ │ 浏览器    │           │
│    └─────────┘ └─────────┘ └──────────┘           │
└──────────────────────────────────────────────────┘
```

一台 RTX 5070 Ti 机器运行推理 + 前端，局域网内所有设备通过浏览器访问。对外暴露两个端口：

| 端口      | 服务                  | 说明               |
| ------- | ------------------- | ---------------- |
| `3000`  | Open WebUI          | 主力聊天界面，类 ChatGPT |
| `8000`  | SillyTavern         | 角色扮演前端（可选）       |
| `21434` | Ollama API（经 Nginx） | 供 agent 代码直接调用   |

---

## 2. 操作系统选择

| 维度                  | Ubuntu Server 24.04 LTS     | Windows 11                |
| ------------------- | --------------------------- | ------------------------- |
| **CUDA 生态**         | 原生，所有工具链无缝                  | 通过 WSL2 或原生 Windows 版     |
| **长期运行稳定性**         | ✅ 设计为 7×24 运行               | ⚠️ 自动更新可能重启               |
| **内存占用**            | ~500MB（无 GUI）               | ~4GB（带 GUI）               |
| **Docker**          | 原生 Linux 容器                 | 通过 Docker Desktop（多一层虚拟化） |
| **远程管理**            | SSH 天然支持                    | 需配置 RDP/SSH               |
| **NVIDIA 驱动**       | `apt install nvidia-driver` | GeForce Experience 或手动安装  |
| **如果你还需要在这台机器上打游戏** | ❌                           | ✅                         |

**建议**：如果这台 5070 Ti 机器**专用于推理**，装 Ubuntu Server 24.04 LTS。如果它还是你的主力 Windows 机器，那就在 Windows 上跑——Ollama 的 Windows 版同样稳定。

以下指南同时覆盖两种系统。

---

## 3. 推理框架选型

| 框架            | 适用场景     | 单用户速度       | 多用户并发     | 安装难度   |
| ------------- | -------- | ----------- | --------- | ------ |
| **Ollama** ⭐  | 个人/家庭服务器 | 快           | 中等（4并发）   | 一行命令   |
| **llama.cpp** | 追求极限性能   | 最快（+10-20%） | 需自行部署     | 编译     |
| **vLLM**      | 10+ 并发用户 | 中等          | 极快（连续批处理） | 较复杂    |
| **LM Studio** | 不碰命令行    | 快           | 弱         | GUI 安装 |

**推荐 Ollama**，理由：
- 安装最简单，`curl -fsSL https://ollama.com/install.sh | sh` 搞定
- 与 llama.cpp 共享推理引擎，单用户速度几乎无损
- 内置模型管理（pull/list/rm）、keep-alive、并发排队
- OpenAI 兼容 API —— 所有前端/代码零修改接入
- 后续想升级到 vLLM 时可以平滑迁移（API 格式一样）

如果你未来需要同时给 5 个以上设备提供推理服务，再考虑迁移到 vLLM。

---

## 4. 安装与配置

### 4.1 系统环境准备

**Ubuntu Server**：

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装 NVIDIA 驱动（如果还没装）
ubuntu-drivers devices                          # 查看推荐版本
sudo apt install nvidia-driver-570 -y           # 用推荐版本号
sudo reboot

# 3. 验证驱动
nvidia-smi
# 应显示：Driver Version: 570.xx | CUDA Version: 12.x

# 4. 安装 Docker（后面部署前端用）
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# 重新登录使 docker 组生效
```

**Windows 11**：

```powershell
# 1. 确认 NVIDIA 驱动已装（去 nvidia.com 下载最新 Game Ready 驱动）
nvidia-smi

# 2. 安装 Docker Desktop（后面部署前端用）
# 去 docker.com 下载 Windows 版安装包

# 3. 安装 Ollama（去 ollama.com 下载 Windows 安装包）
```

### 4.2 安装 Ollama

**Ubuntu**：

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows**：下载 [ollama.com/download](https://ollama.com/download) 的 `.exe` 安装包，双击运行。

安装完成后 Ollama 自动以后台服务运行。验证：

```bash
ollama --version
curl http://localhost:11434/api/tags
# 返回 {"models":[]} 表示正常
```

### 4.3 GPU 验证与调优

```bash
# 拉一个轻量模型测试 GPU 是否被使用
ollama pull qwen3:4b
ollama run qwen3:4b "说一句话证明你在用GPU"

# 查看 GPU 使用
nvidia-smi
# 应该看到 ollama 进程占用了 GPU 显存
```

**关键环境变量**（在 Ollama 启动前设置）：

```bash
# Linux: 编辑 systemd 环境变量
sudo systemctl edit ollama
```

```
[Service]
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_KEEP_ALIVE=1h"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_DEBUG=0"
```

各变量含义：

| 变量 | 值 | 原因 |
|---|---|---|
| `OLLAMA_NUM_PARALLEL` | 4 | 允许 4 个请求同时推理（5070 Ti 16GB 够用） |
| `OLLAMA_MAX_LOADED_MODELS` | 1 | 16GB 显存在同一时刻只放一个模型 |
| `OLLAMA_KEEP_ALIVE` | 1h | 模型加载后保留 1 小时再卸载（家庭使用频率不高） |
| `OLLAMA_FLASH_ATTENTION` | 1 | 开启 Flash Attention，降低 KV Cache 显存 |
| `OLLAMA_KV_CACHE_TYPE` | q8_0 | KV Cache 量化——比默认 f16 省一半显存，质量几乎无损 |

**Windows**：在系统环境变量中设置（或通过 Ollama 托盘图标 → Settings）。

应用后重启服务：

```bash
# Linux
sudo systemctl daemon-reload
sudo systemctl restart ollama

# Windows
# 托盘图标 → Quit Ollama → 重新打开
```

### 4.4 设为开机自启

**Ubuntu**（安装时已自动配置）：

```bash
# 确认开机自启
sudo systemctl enable ollama
sudo systemctl status ollama
```

**Windows**：Ollama 安装后默认开机自启（系统托盘图标 → 设置中确认）。

---

## 5. 模型部署策略

### 5.1 5070 Ti 16GB 的模型矩阵

5070 Ti 有 16GB **独立显存**，不像 Mac 那样系统和模型抢内存。实际可用 ~15.5GB：

| 用途 | 模型 | 参数 | 量化 | 大小 | 速度 |
|---|---|---|---|---|---|
| **日常聊天/中文 RP** | `qwen3-abliterated:14b-v2` | 14.8B | Q4_K_M | 9GB | 50-70 tok/s |
| **最强中文 RP** | `qwen3-abliterated:32b` | 32B | Q3_K_M | ~15GB | 15-25 tok/s |
| **英文 NSFW RP** | `vanilj/mistral-nemo-12b-celeste-v1.9` | 12.2B | Q4_K_M | 7.5GB | 60-90 tok/s |
| **通用助手** | `qwen3:14b` | 14.8B | Q4_K_M | 9GB | 50-70 tok/s |
| **代码** | `qwen3-coder:14b` | 14.8B | Q4_K_M | 9GB | 50-70 tok/s |
| **备用轻量** | `qwen3-abliterated:8b` | 8B | Q4_K_M | 5GB | 80-120 tok/s |

> Qwen3 32B 去审查版用 Q3_K_M 刚好塞进 15GB——这是 5070 Ti 上能跑的最强中文 NSFW 模型。下载命令：`ollama pull huihui_ai/qwen3-abliterated:32b`

**拉取优先级**：先拉 `qwen3-abliterated:14b-v2`（主力），再看需求拉 32B。

### 5.2 模型驻留策略

服务器不像笔记本——你不需要频繁换模型：

```bash
# 方案 A：只驻留一个模型（官方推荐）
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_KEEP_ALIVE=1h
# 1 小时内无人用则卸载，有人用就一直留着

# 方案 B：始终驻留（快速响应，但占显存）
export OLLAMA_KEEP_ALIVE=-1
# 模型永不卸载，直到手动 ollama stop
```

**建议**：家庭使用选方案 A。`1h` 足够你在睡前和早上各用一次而无需重新加载。

---

## 6. 局域网配置与安全

### 6.1 绑定局域网地址

Ollama 默认只监听 `127.0.0.1`（本机）。要局域网访问：

**Ubuntu**：

```bash
sudo systemctl edit ollama
```

添加：

```
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

```
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

**Windows**：系统环境变量 → 新建 `OLLAMA_HOST` = `0.0.0.0:11434` → 重启 Ollama。

> ⚠️ `0.0.0.0` 意味着局域网内任何设备可以无认证调用你的 API。如果你的局域网不可信（合租/公司），跳转到 §6.3 加认证层。

验证：

```bash
# 在另一台设备上（比如 Mac）
curl http://<服务器IP>:11434/api/tags
# 应返回模型列表
```

### 6.2 防火墙规则

**Ubuntu（UFW）**：

```bash
# 如果局域网完全可信——开放端口给内网
sudo ufw allow from 192.168.0.0/16 to any port 11434
sudo ufw allow from 192.168.0.0/16 to any port 3000

# 如果不想暴露 Ollama 端口，只暴露前端端口
# 那么前端通过 localhost 调 Ollama，不需要开放 11434
sudo ufw enable
```

**Windows**：控制面板 → Windows Defender 防火墙 → 高级设置 → 入站规则 → 新建规则 → 端口 → TCP `11434, 3000` → 允许连接 → 仅限 "专用网络"。

### 6.3 Nginx 反向代理 + API Key 认证（推荐）

如果局域网不完全可信，在 Ollama 前加一层 Nginx，要求 API Key 才能调用。

**Ubuntu**：

```bash
sudo apt install nginx apache2-utils -y
```

创建配置文件 `/etc/nginx/sites-available/ollama-proxy`：

```nginx
server {
    listen 21434;    # 对外暴露 21434 而不是 11434

    # 允许局域网，拒绝其他
    allow 192.168.0.0/16;
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    deny all;

    # API Key 验证
    location / {
        if ($http_authorization != "Bearer YOUR-SECRET-KEY-HERE") {
            return 401 '{"error": "Unauthorized. Add Authorization: Bearer <key>"}';
        }

        proxy_pass http://127.0.0.1:11434;
        proxy_set_header Host localhost:11434;
        proxy_buffering off;             # 关键：流式响应不能缓冲
        proxy_read_timeout 3600s;        # 长推理不能超时
        proxy_send_timeout 3600s;
    }
}
```

启用：

```bash
sudo ln -s /etc/nginx/sites-available/ollama-proxy /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

**客户端调用方式**：

```python
# 之后在代码里调的是 Nginx 端口，需要带 key
client = OpenAI(
    base_url="http://192.168.1.100:21434/v1",
    api_key="YOUR-SECRET-KEY-HERE"
)
```

### 6.4 SSH 隧道方案（最简单，单用户）

如果你只是在 Mac 上调用 5070 Ti 的推理能力，不需要局域网暴露——用 SSH 隧道最安全：

```bash
# 在 Mac 上执行
ssh -L 11434:localhost:11434 user@5070ti-server-ip -N

# 之后在 Mac 上，localhost:11434 实际上连到了 5070 Ti
curl http://localhost:11434/api/tags
```

零端口暴露，零认证配置，自带加密。缺点是断开重连需要重跑命令（用 `autossh` 可解决）。

---

## 7. 前端部署

### 7.1 Open WebUI（主力界面）

Open WebUI 是类 ChatGPT 的网页界面，你 Mac 上的浏览器打开就能用：

```bash
# 在 5070 Ti 服务器上
docker run -d \
  --name open-webui \
  --restart always \
  -p 3000:8080 \
  -v open-webui-data:/app/backend/data \
  -e OLLAMA_BASE_URL=http://127.0.0.1:11434 \
  ghcr.io/open-webui/open-webui:main
```

> **Windows**：在 PowerShell 或 Docker Desktop 中运行同样命令。

然后局域网内任何设备打开 `http://<服务器IP>:3000`，即可使用。

- 首次访问需注册账号（数据存在服务器本地 SQLite 里）
- 支持多用户、聊天记录、System Prompt 自定义
- 自动发现 Ollama 的所有模型

### 7.2 SillyTavern（角色扮演专用）

如果你需要角色卡、世界书、表情系统等专业 RP 功能，再装这个：

```bash
git clone https://github.com/SillyTavern/SillyTavern.git
cd SillyTavern
bash start.sh
# 浏览器打开 http://<服务器IP>:8000
```

在 SillyTavern 中配置 API → Text Completion → Ollama → 填入 `http://127.0.0.1:11434`，选择模型即可。

详细配置见 [09-celeste-v1.9-guide.md](09-celeste-v1.9-guide.md) §8。

### 7.3 移动端访问

- **Open WebUI**：手机浏览器直接打开 `http://<服务器IP>:3000`，已做移动端适配
- **SillyTavern**：手机浏览器打开 `http://<服务器IP>:8000`，体验略差但可用
- **第三方 App**：如 `ChatBox`（iOS/Android），填入 Ollama API 地址即可

---

## 8. 日常运维

### 8.1 监控命令

```bash
# 查看哪些模型正在运行（显存占用）
ollama ps
# NAME            ID              SIZE      PROCESSOR    UNTIL
# qwen3-ablit...  xxxxxxxx        9.0 GB    100% GPU    47 min from now

# 查看 GPU 使用
nvidia-smi

# 查看模型列表
ollama list

# 查看服务状态（Ubuntu）
sudo systemctl status ollama

# 查看 Ollama 日志（Ubuntu）
sudo journalctl -u ollama -f

# 查看 Open WebUI 日志
docker logs open-webui -f
```

### 8.2 磁盘清理

模型文件日积月累会吃满磁盘。定期检查：

```bash
# 查看模型占用
du -sh ~/.ollama/models/

# 删除不用的模型
ollama rm qwen3:4b

# 清理 Docker 镜像（更新 Open WebUI 后）
docker system prune -a
```

### 8.3 更新升级

```bash
# Ollama（Ubuntu）
curl -fsSL https://ollama.com/install.sh | sh

# Ollama（Windows）
# 重新下载安装包覆盖安装

# Open WebUI
docker pull ghcr.io/open-webui/open-webui:main
docker stop open-webui && docker rm open-webui
# 然后重新跑 docker run 命令（volume 会保留数据）

# 更新已拉取的模型到最新版本
ollama pull qwen3-abliterated:14b-v2
```

---

## 9. 性能调优

**5070 Ti 的最佳配置**（写入 `sudo systemctl edit ollama` 的 `[Service]` 段）：

```
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_MMAP=1"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_KEEP_ALIVE=1h"
```

**在 Modelfile 中锁定参数**：

```dockerfile
FROM huihui_ai/qwen3-abliterated:14b-v2
PARAMETER num_ctx 8192
PARAMETER temperature 0.85
PARAMETER top_p 0.92
PARAMETER top_k 40
```

- `num_ctx 8192`：14B 模型在 16GB 下设 8K 安全；设 16K 时 KV Cache + 权重可能超过 16GB
- 如果加载失败（OOM），降低 `num_ctx` 到 4096

---

## 10. 客户端接入指南

### 从 Mac 接入

```python
# agent.py 或任何 Python 脚本
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.1.100:21434/v1",   # 服务器 IP
    api_key="YOUR-SECRET-KEY-HERE"              # Nginx 认证 key
)

response = client.chat.completions.create(
    model="breast-wife",
    messages=[{"role": "user", "content": "主人回来了！"}],
    temperature=0.85,
    max_tokens=300
)
```

### 从 SillyTavern（Mac 版）接入

API → Text Completion → Ollama → 填入 `http://192.168.1.100:21434`（或 `:11434` 如果没设 Nginx）。

### 从 iPhone/iPad 接入

1. 浏览器打开 `http://192.168.1.100:3000`（Open WebUI）
2. 或用 ChatBox App → 自定义 API → 填入 Ollama 地址

### 从 curl 测试

```bash
curl -s http://192.168.1.100:21434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR-SECRET-KEY-HERE" \
  -d '{
    "model": "breast-wife",
    "messages": [{"role": "user", "content": "你好"}],
    "temperature": 0.85
  }'
```

---

## 附录：快速部署检查清单

```
□ 操作系统安装完毕
□ NVIDIA 驱动安装并通过 nvidia-smi 验证
□ Docker 安装完毕
□ Ollama 安装并设为开机自启
□ OLLAMA_HOST=0.0.0.0:11434 已设置
□ 环境变量（FLASH_ATTENTION/KV_CACHE_TYPE/KEEP_ALIVE）已配置
□ 至少一个模型已拉取（建议 qwen3-abliterated:14b-v2）
□ 防火墙允许内网访问 3000/21434 端口
□ Nginx 反向代理已配置（如果局域网不完全可信）
□ Open WebUI Docker 容器已运行并设为 --restart always
□ 在另一台设备上通过 http://<IP>:3000 测试通过
```

---

> **相关笔记**：[06-ollama-setup-guide.md](06-ollama-setup-guide.md) | [08-nsfw-local-llm-guide.md](08-nsfw-local-llm-guide.md) | [09-celeste-v1.9-guide.md](09-celeste-v1.9-guide.md)
