"""
处理器基类 — 内容处理器（转写、LLM 整理等）。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProcessResult:
    """处理结果。"""
    success: bool
    output_paths: list[str] = field(default_factory=list)
    text_content: str = ""
    error: str = ""


class BaseProcessor(ABC):
    """处理器抽象基类。"""

    @abstractmethod
    def process(self, input_path: str, **kwargs) -> ProcessResult:
        ...
