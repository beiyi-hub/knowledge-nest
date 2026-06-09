---
name: weixin-article-extractor
description: 提取微信公众号文章（mp.weixin.qq.com）的正文内容。绕过微信反爬验证码，通过伪装微信手机客户端UA + urllib请求 + base64解码提取纯文本。
version: 1.0.0
tags:
  - weixin
  - wechat
  - article
  - extractor
  - 微信公众号
  - 反爬
triggers:
  - mp.weixin.qq.com/s/
  - 微信公众号文章
  - weixin article
  - 公众号链接
---

# Weixin Article Extractor — 微信公众号文章提取

## 概述

提取微信公众号文章（`mp.weixin.qq.com/s/...`）的正文内容。微信有强反爬机制（环境异常验证码），但通过伪装为手机微信内置浏览器UA可以绕过。

## 原理

```
用户发来公众号链接
    ↓
urllib 请求（伪装成微信手机浏览器 UA + MicroMessenger 标识）
    ↓
微信服务器识别为"微信客户端内打开" → 放行 ✅
    ↓
返回完整HTML（正文在 og:description 或 base64编码的 ct 变量中）
    ↓
提取 → 解码 → 去HTML标签 → 得到纯文本
```

## 使用时机

当用户发送 `mp.weixin.qq.com/s/` 开头的链接并要求读取内容时使用。

## 脚本位置

无需独立脚本，直接使用内联 Python 代码。

## 步骤

### Step 1: 伪装微信 UA 发起请求

```python
import urllib.request, re, base64

url = "https://mp.weixin.qq.com/s/xxxxxxxxx"
req = urllib.request.Request(url, headers={
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Mobile Safari/537.36 "
        "MicroMessenger/8.0.47 NetType/WIFI Language/zh_CN"
    ),
    "Referer": "https://mp.weixin.qq.com/"
})
resp = urllib.request.urlopen(req, timeout=15)
html = resp.read().decode("utf-8", errors="replace")
```

### Step 2: 提取 OG Meta 元信息

```python
og_title = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html)
og_desc = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html)
og_author = re.search(r'<meta[^>]*property="og:article:author"[^>]*content="([^"]+)"', html)
```

这些元信息**不受反爬影响**，总是可读的。

### Step 3: 提取正文

微信文章正文有两种存储方式，**按优先级尝试**：

#### 方式 A: base64 编码的 ct 变量（最常见）

```python
ct_match = re.search(r'ct\s*=\s*"([A-Za-z0-9+/=]+)"', html)
if ct_match:
    decoded = base64.b64decode(ct_match.group(1)).decode("utf-8", errors="replace")
    text = re.sub(r"<[^>]+>", "\n", decoded)
    text = re.sub(r"\n[ \t]*\n", "\n\n", text).strip()
    text = re.sub(r"[ \t]+", " ", text)
```

#### 方式 B: js_content 直接 HTML（旧版文章）

```python
match = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
if match:
    text = re.sub(r"<[^>]+>", "\n", match.group(1))
    text = re.sub(r"\n[ \t]*\n", "\n\n", text).strip()
    text = re.sub(r"[ \t]+", " ", text)
```

### Step 4: 展示给用户

```python
print(f"📰 标题: {og_title.group(1)}")
print(f"✍️ 公众号: {og_author.group(1)}")
print(f"\n--- 正文 ({len(text)} 字) ---\n")
print(text)
```

## 完整代码模板（一步到位）

```python
import urllib.request, re, base64

def extract_weixin_article(url: str) -> dict:
    """提取微信公众号文章，返回 {title, author, content, desc}"""
    req = urllib.request.Request(url, headers={
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Mobile Safari/537.36 "
            "MicroMessenger/8.0.47 NetType/WIFI Language/zh_CN"
        ),
        "Referer": "https://mp.weixin.qq.com/"
    })
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode("utf-8", errors="replace")

    # OG Meta
    og_title = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html)
    og_desc = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html)
    og_author = re.search(r'<meta[^>]*property="og:article:author"[^>]*content="([^"]+)"', html)

    # 正文提取
    text = ""
    ct_match = re.search(r'ct\s*=\s*"([A-Za-z0-9+/=]+)"', html)
    if ct_match:
        decoded = base64.b64decode(ct_match.group(1)).decode("utf-8", errors="replace")
        text = re.sub(r"<[^>]+>", "\n", decoded)
    else:
        js_match = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
        if js_match:
            text = re.sub(r"<[^>]+>", "\n", js_match.group(1))

    text = re.sub(r"\n[ \t]*\n", "\n\n", text).strip()
    text = re.sub(r"[ \t]+", " ", text)

    return {
        "title": og_title.group(1) if og_title else "",
        "author": og_author.group(1) if og_author else "",
        "description": og_desc.group(1) if og_desc else "",
        "content": text,
        "url": url
    }

# 使用
result = extract_weixin_article("https://mp.weixin.qq.com/s/xxxxx")
print(f"📰 {result['title']}")
print(f"✍️ {result['author']}")
print(f"\n--- ({len(result['content'])} 字) ---\n{result['content']}")
```

## 注意事项 / 踩坑记录

### ⚠️ 不要用 requests 库

服务器配置了 SOCKS5 代理，`requests` 会自动走代理并报 `Missing dependencies for SOCKS support`。

**✅ 改用 `urllib`（Python 标准库）**，不走 SOCKS 代理。

```python
# ✅ 正确
import urllib.request
resp = urllib.request.urlopen(req)

# ❌ 错误 — 报 SOCKS 错误
import requests
r = requests.get(url, headers=headers)
```

### ⚠️ SOCKS 代理环境变量

如果非要用 requests，先清除代理环境变量：
```bash
unset ALL_PROXY http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
```

### ⚠️ UA 是关键

- 必须有 `MicroMessenger/版本号` 标识
- 最好是手机端 UA（`Android` + `Mobile Safari`）
- 没有 `MicroMessenger` 微信会返回验证码页面
- 实测 `MicroMessenger/8.0.47` 有效

### ⚠️ 正文提取方式不固定

微信会不定期改版，正文存储方式可能变化：
- 当前主流：`ct` 变量中的 base64 编码
- 旧版：`js_content` div 内直接 HTML
- 未来可能：更复杂的加密/编码方式

如果抓取失败，检查 HTML 中是否还能找到 `ct` 或 `js_content`。

### ⚠️ 反爬可能升级

这个方法基于 **UA 伪装**，微信随时可能升级检测机制（比如检测 TLS 指纹、JavaScript 执行能力等），届时此方法可能失效。

### ⚠️ 图片防盗链

提取的正文只包含**纯文本**。文章中的图片有微信防盗链，直接访问会 403。

### ⚠️ 频率限制

不要频繁抓取同一公众号的文章，可能触发账号级别风控。

## 常见问题

### Q: 返回"环境异常"页面
A: UA 伪装失败。检查 `MicroMessenger` 版本号是否最新，或者微信升级了反爬手段。

### Q: 正文为空
A: 尝试两种提取方式（ct 和 js_content）。如果都为空，可能是文章格式特殊（如纯图片文章、视频文章）。

### Q: 请求超时
A: 增加 timeout（建议 15-20s），或检查网络是否正常。
