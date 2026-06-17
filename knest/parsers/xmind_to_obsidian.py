"""
XMind 思维导图 → Obsidian 笔记导入器 — 跨平台兼容。

将 .xmind 文件解析后，为每个 sheet 的每个拓扑节点生成独立笔记，
并自动创建 [[双向链接]] 和 MOC（内容地图）索引。
"""
import json
import os
from pathlib import Path
from typing import Optional

from knest.config import Config
from knest.parsers.xmind_parser import parse_xmind


def import_xmind_to_obsidian(xmind_path: str, config: Optional[Config] = None) -> list[str]:
    """将 .xmind 文件导入到 Obsidian Vault。

    Args:
        xmind_path: .xmind 文件路径
        config: 配置实例

    Returns:
        生成的笔记文件路径列表
    """
    cfg = config or Config()
    sheets = parse_xmind(xmind_path)

    vault = Path(cfg.obsidian_vault)
    notes_base = vault / cfg.obsidian_notes_dir

    # 使用导入文件名作为基础分类
    xmind_name = Path(xmind_path).stem
    category_name = _guess_category_from_xmind(xmind_name)
    base_dir = notes_base / "思维导图" / category_name

    created_files = []

    for sheet_data in sheets:
        sheet_name = sheet_data.get("sheet", "未命名画布")
        root = sheet_data.get("root", {})
        node_dir = base_dir / sheet_name
        node_dir.mkdir(parents=True, exist_ok=True)

        # 生成 MOC（地图索引）
        moc_path = node_dir / f"{sheet_name} — 索引.md"
        moc_lines = [
            f"---",
            f"title: {sheet_name} — 思维导图索引",
            f"created: {__import__('datetime').date.today().isoformat()}",
            f"tags: [\"思维导图\", \"{category_name}\", \"{xmind_name}\"]",
            f"moc: true",
            f"source: \"{xmind_name}.xmind\"",
            f"---\n",
            f"# 🗺️ {sheet_name}\n",
        ]

        def _count_topics(node: dict) -> int:
            """递归统计主题数。"""
            count = 1
            for child in node.get("children", []):
                count += _count_topics(child)
            return count

        topic_count = _count_topics(root)
        moc_lines.append(f"> 来自 `{xmind_name}.xmind` | 共 {topic_count} 个主题\n")

        def _write_topic(topic: dict, parent_links=None, depth=0):
            if parent_links is None:
                parent_links = []

            topic_title = topic.get("title", "未命名节点")
            # 安全文件名
            safe_name = _safe_filename(topic_title)
            note_name = f"{sheet_name} — {safe_name}"
            note_path = node_dir / f"{note_name}.md"

            # 避免冲突
            counter = 1
            while note_path.exists():
                note_path = node_dir / f"{note_name}_{counter}.md"
                counter += 1

            children = topic.get("children", [])

            # 构建笔记内容
            lines = [
                "---",
                f'title: {topic_title}',
                f"created: {__import__('datetime').date.today().isoformat()}",
                f'tags: ["思维导图", "{category_name}", "{xmind_name}"]',
                f'source: "{xmind_name}.xmind"',
                'links:',
            ]
            for pl in parent_links:
                lines.append(f'  - "[[{pl}]]"')
            if children:
                lines.append('children:')
                for child in children:
                    child_name = f"{sheet_name} — {_safe_filename(child.get('title', '未命名节点'))}"
                    lines.append(f'  - "[[{child_name}]]"')
            lines.append("---\n")
            lines.append(f"# {topic_title}\n")
            if parent_links:
                lines.append("**父级节点：** " + " → ".join(
                    [f"[[{p}]]" for p in parent_links]
                ) + "\n")
            if children:
                lines.append("\n**子级节点：**\n")
                for child in children:
                    child_name = f"{sheet_name} — {_safe_filename(child.get('title', '未命名节点'))}"
                    lines.append(f"- [[{child_name}]]")
                lines.append("")

            lines.append(f"\n---\n*此笔记由 {xmind_name}.xmind 自动生成*")
            note_path.write_text("\n".join(lines), encoding="utf-8")
            created_files.append(str(note_path))

            # 添加到 MOC
            indent = "  " * depth
            moc_lines.append(f"{indent}- [[{note_name}]]")
            if topic_title:
                moc_lines.append(f"{indent}  — {topic_title}")

            # 递归处理子节点
            current_links = parent_links + [note_name]
            for child in children:
                _write_topic(child, current_links, depth + 1)

        # 处理所有顶级主题（root 本身 + 其直接子节点）
        root_children = root.get("children", [])
        for child in root_children:
            _write_topic(child)

        # 写入 MOC
        moc_path.write_text("\n".join(moc_lines), encoding="utf-8")
        created_files.append(str(moc_path))

    # 生成全局汇总
    summary_path = vault / "XMind导入汇总.md"
    summary_lines = [
        "---",
        "title: XMind 导入汇总",
        f"created: {__import__('datetime').date.today().isoformat()}",
        'tags: ["思维导图", "汇总"]',
        "---\n",
        "# 📚 XMind 导入汇总\n",
        f"> 来自 `{xmind_name}.xmind` | 共生成 {len(created_files)} 个文件\n",
    ]
    for fp in created_files:
        rel = Path(fp).relative_to(vault)
        summary_lines.append(f"- [[{rel.with_suffix('')}]]")
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    created_files.append(str(summary_path))

    return created_files


def _guess_category_from_xmind(name: str) -> str:
    """从文件名推测分类。"""
    name_lower = name.lower()
    categories = {
        "ai": "AI学习", "机器学习": "AI学习", "llm": "AI学习",
        "python": "编程开发", "编程": "编程开发", "代码": "编程开发",
        "经济学": "经济学", "经济": "经济学", "金融": "经济学",
    }
    for keyword, category in categories.items():
        if keyword in name_lower:
            return category
    return "未分类"


def _safe_filename(name: str) -> str:
    """跨平台安全文件名。"""
    import re
    name = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    name = re.sub(r"\s+", " ", name)
    return name[:80] or "未命名"


def _import_datetime():
    """延迟导入 datetime 以避免干扰 YAML front-matter 格式。"""
    from datetime import date
    return date.today().isoformat()
