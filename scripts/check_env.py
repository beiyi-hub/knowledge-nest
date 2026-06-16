"""
配置验证工具 — 检查系统环境和依赖是否就绪。
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


CHECK_MARK = "✅"
CROSS_MARK = "❌"
WARN_MARK = "⚠️"


def check_python():
    """Python 版本检查。"""
    v = sys.version_info
    ok = v.major == 3 and v.minor >= 9
    status = CHECK_MARK if ok else CROSS_MARK
    print(f"{status} Python {v.major}.{v.minor}.{v.micro} ({'OK' if ok else '需要 >= 3.9'})")


def check_imports():
    """检查核心依赖。"""
    deps = [
        ("requests", "HTTP 请求"),
        ("tqdm", "进度条"),
    ]
    for mod_name, desc in deps:
        try:
            __import__(mod_name)
            print(f"{CHECK_MARK} {mod_name} — {desc}")
        except ImportError:
            print(f"{WARN_MARK} {mod_name} — {desc} (未安装)")

    # 可选依赖
    opt_deps = [
        ("playwright", "B站 cookies 获取"),
        ("faster_whisper", "语音转文字"),
        ("yaml", "YAML 配置支持"),
    ]
    for mod_name, desc in opt_deps:
        try:
            __import__(mod_name)
            print(f"{CHECK_MARK} {mod_name} — {desc}")
        except ImportError:
            print(f"{WARN_MARK} {mod_name} — {desc} (可选，未安装)")


def check_ffmpeg():
    """ffmpeg 检查。"""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
            version = result.stdout.split("\n")[0] if result.stdout else "?"
            print(f"{CHECK_MARK} ffmpeg — {version}")
        except Exception:
            print(f"{CROSS_MARK} ffmpeg — 安装但无法运行")
    else:
        print(f"{CROSS_MARK} ffmpeg — 未安装 (需要: apt install ffmpeg)")


def check_playwright():
    """Playwright 浏览器检查。"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browsers = p.chromium.launch(headless=True)
            browsers.close()
        print(f"{CHECK_MARK} Playwright Chromium — 可用")
    except ImportError:
        pass  # 已在 check_imports 中提示
    except Exception as e:
        print(f"{WARN_MARK} Playwright Chromium — 安装但不可用: {e}")
        print("   请运行: playwright install chromium")


def check_obsidian_vault():
    """Obsidian vault 检查。"""
    vault = os.path.expanduser("~/obsidian-vault")
    if os.path.isdir(vault):
        note_count = len(list(Path(vault).rglob("*.md")))
        print(f"{CHECK_MARK} Obsidian vault: {vault} ({note_count} 篇笔记)")
    else:
        print(f"{WARN_MARK} Obsidian vault: {vault} (不存在，将自动创建)")


def check_env():
    """环境变量检查。"""
    hf = os.environ.get("HF_ENDPOINT", "")
    if hf:
        print(f"{CHECK_MARK} HF_ENDPOINT={hf}")
    else:
        print(f"{WARN_MARK} HF_ENDPOINT 未设置 (国内用户建议设置)")


def main():
    print("=" * 50)
    print("  Knowledge Nest 环境检测")
    print("=" * 50)
    print()

    print("--- Python ---")
    check_python()

    print()
    print("--- 核心依赖 ---")
    check_imports()

    print()
    print("--- 系统工具 ---")
    check_ffmpeg()
    check_playwright()

    print()
    print("--- 环境 ---")
    check_obsidian_vault()
    check_env()

    print()
    print("=" * 50)
    print("  检测完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
