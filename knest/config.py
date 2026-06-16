"""
统一配置管理 — 替代所有硬编码路径。

配置优先级：CLI 参数 > 环境变量 > 配置文件 > 默认值
"""
import os
from pathlib import Path
from typing import Optional


# 默认配置
_DEFAULTS = {
    # 基础目录
    "cache_dir": "~/.knest/cache",
    "output_dir": "~/.knest/output",

    # Obsidian 集成
    "obsidian_vault": "~/obsidian-vault",
    "obsidian_notes_dir": "Notes",

    # B站下载
    "bilibili_quality": 80,  # 80=1080P, 64=720P, 32=480P
    "bilibili_cookie_file": "~/.knest/bilibili_cookies.json",

    # Whisper 转写
    "whisper_model": "base",
    "whisper_language": "zh",
    "hf_endpoint": "https://hf-mirror.com",

    # LLM
    "llm_provider": "",
    "llm_api_key": "",
    "llm_model": "",
}


class Config:
    """配置管理器，支持配置文件、环境变量、CLI 参数三层覆盖。"""

    def __init__(self, config_file: Optional[str] = None):
        self._data = dict(_DEFAULTS)
        if config_file and os.path.exists(config_file):
            self._load_yaml(config_file)
        self._apply_env_overrides()

    def _load_yaml(self, path: str):
        """从 YAML 配置文件加载（如果 pyyaml 不可用则跳过）。"""
        try:
            import yaml
            with open(path, encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f) or {}
                self._data.update(yaml_data)
        except ImportError:
            pass  # 没有 pyyaml 就全用默认值

    def _apply_env_overrides(self):
        """环境变量覆盖。"""
        env_map = {
            "KNEST_CACHE_DIR": "cache_dir",
            "KNEST_OUTPUT_DIR": "output_dir",
            "KNEST_OBSIDIAN_VAULT": "obsidian_vault",
            "KNEST_HF_ENDPOINT": "hf_endpoint",
            "KNEST_WHISPER_MODEL": "whisper_model",
            "KNEST_WHISPER_LANG": "whisper_language",
            "KNEST_BILI_QUALITY": "bilibili_quality",
            "HF_ENDPOINT": "hf_endpoint",  # 兼容原环境变量
        }
        for env_key, config_key in env_map.items():
            val = os.environ.get(env_key)
            if val is not None:
                # 数值类型转换
                if config_key in ("bilibili_quality",):
                    try:
                        val = int(val)
                    except ValueError:
                        pass
                self._data[config_key] = val

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def __getattr__(self, key: str):
        if key in self._data:
            val = self._data[key]
            # 自动展开 ~ 路径
            if isinstance(val, str) and ("~" in val or val.startswith("/~")):
                val = os.path.expanduser(val)
            return val
        raise AttributeError(f"Config has no key '{key}'")

    @property
    def cache_dir(self) -> str:
        return os.path.expanduser(self._data["cache_dir"])

    @property
    def output_dir(self) -> str:
        return os.path.expanduser(self._data["output_dir"])

    @property
    def obsidian_vault(self) -> str:
        return os.path.expanduser(self._data["obsidian_vault"])

    @property
    def obsidian_notes_dir(self) -> str:
        return self._data["obsidian_notes_dir"]

    @property
    def bilibili_cookie_file(self) -> str:
        return os.path.expanduser(self._data["bilibili_cookie_file"])

    def ensure_dirs(self):
        """确保所有必要目录存在。"""
        for key in ("cache_dir", "output_dir"):
            path = getattr(self, key)
            os.makedirs(path, exist_ok=True)
        # 如果 obsidian vault 存在才创建子目录（避免污染非 obsidian 环境）
        vault = self.obsidian_vault
        if os.path.exists(os.path.dirname(vault)):
            os.makedirs(vault, exist_ok=True)

    def to_dict(self) -> dict:
        return dict(self._data)

    def __repr__(self) -> str:
        return f"Config({self._data})"


# 全局默认配置实例
default_config = Config()
