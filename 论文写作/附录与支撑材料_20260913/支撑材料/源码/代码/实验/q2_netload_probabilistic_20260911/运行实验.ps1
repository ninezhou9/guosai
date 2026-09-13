$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$taskScript = Join-Path $PSScriptRoot 'run_experiment.py'
& 'C:/Program Files/Python313/python.exe' -X utf8 $taskScript --stage all
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& 'C:/Program Files/Python313/python.exe' -X utf8 (Join-Path $PSScriptRoot 'make_report.py')
exit $LASTEXITCODE
