#!/usr/bin/env python3
"""
XMind parser — 纯Python，零依赖，解析 .xmind 思维导图文件。

支持 XMind 8（content.xml）和 XMind 2020+（content.json）。
输出格式：树形图、Markdown、缩进文本。

用法：
    python xmind_parser.py 文件.xmind           # 树形图
    python xmind_parser.py 文件.xmind --markdown # Markdown
    python xmind_parser.py 文件.xmind --text     # 缩进文本
"""

import zipfile
import xml.etree.ElementTree as ET
import json
import sys
import os

# ── 命名空间 ──
NS_XMIND_8 = 'urn:xmind:xmap:xmlns:content:2.0'
NS_XMIND_8_ALT = 'urn:xmind:xmap:xmlns:content:2.1'
NS_FO = 'http://www.w3.org/1999/XSL/Format'
NS_SVG = 'http://www.w3.org/2000/svg'
NS_XHTML = 'http://www.w3.org/1999/xhtml'


def _extract_title(el, ns_map):
    """从 topic 元素中提取标题。"""
    # XMind 8
    title_el = el.find(f'{{{ns_map.get("xmind", "")}}}title')
    if title_el is not None and title_el.text:
        return title_el.text.strip()

    # XMind 2020+ JSON
    return el.get('title', '').strip() or '（未命名）'


def _get_children(children_el, ns_map):
    """从 <children> 中提取子节点列表。

    实际结构: <children> → <topics type="attached"> → <topic>...
    """
    children = []
    if children_el is None:
        return children

    ns = ns_map.get('xmind', '')
    # <children> 内部可能有多个 <topics> (attached 和 detached)
    for topics_el in children_el.findall(f'{{{ns}}}topics'):
        for topic_el in topics_el.findall(f'{{{ns}}}topic'):
            title = _extract_title(topic_el, ns_map)
            sub = _get_children(topic_el.find(f'{{{ns}}}children'), ns_map)
            children.append({'title': title, 'children': sub, 'id': topic_el.get('id', '')})
    return children


def _parse_xmind8(content_xml: bytes) -> list:
    """解析 XMind 8 格式的 content.xml。"""
    root = ET.fromstring(content_xml)
    tag = root.tag
    ns_uri = tag[tag.find('{') + 1:tag.find('}')] if '}' in tag else ''
    ns_map = {'xmind': ns_uri}

    sheets = []
    for sheet_el in root.findall(f'{{{ns_uri}}}sheet'):
        sheet_title = sheet_el.get('title', '').strip() or 'Sheet 1'
        root_topic = sheet_el.find(f'{{{ns_uri}}}topic')
        if root_topic is None:
            continue
        root_title = _extract_title(root_topic, ns_map)
        children = _get_children(
            root_topic.find(f'{{{ns_uri}}}children'), ns_map
        )
        sheets.append({
            'sheet': sheet_title,
            'root': {'title': root_title, 'children': children, 'id': root_topic.get('id', '')}
        })
    return sheets


def _parse_xmind2020(content_json: bytes) -> list:
    """解析 XMind 2020+ 格式的 content.json。"""
    data = json.loads(content_json)
    sheets = []
    for sheet in data:
        st = sheet.get('title', 'Sheet 1')
        root = sheet.get('rootTopic', {})
        sheets.append({
            'sheet': st,
            'root': _walk_json_topic(root)
        })
    return sheets


def _walk_json_topic(topic: dict) -> dict:
    """递归遍历 JSON 格式的 topic 树。"""
    title = topic.get('title', '').strip() or '（未命名）'
    children = []
    for child in topic.get('children', {}).get('attached', []):
        children.append(_walk_json_topic(child))
    return {'title': title, 'children': children, 'id': topic.get('id', '')}


def parse_xmind(path: str) -> list:
    """
    解析 .xmind 文件，返回 sheets 列表。

    返回格式：
    [
        {
            'sheet': 'Sheet1',
            'root': {
                'title': '根节点标题',
                'children': [
                    {'title': '子节点', 'children': [...], 'id': '...'},
                    ...
                ],
                'id': '...'
            }
        },
        ...
    ]
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f'文件不存在: {path}')

    with zipfile.ZipFile(path, 'r') as z:
        # 优先 XMind 8 (content.xml)
        if 'content.xml' in z.namelist():
            with z.open('content.xml') as f:
                return _parse_xmind8(f.read())
        # XMind 2020+ (content.json)
        elif 'content.json' in z.namelist():
            with z.open('content.json') as f:
                return _parse_xmind2020(f.read())
        else:
            raise ValueError('无法识别XMind格式: 未找到 content.xml 或 content.json')


# ── 输出格式 ──

def to_tree(sheets: list) -> str:
    """输出树形图文本。"""
    lines = []
    for sheet in sheets:
        lines.append(f'# {sheet["sheet"]}')
        _tree_lines(sheet['root'], lines, prefix='')
        lines.append('')
    return '\n'.join(lines).rstrip()


def _tree_lines(node, lines, prefix):
    """递归生成树形图行。"""
    lines.append(f'{prefix}├── {node["title"]}')
    for i, child in enumerate(node['children']):
        _tree_lines(child, lines, prefix + '│   ')


def to_markdown(sheets: list) -> str:
    """输出 Markdown 格式。"""
    lines = []
    for sheet in sheets:
        lines.append(f'# {sheet["sheet"]}')
        lines.append('')
        _md_lines(sheet['root'], lines, level=2)
        lines.append('')
    return '\n'.join(lines).rstrip()


def _md_lines(node, lines, level=1):
    """递归生成 Markdown 行。"""
    lines.append(f'{"#" * level} {node["title"]}')
    lines.append('')
    for child in node['children']:
        _md_lines(child, lines, level + 1)


def to_text(sheets: list, indent: str = '  ') -> str:
    """输出缩进文本。"""
    lines = []
    for sheet in sheets:
        lines.append(f'{sheet["sheet"]}:')
        _text_lines(sheet['root'], lines, depth=1, indent=indent)
        lines.append('')
    return '\n'.join(lines).rstrip()


def _text_lines(node, lines, depth=0, indent='  '):
    """递归生成缩进文本行。"""
    lines.append(f'{indent * depth}{node["title"]}')
    for child in node['children']:
        _text_lines(child, lines, depth + 1, indent)


# ── CLI ──

def main():
    if len(sys.argv) < 2:
        print(f'用法: python {os.path.basename(sys.argv[0])} 文件.xmind [--markdown|--text]')
        sys.exit(1)

    path = sys.argv[1]
    fmt = 'tree'
    if '--markdown' in sys.argv:
        fmt = 'markdown'
    elif '--text' in sys.argv:
        fmt = 'text'

    try:
        sheets = parse_xmind(path)
    except Exception as e:
        print(f'❌ 解析失败: {e}', file=sys.stderr)
        sys.exit(1)

    if fmt == 'tree':
        print(to_tree(sheets))
    elif fmt == 'markdown':
        print(to_markdown(sheets))
    else:
        print(to_text(sheets))


if __name__ == '__main__':
    main()
