<#
.SYNOPSIS
    Knowledge Nest — PowerShell CLI 入口
.DESCRIPTION
    以 PowerShell 方式调用 knest CLI。
    支持 tab 自动补全（注册下方函数后）。
    
    用法: .\knest.ps1 bilibili BV1xxxxxx
          .\knest.ps1 transcribe video.mp4
          .\knest.ps1 xmind file.xmind --obsidian
          .\knest.ps1 config
.LINK
    https://github.com/beiyi-hub/knowledge-nest
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 查找 Python
$python = "python"
try {
    $null = & $python --version
}
catch {
    try {
        $python = "python3"
        $null = & $python --version
    }
    catch {
        Write-Error "❌ 未找到 Python！请先安装 Python 3.10+"
        exit 1
    }
}

# 虚拟环境优先
$venvPython = Join-Path $ScriptDir ".venv" "Scripts" "python.exe"
if (Test-Path $venvPython) {
    $python = $venvPython
    Write-Verbose "使用虚拟环境: $python"
}

# 传递参数
$cliModule = "knest.cli"
if ($args.Count -eq 0) {
    & $python -m $cliModule --help
}
else {
    & $python -m $cliModule @args
}

exit $LASTEXITCODE

# ── Tab 自动补全（可选） ──
# 注册方式: Add-KnestTabCompletion
function Add-KnestTabCompletion {
    Register-ArgumentCompleter -Native -CommandName "knest" -ScriptBlock {
        param($wordToComplete, $commandAst, $cursorPosition)
        
        $commands = @("bilibili", "transcribe", "xmind", "config", "--help", "--version")
        $commands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }
    }
    Write-Host "✅ knest Tab 补全已注册" -ForegroundColor Green
}
