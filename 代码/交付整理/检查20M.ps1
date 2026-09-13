param([Parameter(Mandatory=$true)][string]$FullPaperPdf)
$taskPdf = Get-Item -LiteralPath $FullPaperPdf -ErrorAction Stop
$taskProject = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$taskZip = Get-Item -LiteralPath (Join-Path $taskProject '论文写作\附录与支撑材料_20260913\支撑材料.zip') -ErrorAction Stop
$taskRaw = (Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot '缓存\支撑材料') -File -Recurse | Measure-Object -Property Length -Sum).Sum
$taskTotal = $taskPdf.Length + $taskZip.Length
[pscustomobject]@{
    '论文PDF字节（应已含附录）' = $taskPdf.Length
    '支撑ZIP字节' = $taskZip.Length
    '上传文件合计字节' = $taskTotal
    '按十进制MB计' = [math]::Round($taskTotal / 1000000, 3)
    '剩余额度字节' = 20000000 - $taskTotal
    'PDF加未打包支撑文件字节' = $taskPdf.Length + $taskRaw
    '不超过20M' = $taskTotal -le 20000000
}
if ($taskTotal -gt 20000000) { exit 1 }
