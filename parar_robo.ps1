$pythonRobo = Join-Path $PSScriptRoot '.runtime\python\python.exe'
Get-CimInstance Win32_Process -Filter "name = 'python.exe'" |
    Where-Object { $_.ExecutablePath -eq $pythonRobo -and $_.CommandLine -match '\brobo\.py\b' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId }
Write-Host 'Monitoramento encerrado.'
