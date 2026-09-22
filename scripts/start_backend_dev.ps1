# start_backend_dev.ps1
# 公考大鹏后端开发服务器启动脚本
# 自动确保虚拟环境存在并安装依赖，随后启动 FastAPI 开发服务器（带热重载）。

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir '..')
$BackendDir = Join-Path $ProjectRoot 'backend'
$VenvDir = Join-Path $BackendDir '.venv'
$VenvPython = Join-Path (Join-Path $VenvDir 'Scripts') 'python.exe'
$VenvActivate = Join-Path (Join-Path $VenvDir 'Scripts') 'Activate.ps1'
# 优先使用 PATH 中的 python 解释器；找不到则回退到环境变量 GKDP_PYTHON
$ManagedPython = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $ManagedPython = (Get-Command python).Source
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $ManagedPython = (Get-Command python3).Source
} elseif ($env:GKDP_PYTHON -and (Test-Path $env:GKDP_PYTHON)) {
    $ManagedPython = $env:GKDP_PYTHON
}
if (-not $ManagedPython) {
    throw '未找到 Python，请将 python 加入 PATH，或设置环境变量 GKDP_PYTHON 指向解释器'
}

if (-not (Test-Path $VenvPython)) {
    Write-Host '[setup] 未找到 .venv，正在创建虚拟环境 ...' -ForegroundColor Yellow
    if (-not (Test-Path $ManagedPython)) {
        throw ('托管 Python 不存在: ' + $ManagedPython)
    }
    & $ManagedPython -m venv $VenvDir
}

$ReqFile = Join-Path $BackendDir 'requirements.txt'
& $VenvPython -c 'import fastapi, sqlmodel, loguru, uvicorn, yaml'
if ($LASTEXITCODE -ne 0) {
    if (-not (Test-Path $ReqFile)) {
        throw ('依赖清单缺失: ' + $ReqFile)
    }
    Write-Host '[setup] 依赖缺失，正在安装（阿里云镜像）...' -ForegroundColor Yellow
    & $VenvPython -m pip install -r $ReqFile -i https://mirrors.aliyun.com/pypi/simple/
} else {
    Write-Host '[setup] 依赖已就绪，跳过安装' -ForegroundColor Green
}

# 自动激活虚拟环境（确保后续 python / pip 均指向 .venv）
if (Test-Path $VenvActivate) {
    . $VenvActivate
    Write-Host '[venv] 已激活虚拟环境' -ForegroundColor Green
} else {
    Write-Host '[venv] 未找到 Activate.ps1，将直接使用虚拟环境 Python' -ForegroundColor DarkYellow
}

# 端口冲突处理：若服务端口已被占用，结束占用进程后再启动
$Port = 8000
try {
    $listeners = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
    if ($listeners) {
        $pids = $listeners.OwningProcess | Sort-Object -Unique
        foreach ($p in $pids) {
            Write-Host ('[port] 端口 ' + $Port + ' 被 PID=' + $p + ' 占用，正在结束 ...') -ForegroundColor Yellow
            Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 1
        Write-Host ('[port] 端口 ' + $Port + ' 已释放，准备启动') -ForegroundColor Green
    }
} catch {
    Write-Host ('[port] 端口检测失败，跳过自动释放: ' + $_.Exception.Message) -ForegroundColor DarkYellow
}

Write-Host '>>> 启动后端 FastAPI 开发服务器' -ForegroundColor Cyan
Write-Host '    地址: http://0.0.0.0:8000   文档: http://0.0.0.0:8000/docs' -ForegroundColor Cyan
Set-Location $BackendDir
& $VenvPython run.py