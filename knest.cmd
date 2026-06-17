@echo off
REM ██╗  ██╗███╗   ██╗███████╗███████╗████████╗
REM ██║ ██╔╝████╗  ██║██╔════╝██╔════╝╚══██╔══╝
REM █████╔╝ ██╔██╗ ██║█████╗  ███████╗   ██║
REM ██╔═██╗ ██║╚██╗██║██╔══╝  ╚════██║   ██║
REM ██║  ██╗██║ ╚████║███████╗███████║   ██║
REM ╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝   ╚═╝
REM Knowledge Nest — Windows Batch Launcher
REM
REM 双击本文件即可运行 knest CLI。
REM 支持将本文件所在目录添加到 PATH。

setlocal enabledelayedexpansion

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"

REM 查找 Python
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PYTHON=python"
) else (
    where python3 >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set "PYTHON=python3"
    ) else (
        echo ❌ 未找到 Python！请先安装 Python 3.10+
        echo    下载: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

REM 虚拟环境优先
if exist "%SCRIPT_DIR%..\.venv\Scripts\python.exe" (
    set "PYTHON=%SCRIPT_DIR%..\.venv\Scripts\python.exe"
    echo ℹ️ 使用虚拟环境
)

REM 传递所有参数给 CLI
if "%~1"=="" (
    "%PYTHON%" -m knest.cli --help
) else (
    "%PYTHON%" -m knest.cli %*
)

exit /b %ERRORLEVEL%
