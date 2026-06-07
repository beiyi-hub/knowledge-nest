     1|---
     2|name: video-to-notes
     3|description: 视频/音频转文字+笔记 — 用 faster-whisper 将视频/音频转为带时间戳的文字、字幕、Markdown笔记。也支持从B站链接下载视频处理（绕过反爬）。
     4|---
     5|
     6|# 视频转笔记 🎬→📝
     7|
     8|用 faster-whisper 将用户发送的视频/音频文件自动转写为文字，并整理成笔记文档。
     9|
    10|## 文件结构
    11|
    12|```
    13|~/video_to_notes/
    14|├── process_video.py      ← 核心处理脚本
    15|├── input/                ← 输入文件放这里
    16|└── output/               ← 处理结果输出（自动创建）
    17|```
    18|
    19|## 脚本位置
    20|
    21|`~/video_to_notes/process_video.py`
    22|
    23|## 使用方法
    24|
    25|```bash
    26|# 基础用法（视频自动提取音频）
    27|python3 ~/video_to_notes/process_video.py input.mp4 --output-dir ./output
    28|
    29|# 指定语言（中文）
    30|python3 ~/video_to_notes/process_video.py input.mp4 --language zh --model base
    31|
    32|# 俄语
    33|python3 ~/video_to_notes/process_video.py input.mp4 --language ru --model small
    34|
    35|# 英语+大模型（更准，但慢）
    36|python3 ~/video_to_notes/process_video.py input.mp4 --language en --model large-v3
    37|
    38|# 直接处理音频文件
    39|python3 ~/video_to_notes/process_video.py audio.mp3 -o ./output -l zh
    40|
    41|# 自定义输出格式
    42|python3 ~/video_to_notes/process_video.py input.mp4 -f md,txt
    43|```
    44|
    45|## B站视频处理流程（通过链接下载）
    46|
    47|当用户发送B站链接时，不能用yt-dlp直接下（B站412反爬）。应采用以下迂回策略：
    48|
    49|### Step 1: 获取B站API数据
    50|
    51|```python
    52|# 获取视频基本信息（cid, title等）
    53|url = f'https://api.bilibili.com/x/web-interface/view?bvid={BV号}'
    54|headers = {
    55|    'User-Agent': 'Mozilla/5.0 ...',
    56|    'Referer': 'https://www.bilibili.com/'
    57|}
    58|```
    59|
    60|从返回的JSON中提取 `cid`, `title`, `duration`。
    61|
    62|### Step 2: 获取视频流地址
    63|
    64|```python
    65|url = f'https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn=80&otype=json&platform=web'
    66|# 关键：需要传buvid3/buvid4等cookie，否则返回412
    67|```
    68|
    69|获取 `data.durl[0].url` 为视频下载地址。
    70|
    71|### Step 3: 下载视频
    72|
    73|```python
    74|# 直接 requests stream 下载到 ~/video_to_notes/input/
    75|r = requests.get(video_url, headers=headers, stream=True)
    76|```
    77|
    78|### Step 4: 用 process_video.py 处理
    79|
    80|```bash
    81|python3 ~/video_to_notes/process_video.py ~/video_to_notes/input/视频名.mp4 -l zh -m base -o ~/video_to_notes/output/
    82|```
    83|
    84|### 完整B站下载脚本模板（Playwright sync API + requests）
    85|
    86|下面是一个完整的、经过验证的 Python 脚本，直接从 B站链接下载视频到 `~/video_to_notes/input/`：
    87|
    88|```python
    89|import requests, json, os, time
    90|from tqdm import tqdm
    91|from playwright.sync_api import sync_playwright
    92|
    93|bvid = "BV1fs5b6UE4z"  # 从B站链接中提取
    94|
    95|# Step 1: 获取视频基本信息
    96|info_url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
    97|headers = {
    98|    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    99|    'Referer': 'https://www.bilibili.com/'
   100|}
   101|info = requests.get(info_url, headers=headers).json()
   102|cid = info['data']['cid']
   103|title = info['data']['title']
   104|print(f"📺 {title} | 时长: {info['data']['duration']}s")
   105|
   106|# Step 2: 用Playwright获取新鲜cookies（防412）
   107|with sync_playwright() as p:
   108|    browser = p.chromium.launch(headless=True)
   109|    ctx = browser.new_context()
   110|    page = ctx.new_page()
   111|    page.goto('https://www.bilibili.com/', wait_until='networkidle')
   112|    cookies = ctx.cookies()
   113|    browser.close()
   114|
   115|cookie_str = '; '.join([f'{c["name"]}={c["value"]}' for c in cookies])
   116|headers['Cookie'] = cookie_str
   117|
   118|# Step 3: 获取视频流地址（qn=80=高清1080P）
   119|play_url = f'https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn=80&otype=json&platform=web'
   120|play = requests.get(play_url, headers=headers).json()
   121|video_url = play['data']['durl'][0]['url']
   122|
   123|# Step 4: 下载（带进度条）
   124|os.makedirs(os.path.expanduser('~/video_to_notes/input'), exist_ok=True)
   125|safe_title = title.replace('/', '_').replace(' ', '')
   126|out_path = os.path.expanduser(f'~/video_to_notes/input/{safe_title}.mp4')
   127|
   128|r = requests.get(video_url, stream=True)
   129|total = int(r.headers.get('content-length', 0))
   130|with open(out_path, 'wb') as f:
   131|    for chunk in tqdm(r.iter_content(1024*1024), total=total//(1024*1024), unit='MB'):
   132|        f.write(chunk)
   133|print(f"✅ 下载完成: {out_path} ({total/1024/1024:.1f} MB)")
   134|```
   135|
   136|⚠️ **关键注意事项：**
   137|- 必须用 `sync_playwright`（同步版），**不要用** `async_playwright`（需要额外asyncio框架）
   138|- 每次下载前获取新鲜cookies，B站cookie会过期
   139|- `qn=80` = 1080P高清，`qn=32` = 480P，`qn=16` = 360P
   140|- 下载后记得 `browser.close()` 避免Playwright进程泄漏
   141|- 约25分钟的视频~156MB，大视频用 `tqdm` 展示进度条
   142|
   143|**简化版（直接用requests，不用Playwright）：**
   144|如果之前已经获取过cookies并保存了，可以直接加载：
   145|```python
   146|import json
   147|with open(os.path.expanduser('~/.hermes/bilibili_cookies.json')) as f:
   148|    cookies = json.load(f)
   149|cookie_str = '; '.join([f'{c["name"]}={c["value"]}' for c in cookies])
   150|```
   151|
   152|## 参数说明
   153|
   154|| 参数 | 默认值 | 说明 |
   155||------|--------|------|
   156|| `--model, -m` | `base` | 模型大小: tiny/base/small/medium/large-v3 |
   157|| `--language, -l` | 自动检测 | 语言代码: zh/ru/en/jp 等 |
   158|| `--output-dir, -o` | `./output` | 输出目录 |
   159|| `--formats, -f` | `md,txt,srt,json` | 输出格式，逗号分隔 |
   160|
   161|## 模型选择建议
   162|
   163|| 模型 | 速度 | 准确率 | 显存需求 |
   164||------|------|--------|---------|
   165|| tiny | ⚡极快 | ⭐⭐ | ~1GB |
   166|| base | 🚀快 | ⭐⭐⭐ | ~1GB |
   167|| small | ⚡中等 | ⭐⭐⭐⭐ | ~2GB |
   168|| medium | 🐢慢 | ⭐⭐⭐⭐⭐ | ~5GB |
   169|| large-v3 | 🐌最慢 | ⭐⭐⭐⭐⭐ | ~10GB |
   170|
   171|**建议：** CPU环境用 `base`（13分钟视频约2-3分钟处理完），中文准确率约95%。
   172|如需更高准确率，装 CUDA 后用 `small` 或 `medium`。
   173|
   174|## 已知问题 & 避坑指南
   175|
   176|### 🔴 yt-dlp 安装失败（SOCKS代理冲突）
   177|该服务器有SOCKS5代理配置，pip install yt-dlp 会报 `Missing dependencies for SOCKS support`。
   178|**解决方法：**
   179|```bash
   180|# 方法1：取消代理再装
   181|unset ALL_PROXY all_proxy http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
   182|pip3 install yt-dlp --index-url http://mirrors.tencentyun.com/pypi/simple --trusted-host mirrors.tencentyun.com
   183|
   184|# 方法2：跳过依赖检查（推荐）
   185|pip3 install yt-dlp --no-build-isolation --no-deps
   186|```
   187|
   188|### 🔴 yt-dlp 下载B站视频失败（HTTP 412）
   189|B站有强反爬，直接yt-dlp下载必定412。
   190|**解决方法：** 走B站API + Python requests 直接下载，不能用yt-dlp。
   191|
   192|### 🔴 HuggingFace 模型下载失败（国内网络）
   193|HuggingFace被墙，faster-whisper初始化时自动下载模型会报 `Network is unreachable`。
   194|**解决方法：** 设置HF国内镜像环境变量：
   195|```bash
   196|export HF_ENDPOINT=https://hf-mirror.com
   197|```
   198|或者在脚本中加入 `os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")`
   199|
   200|### 🔴 Whisper转写准确率问题
   201|base模型的"外部扣顶"（VibeCoding）、"红白鸡小把王"（红白机小霸王）等识别错误是正常现象。
   202|- 中文专有名词/英文混读场景下base模型准确率约90-95%
   203|- 需要更高准确率 → 换 small 或 medium 模型
   204|- 可以配合后续LLM推理来修正专有名词
   205|
   206|### 🔴 微信发送文件失败
   207|微信的文件传输通道有限制，处理后的大文件可能发不过去。
   208|**替代方案：** 直接在聊天框展示笔记内容，或让用户上服务器取文件。
   209|
   210|### 🔴 B站视频时长与下载时间估算
   211|经验数据：
   212|- 25分钟视频（156MB）下载约需 **2-3分钟**（100M带宽）
   213|- Whisper base模型转写25分钟音频约需 **3-5分钟**（CPU）
   214|- 总耗时：下载 + 转写 + LLM整理 ≈ 6-10分钟
   215|- 子任务（delegate_task）处理大文件可能因超时而失败，建议主线程直接处理
   216|
   217|### 🔴 翻译版视频（英文原声中文字幕）
   218|此对话中处理了一个翻译搬运视频（英文原声带中字）：
   219|- Whisper base模型识别为中文（置信度100%）→ 转写结果其实是**英文原文+少量中文**混在一起
   220|- 因为视频是英文原声，Whisper检测到英文后强行输出，导致转写混杂
   221|- **解决方法：**
   222|  - 如果是翻译版/配音版 → `-l zh` 可以
   223|  - 如果是英文原声 + 中文字幕 → 应识别为英文 `-l en`，笔记由字幕提取
   224|  - 更好的做法：用 `youtube-content` skill 获取字幕，或提取中文字幕轨道
   225|
   226|### 🔴 长转写文本的LLM整理策略
   227|Whisper输出的全文可能很长（25分钟视频 ~ 1700行文本），LLM整理策略：
   228|1. 先 `read_file` 分块读取全文（offset/limit分段）
   229|2. 关注核心内容，不要逐句修正Whisper错误
   230|3. 把Whisper误识的专有名词在整理时推理修正
   231|4. 整理成结构化笔记（而不是直接展示时间轴）
   232|5. 笔记存入 Obsidian Vault 后，在聊天框中展示**整理后的摘要版**
   233|
   234|## 笔记存入 Obsidian Vault 规范
   235|
   236|所有视频笔记处理完毕后，**必须**将整理后的笔记存入 Obsidian vault。
   237|
   238|### Vault 路径
   239|
   240|```
   241|OBSIDIAN_VAULT_PATH = ~/obsidian-vault
   242|```
   243|
   244|### 分类规则
   245|
   246|根据视频内容主题，笔记存入对应的子文件夹：
   247|
   248|| 视频类型 | 目标文件夹 | 示例 |
   249||---------|-----------|------|
   250|| AI/技术学习 | `Notes/AI学习/` | 吴恩达课程、机器学习教程 |
   251|| 编程/开发 | `Notes/编程开发/` | Python教程、框架使用 |
   252|| 经济学/商科 | `Notes/经济学/` | 经济分析、金融知识 |
   253|| 英语/语言 | `Notes/语言学习/` | 雅思备考、口语教程 |
   254|| 学术/论文 | `Notes/学术研究/` | 论文解读、研究方法 |
   255|| B站vlog/娱乐 | `Notes/日常杂谈/` | Vlog、生活感悟 |
   256|| 其他/未分类 | `Notes/未分类/` | 暂时归不进去的 |
   257|
   258|如果分类不存在，自动创建对应文件夹。
   259|
   260|### 笔记 Front-matter 规范
   261|
   262|每篇笔记必须包含 YAML front-matter：
   263|
   264|```yaml
   265|---
   266|tags: [AI, 吴恩达, 学习笔记]
   267|created: YYYY-MM-DD
   268|source: "B站 UP主名 → BV号"
   269|rating: ⭐⭐⭐⭐⭐
   270|topics: [核心主题1, 核心主题2]
   271|---
   272|```
   273|
   274|### 笔记结构模板
   275|
   276|```markdown
   277|---
   278|tags: [标签1, 标签2]
   279|created: YYYY-MM-DD
   280|source: "平台 UP主 → BV号/链接"
   281|---
   282|
   283|# 笔记标题
   284|
   285|> 一句话摘要
   286|
   287|---
   288|
   289|## 📌 核心观点
   290|
   291|- 观点1
   292|- 观点2
   293|
   294|## 📂 详细内容
   295|
   296|按逻辑分段
   297|
   298|## 💡 我的思考
   299|
   300|个人的关联和感悟
   301|
   302|## 🔗 关联笔记
   303|
   304|- [[其他笔记名]]
   305|
   306|## 📎 附件
   307|
   308|原始视频链接或其他资源
   309|```
   310|
   311|### Step 4: LLM整理笔记 + 存入Obsidian Vault
   312|
   313|**重要：笔记内容由LLM整理，而不是直接使用Whisper原始输出。** 流程为：
   314|
   315|1. **阅读Whisper输出的全文**（`_notes.md`或`_transcript.txt`）
   316|2. **LLM整理**成规范格式的笔记（带YAML front-matter + 结构化内容）
   317|3. **存入Obsidian Vault**对应分类文件夹
   318|4. 在聊天中向用户展示笔记摘要
   319|
   320|**分类判断指南：**
   321|- 纯技术/AI教程 → `Notes/AI学习/`
   322|- 编程/框架/工具 → `Notes/编程开发/`
   323|- 经济分析、贸易、金融 → `Notes/经济学/`
   324|- 国际政治、地缘政治 → 如果偏分析性质→`Notes/经济学/`，如果偏时事评论→`Notes/日常杂谈/`
   325|- 英语学习 → `Notes/语言学习/`
   326|- Vlog/娱乐/生活 → `Notes/日常杂谈/`
   327|- 学术论文解读 → `Notes/学术研究/`
   328|
   329|**注意：** 不要直接用Process_video.py输出的`_笔记.md`，它只是Whisper的时间轴转写。**必须用LLM重新整理**，并用`write_file`写入Obsidian vault。
   330|
   331|**笔记Front-matter示例：**
   332|```yaml
   333|---
   334|tags: [标签1, 标签2, 标签3]
   335|created: YYYY-MM-DD
   336|source: "B站 UP主名 → BV号"
   337|rating: ⭐⭐⭐⭐⭐
   338|topics: [核心主题1, 核心主题2]
   339|---
   340|```
   341|
   342|## 注意事项
   343|
   344|- 输入支持：mp4, mkv, avi, mov, wmv, flv, webm, m4v, mp3, wav, ogg, flac
   345|- 中文建议用 `--language zh` 指定，避免自动检测错误
   346|- 输出的 `*_笔记.md` 包含全文概要 + 时间线，可直接给用户展示
   347|- **必须**存入 Obsidian vault，不能只留在 `video_to_notes/output/`
   348|