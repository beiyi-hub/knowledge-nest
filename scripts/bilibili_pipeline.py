#!/usr/bin/env python3
"""
B站视频流水线 — 下载 + 转写 一键完成。

绕过 B站 412 反爬：使用 Playwright 获取 cookies → API 取流地址 → requests 下载。

用法：
    python bilibili_pipeline.py BV1xxxxxx                # BV号
    python bilibili_pipeline.py https://bili.../BV...    # 完整链接
    python bilibili_pipeline.py BV1xxxxxx --lang en      # 英文视频
    python bilibili_pipeline.py BV1xxxxxx --model small  # 高精度转写
    python bilibili_pipeline.py BV1xxxxxx --dry-run      # 仅下载不转写
"""
import requests
import json
import os
import sys
import re
import subprocess
from tqdm import tqdm

INPUT_DIR = os.path.expanduser('~/video_to_notes/input')
OUTPUT_DIR = os.path.expanduser('~/video_to_notes/output')


def extract_bvid(text: str) -> str:
    """从链接或文本中提取 BV 号。"""
    m = re.search(r'BV[a-zA-Z0-9]+', text)
    return m.group(0) if m else None


def download_bilibili(bvid: str):
    """下载 B站 视频，返回 (视频路径, 视频信息dict)。"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com/'
    }

    print(f'📺 获取视频信息: {bvid}')
    info = requests.get(
        f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}',
        headers=headers
    ).json()

    if info.get('code') != 0:
        raise Exception(f'API 错误: {info.get("message", info)}')

    data = info['data']
    cid = data['cid']
    title = data['title']
    up = data['owner']['name']
    duration = data['duration']
    print(f'  标题: {title}')
    print(f'  UP主: {up} | 时长: {duration // 60}分{duration % 60}秒')

    # Playwright 获取 cookies
    print('🍪 获取 B站 cookies...')
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto('https://www.bilibili.com/', wait_until='networkidle')
        cookies = ctx.cookies()
        browser.close()

    cookie_str = '; '.join([f'{c["name"]}={c["value"]}' for c in cookies])
    headers['Cookie'] = cookie_str

    # 获取视频流地址
    print('🎬 获取视频流地址...')
    play_url = (
        f'https://api.bilibili.com/x/player/playurl'
        f'?bvid={bvid}&cid={cid}&qn=80&otype=json&platform=web'
    )
    play = requests.get(play_url, headers=headers).json()
    if play.get('code') != 0:
        raise Exception(f'播放 API 错误: {play.get("message")}')

    video_url = play['data']['durl'][0]['url']

    # 下载
    os.makedirs(INPUT_DIR, exist_ok=True)
    safe_title = re.sub(r'[\\/:*?"<>|]', '_', title).strip()[:80]
    out_path = os.path.join(INPUT_DIR, f'{safe_title}.mp4')

    print('⬇️ 下载中...')
    r = requests.get(video_url, stream=True)
    total = int(r.headers.get('content-length', 0))
    with open(out_path, 'wb') as f:
        with tqdm(total=total, unit='B', unit_scale=True, desc=safe_title[:20]) as pbar:
            for chunk in r.iter_content(1024 * 1024):
                f.write(chunk)
                pbar.update(len(chunk))

    file_size = os.path.getsize(out_path)
    print(f'✅ 下载完成: {out_path} ({file_size / 1024 / 1024:.1f} MB)')

    return out_path, {
        'bvid': bvid,
        'title': title,
        'up': up,
        'duration': duration,
        'url': f'https://www.bilibili.com/video/{bvid}',
    }


def transcribe(video_path: str, lang: str = 'zh', model: str = 'base'):
    """使用 faster-whisper 转写视频。"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    env = os.environ.copy()
    env['HF_ENDPOINT'] = 'https://hf-mirror.com'

    cmd = [
        'python3', os.path.expanduser('~/video_to_notes/process_video.py'),
        video_path,
        '-l', lang,
        '-m', model,
        '-o', OUTPUT_DIR,
        '-f', 'md,txt,srt,json',
    ]

    print(f'🎙️ 转写中... (语言={lang}, 模型={model})')
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=600)

    if result.returncode != 0:
        print(f'❌ 转写出错: {result.stderr}')
        return None

    base = os.path.splitext(os.path.basename(video_path))[0]
    note_path = os.path.join(OUTPUT_DIR, f'{base}_笔记.md')
    transcript_path = os.path.join(OUTPUT_DIR, f'{base}_transcript.txt')

    print(f'✅ 转写完成!')
    print(f'  📝 笔记草稿: {note_path}')
    print(f'  📄 全文文本: {transcript_path}')
    return transcript_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'用法: python {os.path.basename(sys.argv[0])} BV号或链接 [选项]')
        sys.exit(1)

    bvid = extract_bvid(sys.argv[1])
    if not bvid:
        print(f'❌ 无法提取 BV 号: {sys.argv[1]}')
        sys.exit(1)

    lang, model = 'zh', 'base'
    dry_run = False
    for i, arg in enumerate(sys.argv):
        if arg == '--lang' and i + 1 < len(sys.argv):
            lang = sys.argv[i + 1]
        elif arg == '--model' and i + 1 < len(sys.argv):
            model = sys.argv[i + 1]
        elif arg == '--dry-run':
            dry_run = True

    try:
        video_path, info = download_bilibili(bvid)
        if dry_run:
            print('🔄 --dry-run 模式，跳过转写')
        else:
            transcript = transcribe(video_path, lang, model)
            print(f'\n💡 现在可以用 AI 整理转写稿为 Obsidian 笔记')
    except Exception as e:
        print(f'❌ 出错: {e}')
        sys.exit(1)
