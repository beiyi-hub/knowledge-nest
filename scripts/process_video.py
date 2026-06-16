#!/usr/bin/env python3
"""
视频/音频转文字+笔记 🎬→📝
基于 faster-whisper，支持多种输出格式。

用法:
  python process_video.py <视频/音频文件路径> [选项]

例子:
  python process_video.py ~/video.mp3
  python process_video.py lecture.mp4 --model base --language zh
  python process_video.py meeting.mkv --model small --output-dir ~/notes
  python process_video.py audio.mp3 -f md,txt,srt,json
"""

import argparse
import os
import sys
import subprocess
import json
from datetime import timedelta
from pathlib import Path

# ─── faster-whisper ───
from faster_whisper import WhisperModel


def format_timestamp(seconds: float) -> str:
    """把秒数转成 HH:MM:SS,mmm 格式"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def extract_audio(video_path: str, output_audio: str) -> str:
    """用 ffmpeg 提取音频，返回音频文件路径"""
    print(f"🎵 正在提取音频: {video_path} → {output_audio}")
    result = subprocess.run(
        ["ffmpeg", "-i", video_path,
         "-vn",                     # 不要视频流
         "-acodec", "mp3",          # MP3编码
         "-ab", "128k",             # 128kbps 足够语音
         "-ar", "16000",            # 16kHz 适合Whisper
         "-ac", "1",                # 单声道
         "-y",                      # 覆盖已有文件
         output_audio,
         "-loglevel", "error"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"❌ ffmpeg 错误: {result.stderr}")
        sys.exit(1)
    print(f"✅ 音频提取完成: {output_audio}")
    return output_audio


def transcribe_audio(audio_path: str, model_size: str, language: str = None):
    """用 faster-whisper 转写音频，返回带时间戳的文本段"""
    print(f"🎙️ 正在转写音频... (模型: {model_size}, 语言: {language or '自动检测'})")

    # 设置HF镜像（国内网络环境）
    hf_endpoint = os.environ.get("HF_ENDPOINT", "")
    if hf_endpoint:
        os.environ.setdefault("HF_ENDPOINT", hf_endpoint)
    else:
        os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

    # 判断设备
    device = "cuda" if os.path.exists("/usr/bin/nvidia-smi") else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    print(f"💻 使用设备: {device}, 精度: {compute_type}")

    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    kwargs = {"audio": audio_path}
    if language:
        kwargs["language"] = language

    segments, info = model.transcribe(**kwargs)

    detected_lang = info.language
    detected_prob = info.language_probability
    print(f"🌐 检测到语言: {detected_lang} (置信度: {detected_prob:.2%})")

    segments_list = []
    for seg in segments:
        segments_list.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        })

    return segments_list, detected_lang


def save_as_text(segments, output_path: str):
    """保存为纯文本（带时间戳）"""
    lines = []
    for seg in segments:
        start_ts = format_timestamp(seg["start"])
        lines.append(f"[{start_ts}] {seg['text']}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"📄 文本（带时间戳）保存: {output_path}")


def save_as_srt(segments, output_path: str):
    """保存为 SRT 字幕格式"""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start_ts = format_timestamp(seg["start"])
            end_ts = format_timestamp(seg["end"])
            f.write(f"{i}\n")
            f.write(f"{start_ts.replace(',', ' --> ')} {end_ts}\n")
            f.write(f"{seg['text']}\n\n")
    print(f"📑 SRT字幕保存: {output_path}")


def save_as_markdown(segments, output_path: str, title: str = "视频笔记"):
    """保存为Markdown笔记格式"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")

        full_text = " ".join(seg["text"] for seg in segments)
        f.write("## 📝 全文概要\n\n")
        f.write(f"{full_text}\n\n---\n\n## ⏱️ 详细时间线\n\n")

        for seg in segments:
            start_ts = format_timestamp(seg["start"]).replace(",", ".")
            f.write(f"**[{start_ts}]** {seg['text']}\n\n")

    print(f"📝 Markdown笔记保存: {output_path}")


def save_as_json(segments, output_path: str, language: str):
    """保存为 JSON 格式"""
    data = {
        "language": language,
        "total_segments": len(segments),
        "duration_seconds": segments[-1]["end"] if segments else 0,
        "segments": segments,
        "full_text": " ".join(seg["text"] for seg in segments),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"📊 JSON保存: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="视频/音频转文字+笔记")
    parser.add_argument("input", help="输入文件（视频或音频，支持 mp4/mkv/avi/mov/mp3/wav 等）")
    parser.add_argument("--output-dir", "-o", default="./output", help="输出目录 (默认: ./output)")
    parser.add_argument("--model", "-m", default="base",
                        choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="Whisper模型大小 (默认: base)")
    parser.add_argument("--language", "-l", default=None,
                        help="语言代码，如 zh/ru/en (默认: 自动检测)")
    parser.add_argument("--formats", "-f", default="md,txt,srt",
                        help="输出格式，逗号分隔 (默认: md,txt,srt)")
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    if not os.path.exists(input_path):
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)

    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    base_name = Path(input_path).stem
    formats = [f.strip() for f in args.formats.split(",")]

    # 1. 提取音频（如果输入是视频文件）
    audio_path = input_path
    video_exts = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"}
    if Path(input_path).suffix.lower() in video_exts:
        audio_path = os.path.join(output_dir, f"{base_name}_audio.mp3")
        audio_path = extract_audio(input_path, audio_path)
    else:
        print(f"🎵 输入是音频文件，跳过提取步骤")

    # 2. 转写音频
    segments, detected_lang = transcribe_audio(audio_path, args.model, args.language)

    if not segments:
        print("❌ 没有识别到任何文本内容")
        sys.exit(1)

    # 3. 保存各种格式
    print(f"\n📦 共识别 {len(segments)} 个片段\n")

    if "txt" in formats:
        save_as_text(segments, os.path.join(output_dir, f"{base_name}_transcript.txt"))
    if "srt" in formats:
        save_as_srt(segments, os.path.join(output_dir, f"{base_name}_subtitle.srt"))
    if "md" in formats:
        save_as_markdown(segments, os.path.join(output_dir, f"{base_name}_笔记.md"))
    if "json" in formats:
        save_as_json(segments, os.path.join(output_dir, f"{base_name}_data.json"), detected_lang)

    print(f"\n✅ 全部完成！输出目录: {output_dir}")
    print(f"   📝 Markdown笔记: {base_name}_笔记.md")
    print(f"   📄 文本: {base_name}_transcript.txt")
    print(f"   📑 字幕: {base_name}_subtitle.srt")


if __name__ == "__main__":
    main()
