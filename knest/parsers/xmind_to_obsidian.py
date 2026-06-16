"""
XMind → Obsidian 导入器。

将 .xmind 思维导图中的每个节点转换为独立的 Obsidian 笔记，
自动建立 [[双向链接]] 和 MOC（Map of Content）索引页。

基于 knest 配置系统，路径全部可配置。
"""
import os
import re
from datetime import date
from typing import Optional

from knest.config import Config
from knest.writers.obsidian import make_front_matter
from knest.parsers.xmind_parser import parse_xmind


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    name = re.sub(r"\s+", " ", name)
    return name or "未命名"


def _collect_all_nodes(node: dict, parent_title: str = None) -> list[dict]:
    """递归收集所有节点（flat list）。"""
    nodes = []
    nodes.append({
        "title": node["title"],
        "children": [c["title"] for c in node["children"]],
        "parent": parent_title,
        "id": node.get("id", ""),
    })
    for child in node["children"]:
        nodes.extend(_collect_all_nodes(child, node["title"]))
    return nodes


def _generate_moc(sheet_title: str, root: dict, nodes: list[dict]) -> str:
    """生成 MOC 索引页。"""
    lines = []
    lines.append(make_front_matter(
        title=f"{sheet_title} — 索引",
        tags=["xmind", "思维导图", "MOC"],
    ))
    lines.append("")
    lines.append(f"# {sheet_title} — 思维导图索引")
    lines.append("")
    lines.append(f"> 由 XMind 文件自动导入，共 {len(nodes)} 个节点")
    lines.append("")
    lines.append("## 节点总览")
    lines.append("")

    def write_branch(node, depth=0):
        spacing = "  " * depth
        lines.append(f"{spacing}- [[{node['title']}]]")
        for c in node["children"]:
            write_branch(c, depth + 1)

    write_branch(root)
    lines.append("")
    return "\n".join(lines)


def _generate_note(node: dict, sheet_title: str) -> str:
    """生成单个节点笔记。"""
    tags = ["xmind", "思维导图"]
    source_parts = []
    if sheet_title:
        source_parts.append(f"XMind → {sheet_title}")
    if node["parent"]:
        source_parts.append(f"属于: {node['parent']}")
    source_parts.append("思维导图导入")
    source = " | ".join(source_parts)

    lines = []
    lines.append(make_front_matter(
        title=node["title"],
        tags=tags,
        source=source,
    ))
    if node["parent"]:
        lines.append(f"parent: \"{node['parent']}\"")
    lines.append("---")
    lines.append("")
    lines.append(f"# {node['title']}")
    lines.append("")

    if node["parent"]:
        lines.append(f"> 属于：[[{node['parent']}]]")
        lines.append("")

    if node["children"]:
        lines.append("## 分支")
        lines.append("")
        for child_title in node["children"]:
            lines.append(f"- [[{child_title}]]")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*此笔记由 XMind 思维导图「{sheet_title}」自动导入。*")
    lines.append("")

    return "\n".join(lines)


def xmind_to_obsidian(
    path: str,
    config: Optional[Config] = None,
    subdir: str = "",
    summary: bool = False,
    moc_only: bool = False,
) -> list[str]:
    """将 XMind 文件导入 Obsidian Vault。

    Args:
        path: .xmind 文件路径
        config: 配置实例（默认使用全局配置）
        subdir: 笔记存放的子目录（如 "思维导图"）
        summary: 是否生成汇总页
        moc_only: 只生成 MOC 索引

    Returns:
        生成的文件路径列表
    """
    config = config or Config()
    vault = config.obsidian_vault

    # 智能分类：从文件路径或内容检测
    category = "未分类"
    if subdir:
        category = os.path.dirname(subdir) if "/" in subdir else "未分类"

    notes_base = os.path.join(vault, config.obsidian_notes_dir)
    base_dir = os.path.join(notes_base, category)
    if subdir:
        if "/" in subdir:
            base_dir = os.path.join(notes_base, subdir)
        else:
            base_dir = os.path.join(base_dir, subdir)
    os.makedirs(base_dir, exist_ok=True)

    sheets = parse_xmind(path)
    generated_files = []
    sheets_nodes = []

    for sheet in sheets:
        sheet_title = sheet["sheet"]
        root = sheet["root"]

        all_nodes = _collect_all_nodes(root)
        sheet_name = sanitize_filename(sheet_title)
        node_dir = os.path.join(base_dir, sheet_name)
        os.makedirs(node_dir, exist_ok=True)

        sheets_nodes.append((sheet_title, root, all_nodes))

        # MOC 索引
        moc_content = _generate_moc(sheet_title, root, all_nodes)
        moc_path = os.path.join(base_dir, f"{sheet_name} — 索引.md")
        with open(moc_path, "w", encoding="utf-8") as f:
            f.write(moc_content)
        generated_files.append(moc_path)

        if not moc_only:
            for node_info in all_nodes:
                note_content = _generate_note(node_info, sheet_title)
                note_name = sanitize_filename(node_info["title"])
                note_path = os.path.join(node_dir, f"{note_name}.md")

                counter = 1
                while os.path.exists(note_path):
                    note_path = os.path.join(node_dir, f"{note_name}_{counter}.md")
                    counter += 1

                with open(note_path, "w", encoding="utf-8") as f:
                    f.write(note_content)
                generated_files.append(note_path)

    if summary and sheets_nodes:
        summary_content = _generate_summary_page(sheets_nodes)
        summary_path = os.path.join(vault, "XMind导入汇总.md")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary_content)
        generated_files.append(summary_path)

    return generated_files


def _generate_summary_page(sheets_nodes: list) -> str:
    """生成汇总页。"""
    lines = []
    lines.append(make_front_matter(
        title="XMind 导入汇总",
        tags=["xmind", "汇总", "思维导图"],
    ))
    lines.append("")
    lines.append("# 🗺️ XMind 思维导图导入汇总")
    lines.append("")
    lines.append("| 思维导图 | 节点数 | 根主题 |")
    lines.append("|---------|--------|--------|")

    for sheet_title, root, nodes in sheets_nodes:
        lines.append(f"| [[{sheet_title} — 索引]] | {len(nodes)} | {root['title']} |")

    lines.append("")
    return "\n".join(lines)
