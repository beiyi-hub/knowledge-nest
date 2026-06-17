"""
统一配置管理 — 跨平台路径安全，全面替代所有硬编码路径。

配置优先级：CLI 参数 > 环境变量 > 配置文件 > 默认值
平台适配：自动检测 Linux / macOS / Windows，自动切换路径风格。
"""

import os
import platform
import sys
from pathlib import Path
from typing import Any, Optional

# ── 平台检测 ──────────────────────────────────────────────
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"


def _user_home() -> Path:
    """跨平台可靠的用户主目录获取。"""
    # Windows: %USERPROFILE% 优先
    if IS_WINDOWS:
        return Path(os.environ.get("USERPROFILE", os.path.expanduser("~")))
    return Path(os.path.expanduser("~"))


def _resolve_path(path_str: str) -> Path:
    """将路径字符串（支持 ~、%VAR%、环境变量）解析为绝对 Path。"""
    if not path_str:
        return Path()

    # Windows 环境变量展开 %APPDATA%, %USERPROFILE% 等
    if IS_WINDOWS:
        import re
        path_str = re.sub(
            r"%([^%]+)%",
            lambda m: os.environ.get(m.group(1), m.group(0)),
            path_str,
        )
        # 正斜杠转反斜杠
        path_str = path_str.replace("/", "\\")

    # 展开 ~
    path = Path(os.path.expanduser(path_str))
    # Windows 上统一用反斜杠风格存储
    if IS_WINDOWS:
        path = Path(str(path).replace("/", "\\"))
    return path.resolve()


def _win_default_appdata() -> Path:
    """Windows: 用 %APPDATA% 或 %LOCALAPPDATA% 存储应用数据。"""
    appdata = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "knest"
    return _user_home() / ".knest"


def _platform_default(key: str) -> str:
    """根据平台返回不同的默认值。"""
    home = _user_home()
    defaults = _DEFAULTS.copy()

    if IS_WINDOWS:
        appdata = _win_default_appdata()
        defaults.update({
            # Windows 下：%LOCALAPPDATA%\\knest 取代 ~/.knest
            "cache_dir": str(appdata / "cache"),
            "output_dir": str(appdata / "output"),
            "bilibili_cookie_file": str(appdata / "bilibili_cookies.json"),
            # Obsidian vault 常见位置
            "obsidian_vault": str(home / "Documents" / "obsidian-vault"),
            "obsidian_notes_dir": "Notes",
            # Whisper
            "whisper_model": "base",
            "whisper_language": "zh",
            # Windows 上 HF 镜像默认不变
            "hf_endpoint": "https://hf-mirror.com",
            # B站
            "bilibili_quality": 80,
            # LLM
            "llm_provider": "",
            "llm_api_key": "",
            "llm_model": "",
            # Windows 特有配置
            "ffmpeg_path": "ffmpeg.exe",  # 可从 PATH 或自动下载
            "playwright_browsers_dir": str(appdata / "playwright-browsers"),
        })

    return defaults.get(key, _DEFAULTS.get(key, ""))


# 通用默认值（跨平台共享）
_DEFAULTS: dict[str, Any] = {
    "cache_dir": "~/.knest/cache",
    "output_dir": "~/.knest/output",
    "obsidian_vault": "~/obsidian-vault",
    "obsidian_notes_dir": "Notes",
    "bilibili_quality": 80,
    "bilibili_cookie_file": "~/.knest/bilibili_cookies.json",
    "whisper_model": "base",
    "whisper_language": "zh",
    "hf_endpoint": "https://hf-mirror.com",
    "llm_provider": "",
    "llm_api_key": "",
    "llm_model": "",
}


class Config:
    """配置管理器，跨平台路径安全。

    用法:
        cfg = Config()
        print(cfg.cache_dir)       # Windows → C:\\Users\\xxx\\AppData\\Local\\knest\\cache
        print(cfg.obsidian_vault)  # Linux   → /home/xxx/obsidian-vault
    """

    def __init__(self, config_file: Optional[str] = None):
        # 先加载通用默认值
        self._data = dict(_DEFAULTS)
        # 再覆盖平台默认值
        self._apply_platform_defaults()
        # 再加载配置文件
        if config_file:
            self._load_yaml(config_file)
            # 检查是否存在默认位置的配置文件
        elif not config_file:
            auto_path = self._auto_config_path()
            if auto_path and auto_path.exists():
                self._load_yaml(str(auto_path))
        # 最后环境变量覆盖（最高优先级）
        self._apply_env_overrides()

    # ── 内部方法 ──────────────────────────────────────────

    def _apply_platform_defaults(self):
        """用平台特定默认值覆盖通用默认值。"""
        if IS_WINDOWS:
            appdata = _win_default_appdata()
            home = _user_home()
            self._data.update({
                "cache_dir": str(appdata / "cache"),
                "output_dir": str(appdata / "output"),
                "bilibili_cookie_file": str(appdata / "bilibili_cookies.json"),
                "obsidian_vault": str(home / "Documents" / "obsidian-vault"),
                "obsidian_notes_dir": "Notes",
            })

    def _auto_config_path(self) -> Optional[Path]:
        """查找默认位置的配置文件。"""
        if IS_WINDOWS:
            candidates = [
                _win_default_appdata() / "config.yaml",
                _user_home() / ".knest" / "config.yaml",
                Path(os.environ.get("USERPROFILE", "")) / ".knest" / "config.yaml",
            ]
        else:
            candidates = [
                Path("~/.knest/config.yaml").expanduser(),
                Path("config.yaml"),
            ]
        for p in candidates:
            if p.exists():
                return p
        return None

    def _load_yaml(self, path: str):
        try:
            import yaml
            resolved = _resolve_path(path)
            if resolved.exists():
                with open(resolved, encoding="utf-8") as f:
                    yaml_data = yaml.safe_load(f) or {}
                    self._data.update(yaml_data)
        except ImportError:
            pass

    def _apply_env_overrides(self):
        env_map = {
            "KNEST_CACHE_DIR": "cache_dir",
            "KNEST_OUTPUT_DIR": "output_dir",
            "KNEST_OBSIDIAN_VAULT": "obsidian_vault",
            "KNEST_HF_ENDPOINT": "hf_endpoint",
            "KNEST_WHISPER_MODEL": "whisper_model",
            "KNEST_WHISPER_LANG": "whisper_language",
            "KNEST_BILI_QUALITY": "bilibili_quality",
            "HF_ENDPOINT": "hf_endpoint",
            "KNEST_FFMPEG_PATH": "ffmpeg_path",
        }
        for env_key, config_key in env_map.items():
            val = os.environ.get(env_key)
            if val is not None:
                if config_key in ("bilibili_quality",):
                    try:
                        val = int(val)
                    except ValueError:
                        pass
                self._data[config_key] = val

    # ── 对外 API ──────────────────────────────────────────

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def __getattr__(self, key: str):
        if key in self._data:
            return self._data[key]
        raise AttributeError(f"Config has no key '{key}'")

    def get_path(self, key: str) -> Path:
        """获取路径值，返回跨平台安全的 Path 对象。"""
        val = self._data.get(key, "")
        if not val:
            return Path()
        return _resolve_path(str(val))

    @property
    def cache_dir(self) -> str:
        return str(self.get_path("cache_dir"))

    @property
    def output_dir(self) -> str:
        return str(self.get_path("output_dir"))

    @property
    def obsidian_vault(self) -> str:
        return str(self.get_path("obsidian_vault"))

    @property
    def obsidian_notes_dir(self) -> str:
        return self._data.get("obsidian_notes_dir", "Notes")

    @property
    def bilibili_cookie_file(self) -> str:
        return str(self.get_path("bilibili_cookie_file"))

    def ensure_dirs(self):
        """确保所有必要目录存在，跨平台安全。"""
        for key in ("cache_dir", "output_dir"):
            p = self.get_path(key)
            p.mkdir(parents=True, exist_ok=True)

        vault = self.get_path("obsidian_vault")
        if vault.parent.exists():
            vault.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict:
        return dict(self._data)

    def __repr__(self) -> str:
        return f"Config({self._data})"


# 全局默认配置实例
default_config = Config()


# ── 便捷模块级函数 ─────────────────────────────────────────

def system_info() -> dict:
    """返回系统信息摘要，用于诊断和调试。"""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python": sys.version,
        "is_windows": IS_WINDOWS,
        "is_macos": IS_MACOS,
        "is_linux": IS_LINUX,
        "home": str(_user_home()),
        "appdata": str(_win_default_appdata()) if IS_WINDOWS else "N/A",
    }
