# B站视频处理指南

## 反爬策略

B站对自动化工具（如 yt-dlp）实施了 412 反爬策略。**不能直接用 yt-dlp 下载。** 正确的做法：

### 方案：API + Playwright Cookies + Requests

```
1. B站公开 API → 获取视频信息（标题、cid、时长）
2. Playwright → 打开 bilibili.com 获取新鲜 cookies
3. B站播放 API + cookies → 获取视频流地址（m3u8/mp4）
4. requests stream → 下载到本地
5. faster-whisper → 转写为文字
6. LLM → 整理为结构化笔记
```

### 关键参数

- `qn=80` — 1080P 高清
- `qn=64` — 720P
- `qn=32` — 480P
- `qn=16` — 360P

### 注意事项

1. **Cookies 会过期** — 每次下载前必须重新获取
2. **Playwright headless 模式**可以正常工作
3. **Referer 必须设置**为 `https://www.bilibili.com/`
4. 视频大小参考：25 分钟 ≈ 156MB（1080P）
