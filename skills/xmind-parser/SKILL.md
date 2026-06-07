     1|---
     2|name: xmind-parser
     3|description: 解析 .xmind 思维导图文件，支持 XMind 8 和 XMind 2020+ 格式。提取主题树并转换为 Markdown / 文本 / 树形图输出。纯Python标准库实现，无第三方依赖。
     4|version: 1.1.0
     5|tags: [xmind, mindmap, 思维导图, parser, productivity]
     6|triggers:
     7|  - .xmind 文件
     8|  - 思维导图
     9|  - xmind
    10|  - mindmap
    11|  - 解析xmind
    12|---
    13|
    14|# XMind Parser — 思维导图解析
    15|
    16|## 概述
    17|
    18|解析 `.xmind` 文件（本质是 ZIP 包中的 XML/JSON），提取思维导图的主题层级树。支持 XMind 8（content.xml）和 XMind 2020+（content.json）两种格式。
    19|
    20|## 脚本位置
    21|
    22|`~/.hermes/skills/productivity/xmind-parser/xmind_parser.py`
    23|
    24|## 使用方法
    25|
    26|```bash
    27|# 树形图输出（默认）
    28|python3 ~/.hermes/skills/productivity/xmind-parser/xmind_parser.py 文件.xmind
    29|
    30|# Markdown 导出（适合存入 Obsidian）
    31|python3 ~/.hermes/skills/productivity/xmind-parser/xmind_parser.py 文件.xmind --markdown
    32|
    33|# 缩进文本
    34|python3 ~/.hermes/skills/productivity/xmind-parser/xmind_parser.py 文件.xmind --text
    35|```
    36|
    37|## 编程调用（agent内部使用）
    38|
    39|```python
    40|import sys
    41|sys.path.insert(0, '/home/ubuntu/.hermes/skills/productivity/xmind-parser')
    42|from xmind_parser import parse_xmind, to_markdown, to_text
    43|
    44|sheets = parse_xmind('文件.xmind')
    45|for sheet in sheets:
    46|    md = to_markdown(sheet['root'])
    47|    print(md)  # 可写入 Obsidian
    48|```
    49|
    50|## 输出示例
    51|
    52|```
    53|经济学
    54|├── 古典经济学
    55|│   ├── 看不见的手
    56|│   └── 比较优势
    57|├── 马克思主义
    58|│   ├── 劳动价值论
    59|│   ├── 剩余价值
    60|│   └── 历史唯物主义
    61|└── 博弈论
    62|    ├── 囚徒困境
    63|    └── 纳什均衡
    64|```
    65|
    66|## 兼容性
    67|
    68|| 格式 | XMind 8 | XMind 2020+ |
    69||------|---------|------------|
    70|| content.xml | ✅ 原生支持 | ❌ |
    71|| content.json | ❌ | ✅ 原生支持 |
    72|
    73|## 依赖
    74|
    75|- Python 标准库（zipfile, xml.etree.ElementTree）
    76|- 无第三方依赖
    77|
    78|---
    79|
    80|## XMind → Obsidian 联动
    81|
    82|将思维导图自动导入 Obsidian Vault，每个分支变成独立笔记，自动建立 [[双向链接]]。
    83|
    84|### 使用方法
    85|
    86|```bash
    87|# 基础导入
    88|python3 ~/.hermes/skills/productivity/xmind-parser/xmind_to_obsidian.py 文件.xmind
    89|
    90|# 指定导入目录（默认 ~/obsidian-vault）
    91|python3 ~/.hermes/skills/productivity/xmind-parser/xmind_to_obsidian.py 文件.xmind \\
    92|  --vault ~/obsidian-vault --dir "Notes/经济学/思维导图"
    93|
    94|# 只生成 MOC 索引（不建单页）
    95|python3 ~/.hermes/skills/productivity/xmind-parser/xmind_to_obsidian.py 文件.xmind --moc-only
    96|
    97|# 同时生成汇总页
    98|python3 ~/.hermes/skills/productivity/xmind-parser/xmind_to_obsidian.py 文件.xmind --summary
    99|```
   100|
   101|### 生成的笔记示例
   102|
   103|**根节点「经济学」**
   104|```
   105|---
   106|title: 经济学
   107|created: 2026-06-07
   108|source: "XMind → 经济学思维导图"
   109|tags: [xmind, 思维导图]
   110|---
   111|# 经济学
   112|## 分支
   113|- [[古典经济学]] — *2 个子分支*
   114|- [[凯恩斯主义]] — *3 个子分支*
   115|- [[行为经济学]] — *3 个子分支*
   116|```
   117|
   118|**子节点「凯恩斯主义」**
   119|```
   120|---
   121|title: 凯恩斯主义
   122|created: 2026-06-07
   123|source: "XMind → 经济学思维导图"
   124|tags: [xmind, 思维导图]
   125|parent: "经济学"
   126|---
   127|# 凯恩斯主义
   128|> 属于：[[经济学]]
   129|## 分支
   130|- [[总需求]]
   131|- [[乘数效应]]
   132|- [[政府干预]]
   133|```
   134|
   135|### 生成的文件
   136|
   137|```
   138|~/obsidian-vault/Notes/经济学/思维导图/
   139|├── 思维导图索引.md          # MOC — 全图索引页
   140|├── 经济学思维导图/           # 按画布分文件夹
   141|│   ├── 经济学.md            # 根节点
   142|│   ├── 古典经济学.md
   143|│   ├── 凯恩斯主义.md
   144|│   ├── 总需求.md            # 叶子节点
   145|│   ├── 乘数效应.md
   146|│   └── ...
   147|└── ~/obsidian-vault/XMind导入汇总.md  # 汇总（--summary模式）
   148|```
   149|### ❌ pip install xmind 不可用
   150|xmind的PyPI包（1.2.0）API与最新XMind格式不兼容：
   151|- `xmind.Workbook()` 不存在 → `from xmind.core.workbook import WorkbookDocument`
   152|- `SheetElement(wb)` 报 `hasAttribute` 错误 → 底层DOM解析bug
   153|- **解决方案：** 不要依赖xmind库，用 `zipfile + xml.etree.ElementTree` 手搓解析
   154|
   155|### ❌ Python3.11 vs 3.12 路径冲突
   156|系统装了python3.12但Hermes用uv管理的python3.11虚拟环境：
   157|- `pip install --user xmind` → 装到3.12的site-packages，3.11找不到
   158|- **解决方案：** 纯标准库实现，零依赖，不装任何外部包
   159|
   160|### ❌ f-string backslash 语法错误
   161|```python
   162|# Python3.11不支持f-string中的反斜杠
   163|title = sheet_el.get(f'{{{ns.get("xmind", "")}}}title', '')  # SyntaxError
   164|# 先提取变量
   165|ns_uri = ns.get('xmind', '')
   166|title = sheet_el.get(f'{{{ns_uri}}}title', '')  # OK
   167|```
   168|
   169|### ❌ XMind 8 namespace 问题
   170|XMind 8的content.xml使用 `urn:xmind:xmap:xmlns:content:2.0` 命名空间，但解析时命名空间URI可能不同。解析器自动检测并适配。
   171|
   172|### ✅ 创建测试XMind文件
   173|用原始XML手动构造content.xml，写入ZIP包即可：
   174|```xml
   175|<xmap-content xmlns="urn:xmind:xmap:xmlns:content:2.0">
   176|  <sheet title="Sheet1">
   177|    <topic id="root">
   178|      <title>根节点</title>
   179|      <children><topics type="attached">...</topics></children>
   180|    </topic>
   181|  </sheet>
   182|</xmap-content>
   183|```
   184|
   185|## 依赖
   186|
   187|- Python 标准库（zipfile, xml.etree.ElementTree, json）
   188|- 零第三方依赖
   189|