$ErrorActionPreference = "Stop"

$Repo = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Repo

$LogDir = Join-Path $Repo "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$StdOut = Join-Path $LogDir "hourly_deepseek_autonomy_task_stdout.log"
$StdErr = Join-Path $LogDir "hourly_deepseek_autonomy_task_stderr.log"

if ($env:HOURLY_DEEPSEEK_AUTONOMY_ENABLED -ne "1") {
    "Hourly DeepSeek autonomy disabled. Set HOURLY_DEEPSEEK_AUTONOMY_ENABLED=1 to run." | Set-Content -Path $StdOut -Encoding UTF8
    "" | Set-Content -Path $StdErr -Encoding UTF8
    exit 0
}

if (-not $env:FILE_EMAIL_DELIVERY) {
    $env:FILE_EMAIL_DELIVERY = "resend_dry_run"
}

$Args = @(
    "src/hourly_deepseek_autonomy_seq001_v001.py",
    "--root", ".",
    "--limit", "8",
    "--timeout-s", "160"
)

& py @Args > $StdOut 2> $StdErr
exit $LASTEXITCODE
