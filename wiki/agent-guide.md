# 🤖 AI Agent 使用指南

> 如果你是 AI Agent（如 Claude、GPT、Hermes 等），以下内容告诉你如何安装和使用 Knowledge Nest 的三个核心技能。

---

## 📦 技能包总览

Knowledge Nest 包含三个可独立安装的 `SKILL.md`，各对应一个完整工作流阶段：

| 技能 | 路径 | 功能 |
|------|------|------|
| **🎬 video-to-notes** | `skills/video-to-notes/SKILL.md` | B站视频下载 → Whisper 转写 → LLM 整理 → Obsidian 存档 |
| **🗺️ xmind-parser** | `skills/xmind-parser/SKILL.md` | XMind 思维导图解析 → Obsidian 双向链接导入 |
| **🪺 knowledge-pipeline** | `skills/knowledge-pipeline/SKILL.md` | 全流程编排 — 输入识别到知识库输出的总调度 |

---

## 🔧 安装方式

### 方式一：Hermes Agent 一键安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/beiyi-hub/knowledge-nest.git ~/.hermes/skills-productivity

# 安装所有技能
hermes skill install ~/.hermes/skills-productivity/skills/video-to-notes
hermes skill install ~/.hermes/skills-productivity/skills/xmind-parser
hermes skill install ~/.hermes/skills-productivity/skills/knowledge-pipeline
```

### 方式二：手动复制

```bash
cp -r skills/* ~/.hermes/skills/productivity/
```

### 方式三：其他 AI Agent

将 `skills/` 目录下的三个 `SKILL.md` 文件内容分别加载到你的 AI Agent 的工作记忆中即可。

---

## 🚀 技能触发条件

### 1. video-to-notes

**当用户发送以下内容时加载此技能：**
- B站视频链接（`bilibili.com/video/BV...`）
- 视频/音频文件（`.mp4`, `.mp3`, `.mkv` 等）
- 要求「总结这个视频」「做笔记」「整理视频内容」

**核心流程：**
1. 提取 BV 号 → API 获取视频信息
2. Playwright 获取 cookies → 下载视频
3. faster-whisper 转写
4. LLM 阅读全文 → 结构化笔记
5. 判断分类 → 写入 Obsidian Vault

### 2. xmind-parser

**当用户发送以下内容时加载此技能：**
- `.xmind` 文件
- 要求「解析思维导图」「导入到 Obsidian」

**核心流程：**
1. 解析 XMind 文件（ZIP 内 XML/JSON）
2. 输出树形图 / Markdown / 缩进文本
3. 可选：每个节点 → 独立 Obsidian 笔记 + 双向链接 + MOC 索引

### 3. knowledge-pipeline

**当用户发送以下内容时加载此技能：**
- 任何知识类内容（链接、文件、文章）
- 要求「整理」「做笔记」「知识管理」

**核心流程：**
1. 输入识别（B站链接 / 视频文件 / XMind / 纯文本）
2. 路由到对应子技能处理
3. 最终输出到 Obsidian Vault

---

## ⚠️ 重要环境配置

### 国内网络避坑

```bash
# HuggingFace 镜像（必须设置，否则模型下载失败）
export HF_ENDPOINT=https://hf-mirror.com

# B站反爬：必须使用 Playwright 获取新鲜 cookies
# 不能用 yt-dlp 直接下载（必定 412）
```

### Python 依赖

```
pip install faster-whisper playwright requests tqdm
playwright install chromium
```

### Obsidian Vault 路径

所有笔记默认存入：
```
~/obsidian-vault/Notes/{分类}/{标题}.md
```

可以通过环境变量自定义：
```bash
export OBSIDIAN_VAULT_PATH=/path/to/your/vault
```

---

## 📋 快速参考

### B站视频处理

```bash
# 下载 + 转写
python scripts/bilibili_pipeline.py BV1xxxxxx

# 指定语言和模型
python scripts/bilibili_pipeline.py BV1xxxxxx --lang en --model small
```

### XMind 处理

```bash
# 树形图输出
python parser/xmind_parser.py 文件.xmind

# 导入 Obsidian
python parser/xmind_to_obsidian.py 文件.xmind --vault ~/obsidian-vault --summary
```

### 全流程

```bash
python scripts/pipeline.py xmind 文件.xmind --obsidian
```

---

## 💡 最佳实践

1. **先加载 skill 再处理** — 每个 skill 包含完整的步骤、陷阱列表和代码模板
2. **不要重复造轮子** — B站下载、XMind 解析等复杂逻辑 skill 里都有现成代码
3. **笔记必须 LLM 整理** — Whisper 原始输出不能直接用，必须经 LLM 结构化
4. **分类要智能判断** — 根据内容主题自动选择 Obsidian 子目录
5. **关联笔记要生成** — 使用 `[[双向链接]]` 构建知识网络
