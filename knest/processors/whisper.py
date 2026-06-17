"""
Whisper 语音转文字处理器 — 跨平台兼容。

使用 faster-whisper 将视频/音频转为带时间戳的文字。
支持多语言（中文、英文、俄语等），自动选择模型大小。
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from knest.processors import BaseProcessor, ProcessResult
from knest.config import Config, IS_WINDOWS


class WhisperProcessor(BaseProcessor):
    """faster-whisper 语音转文字处理器，跨平台。"""

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
            ProcessResult
        """
        language = kwargs.get("language", self.config.whisper_language)
        model = kwargs.get("model", self.config.whisper_model)
        output_dir = kwargs.get("output_dir") or self.config.output_dir
        formats = kwargs.get("formats", "md,txt,srt,json")

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # 设置 HF 国内镜像
        env = os.environ.copy()
        env["HF_ENDPOINT"] = self.config.hf_endpoint

        # 检测输入类型：视频需先提取音频
        audio_path = Path(input_path)
        is_video = self._is_video_file(input_path)
        if is_video:
            print(f"[Whisper] 从视频提取音频...")
            audio_path = out_dir / f"{audio_path.stem}_audio.mp3"
            if not audio_path.exists():
                result = subprocess.run(
                    self._ffmpeg_cmd(input_path, str(audio_path)),
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
        cmd = self._build_command(str(audio_path), language, model, str(out_dir), formats)
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=1800)
        except FileNotFoundError:
            return ProcessResult(
                success=False,
                error="faster-whisper 未安装或未找到转写脚本",
            )

        if result.returncode != 0:
            return ProcessResult(
                success=False,
                error=f"转写出错: {result.stderr}",
            )

        # 收集输出文件
        base = Path(input_path).stem
        output_paths = []
        text_content = ""
        for fmt in formats.split(","):
            fmt = fmt.strip()
            if fmt == "md":
                p = out_dir / f"{base}_笔记.md"
            elif fmt == "txt":
                p = out_dir / f"{base}_transcript.txt"
            elif fmt == "srt":
                p = out_dir / f"{base}_subtitle.srt"
            elif fmt == "json":
                p = out_dir / f"{base}_transcript.json"
            else:
                continue
            if p.exists():
                output_paths.append(str(p))
                if fmt == "txt":
                    text_content = p.read_text(encoding="utf-8")

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
        return Path(path).suffix.lower() in video_exts

    def _ffmpeg_cmd(self, input_path: str, output_path: str) -> list[str]:
        """跨平台 ffmpeg 命令。"""
        ffmpeg_bin = "ffmpeg"
        if IS_WINDOWS:
            custom = self.config.get("ffmpeg_path")
            if custom:
                ffmpeg_bin = custom
            elif not self._which("ffmpeg"):
                # 尝试 exe
                ffmpeg_bin = "ffmpeg.exe"
        return [ffmpeg_bin, "-i", input_path, "-vn", "-acodec", "libmp3lame",
                "-q:a", "2", output_path, "-y"]

    def _build_command(self, audio_path: str, language: str, model: str,
                       output_dir: str, formats: str) -> list[str]:
        """构建转写命令 — 跨平台使用正确 Python 可执行文件。"""
        # 尝试项目内脚本
        script_dir = Path(__file__).resolve().parent.parent.parent
        script_candidates = [
            script_dir / "scripts" / "process_video.py",
            script_dir / "scripts" / "whisper_transcribe.py",
        ]

        script_path = None
        for candidate in script_candidates:
            if candidate.exists():
                script_path = str(candidate)
                break

        if not script_path:
            raise FileNotFoundError(
                "未找到转写脚本。请提供 process_video.py 或安装 whisper-transcribe。\n"
                f"查找路径: {script_candidates}"
            )

        # Windows 上用 python，Linux/macOS 上用 python3
        python_exe = "python" if IS_WINDOWS else "python3"

        cmd = [
            python_exe,
            script_path,
            audio_path,
            "-l", language,
            "-m", model,
            "-o", output_dir,
            "-f", formats,
        ]
        return cmd

    @staticmethod
    def _which(name: str) -> bool:
        """检查可执行文件在 PATH 中是否存在。"""
        try:
            subprocess.run([name, "--version"], capture_output=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
