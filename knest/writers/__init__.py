"""
写入器基类 — 将处理结果写入目标格式/平台。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class WriteResult:
    """写入结果。"""
    success: bool
    path: str = ""
    error: str = ""


class BaseWriter(ABC):
    """写入器抽象基类。"""

    @abstractmethod
    def write(self, content: str, title: str, **kwargs) -> WriteResult:
        ...
