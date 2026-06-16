"""
Obsidian 笔记写入器。

将 LLM 整理后的结构化笔记写入 Obsidian Vault，
支持自动分类、YAML front-matter、[[双向链接]]。
"""
import os
from datetime import date
from typing import Optional

from knest.writers import BaseWriter, WriteResult
from knest.config import Config


# 内容类型 → Obsidian 子目录映射
CATEGORY_MAP = {
    "ai": "AI学习",
    "ml": "AI学习",
    "机器学习": "AI学习",
    "llm": "AI学习",
    "deep learning": "AI学习",
    "编程": "编程开发",
    "python": "编程开发",
    "开发": "编程开发",
    "框架": "编程开发",
    "经济学": "经济学",
    "经济": "经济学",
    "商科": "经济学",
    "金融": "经济学",
    "国际政治": "日常杂谈",
    "时事": "日常杂谈",
    "vlog": "日常杂谈",
    "语言": "语言学习",
    "英语": "语言学习",
    "雅思": "语言学习",
    "俄语": "语言学习",
    "学术": "学术研究",
    "论文": "学术研究",
}

DEFAULT_CATEGORY = "未分类"


def guess_category(title: str = "", tags: list[str] = None, content: str = "") -> str:
    """根据标题、标签和内容智能判断分类。"""
    text = f"{title} {' '.join(tags or [])} {content[:200]}".lower()

    for keyword, category in CATEGORY_MAP.items():
        if keyword.lower() in text:
            return category

    return DEFAULT_CATEGORY


def make_front_matter(
    title: str,
    tags: list[str],
    source: str = "",
    rating: str = "",
    topics: list[str] = None,
    category: str = "",
) -> str:
    """生成 YAML front-matter。"""
    lines = ["---"]
    lines.append(f"title: {title}")
    lines.append(f"created: {date.today().isoformat()}")
    if source:
        lines.append(f'source: "{source}"')
    lines.append(f"tags: {json.dumps(tags, ensure_ascii=False)}")
    if rating:
        lines.append(f"rating: \"{rating}\"")
    if topics:
        lines.append(f"topics: {json.dumps(topics, ensure_ascii=False)}")
    if category:
        lines.append(f"category: \"{category}\"")
    lines.append("---")
    return "\n".join(lines)


class ObsidianWriter(BaseWriter):
    """将笔记写入 Obsidian Vault。"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

    @property
    def vault_path(self) -> str:
        return self.config.obsidian_vault

    @property
    def notes_base(self) -> str:
        return os.path.join(self.vault_path, self.config.obsidian_notes_dir)

    def write(self, content: str, title: str, **kwargs) -> WriteResult:
        """写入笔记到 Obsidian Vault。

        Args:
            content: 笔记完整内容（含 YAML front-matter）
            title: 笔记标题（用作文件名）
            **kwargs:
                category: 分类目录名（如 "AI学习", "经济学"），auto 则自动判断
                tags: 标签列表
                source: 来源描述
                subdir: 子目录（如 "思维导图"）

        Returns:
            WriteResult
        """
        category = kwargs.get("category", "auto")
        tags = kwargs.get("tags", [])
        source = kwargs.get("source", "")
        subdir = kwargs.get("subdir", "")

        # 自动分类
        if category == "auto":
            category = guess_category(title, tags, content)

        # 构建目标路径
        target_dir = os.path.join(self.notes_base, category)
        if subdir:
            target_dir = os.path.join(target_dir, subdir)

        os.makedirs(target_dir, exist_ok=True)

        # 安全文件名
        safe_title = self._sanitize_filename(title)
        file_path = os.path.join(target_dir, f"{safe_title}.md")

        # 避免文件名冲突
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(target_dir, f"{safe_title}_{counter}.md")
            counter += 1

        # 写入
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"  ✅ 写入: {file_path}")
        return WriteResult(success=True, path=file_path)

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        import re
        name = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
        name = re.sub(r"\s+", " ", name)
        return name or "未命名"


# 确保 json 可用
import json
