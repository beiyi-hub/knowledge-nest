"""
采集器基类 — 所有内容源采集器继承此类。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MediaInfo:
    """采集到的媒体信息。"""
    title: str
    source_url: str
    source_platform: str  # "bilibili", "youtube", "local_file", ...
    duration: int  # seconds
    uploader: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    cover_url: str = ""
    # 下载后的本地路径
    local_path: str = ""


class BaseCollector(ABC):
    """采集器抽象基类。

    子类需实现 collect()，返回 MediaInfo。
    """

    @abstractmethod
    def collect(self, target: str, **kwargs) -> MediaInfo:
        """采集内容

        Args:
            target: 目标标识（URL、文件路径、ID 等）
            **kwargs: 额外参数（语言、画质等）

        Returns:
            MediaInfo: 采集到的媒体信息
        """
        ...
