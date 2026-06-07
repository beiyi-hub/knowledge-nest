     1|#!/usr/bin/env python3
     2|"""
     3|XMind → Obsidian 联动工具
     4|
     5|功能：
     6|1. 解析 .xmind 思维导图
     7|2. 自动写入 Obsidian Vault，每个主题分支变成独立笔记
     8|3. 自动建立 [[双向链接]] 保持思维导图的层级关系
     9|4. 自动生成索引页（MOC - Map of Content）
    10|
    11|用法：
    12|  python3 xmind_to_obsidian.py 文件.xmind                # 导入默认路径
    13|  python3 xmind_to_obsidian.py 文件.xmind --vault ~/obsidian-vault --dir 经济学/思维导图
    14|  python3 xmind_to_obsidian.py 文件.xmind --moc-only     # 只生成索引页
    15|  python3 xmind_to_obsidian.py 文件.xmind --flat         # 扁平模式（不嵌套文件夹）
    16|"""
    17|import sys
    18|import os
    19|from pathlib import Path
    20|import datetime
    21|import re
    22|
    23|# 导入 xmind_parser
    24|sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
    25|try:
    26|    from xmind_parser import parse_xmind
    27|except ImportError:
    28|    # Fallback: try relative import
    29|    from xmind_parser import parse_xmind
    30|
    31|VAULT_DEFAULT = os.path.expanduser('~/obsidian-vault')
    32|
    33|def sanitize_filename(name):
    34|    """将标题转为安全的文件名。"""
    35|    # 替换特殊字符
    36|    name = name.replace('/', '-').replace('\\', '-')
    37|    name = name.replace(':', '-').replace('*', '').replace('?', '')
    38|    name = name.replace('"', '').replace('<', '').replace('>', '').replace('|', '')
    39|    # 限制长度
    40|    if len(name) > 80:
    41|        name = name[:80]
    42|    return name.strip()
    43|
    44|def slugify(text):
    45|    """简化文本为URL友好的slug。"""
    46|    text = text.lower()
    47|    text = re.sub(r'[^\w\s-]', '', text)
    48|    text = re.sub(r'[-\s]+', '-', text)
    49|    return text.strip('-')
    50|
    51|def topic_to_obsidian(topic, parent_title=None, level=1, vault_dir=None, target_subdir='', sheet_title=''):
    52|    """
    53|    把 topic 树变成 Obsidian 笔记文件。
    54|    返回生成的笔记文件路径列表。
    55|    """
    56|    created_files = []
    57|    title = topic['title']
    58|    children = topic.get('children', [])
    59|    
    60|    if not title:
    61|        return created_files
    62|    
    63|    # 构建笔记内容
    64|    lines = []
    65|    lines.append('---')
    66|    lines.append(f'title: {title}')
    67|    lines.append(f'created: {datetime.date.today()}')
    68|    lines.append(f'source: "XMind → {sheet_title}"')
    69|    lines.append(f'tags: [xmind, 思维导图]')
    70|    if parent_title:
    71|        lines.append(f'parent: "{parent_title}"')
    72|    lines.append('---')
    73|    lines.append('')
    74|    lines.append(f'# {title}')
    75|    lines.append('')
    76|    
    77|    # 父笔记链接
    78|    if parent_title:
    79|        parent_filename = sanitize_filename(parent_title)
    80|        lines.append(f'> 属于：[[{parent_filename}]]')
    81|        lines.append('')
    82|    
    83|    # 如果这个节点有子主题，生成子主题列表+链接
    84|    if children:
    85|        lines.append('## 分支')
    86|        lines.append('')
    87|        for child in children:
    88|            child_title = child['title']
    89|            child_filename = sanitize_filename(child_title)
    90|            child_count = len(child.get('children', []))
    91|            if child_count:
    92|                lines.append(f'- [[{child_filename}]] — *{child_count} 个子分支*')
    93|            else:
    94|                lines.append(f'- [[{child_filename}]]')
    95|        lines.append('')
    96|    
    97|    # 如果是叶子节点（没有子主题），留空供笔记
    98|    if not children:
    99|        lines.append('> *此节点由 XMind 导入，可在此补充笔记内容*')
   100|        lines.append('')
   101|    
   102|    # 同级节点导航
   103|    lines.append('---')
   104|    lines.append('')
   105|    lines.append(f'*从 XMind 「{sheet_title}」导入 · {datetime.date.today()}*')
   106|    
   107|    content = '\n'.join(lines)
   108|    
   109|    # 确定保存路径
   110|    if vault_dir:
   111|        # 每个主题独立文件夹（保留层级）或扁平模式
   112|        if target_subdir:
   113|            note_path = Path(vault_dir) / target_subdir / f'{sanitize_filename(title)}.md'
   114|        else:
   115|            note_path = Path(vault_dir) / f'{sanitize_filename(title)}.md'
   116|        
   117|        note_path.parent.mkdir(parents=True, exist_ok=True)
   118|        
   119|        # 避免覆盖已有笔记
   120|        if note_path.exists():
   121|            # 读取已有内容，如果不含 xmind tag 则跳过
   122|            existing = note_path.read_text(encoding='utf-8')
   123|            if 'xmind' not in existing and 'source: "XMind' not in existing:
   124|                # 追加 xmind 链接
   125|                existing = existing.rstrip() + '\n\n---\n\n*关联 XMind 「{sheet_title}」· {date}*\n'.format(
   126|                    sheet_title=sheet_title, date=datetime.date.today())
   127|                note_path.write_text(existing, encoding='utf-8')
   128|                created_files.append(str(note_path))
   129|                # 仍然为子主题创建文件
   130|                for child in children:
   131|                    created_files.extend(
   132|                        topic_to_obsidian(child, title, level + 1, vault_dir, target_subdir, sheet_title)
   133|                    )
   134|                return created_files
   135|        
   136|        note_path.write_text(content, encoding='utf-8')
   137|        created_files.append(str(note_path))
   138|    
   139|    # 递归处理子主题
   140|    for child in children:
   141|        created_files.extend(
   142|            topic_to_obsidian(child, title, level + 1, vault_dir, target_subdir, sheet_title)
   143|        )
   144|    
   145|    return created_files
   146|
   147|def generate_moc(sheets, vault_dir, target_subdir=''):
   148|    """生成 MOC（Map of Content）索引页。"""
   149|    lines = []
   150|    lines.append('---')
   151|    lines.append(f'title: 思维导图索引')
   152|    lines.append(f'created: {datetime.date.today()}')
   153|    lines.append('tags: [xmind, index, MOC]')
   154|    lines.append('---')
   155|    lines.append('')
   156|    lines.append('# 🧠 思维导图索引')
   157|    lines.append('')
   158|    lines.append('> 此页由 XMind 导入工具自动生成，汇总所有导入的思维导图。')
   159|    lines.append('')
   160|    lines.append('---')
   161|    lines.append('')
   162|    
   163|    for sheet in sheets:
   164|        sheet_title = sheet['title']
   165|        root_title = sheet['root']['title']
   166|        root_filename = sanitize_filename(root_title)
   167|        
   168|        lines.append(f'## 📋 {sheet_title}')
   169|        lines.append('')
   170|        lines.append(f'**根节点：** [[{root_filename}]]')
   171|        lines.append('')
   172|        lines.append('### 结构概览')
   173|        lines.append('')
   174|        
   175|        # 生成缩进版的树结构（用Obsidian链接）
   176|        def render_tree(topic, indent=0):
   177|            result = []
   178|            title = topic['title']
   179|            filename = sanitize_filename(title)
   180|            children = topic.get('children', [])
   181|            
   182|            prefix = '  ' * indent
   183|            if children:
   184|                result.append(f'{prefix}- [[{filename}]] (子分支: {len(children)})')
   185|            else:
   186|                result.append(f'{prefix}- [[{filename}]]')
   187|            
   188|            for child in children:
   189|                result.extend(render_tree(child, indent + 1))
   190|            
   191|            return result
   192|        
   193|        tree_lines = render_tree(sheet['root'])
   194|        for line in tree_lines:
   195|            lines.append(line)
   196|        
   197|        lines.append('')
   198|        lines.append('---')
   199|        lines.append('')
   200|    
   201|    lines.append(f'*最后更新：{datetime.date.today()}*')
   202|    
   203|    content = '\n'.join(lines)
   204|    
   205|    # 写入
   206|    if vault_dir:
   207|        if target_subdir:
   208|            moc_path = Path(vault_dir) / target_subdir / '思维导图索引.md'
   209|        else:
   210|            moc_path = Path(vault_dir) / '思维导图索引.md'
   211|        moc_path.parent.mkdir(parents=True, exist_ok=True)
   212|        moc_path.write_text(content, encoding='utf-8')
   213|        return str(moc_path)
   214|    
   215|    return None
   216|
   217|def generate_summary_note(sheets, vault_dir):
   218|    """生成一张汇总笔记，包含所有XMind的结构概览+链接。"""
   219|    lines = []
   220|    now = datetime.datetime.now()
   221|    
   222|    lines.append('---')
   223|    lines.append(f'title: XMind 导入汇总')
   224|    lines.append(f'created: {now.strftime("%Y-%m-%d %H:%M")}')
   225|    lines.append(f'tags: [xmind, 导入, summary]')
   226|    lines.append('---')
   227|    lines.append('')
   228|    lines.append('# 📦 XMind 导入汇总')
   229|    lines.append('')
   230|    lines.append(f'**导入时间：** {now.strftime("%Y-%m-%d %H:%M")}')
   231|    lines.append(f'**文件数：** {len(sheets)} 个画布')
   232|    lines.append('')
   233|    lines.append('---')
   234|    lines.append('')
   235|    
   236|    for sheet in sheets:
   237|        sheet_title = sheet['title']
   238|        root = sheet['root']
   239|        lines.append(f'## 🗺️ {sheet_title}')
   240|        lines.append('')
   241|        lines.append(f'- 根主题：**{root["title"]}**')
   242|        lines.append(f'- 深度：{max_depth(root)} 层')
   243|        lines.append(f'- 节点数：{count_nodes(root)} 个')
   244|        lines.append('')
   245|        
   246|        # 列出所有叶子节点（便于快速链接）
   247|        leaves = get_leaves(root)
   248|        if leaves:
   249|            lines.append(f'📌 末端节点（{len(leaves)}个）：')
   250|            lines.append('  ' + ', '.join([f'[[{sanitize_filename(l)}]]' for l in leaves]))
   251|        
   252|        lines.append('')
   253|        lines.append('---')
   254|        lines.append('')
   255|    
   256|    lines.append('---')
   257|    lines.append(f'*由 Hermes Agent XMind → Obsidian 工具生成*')
   258|    
   259|    content = '\n'.join(lines)
   260|    
   261|    if vault_dir:
   262|        summary_path = Path(vault_dir) / 'XMind导入汇总.md'
   263|        summary_path.write_text(content, encoding='utf-8')
   264|        return str(summary_path)
   265|    return None
   266|
   267|def max_depth(topic):
   268|    """计算树的最大深度。"""
   269|    children = topic.get('children', [])
   270|    if not children:
   271|        return 1
   272|    return 1 + max(max_depth(c) for c in children)
   273|
   274|def count_nodes(topic):
   275|    """计算节点总数。"""
   276|    count = 1
   277|    for child in topic.get('children', []):
   278|        count += count_nodes(child)
   279|    return count
   280|
   281|def get_leaves(topic):
   282|    """获取所有叶子节点的标题。"""
   283|    children = topic.get('children', [])
   284|    if not children:
   285|        return [topic['title']]
   286|    leaves = []
   287|    for child in children:
   288|        leaves.extend(get_leaves(child))
   289|    return leaves
   290|
   291|def main():
   292|    import argparse
   293|    
   294|    parser = argparse.ArgumentParser(description='XMind → Obsidian 思维导图导入工具')
   295|    parser.add_argument('xmind_file', help='.xmind 文件路径')
   296|    parser.add_argument('--vault', default=VAULT_DEFAULT, help=f'Obsidian vault 路径 (默认: {VAULT_DEFAULT})')
   297|    parser.add_argument('--dir', default='', help='vault 内子目录 (如 "Notes/经济学/思维导图")')
   298|    parser.add_argument('--moc-only', action='store_true', help='只生成 MOC 索引页，不生成单个笔记')
   299|    parser.add_argument('--flat', action='store_true', help='扁平模式：所有笔记放在同一目录')
   300|    parser.add_argument('--summary', action='store_true', help='同时生成汇总笔记')
   301|    
   302|    args = parser.parse_args()
   303|    
   304|    if not os.path.exists(args.xmind_file):
   305|        print(f"❌ 文件不存在: {args.xmind_file}")
   306|        sys.exit(1)
   307|    
   308|    vault_path = os.path.expanduser(args.vault)
   309|    target_dir = args.dir
   310|    
   311|    print(f"📖 解析: {args.xmind_file}")
   312|    sheets = parse_xmind(args.xmind_file)
   313|    print(f"✅ 发现 {len(sheets)} 个画布")
   314|    
   315|    if args.moc_only:
   316|        # 只生成 MOC
   317|        moc_path = generate_moc(sheets, vault_path, target_dir)
   318|        if moc_path:
   319|            print(f"📄 MOC 索引页: {moc_path}")
   320|        return
   321|    
   322|    total_files = 0
   323|    for sheet in sheets:
   324|        sheet_title = sheet['title']
   325|        root = sheet['root']
   326|        
   327|        print(f"\n📋 画布: {sheet_title}")
   328|        print(f"  根节点: {root['title']} ({count_nodes(root)} 个节点)")
   329|        
   330|        if not args.flat and target_dir:
   331|            # 按画布名分文件夹
   332|            subdir = os.path.join(target_dir, sanitize_filename(sheet_title))
   333|        else:
   334|            subdir = target_dir
   335|        
   336|        # 生成单个笔记
   337|        files = topic_to_obsidian(
   338|            root, 
   339|            parent_title=None, 
   340|            level=1, 
   341|            vault_dir=vault_path, 
   342|            target_subdir=subdir,
   343|            sheet_title=sheet_title
   344|        )
   345|        total_files += len(files)
   346|        print(f"  生成了 {len(files)} 个笔记文件")
   347|    
   348|    # MOC
   349|    moc_path = generate_moc(sheets, vault_path, target_dir)
   350|    print(f"\n📄 MOC 索引页: {moc_path}")
   351|    
   352|    # 汇总
   353|    if args.summary:
   354|        summary_path = generate_summary_note(sheets, vault_path)
   355|        print(f"📄 汇总页: {summary_path}")
   356|    
   357|    print(f"\n✅ 完成！共创建/更新 {total_files} 个笔记文件")
   358|    print(f"📂 位置: {os.path.join(vault_path, target_dir) if target_dir else vault_path}")
   359|
   360|if __name__ == '__main__':
   361|    main()
   362|