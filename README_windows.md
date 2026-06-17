# 🪺 Knowledge Nest — Windows 使用指南

> **视频 → 笔记 → Obsidian → 思维导图 — 专为 Windows 优化的版本**

---

## 📦 安装

### 前置要求

- **Python 3.10+** — [下载](https://www.python.org/downloads/)
  - 安装时 **务必勾选** "Add Python to PATH"
- **PowerShell 5.1+** — Windows 10/11 自带

### 快速安装

打开 **PowerShell**，进入项目目录，运行：

```powershell
# 一键安装（推荐）
.\scripts\install_windows.ps1

# 如果遇到执行策略限制，先运行：
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

安装脚本会自动完成：
1. ✅ 检测 Python 版本
2. ✅ 创建虚拟环境 `.venv`
3. ✅ 安装核心 Python 包
4. ✅ 自动下载 ffmpeg（如果 PATH 中没有）
5. ✅ 安装 Playwright 浏览器

### 可选参数

```powershell
# 仅安装 Python 包，跳过 ffmpeg
.\scripts\install_windows.ps1 -NoSystemDeps

# 跳过 Playwright 浏览器安装
.\scripts\install_windows.ps1 -SkipPlaywright
```

---

## 🚀 使用

### 方式一：Batch 入口（推荐）

双击 `knest.cmd` 或直接在终端运行：

```cmd
knest.cmd --help
knest.cmd bilibili BV1xxxxxx
knest.cmd transcribe video.mp4
knest.cmd xmind file.xmind --obsidian
knest.cmd config
```

### 方式二：PowerShell 入口

```powershell
.\knest.ps1 --help
```

### 方式三：直接调用 Python 模块

```cmd
python -m knest.cli --help
```

### 添加到系统 PATH（方便全局使用）

将项目目录添加到 `%PATH%` 后，可以随处运行 `knest`：

1. **Win + R** → `sysdm.cpl` → **高级** → **环境变量**
2. 在 **系统变量** 中找到 `Path` → **编辑**
3. **新建** → 添加项目目录路径（如 `C:\Users\你的用户名\knowledge-nest`）
4. 确定保存，重新打开终端

---

## ⚙️ 配置

```powershell
# 复制配置模板，然后编辑
copy config.yaml.example config.yaml
notepad config.yaml
```

**Windows 默认路径说明：**
- 缓存目录：`%LOCALAPPDATA%\knest\cache`
- 输出目录：`%LOCALAPPDATA%\knest\output`
- Obsidian Vault：`%USERPROFILE%\Documents\obsidian-vault`
- B站 cookies：`%LOCALAPPDATA%\knest\bilibili_cookies.json`

如需自定义，在 `config.yaml` 中设置（支持 `%APPDATA%` 和 `~`）：

```yaml
cache_dir: D:\knest-cache
obsidian_vault: D:\Obsidian\MyVault
```

---

## 🧩 已知问题

| 问题 | 原因 | 解决 |
|------|------|------|
| ❌ `ffmpeg` 未找到 | 不在 PATH 中 | 运行安装脚本或手动下载 ffmpeg |
| ❌ Playwright 浏览器启动失败 | 系统缺少 Visual C++ 运行时 | 安装 [VC++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) |
| ⚠️ 虚拟环境激活失败 | 执行策略限制 | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| ⚠️ 文件名含不可见字符 | Windows 文件系统限制 | 已自动替换 `\ / : * ? " < > \|` 为 `_` |

---

## 🔄 升级

```powershell
git pull origin win-support
.\scripts\install_windows.ps1
```

---

## 💡 提示

- 路径中的 **正斜杠 `/`** 和 **反斜杠 `\`** 都可以用，脚本会自动处理
- `%APPDATA%`、`%USERPROFILE%` 等环境变量可以在配置文件中直接使用
- 推荐在 `config.yaml` 中使用 **反斜杠** 风格路径（如 `D:\Vault`）
- 如果 Obsidian Vault 在 OneDrive/Dropbox 中，直接填同步目录路径即可
