$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
& 'C:\Program Files\Python313\python.exe' "$PSScriptRoot\q2_solution.py"
if ($LASTEXITCODE -ne 0) { throw "第二问运行失败，退出码 $LASTEXITCODE" }
