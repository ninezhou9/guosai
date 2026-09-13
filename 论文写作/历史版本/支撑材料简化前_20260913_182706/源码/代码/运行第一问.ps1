$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
& 'C:\Program Files\Python313\python.exe' "$PSScriptRoot\q1_solution.py"
if ($LASTEXITCODE -ne 0) { throw "第一问求解失败，退出码 $LASTEXITCODE" }
