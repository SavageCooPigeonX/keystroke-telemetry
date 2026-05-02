$ErrorActionPreference = "Stop"

$TaskName = "Pigeon DeepSeek Hourly Autonomy"
$Runner = Resolve-Path (Join-Path $PSScriptRoot "run_hourly_deepseek_autonomy.ps1")
$Argument = "-NoProfile -ExecutionPolicy Bypass -File `"$($Runner.Path)`""
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $Argument
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Compile operator intent, run hourly DeepSeek autonomy, and email the receipt." `
    -Force | Out-Null

Write-Host "Installed $TaskName. Next run: $($Trigger.StartBoundary). Repeats hourly."
