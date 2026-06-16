"""
Whisper 语音转文字处理器。

使用 faster-whisper 将视频/音频转为带时间戳的文字。
支持多语言（中文、英文、俄语等），自动选择模型大小。
"""
import os
import subprocess
from typing import Optional

from knest.processors import BaseProcessor, ProcessResult
from knest.config import Config
import sys


class WhisperProcessor(BaseProcessor):
    """faster-whisper 语音转文字处理器。"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

    def process(self, input_path: str, **kwargs) -> ProcessResult:
        """转写视频/音频文件为文字。

        Args:
            input_path: 视频或音频文件路径
            **kwargs:
                language: 语言代码 (zh/en/ru/ja, 默认 config.whisper_language)
                model: 模型大小 (tiny/base/small/medium/large-v3, 默认 config.whisper_model)
                output_dir: 输出目录（默认 config.output_dir）
                formats: 输出格式 (md,txt,srt,json, 默认 "md,txt,srt,json")

        Returns:
            ProcessResult: 包含转写文本和输出文件路径
        """
        language = kwargs.get("language", self.config.whisper_language)
        model = kwargs.get("model", self.config.whisper_model)
        output_dir = kwargs.get("output_dir") or self.config.output_dir
        formats = kwargs.get("formats", "md,txt,srt,json")

        os.makedirs(output_dir, exist_ok=True)

        # 设置 HF 国内镜像
        env = os.environ.copy()
        env["HF_ENDPOINT"] = self.config.hf_endpoint

        # 检测输入类型：视频需先提取音频
        audio_path = input_path
        is_video = self._is_video_file(input_path)
        if is_video:
            print(f"[Whisper] 从视频提取音频...")
            audio_path = os.path.join(
                output_dir,
                os.path.splitext(os.path.basename(input_path))[0] + "_audio.mp3",
            )
            if not os.path.exists(audio_path):
                result = subprocess.run(
                    ["ffmpeg", "-i", input_path, "-vn", "-acodec", "libmp3lame",
                     "-q:a", "2", audio_path, "-y"],
                    capture_output=True, text=True, timeout=600,
                )
                if result.returncode != 0:
                    return ProcessResult(
                        success=False,
                        error=f"音频提取失败: {result.stderr}",
                    )
                print(f"  ✅ 音频提取完成: {audio_path}")

        # 调用 faster-whisper
        print(f"[Whisper] 转写中... (语言={language}, 模型={model})")
        cmd = self._build_command(audio_path, language, model, output_dir, formats)
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=1800)
        except FileNotFoundError:
            return ProcessResult(
                success=False,
                error="faster-whisper 未安装或未找到 process_video.py",
            )

        if result.returncode != 0:
            return ProcessResult(
                success=False,
                error=f"转写出错: {result.stderr}",
            )

        # 收集输出文件
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_paths = []
        text_content = ""
        for fmt in formats.split(","):
            fmt = fmt.strip()
            if fmt == "md":
                p = os.path.join(output_dir, f"{base}_笔记.md")
            elif fmt == "txt":
                p = os.path.join(output_dir, f"{base}_transcript.txt")
            elif fmt == "srt":
                p = os.path.join(output_dir, f"{base}_subtitle.srt")
            elif fmt == "json":
                p = os.path.join(output_dir, f"{base}_transcript.json")
            else:
                continue
            if os.path.exists(p):
                output_paths.append(p)
                if fmt == "txt":
                    with open(p, encoding="utf-8") as f:
                        text_content = f.read()

        print(f"  ✅ 转写完成!")
        for p in output_paths:
            print(f"     📄 {p}")

        return ProcessResult(
            success=True,
            output_paths=output_paths,
            text_content=text_content,
        )

    def _is_video_file(self, path: str) -> bool:
        """判断是否为视频文件（vs 纯音频）。"""
        video_exts = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"}
        ext = os.path.splitext(path)[1].lower()
        return ext in video_exts

    def _build_command(self, audio_path: str, language: str, model: str,
                       output_dir: str, formats: str) -> list[str]:
        """构建 process_video.py 命令。

        优先使用项目自带的 process_video.py，
        如果没有则尝试系统安装的版本。
        """
        # 尝试项目内脚本
        script_candidates = [
            os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "process_video.py"),
            os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "whisper_transcribe.py"),
        ]

        script_path = None
        for candidate in script_candidates:
            abs_path = os.path.abspath(candidate)
            if os.path.exists(abs_path):
                script_path = abs_path
                break

        if not script_path:
            # 给用户清晰的提示信息
            raise FileNotFoundError(
                "未找到转写脚本。请提供 process_video.py 或安装 whisper-transcribe。\n"
                f"查找路径: {script_candidates}"
            )

        cmd = [
            "python3",
            script_path,
            audio_path,
            "-l", language,
            "-m", model,
            "-o", output_dir,
            "-f", formats,
        ]
        return cmd
