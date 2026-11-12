param(
    [string]$TaskName = "JARVIS Daily Clips",
    [string]$RunAt = "08:00"
)

$Project = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = (Get-Command python).Source
$Action = New-ScheduledTaskAction -Execute $Python -Argument "daily.py" -WorkingDirectory $Project
$Trigger = New-ScheduledTaskTrigger -Daily -At $RunAt
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Description "Run the JARVIS faceless YouTube Shorts batch" -Force
Write-Host "Registered $TaskName at $RunAt using $Python"