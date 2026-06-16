# 🪺 Knowledge Nest

> **视频 → 笔记 → Obsidian → 思维导图 — 一键构建你的体系化知识库**

把散落的视频、文章、思维导图，变成结构化的、可检索的、互联的知识网络。

---

## ✨ 能做什么

| 输入 | 输出 |
|------|------|
| 🎬 **B站/任意视频链接** | Whisper 转写 → LLM 结构化笔记 → Obsidian 存档 |
| 🗺️ **XMind 思维导图** (`.xmind`) | 自动解析 → 每个节点变为独立笔记 → 自动生成 [[双向链接]] |
| 📄 **已有笔记/文章** | LLM 整理 → 按分类存入 Obsidian Vault |
| 🔗 **全部互联** | 知识点自动双向链接，形成可探索的知识图谱 |

---

## 🚀 快速开始

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/beiyi-hub/knowledge-nest.git
cd knowledge-nest

# 2. 安装（推荐在虚拟环境中）
pip install -e .

# 3. 验证安装
python -m knest.cli config
```

### 依赖安装

```bash
# 核心依赖（必须）
pip install requests tqdm

# Whisper 转写（可选，用于视频处理）
pip install faster-whisper

# B站下载（可选）
pip install playwright && python -m playwright install chromium

# 系统工具
# Ubuntu: sudo apt install ffmpeg
# macOS: brew install ffmpeg
```

### 配置

```bash
# 查看当前配置
knest config

# 使用配置文件（可选）
cp config.yaml.example config.yaml
# 编辑 config.yaml 修改路径等
knest --config config.yaml config
```

也可以使用环境变量覆盖：
```bash
export KNEST_OBSIDIAN_VAULT=/path/to/vault
export KNEST_HF_ENDPOINT=https://hf-mirror.com
```

---

## 📖 使用指南

### B站视频 → Obsidian 笔记

```bash
# 下载 B站视频（自动转写）
knest bilibili BV1xxxxxx

# 指定语言和模型
knest bilibili BV1xxxxxx --language en --model small

# 仅下载不转写
knest bilibili BV1xxxxxx --dry-run

# 指定画质（32=480P, 64=720P, 80=1080P）
knest bilibili BV1xxxxxx --quality 32
```

### 转写本地视频/音频

```bash
knest transcribe input.mp4
knest transcribe input.mp4 --language ru --model small
knest transcribe audio.mp3 --language zh
```

### XMind 思维导图 → Obsidian 知识网络

```bash
# 查看思维导图结构（树形图）
knest xmind 文件.xmind

# 输出 Markdown
knest xmind 文件.xmind --markdown

# 导入到 Obsidian（自动生成每个节点的笔记 + 双向链接）
knest xmind 文件.xmind --obsidian

# 完整导入：指定目录 + 生成汇总页
knest xmind 文件.xmind --obsidian --dir "Notes/经济学/思维导图" --summary
```

---

## 🏗️ 架构

```
knowledge-nest/
├── knest/                      ← 🔥 核心 Python 包（pip install 可安装）
│   ├── __init__.py             ← 包元信息
│   ├── config.py               ← 统一配置管理（环境变量/配置文件/CLI参数）
│   ├── cli.py                  ← CLI 入口（knest 命令）
│   ├── collectors/             ← 内容采集器（可扩展）
│   │   ├── __init__.py         ← 抽象基类
│   │   └── bilibili.py         ← B站采集器（绕过 412 反爬）
│   ├── processors/             ← 处理器
│   │   ├── __init__.py         ← 抽象基类
│   │   └── whisper.py          ← faster-whisper 转写
│   ├── writers/                ← 写入器
│   │   ├── __init__.py         ← 抽象基类
│   │   └── obsidian.py         ← Obsidian 笔记写入（自动分类）
│   └── parsers/                ← 文件解析器
│       ├── __init__.py
│       ├── xmind_parser.py     ← XMind 解析器（零依赖）
│       └── xmind_to_obsidian.py ← XMind → Obsidian 导入
├── scripts/                    ← 辅助脚本
│   ├── process_video.py        ← Whisper 转写脚本（需自备）
│   └── check_env.py            ← 环境检测
├── skills/                     ← 🤖 AI Agent 技能包（Hermes/Claude 等）
├── wiki/                       ← 文档
├── tests/                      ← 测试
├── pyproject.toml              ← pip install 配置
├── config.yaml.example         ← 配置文件模板
└── README.md
```

### 设计原则

1. **零依赖优先** — XMind 解析器纯 Python 标准库实现
2. **一切可配置** — 没有硬编码路径，所有路径通过配置管理
3. **模块化可扩展** — 采集器/处理器/写入器全用抽象基类，新增平台只需继承
4. **跨平台友好** — 使用 `os.path.join`/`pathlib`，告别硬编码
5. **AI 增强不替代** — LLM 做结构化，知识组织由你掌控

---

## 🔧 扩展开发

### 添加新的内容源（如 YouTube）

```python
from knest.collectors import BaseCollector, MediaInfo

class YouTubeCollector(BaseCollector):
    def collect(self, target: str, **kwargs) -> MediaInfo:
        # 实现你的下载逻辑
        ...
```

### 自定义写入器（如 Notion、Logseq）

```python
from knest.writers import BaseWriter, WriteResult

class NotionWriter(BaseWriter):
    def write(self, content, title, **kwargs) -> WriteResult:
        # 通过 API 写入 Notion
        ...
```

---

## 🧪 环境检测

```bash
python scripts/check_env.py
```

---

## 📜 License

MIT © [北颐](https://github.com/beiyi-hub)

---

> **「知识不是孤岛，而是群岛。」** — 从零散视频到互联知识库，Knowledge Nest 帮你搭桥。
