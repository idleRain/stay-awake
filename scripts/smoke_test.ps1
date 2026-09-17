# 烟测脚本：启动打包产物并验证可正常进入托盘状态，结束后自动清理。
# 用法：pwsh scripts/smoke_test.ps1（需先完成构建，产物位于 dist/StayAwake.exe）
# 覆盖范围：导入层崩溃、资源加载失败、单实例冲突，均表现为进程出现错误弹窗或退出。
# 已知盲区：托盘图标渲染在 pystray 的 setup 线程中失败时进程仍存活且无弹窗。

$ErrorActionPreference = 'Stop'

$exe = Join-Path $PSScriptRoot '..\dist\StayAwake.exe'
if (-not (Test-Path $exe)) {
    throw "未找到打包产物：$exe，请先运行 python scripts/build.py"
}

# 清理已有实例，避免单实例互斥量令本次烟测弹出任一实例已运行的提示框。
Get-Process StayAwake -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

Start-Process -FilePath $exe
Start-Sleep -Seconds 3

$procs = Get-Process StayAwake -ErrorAction SilentlyContinue
if (-not $procs) {
    throw "烟测失败：进程未存活，启动即崩溃。"
}

# 正常运行时应用仅驻留托盘，所有进程的主窗口标题均为空；
# 任一非空标题即代表出现弹窗，可能是导入崩溃或启动失败提示。
# 注意无主窗口时该属性为 $null，不能用 -ne '' 判断，否则空标题会被误判为弹窗。
$popup = $procs | Where-Object { -not [string]::IsNullOrEmpty($_.MainWindowTitle) }
if ($popup) {
    $procs | Stop-Process -Force
    throw ("烟测失败：出现意外弹窗，窗口标题「{0}」。请检查被排除模块清单。" -f $popup[0].MainWindowTitle)
}

$procs | Stop-Process -Force
Write-Output ("烟测通过：{0} 个进程存活且无错误弹窗。" -f $procs.Count)
