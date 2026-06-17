<#
.SYNOPSIS
    Knowledge Nest — Windows 自动安装脚本
.DESCRIPTION
    检测 Python、ffmpeg、Playwright 并安装所有依赖。
    支持 PowerShell 5.1+ (Windows 10/11)。
.EXAMPLE
    .\install_windows.ps1                    # 完全安装
    .\install_windows.ps1 -SkipPlaywright   # 跳过浏览器安装
    .\install_windows.ps1 -NoSystemDeps     # 仅安装 Python 包
#>

param(
    [switch]$SkipPlaywright,
    [switch]$NoSystemDeps,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Knowledge Nest ⚡ Windows 安装"

# ── 颜色辅助 ──
function Write-Info  { Write-Host "ℹ️ " -NoNewline; Write-Host "$args" -ForegroundColor Cyan }
function Write-Ok    { Write-Host "✅ " -NoNewline; Write-Host "$args" -ForegroundColor Green }
function Write-Warn  { Write-Host "⚠️ " -NoNewline; Write-Host "$args" -ForegroundColor Yellow }
function Write-Err   { Write-Host "❌ " -NoNewline; Write-Host "$args" -ForegroundColor Red }

# ── 帮助 ──
if ($Help) {
    Get-Help $PSCommandPath -Detailed
    exit 0
}

Write-Host "══════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host " 🪺 Knowledge Nest — Windows Setup" -ForegroundColor Magenta
Write-Host "══════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host ""

# ── 1. 检测 Python ──
Write-Info "Step 1/5: 检测 Python..."
$python = "python"
try {
    $pyVersion = & $python --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "python 不可用" }
    Write-Ok "Python: $($pyVersion.Trim())"
}
catch {
    # 尝试 python3
    $python = "python3"
    try {
        $pyVersion = & $python --version 2>&1
        if ($LASTEXITCODE -ne 0) { throw "python3 也不可用" }
        Write-Ok "Python: $($pyVersion.Trim())"
    }
    catch {
        Write-Err "未检测到 Python！"
        Write-Host "请从 https://www.python.org/downloads/ 安装 Python 3.10+"
        Write-Host "安装时请勾选 'Add Python to PATH'"
        exit 1
    }
}

# ── 2. 创建虚拟环境（可选但推荐） ──
Write-Info "Step 2/5: 设置虚拟环境..."
$venvPath = Join-Path $PSScriptRoot ".." ".venv"
if (-not (Test-Path $venvPath)) {
    & $python -m venv $venvPath
    Write-Ok "虚拟环境已创建: $venvPath"
}
else {
    Write-Ok "虚拟环境已存在: $venvPath"
}

# 激活 venv
$activateScript = Join-Path $venvPath "Scripts" "Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
    $python = "python"
    Write-Ok "虚拟环境已激活"
}

# ── 3. 安装 Python 依赖 ──
Write-Info "Step 3/5: 安装 Python 依赖..."
$reqFile = Join-Path $PSScriptRoot ".." "requirements.txt"
if (Test-Path $reqFile) {
    & $python -m pip install --upgrade pip -q
    & $python -m pip install -e "$(Join-Path $PSScriptRoot '..')" -q
    Write-Ok "核心包安装完成 (pip install -e .)"
}
else {
    Write-Warn "未找到 requirements.txt"
}

# ── 4. 系统依赖 (ffmpeg) ──
if (-not $NoSystemDeps) {
    Write-Info "Step 4/5: 检测系统依赖..."

    # 检查 ffmpeg
    try {
        $ffmpegVer = & ffmpeg -version 2>&1 | Select-Object -First 1
        Write-Ok "ffmpeg: $($ffmpegVer.Trim())"
    }
    catch {
        Write-Warn "ffmpeg 未安装在 PATH 中，尝试自动下载..."
        try {
            $ffmpegUrl = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            $tempDir = Join-Path $env:TEMP "knest-ffmpeg"
            $null = New-Item -ItemType Directory -Force -Path $tempDir
            $zipPath = Join-Path $tempDir "ffmpeg.zip"

            Write-Info "下载 ffmpeg..."
            Invoke-WebRequest -Uri $ffmpegUrl -OutFile $zipPath -UseBasicParsing

            Write-Info "解压 ffmpeg..."
            Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force

            # 找到 ffmpeg.exe
            $ffmpegExe = Get-ChildItem -Path $tempDir -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
            if ($ffmpegExe) {
                $ffmpegBin = Join-Path $PSScriptRoot ".." "bin"
                $null = New-Item -ItemType Directory -Force -Path $ffmpegBin
                Copy-Item $ffmpegExe.FullName -Destination (Join-Path $ffmpegBin "ffmpeg.exe") -Force

                # 添加到当前会话 PATH
                $env:Path = "$ffmpegBin;$env:Path"
                Write-Ok "ffmpeg 已安装到 $ffmpegBin"
                Write-Warn "请手动将 $ffmpegBin 添加到系统 PATH 环境变量，或重新打开终端"
            }
        }
        catch {
            Write-Err "ffmpeg 自动下载失败: $_"
            Write-Host "请手动下载安装: https://ffmpeg.org/download.html"
        }
    }
}
else {
    Write-Info "Step 4/5: 跳过系统依赖 (已指定 -NoSystemDeps)"
}

# ── 5. Playwright 浏览器 ──
if (-not $SkipPlaywright) {
    Write-Info "Step 5/5: 安装 Playwright 浏览器..."
    try {
        & $python -m playwright install chromium --with-deps
        Write-Ok "Playwright 浏览器安装完成"
    }
    catch {
        Write-Warn "Playwright 浏览器安装失败: $_"
        Write-Host "可手动安装: python -m playwright install chromium"
    }
}
else {
    Write-Info "Step 5/5: 跳过 Playwright (已指定 -SkipPlaywright)"
}

# ── 完成 ──
Write-Host ""
Write-Host "══════════════════════════════════════════════" -ForegroundColor Green
Write-Host " ✅ Knowledge Nest 安装完成！" -ForegroundColor Green
Write-Host "══════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "下一步："
Write-Host "  1. 复制配置模板: copy config.yaml.example config.yaml"
Write-Host "  2. 编辑 config.yaml 设置 Obsidian Vault 路径"
Write-Host "  3. 运行: knest --help"
Write-Host ""
Write-Host "需要管理员权限时请以管理员身份运行 PowerShell"
