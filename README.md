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

## 🏗️ 架构

```
用户输入 (链接/文件)
     │
     ▼
┌────────────────────────────┐
│  Phase 1: 内容采集         │
│  ├ B站视频下载 (反爬绕过)  │
│  ├ Whisper 语音转文字      │
│  └ XMind 思维导图解析      │
└────────────────────────────┘
     │
     ▼
┌────────────────────────────┐
│  Phase 2: AI 结构化        │
│  ├ LLM 提炼核心观点        │
│  ├ 分类 + 标签生成         │
│  └ 知识关联识别            │
└────────────────────────────┘
     │
     ▼
┌────────────────────────────┐
│  Phase 3: 知识库写入       │
│  ├ Obsidian Vault 分类存储 │
│  ├ YAML Front-matter 元数据│
│  └ [[双向链接]] 知识网络   │
└────────────────────────────┘
     │
     ▼
┌────────────────────────────┐
│  Phase 4: 思维导图联动     │
│  ├ XMind → 节点化笔记      │
│  ├ MOC 索引页自动生成      │
│  └ Obsidian Graph 可视化   │
└────────────────────────────┘
```

---

## 🚀 快速开始

### 前置条件

```bash
# Python 3.8+
# 安装 Whisper
pip install faster-whisper

# 安装 Playwright（B站下载需要）
pip install playwright && python -m playwright install chromium

# 安装 ffmpeg
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
```

### B站视频 → Obsidian 笔记

```bash
# 1. 下载视频
python scripts/bilibili_pipeline.py BV1xxxxxx

# 2. Whisper 转写（中文）
python scripts/video_to_notes.py input.mp4 -l zh

# 3. LLM 整理 → Obsidian（参考 wiki/note-format.md）
# 阅读转写稿 → AI 结构化 → write_file 到 Obsidian vault
```

### XMind 思维导图 → Obsidian 知识网络

```bash
# 一键导入
python parser/xmind_to_obsidian.py 你的导图.xmind --vault ~/obsidian-vault

# 仅查看结构
python parser/xmind_parser.py 你的导图.xmind

# Markdown 导出
python parser/xmind_parser.py 你的导图.xmind --markdown
```

### 完整流水线

```bash
# 一条命令搞定全部（需要 AI agent 环境）
pip install -r requirements.txt
```

---

## 📦 仓库结构

```
knowledge-nest/
├── README.md                 ← 项目介绍
├── LICENSE                   ← MIT 开源
├── requirements.txt          ← Python 依赖
├── visualization.html        ← 工作流可视化页面
├── scripts/                  ← 核心脚本
│   ├── pipeline.py           ← 统一入口
│   └── bilibili_pipeline.py  ← B站下载+转写一体化
├── parser/                   ← 解析工具
│   ├── xmind_parser.py       ← XMind 解析器（零依赖）
│   └── xmind_to_obsidian.py  ← XMind → Obsidian 导入
├── skills/                   ← 🤖 AI Agent 可装载的技能包
│   ├── video-to-notes/       ← 🎬 B站→Whisper→LLM→Obsidian
│   │   └── SKILL.md
│   ├── xmind-parser/         ← 🗺️ XMind→Obsidian 导入
│   │   ├── SKILL.md
│   │   ├── xmind_parser.py
│   │   └── xmind_to_obsidian.py
│   └── knowledge-pipeline/   ← 🪺 全流程编排
│       └── SKILL.md
├── wiki/                     ← 文档
│   ├── note-format.md        ← 笔记格式规范
│   ├── bilibili-guide.md     ← B站视频处理指南
│   ├── obsidian-workflow.md  ← Obsidian 工作流
│   └── agent-guide.md        ← 🤖 AI Agent 使用指南
├── examples/                 ← 示例
│   ├── sample-note.md        ← 示例笔记
│   └── economics.xmind       ← 示例思维导图
└── tests/                    ← 测试
    └── test_xmind.py         ← XMind 解析器测试
```

### 🤖 给 AI Agent 用的

如果你是 AI Agent（Hermes、Claude、GPT 等），直接装载 `skills/` 目录下的技能包：

```bash
# Hermes Agent
hermes skill install skills/video-to-notes
hermes skill install skills/xmind-parser
hermes skill install skills/knowledge-pipeline

# 其他 Agent：加载 skills/*/SKILL.md 到工作记忆即可
```

每个 `SKILL.md` 包含完整的步骤、代码模板和避坑指南，Agent 可自主执行。

---

## 🧠 设计理念

### 为什么叫 Knowledge Nest？

像鸟巢一样 —— 把零散的知识碎片（视频、文章、导图）衔回来，整理成温暖、有序的「知识巢穴」。

### 核心原则

1. **零依赖优先** — XMind 解析器纯 Python 标准库实现，无需安装任何第三方包
2. **AI 增强，不替代** — Whisper 做转写，LLM 做结构化，但最终的知识组织由你掌控
3. **Obsidian 原生** — 生成的笔记开箱即用，[[双向链接]]、Graph View、Tag 全兼容
4. **反爬友好** — B站下载绕过了 412 屏蔽，使用 Playwright 获取合法 cookies

---

## 🤝 贡献

欢迎 PR！特别是：
- 更多视频平台支持（YouTube 已部分支持）
- 更好的 LLM 提示词模板
- 更多思维导图格式支持

---

## 📜 License

MIT © [北颐](https://github.com/beiyi-hub)

---

> **「知识不是孤岛，而是群岛。」** — 从零散视频到互联知识库，Knowledge Nest 帮你搭桥。
