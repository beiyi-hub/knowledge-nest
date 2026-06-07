     1|---
     2|name: knowledge-pipeline
     3|description: 知识内容全流程流水线 — 从B站/视频链接到AI笔记到Obsidian Vault再到XMind思维导图联动。支持：B站视频下载、Whisper转写、LLM整理笔记、Obsidian分类存档、XMind解析导入、双向链接知识网络构建。
     4|version: 2.0.0
     5|tags: [knowledge, pipeline, bilibili, obsidian, xmind, notes, 知识管理, 笔记, 视频转文字]
     6|triggers:
     7|  - B站链接
     8|  - 视频链接
     9|  - 整理笔记
    10|  - 知识管理
    11|  - 思维导图
    12|  - xmind文件
    13|  - obsidian导入
    14|---
    15|
    16|# Knowledge Pipeline — 知识内容全流程流水线
    17|
    18|> 一条命令，从视频链接到结构化知识库。
    19|
    20|## 流程总览
    21|
    22|```
    23|用户发链接/文件
    24|    │
    25|    ▼
    26|┌─────────────────────────────────────────────┐
    27|│  Phase 0: 输入识别                           │
    28|│  ├  B站/YouTube链接 → 下载视频               │
    29|│  ├  .mp4/.mp3文件 → 直接转写                │
    30|│  └  .xmind文件 → 解析+导入Obsidian          │
    31|└─────────────────────────────────────────────┘
    32|    │
    33|    ▼
    34|┌─────────────────────────────────────────────┐
    35|│  Phase 1: 转写 (Whisper)                    │
    36|│  ├  faster-whisper → 中文/英文/俄语         │
    37|│  ├  输出: 时间轴文本 + SRT + 笔记草稿       │
    38|│  └  注意: HF国内镜像 (hf-mirror.com)        │
    39|└─────────────────────────────────────────────┘
    40|    │
    41|    ▼
    42|┌─────────────────────────────────────────────┐
    43|│  Phase 2: LLM整理 (关键步骤)                │
    44|│  ├  阅读Whisper全文 → LLM整理               │
    45|│  ├  结构化: YAML front-matter + 分级内容    │
    46|│  └  判断分类 → 写入对应Obsidian目录         │
    47|└─────────────────────────────────────────────┘
    48|    │
    49|    ▼
    50|┌─────────────────────────────────────────────┐
    51|│  Phase 3: Obsidian 存入                     │
    52|│  ├  自动分类到: AI学习/编程/经济学/语言...  │
    53|│  ├  标准front-matter + [[双向链接]]         │
    54|│  └  兼容知识图谱 → 后续可检索关联           │
    55|└─────────────────────────────────────────────┘
    56|    │
    57|    ▼
    58|┌─────────────────────────────────────────────┐
    59|│  Phase 4 (可选): XMind 思维导图联动         │
    60|│  ├  解析 .xmind → 提取主题树               │
    61|│  ├  导入 Obsidian → 每个节点=独立笔记      │
    62|│  └  自动建立 [[双向链接]] + MOC索引页       │
    63|└─────────────────────────────────────────────┘
    64|```
    65|
    66|---
    67|
    68|## Phase 0: 输入识别
    69|
    70|| 收到什么 | 做什么 |
    71||---------|--------|
    72|| B站链接 (bilibili.com/video/BV...) | 下载视频 → Phase 1 |
    73|| YouTube链接 | 用 `youtube-content` skill 获取转录 |
    74|| .mp4/.mp3/.mkv文件 | 直接用 process_video.py 转写 |
    75|| .xmind文件 | 跳转到 Phase 4 |
    76|| 只有文字/文章 | 直接LLM整理 → Phase 3 |
    77|
    78|### B站下载（核心：绕过412反爬）
    79|
    80|**不能**用 yt-dlp（B站412封杀），必须走 B站API + Playwright cookies。
    81|
    82|完整脚本模板（已验证可用）：
    83|
    84|```python
    85|import requests, json, os
    86|from tqdm import tqdm
    87|from playwright.sync_api import sync_playwright
    88|
    89|bvid = "BV编号"  # 从链接提取
    90|headers = {
    91|    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    92|    'Referer': 'https://www.bilibili.com/'
    93|}
    94|
    95|# Step 1: 获取cid
    96|info = requests.get(f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}', headers=headers).json()
    97|cid = info['data']['cid']
    98|title = info['data']['title']
    99|
   100|# Step 2: 获取新鲜cookies
   101|with sync_playwright() as p:
   102|    browser = p.chromium.launch(headless=True)
   103|    ctx = browser.new_context()
   104|    page = ctx.new_page()
   105|    page.goto('https://www.bilibili.com/', wait_until='networkidle')
   106|    cookies = ctx.cookies()
   107|    browser.close()
   108|
   109|cookie_str = '; '.join([f'{c["name"]}={c["value"]}' for c in cookies])
   110|headers['Cookie'] = cookie_str
   111|
   112|# Step 3: 获取视频流地址
   113|play = requests.get(f'https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn=80', headers=headers).json()
   114|video_url = play['data']['durl'][0]['url']
   115|
   116|# Step 4: 下载
   117|os.makedirs(os.path.expanduser('~/video_to_notes/input'), exist_ok=True)
   118|safe_title = title.replace('/', '_').replace(' ', '')
   119|out = os.path.expanduser(f'~/video_to_notes/input/{safe_title}.mp4')
   120|r = requests.get(video_url, stream=True)
   121|total = int(r.headers.get('content-length', 0))
   122|with open(out, 'wb') as f:
   123|    for chunk in tqdm(r.iter_content(1024*1024), total=total//(1024*1024), unit='MB'):
   124|        f.write(chunk)
   125|```
   126|
   127|**关键参数：** `qn=80` = 1080P, `qn=32` = 480P, `qn=16` = 360P
   128|
   129|---
   130|
   131|## Phase 1: Whisper转写
   132|
   133|使用 `~/video_to_notes/process_video.py` 脚本。
   134|
   135|### 命令
   136|
   137|```bash
   138|export HF_ENDPOINT=https://hf-mirror.com  # 国内镜像必设
   139|python3 ~/video_to_notes/process_video.py input.mp4 -l zh -m base -o ~/video_to_notes/output/
   140|```
   141|
   142|### 语言参数
   143|
   144|| 内容语言 | 参数 | 推荐模型 |
   145||---------|------|---------|
   146|| 中文 | `-l zh` | base（快）或 small（准） |
   147|| 英文 | `-l en` | base 或 small |
   148|| 俄语 | `-l ru` | small（俄语base准确率低） |
   149|| 自动 | 不传 | base |
   150|
   151|### 输出文件
   152|
   153|```
   154|~/video_to_notes/output/
   155|├── 视频名_transcript.txt   # 全文时间轴文本
   156|├── 视频名_subtitle.srt     # 字幕
   157|├── 视频名_笔记.md          # Whisper粗版笔记（时间线+摘要）
   158|└── 视频名_audio.mp3        # 提取的音频
   159|```
   160|
   161|### ⚠️ 注意事项
   162|
   163|- **HF国内镜像**：必须 `export HF_ENDPOINT=https://hf-mirror.com` 否则模型下载失败
   164|- **SOCKS代理**：如果 pip 报 Missing dependencies for SOCKS support，先 `unset ALL_PROXY all_proxy`
   165|- **不要直接使用`_笔记.md`**：那是Whisper原始输出，必须经LLM整理（Phase 2）
   166|
   167|---
   168|
   169|## Phase 2: LLM整理（核心步骤）
   170|
   171|**这是最关键的步骤。** 不要直接把Whisper输出扔给用户——必须：
   172|1. **完整阅读** Whisper输出的全文（`read_file`）
   173|2. **LLM整理**成结构化笔记
   174|3. **写入 Obsidian Vault**
   175|
   176|### 笔记结构标准
   177|
   178|```markdown
   179|---
   180|tags: [标签1, 标签2, 标签3]
   181|created: YYYY-MM-DD
   182|source: "B站 UP主名 → BV号"
   183|rating: ⭐⭐⭐⭐⭐
   184|topics: [核心主题1, 核心主题2]
   185|---
   186|
   187|# 笔记标题
   188|
   189|> 一句话摘要
   190|
   191|---
   192|
   193|## 📌 核心观点
   194|
   195|- ...
   196|
   197|## 📂 详细内容
   198|
   199|按逻辑分段
   200|
   201|## 💡 我的思考
   202|
   203|## 🔗 关联笔记
   204|
   205|## 📎 附件
   206|```
   207|
   208|### 分类规则
   209|
   210|| 内容类型 | Obsidian目录 | 示例 |
   211||---------|-------------|------|
   212|| AI/技术教程 | `Notes/AI学习/` | 机器学习、LLM教程 |
   213|| 编程/开发 | `Notes/编程开发/` | Python、框架使用 |
   214|| 经济学/商科 | `Notes/经济学/` | 经济分析、金融 |
   215|| 国际政治/时事评论 | `Notes/日常杂谈/` | 地缘分析、时评 |
   216|| 语言学习 | `Notes/语言学习/` | 雅思、口语 |
   217|| 学术研究 | `Notes/学术研究/` | 论文解读 |
   218|| Vlog/娱乐 | `Notes/日常杂谈/` | 生活分享 |
   219|
   220|### Whispers原始文本常见错误
   221|
   222|base模型在以下场景准确率下降：
   223|- 中英文混读 → 英文部分容易识别错
   224|- 专有名词 → "外部扣顶" = VibeCoding, "红白鸡小把王" = 红白机小霸王
   225|- LLM整理时需要根据上下文**推理修正**
   226|
   227|---
   228|
   229|## Phase 3: Obsidian Vault写入
   230|
   231|### Vault路径
   232|
   233|```
   234|OBSIDIAN_VAULT = ~/obsidian-vault
   235|```
   236|
   237|### 写入方式
   238|
   239|```python
   240|# 确定路径
   241|category = "经济学"  # 根据内容判断
   242|vault_path = os.path.expanduser(f'~/obsidian-vault/Notes/{category}/笔记标题.md')
   243|
   244|# 用 write_file 写入
   245|# 笔记内容需包含YAML front-matter
   246|```
   247|
   248|### 文件夹自动创建
   249|
   250|如果目标分类文件夹不存在，自动创建：
   251|```python
   252|os.makedirs(os.path.dirname(vault_path), exist_ok=True)
   253|```
   254|
   255|---
   256|
   257|## Phase 4: XMind思维导图联动（可选）
   258|
   259|当用户发送 `.xmind` 文件时，或想把已有笔记生成XMind结构时使用。
   260|
   261|### 脚本位置
   262|
   263|```
   264|~/.hermes/skills/productivity/xmind-parser/
   265|├── xmind_parser.py          # 基础解析器（树/文本/Markdown输出）
   266|└── xmind_to_obsidian.py     # XMind→Obsidian导入（双向链接版）
   267|```
   268|
   269|### 解析XMind
   270|
   271|```bash
   272|# 树形图
   273|python3 ~/.hermes/skills/productivity/xmind-parser/xmind_parser.py 文件.xmind
   274|
   275|# Markdown
   276|python3 ~/.hermes/skills/productivity/xmind-parser/xmind_parser.py 文件.xmind --markdown
   277|```
   278|
   279|### 导入到Obsidian
   280|
   281|```bash
   282|# 完整导入（生成节点笔记 + MOC索引）
   283|python3 ~/.hermes/skills/productivity/xmind-parser/xmind_to_obsidian.py 文件.xmind \
   284|  --vault ~/obsidian-vault --dir "Notes/经济学/思维导图" --summary
   285|```
   286|
   287|### XMind导入效果
   288|
   289|每个主题节点 → 独立 `.md` 文件，包含：
   290|- YAML front-matter（标题、创建日期、来源、父节点）
   291|- `[[双向链接]]` 指向父节点和子节点
   292|- 分支概览列表
   293|- MOC索引页汇总全部结构
   294|
   295|### 兼容性
   296|
   297|自动检测 XMind 8（content.xml）和 XMind 2020+（content.json）
   298|
   299|---
   300|
   301|## 完整工作流示例
   302|
   303|### 场景1：B站链接 → 笔记
   304|
   305|```
   306|用户发: https://www.bilibili.com/video/BV1xxxx
   307|  ↓
   308|1. 提取BV号，获取视频信息（标题、cid、时长、UP主）
   309|2. Playwright获取cookies → 获取视频流地址 → 下载
   310|3. Whisper转写（指定语言）
   311|4. LLM阅读全文 → 整理结构化笔记
   312|5. 判断分类 → 写入 ~/obsidian-vault/Notes/分类/标题.md
   313|6. 展示摘要给用户
   314|```
   315|
   316|### 场景2：XMind文件 → Obsidian知识网络
   317|
   318|```
   319|用户发: 经济学.xmind
   320|  ↓
   321|1. 解析xmind（ZIP内XML/JSON）
   322|2. 生成每个节点的独立笔记（含YAML + 双向链接）
   323|3. 生成MOC索引页
   324|4. 可选：生成汇总页
   325|```
   326|
   327|### 场景3：全流程——视频→笔记→XMind导入
   328|
   329|```
   330|B站链接 → 下载 → Whisper → LLM整理 → Obsidian笔记
   331|                                                    ↓
   332|                                              导出为XMind
   333|                                                    ↓
   334|                                           XMind导入Obsidian
   335|                                           （建立知识网络）
   336|```
   337|
   338|---
   339|
   340|## 依赖清单
   341|
   342|| 工具 | 用途 | 安装方式 |
   343||------|------|---------|
   344|| faster-whisper | 语音转文字 | `uv pip install faster-whisper` |
   345|| playwright | B站cookies/反爬 | 系统安装 |
   346|| requests | HTTP下载 | Hermes自带 |
   347|| tqdm | 下载进度条 | Hermes自带 |
   348|| zipfile | XMind解析 | Python标准库 |
   349|| xml.etree.ElementTree | XMind XML解析 | Python标准库 |
   350|| ffmpeg | 视频音频提取 | `apt install ffmpeg` |
   351|| edge-tts (可选) | TTS配音 | `pip install edge-tts` |
   352|
   353|---
   354|
   355|## 已知问题 & 避坑指南
   356|
   357|### 🔴 B站412反爬
   358|- yt-dlp 直接下载B站视频必定412
   359|- **必须**用 B站API + Playwright cookies + requests stream
   360|- cookies会过期，每次下载前要重新获取
   361|
   362|### 🔴 HF国内网络
   363|- HuggingFace被墙
   364|- **必须** `export HF_ENDPOINT=https://hf-mirror.com`
   365|
   366|### 🔴 SOCKS代理冲突
   367|- pip安装报 `Missing dependencies for SOCKS support`
   368|- **解决方法：** `unset ALL_PROXY all_proxy http_proxy https_proxy HTTP_PROXY HTTPS_PROXY`
   369|
   370|### 🔴 Python版本路径
   371|- Hermes用Python 3.11（uv管理的虚拟环境）
   372|- 系统同时装了3.12
   373|- **装包用** `uv pip install`，不用系统pip
   374|
   375|### 🔴 XMind库不可用
   376|- PyPI上的 `xmind` 包API不兼容
   377|- **解决方案：** 纯标准库实现
   378|
   379|### 🔴 大文件处理建议
   380|此对话中通过实践发现：
   381|- B站20分钟视频（~37MB）下载约 **45秒**，25分钟视频（~156MB）下载约 **2.5分钟**
   382|- Whisper base模型转写速度约 **10秒处理1分钟音频**
   383|- **重要：** 对于 5+ 步的视频处理流程，尽量在主线程中直接执行
   384|  - `delegate_task` 子任务可能因超时失败（每次工具调用都有时间限制）
   385|  - 主线程中分步执行 + `terminal`(timeout=600) 更可靠
   386|  - 分段操作：下载 → 转写 → 读取 → LLM整理 → 写入Obsidian，每步独立验证
   387|
   388|### 🔴 长文本LLM处理限制
   389|- 25分钟视频的Whisper转写输出约 **1700行/40KB**
   390|- `read_file` 分块读取（offset=1, limit=500, 再 offset=501...）
   391|- 一次不要加载全部内容到LLM上下文，分段阅读后总结
   392|- 更高效：先读前100行了解内容基调，再跳读到关键段落
   393|