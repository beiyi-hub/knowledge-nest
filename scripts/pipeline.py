#!/usr/bin/env python3
"""
Pipeline — 一键全流程入口。

用法：
    python pipeline.py bilibili BV1xxxxxx          # B站视频
    python pipeline.py xmind 文件.xmind             # XMind 解析
    python pipeline.py xmind 文件.xmind --obsidian  # XMind → Obsidian
    python pipeline.py xmind 文件.xmind --markdown  # XMind → Markdown
"""
import sys
import os
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARSER_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'parser')


def main():
    if len(sys.argv) < 3:
        print("用法:")
        print("  python pipeline.py bilibili BV号 [选项]")
        print("  python pipeline.py xmind 文件.xmind [--obsidian|--markdown]")
        sys.exit(1)

    mode = sys.argv[1]
    target = sys.argv[2]
    extra = sys.argv[3:]

    if mode == 'bilibili':
        script = os.path.join(SCRIPT_DIR, 'bilibili_pipeline.py')
        cmd = ['python3', script, target] + extra

    elif mode == 'xmind':
        if '--obsidian' in extra:
            script = os.path.join(PARSER_DIR, 'xmind_to_obsidian.py')
            cmd = ['python3', script, target]
            i = 0
            while i < len(extra):
                if extra[i] == '--dir' and i + 1 < len(extra):
                    cmd += ['--dir', extra[i+1]]
                    i += 2
                elif extra[i] in ('--summary', '--moc-only'):
                    cmd.append(extra[i])
                    i += 1
                elif extra[i] == '--obsidian':
                    i += 1
                else:
                    i += 1
        elif '--markdown' in extra:
            cmd = ['python3', os.path.join(PARSER_DIR, 'xmind_parser.py'), target, '--markdown']
        else:
            cmd = ['python3', os.path.join(PARSER_DIR, 'xmind_parser.py'), target]
    else:
        print(f"❌ 未知模式: {mode}")
        sys.exit(1)

    print('$ ' + ' '.join(cmd) + '\n')
    sys.exit(subprocess.run(cmd).returncode)


if __name__ == '__main__':
    main()
