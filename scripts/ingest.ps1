# 真题入库脚本（Windows）
# 资料目录由用户通过 --seed 传入，不要硬编码本机路径

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Backend = Join-Path $Root "backend"
$Py = Join-Path $Backend ".venv" "Scripts" "python.exe"
$Ingest = Join-Path $Root "scripts" "ingest.py"

if (-not (Test-Path $Py)) {
    Write-Error "找不到 Python 解释器：$Py"
    exit 1
}

# 透传所有参数给用户态入库脚本
& $Py $Ingest @args
