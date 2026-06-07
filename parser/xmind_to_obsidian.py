#!/usr/bin/env python3
"""
XMind → Obsidian 导入器。

将 .xmind 思维导图中的每个节点转换为独立的 Obsidian 笔记，
自动建立 [[双向链接]] 和 MOC（Map of Content）索引页。

用法：
    python xmind_to_obsidian.py 文件.xmind
    python xmind_to_obsidian.py 文件.xmind --vault ~/obsidian-vault
    python xmind_to_obsidian.py 文件.xmind --dir "Notes/经济学/思维导图"
    python xmind_to_obsidian.py 文件.xmind --summary    # 同时生成汇总页
    python xmind_to_obsidian.py 文件.xmind --moc-only   # 只生成 MOC 索引
"""

import sys
import os
from datetime import date
import re

from xmind_parser import parse_xmind, to_tree


def sanitize_filename(name: str) -> str:
    """将标题转为安全的文件名。"""
    name = re.sub(r'[\\/:*?"<>|]', '_', name).strip()
    name = re.sub(r'\s+', ' ', name)
    return name or '未命名'


def _collect_all_nodes(node: dict, parent_title: str = None) -> list:
    """递归收集所有节点（flat list），包含层级信息。"""
    nodes = []
    entry = {
        'title': node['title'],
        'children': [c['title'] for c in node['children']],
        'parent': parent_title,
        'id': node.get('id', ''),
    }
    nodes.append(entry)
    for child in node['children']:
        nodes.extend(_collect_all_nodes(child, node['title']))
    return nodes


def _generate_moc(sheet_title: str, root: dict, nodes: list) -> str:
    """生成 MOC 索引页内容。"""
    lines = []
    lines.append('---')
    lines.append(f'title: {sheet_title} — 索引')
    lines.append('tags: [xmind, 思维导图, MOC]')
    lines.append(f'created: {date.today().isoformat()}')
    lines.append('---')
    lines.append('')
    lines.append(f'# {sheet_title} — 思维导图索引')
    lines.append('')
    lines.append(f'> 由 XMind 文件自动导入，共 {len(nodes)} 个节点')
    lines.append('')
    lines.append('## 节点总览')
    lines.append('')

    # 递归写树
    def write_branch(node, depth=0):
        spacing = '  ' * depth
        lines.append(f'{spacing}- [[{node["title"]}]]')
        for c in node['children']:
            write_branch(c, depth + 1)

    write_branch(root)
    lines.append('')
    return '\n'.join(lines)


def _generate_note(node: dict, sheet_title: str, vault_dir: str) -> str:
    """生成单个节点笔记的内容。"""
    lines = []
    lines.append('---')
    lines.append(f'title: {node["title"]}')
    lines.append(f'created: {date.today().isoformat()}')
    lines.append('tags: [xmind, 思维导图]')

    source_parts = []
    if sheet_title:
        source_parts.append(f'XMind → {sheet_title}')
    if node['parent']:
        source_parts.append(f'属于: {node["parent"]}')
    source_parts.append('思维导图导入')
    lines.append(f'source: "{\' | \'.join(source_parts)}"')

    if node['parent']:
        lines.append(f'parent: "{node["parent"]}"')
    lines.append('---')
    lines.append('')
    lines.append(f'# {node["title"]}')
    lines.append('')

    if node['parent']:
        lines.append(f'> 属于：[[{node["parent"]}]]')
        lines.append('')

    if node['children']:
        lines.append('## 分支')
        lines.append('')
        for child_title in node['children']:
            lines.append(f'- [[{child_title}]]')
        lines.append('')

    lines.append('---')
    lines.append('')
    lines.append(f'*此笔记由 XMind 思维导图「{sheet_title}」自动导入。*')
    lines.append('')

    return '\n'.join(lines)


def _generate_summary_page(sheets_nodes: list) -> str:
    """生成汇总页，列出所有导入的思维导图。"""
    lines = []
    lines.append('---')
    lines.append('title: XMind 导入汇总')
    lines.append('tags: [xmind, 汇总, 思维导图]')
    lines.append(f'created: {date.today().isoformat()}')
    lines.append('---')
    lines.append('')
    lines.append('# 🗺️ XMind 思维导图导入汇总')
    lines.append('')
    lines.append(f'> 汇总日期: {date.today().isoformat()}')
    lines.append('')
    lines.append('| 思维导图 | 节点数 | 根主题 |')
    lines.append('|---------|--------|--------|')

    for sheet_title, root, nodes in sheets_nodes:
        lines.append(f'| [[{sheet_title} — 索引]] | {len(nodes)} | {root["title"]} |')

    lines.append('')
    return '\n'.join(lines)


def xmind_to_obsidian(path: str, vault: str = None, subdir: str = None,
                      summary: bool = False, moc_only: bool = False) -> list:
    """
    将 XMind 文件导入 Obsidian Vault。

    参数:
        path: .xmind 文件路径
        vault: Obsidian vault 根目录（默认 ~/obsidian-vault）
        subdir: 笔记存放的子目录（默认 Notes/未分类/思维导图）
        summary: 是否生成汇总页
        moc_only: 是否只生成 MOC 索引，不建单页

    返回:
        生成的文件路径列表
    """
    if vault is None:
        vault = os.path.expanduser('~/obsidian-vault')
    if subdir is None:
        subdir = 'Notes/未分类/思维导图'

    sheets = parse_xmind(path)
    base_dir = os.path.join(vault, subdir)
    os.makedirs(base_dir, exist_ok=True)

    generated_files = []
    sheets_nodes = []

    for sheet in sheets:
        sheet_title = sheet['sheet']
        root = sheet['root']

        # 收集所有节点
        all_nodes = _collect_all_nodes(root)
        sheet_name = sanitize_filename(sheet_title)
        node_dir = os.path.join(base_dir, sheet_name)
        os.makedirs(node_dir, exist_ok=True)

        sheets_nodes.append((sheet_title, root, all_nodes))

        # 生成 MOC 索引
        moc_content = _generate_moc(sheet_title, root, all_nodes)
        moc_path = os.path.join(base_dir, f'{sheet_name} — 索引.md')
        with open(moc_path, 'w', encoding='utf-8') as f:
            f.write(moc_content)
        generated_files.append(moc_path)

        if not moc_only:
            # 为每个节点生成笔记
            for node_info in all_nodes:
                note_content = _generate_note(node_info, sheet_title, node_dir)
                note_name = sanitize_filename(node_info['title'])
                note_path = os.path.join(node_dir, f'{note_name}.md')

                # 避免文件名冲突
                counter = 1
                while os.path.exists(note_path):
                    note_path = os.path.join(node_dir, f'{note_name}_{counter}.md')
                    counter += 1

                with open(note_path, 'w', encoding='utf-8') as f:
                    f.write(note_content)
                generated_files.append(note_path)

    if summary and sheets_nodes:
        summary_content = _generate_summary_page(sheets_nodes)
        summary_path = os.path.join(vault, 'XMind导入汇总.md')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        generated_files.append(summary_path)

    return generated_files


def main():
    if len(sys.argv) < 2:
        print(f'用法: python {os.path.basename(sys.argv[0])} 文件.xmind [选项]')
        print('选项:')
        print('  --vault <路径>    Obsidian vault 目录')
        print('  --dir <目录>      笔记存放子目录')
        print('  --summary         生成汇总页')
        print('  --moc-only        只生成 MOC 索引')
        sys.exit(1)

    path = sys.argv[1]
    vault = None
    subdir = None
    gen_summary = False
    moc_only = False

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--vault' and i + 1 < len(sys.argv):
            vault = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--dir' and i + 1 < len(sys.argv):
            subdir = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--summary':
            gen_summary = True
            i += 1
        elif sys.argv[i] == '--moc-only':
            moc_only = True
            i += 1
        else:
            i += 1

    try:
        files = xmind_to_obsidian(path, vault, subdir, gen_summary, moc_only)
        print(f'✅ 生成 {len(files)} 个文件:')
        for f in files:
            print(f'  📄 {f}')
    except Exception as e:
        print(f'❌ 导入失败: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
