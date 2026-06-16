"""
B站 (Bilibili) 视频采集器。

绕过 412 反爬策略：
1. B站公开 API → 获取视频信息
2. Playwright 获取新鲜 cookies
3. 播放 API + cookies → 视频流地址
4. requests stream → 下载到本地

使用方式：
    collector = BilibiliCollector()
    info = collector.collect("BV1xxxxxx")
    # info.local_path 即为下载后的文件路径
"""
import os
import re
import sys
import json
import requests
from pathlib import Path
from typing import Optional
from tqdm import tqdm

from knest.collectors import BaseCollector, MediaInfo
from knest.config import Config


class BilibiliCollector(BaseCollector):
    """B站视频采集器。"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.bilibili.com/",
        }

    @staticmethod
    def extract_bvid(text: str) -> Optional[str]:
        """从链接或文本中提取 BV 号。"""
        m = re.search(r"BV[a-zA-Z0-9]+", text)
        return m.group(0) if m else None

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """清理文件名中的非法字符。"""
        return re.sub(r'[\\/:*?"<>|]', "_", name).strip()[:80]

    def collect(self, target: str, **kwargs) -> MediaInfo:
        """下载 B站视频。

        Args:
            target: BV号 或 B站完整链接
            **kwargs:
                quality: 画质 (16=360P, 32=480P, 64=720P, 80=1080P)
                output_dir: 下载目录（默认 use config.cache_dir）

        Returns:
            MediaInfo: 包含标题、UP主、时长、本地路径等信息
        """
        bvid = self.extract_bvid(target)
        if not bvid:
            raise ValueError(f"无法提取 BV 号: {target}")

        quality = kwargs.get("quality", self.config.bilibili_quality)
        output_dir = kwargs.get("output_dir") or self.config.cache_dir
        os.makedirs(output_dir, exist_ok=True)

        # ── Step 1: 获取视频信息 ──
        print(f"[B站] 获取视频信息: {bvid}")
        info_resp = requests.get(
            f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}",
            headers=self._headers,
            timeout=15,
        )
        info_data = info_resp.json()
        if info_data.get("code") != 0:
            raise RuntimeError(f"API 错误: {info_data.get('message', info_data)}")

        data = info_data["data"]
        cid = data["cid"]
        title = data["title"]
        uploader = data["owner"]["name"]
        duration = data["duration"]
        print(f"  📺 {title}")
        print(f"  👤 {uploader} | ⏱ {duration // 60}分{duration % 60}秒")

        # ── Step 2: 获取 cookies（绕过 412） ──
        cookies = self._get_cookies()
        cookie_str = "; ".join([f'{c["name"]}={c["value"]}' for c in cookies])

        # ── Step 3: 获取视频流地址 ──
        print("[B站] 获取视频流地址...")
        play_url = (
            f"https://api.bilibili.com/x/player/playurl"
            f"?bvid={bvid}&cid={cid}&qn={quality}&otype=json&platform=web"
        )
        play_resp = requests.get(
            play_url,
            headers={**self._headers, "Cookie": cookie_str},
            timeout=15,
        )
        play_data = play_resp.json()
        if play_data.get("code") != 0:
            raise RuntimeError(f"播放 API 错误: {play_data.get('message')}")

        video_url = play_data["data"]["durl"][0]["url"]

        # ── Step 4: 下载视频 ──
        safe_title = self.sanitize_filename(title)
        out_path = os.path.join(output_dir, f"{safe_title}.mp4")

        print("[B站] 下载中...")
        r = requests.get(video_url, headers=self._headers, stream=True, timeout=30)
        total = int(r.headers.get("content-length", 0))
        with open(out_path, "wb") as f:
            with tqdm(total=total, unit="B", unit_scale=True, desc=safe_title[:20]) as pbar:
                for chunk in r.iter_content(1024 * 1024):
                    f.write(chunk)
                    pbar.update(len(chunk))

        file_size = os.path.getsize(out_path)
        print(f"  ✅ 下载完成: {file_size / 1024 / 1024:.1f} MB")

        return MediaInfo(
            title=title,
            source_url=f"https://www.bilibili.com/video/{bvid}",
            source_platform="bilibili",
            duration=duration,
            uploader=uploader,
            local_path=out_path,
        )

    def _get_cookies(self) -> list[dict]:
        """获取 B站 cookies。

        优先从缓存文件加载，失效则用 Playwright 重新获取。
        """
        cookie_file = self.config.bilibili_cookie_file

        # 尝试从缓存加载
        if os.path.exists(cookie_file):
            with open(cookie_file, encoding="utf-8") as f:
                return json.load(f)

        # Playwright 获取新鲜 cookies
        return self._fresh_cookies(cookie_file)

    def _fresh_cookies(self, save_path: str) -> list[dict]:
        """用 Playwright 获取新鲜 cookies。"""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError(
                "需要安装 Playwright: pip install playwright && playwright install chromium"
            )

        print("[B站] 🍪 获取新鲜 cookies (Playwright)...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context()
            page = ctx.new_page()
            page.goto("https://www.bilibili.com/", wait_until="networkidle")
            cookies = ctx.cookies()
            browser.close()

        # 缓存 cookies
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f)

        return cookies
