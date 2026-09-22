# start_frontend_dev.ps1
# 公考大鹏前端开发服务器启动脚本
# 确保 node_modules 已安装，随后启动 Vue + Vite 开发服务器。
# 开发期 /api 已由 vite.config.js 代理到后端 8000，无需手动处理跨域。

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir '..')
$FrontendDir = Join-Path $ProjectRoot 'frontend'

Set-Location $FrontendDir

if (-not (Test-Path (Join-Path $FrontendDir 'node_modules'))) {
    Write-Host '[setup] 未找到 node_modules，正在 npm install ...' -ForegroundColor Yellow
    & npm install
    if ($LASTEXITCODE -ne 0) {
        throw 'npm install 失败，请检查 Node.js / npm 环境'
    }
} else {
    Write-Host '[setup] 依赖已就绪，跳过 npm install' -ForegroundColor Green
}

Write-Host '>>> 启动前端 Vue + Vite 开发服务器' -ForegroundColor Cyan
Write-Host '    地址: http://localhost:5173' -ForegroundColor Cyan
& npm run dev
