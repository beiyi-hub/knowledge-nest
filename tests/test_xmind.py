#!/usr/bin/env python3
"""XMind 解析器单元测试。"""
import sys
import os
import tempfile
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'parser'))
from xmind_parser import parse_xmind, to_tree, to_markdown, to_text


def _make_xmind8_xml():
    """生成 XMind 8 格式的 content.xml。"""
    NS = 'urn:xmind:xmap:xmlns:content:2.0'
    ET.register_namespace('', NS)

    root = ET.Element(f'{{{NS}}}xmap-content')
    sheet = ET.SubElement(root, f'{{{NS}}}sheet')
    sheet.set('title', '测试导图')

    topic = ET.SubElement(sheet, f'{{{NS}}}topic')
    title_el = ET.SubElement(topic, f'{{{NS}}}title')
    title_el.text = '根节点'

    children = ET.SubElement(topic, f'{{{NS}}}children')
    topics = ET.SubElement(children, f'{{{NS}}}topics')
    topics.set('type', 'attached')

    for name in ['子节点A', '子节点B']:
        child = ET.SubElement(topics, f'{{{NS}}}topic')
        ct = ET.SubElement(child, f'{{{NS}}}title')
        ct.text = name

    return ET.tostring(root, encoding='unicode')


def _make_test_xmind(tmpdir):
    """创建一个带 XML 的测试 .xmind 文件。"""
    path = os.path.join(tmpdir, 'test.xmind')
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('content.xml', _make_xmind8_xml().encode('utf-8'))
        z.writestr('meta.xml', '<meta></meta>')
    return path


def test_parse_basic():
    """测试基础解析。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _make_test_xmind(tmpdir)
        sheets = parse_xmind(path)
        assert len(sheets) == 1
        assert sheets[0]['sheet'] == '测试导图'
        assert sheets[0]['root']['title'] == '根节点'
        assert len(sheets[0]['root']['children']) == 2
        assert sheets[0]['root']['children'][0]['title'] == '子节点A'
        assert sheets[0]['root']['children'][1]['title'] == '子节点B'
    print('✅ test_parse_basic 通过')


def test_to_tree():
    """测试树形图输出。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _make_test_xmind(tmpdir)
        sheets = parse_xmind(path)
        tree = to_tree(sheets)
        assert '根节点' in tree
        assert '子节点A' in tree
        assert '子节点B' in tree
        assert tree.count('├──') >= 2
    print('✅ test_to_tree 通过')


def test_to_markdown():
    """测试 Markdown 输出。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _make_test_xmind(tmpdir)
        sheets = parse_xmind(path)
        md = to_markdown(sheets)
        assert md.startswith('#')
        assert '## 根节点' in md
        assert '### 子节点A' in md
    print('✅ test_to_markdown 通过')


def test_to_text():
    """测试缩进文本输出。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _make_test_xmind(tmpdir)
        sheets = parse_xmind(path)
        text = to_text(sheets)
        assert '测试导图:' in text
        assert '根节点' in text
        assert '子节点A' in text
    print('✅ test_to_text 通过')


if __name__ == '__main__':
    test_parse_basic()
    test_to_tree()
    test_to_markdown()
    test_to_text()
    print('\n🎉 全部测试通过！')
