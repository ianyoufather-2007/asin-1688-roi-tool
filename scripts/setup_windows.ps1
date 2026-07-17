param(
    [switch]$WithBrowser,
    [switch]$Dev
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvPath = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

Push-Location $projectRoot
try {
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
        throw "未找到 Python Launcher（py），请先安装 Python 3.11 至 3.14。"
    }

    $pythonVersion = & py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ($LASTEXITCODE -ne 0) { throw "无法读取 Python 版本。" }
    $version = [version]$pythonVersion
    if ($version -lt [version]"3.11" -or $version -ge [version]"3.15") {
        throw "需要 Python 3.11 至 3.14，当前版本为 $pythonVersion。"
    }

    if (-not (Test-Path -LiteralPath $venvPython)) {
        Write-Host "创建虚拟环境：$venvPath"
        & py -m venv $venvPath
        if ($LASTEXITCODE -ne 0) { throw "创建虚拟环境失败。" }
    }

    $extras = @()
    if ($WithBrowser) { $extras += "browser" }
    if ($Dev) { $extras += "dev" }
    $installTarget = if ($extras.Count -gt 0) {
        ".[" + ($extras -join ",") + "]"
    } else {
        "."
    }

    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "升级 pip 失败。" }
    & $venvPython -m pip install -e $installTarget
    if ($LASTEXITCODE -ne 0) { throw "安装项目依赖失败。" }

    Write-Host "安装完成。"
    Write-Host "CLI：.venv\Scripts\python.exe -m asin_1688_roi.cli --help"
    if ($WithBrowser) {
        Write-Host "GUI：.venv\Scripts\python.exe -m asin_1688_roi.gui"
    }
} finally {
    Pop-Location
}
