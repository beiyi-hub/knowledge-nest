"""
Knowledge Nest CLI — 统一命令行入口。

用法：
    knest bilibili BV1xxxxxx            # 下载 B站视频
    knest bilibili BV1xxxxxx --quality 32  # 480P
    knest transcribe input.mp4           # 转写视频/音频
    knest xmind 文件.xmind               # 解析思维导图
    knest xmind 文件.xmind --obsidian    # 导入 Obsidian
    knest config                         # 查看当前配置
"""

import os
import sys
import json
import argparse

from knest.config import Config, default_config
from knest.collectors.bilibili import BilibiliCollector
from knest.processors.whisper import WhisperProcessor
from knest.writers.obsidian import ObsidianWriter, guess_category
from knest.parsers.xmind_parser import parse_xmind, to_tree, to_markdown
from knest.parsers.xmind_to_obsidian import xmind_to_obsidian


def cmd_bilibili(args):
    """B站视频下载 + 转写。"""
    config = Config(args.config)
    collector = BilibiliCollector(config)

    info = collector.collect(
        args.target,
        quality=args.quality or config.bilibili_quality,
    )

    print(f"\n📺 {info.title}")
    print(f"   UP主: {info.uploader}")
    print(f"   时长: {info.duration // 60}分{info.duration % 60}秒")
    print(f"   文件: {info.local_path}")

    if not args.dry_run:
        # 自动转写
        processor = WhisperProcessor(config)
        result = processor.process(
            info.local_path,
            language=args.language or config.whisper_language,
            model=args.model or config.whisper_model,
        )
        if result.success:
            print(f"\n✅ 转写完成! 输出文件:")
            for p in result.output_paths:
                print(f"   📄 {p}")

    return info


def cmd_transcribe(args):
    """转写本地视频/音频文件。"""
    config = Config(args.config)
    processor = WhisperProcessor(config)

    result = processor.process(
        args.input,
        language=args.language or config.whisper_language,
        model=args.model or config.whisper_model,
    )

    if result.success:
        print(f"✅ 转写完成! 输出文件:")
        for p in result.output_paths:
            print(f"   📄 {p}")
    else:
        print(f"❌ 转写失败: {result.error}")
        sys.exit(1)

    return result


def cmd_xmind(args):
    """解析 / 导入 XMind 思维导图。"""
    config = Config(args.config)

    if args.obsidian:
        files = xmind_to_obsidian(
            args.target,
            config=config,
            subdir=args.dir or "",
            summary=args.summary,
            moc_only=args.moc_only,
        )
        print(f"✅ 生成 {len(files)} 个文件:")
        for f in files:
            print(f"   📄 {f}")
    elif args.markdown:
        sheets = parse_xmind(args.target)
        print(to_markdown(sheets))
    elif args.text:
        from knest.parsers.xmind_parser import to_text
        sheets = parse_xmind(args.target)
        print(to_text(sheets))
    else:
        sheets = parse_xmind(args.target)
        print(to_tree(sheets))


def cmd_config(args):
    """查看当前配置。"""
    config = Config(args.config)
    print("=== Knowledge Nest 配置 ===")
    print(json.dumps(config.to_dict(), ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Knowledge Nest — 从零散内容到结构化知识库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  knest bilibili BV1xxxxxx
  knest bilibili BV1xxxxxx --quality 32 --dry-run
  knest transcribe video.mp4 -l en -m small
  knest xmind 文件.xmind
  knest xmind 文件.xmind --obsidian --summary
  knest config
        """,
    )
    parser.add_argument("--config", "-c", help="配置文件路径（YAML）")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # bilibili
    bili = subparsers.add_parser("bilibili", help="下载B站视频")
    bili.add_argument("target", help="BV号或B站链接")
    bili.add_argument("--quality", "-q", type=int, choices=[16, 32, 64, 80], help="画质")
    bili.add_argument("--language", "-l", help="转写语言")
    bili.add_argument("--model", "-m", help="Whisper模型大小")
    bili.add_argument("--dry-run", action="store_true", help="仅下载，不转写")

    # transcribe
    tr = subparsers.add_parser("transcribe", help="转写视频/音频文件")
    tr.add_argument("input", help="输入文件路径")
    tr.add_argument("--language", "-l", help="语言代码 (zh/en/ru)")
    tr.add_argument("--model", "-m", help="模型大小 (tiny/base/small/medium/large-v3)")

    # xmind
    xm = subparsers.add_parser("xmind", help="解析/导入XMind思维导图")
    xm.add_argument("target", help=".xmind 文件路径")
    xm.add_argument("--obsidian", action="store_true", help="导入到 Obsidian")
    xm.add_argument("--markdown", action="store_true", help="输出 Markdown")
    xm.add_argument("--text", action="store_true", help="输出缩进文本")
    xm.add_argument("--dir", help="Obsidian 子目录 (搭配 --obsidian)")
    xm.add_argument("--summary", action="store_true", help="生成汇总页 (搭配 --obsidian)")
    xm.add_argument("--moc-only", action="store_true", help="只生成MOC索引 (搭配 --obsidian)")

    # config
    subparsers.add_parser("config", help="查看当前配置")

    args = parser.parse_args()

    if args.command == "bilibili":
        cmd_bilibili(args)
    elif args.command == "transcribe":
        cmd_transcribe(args)
    elif args.command == "xmind":
        cmd_xmind(args)
    elif args.command == "config":
        cmd_config(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
