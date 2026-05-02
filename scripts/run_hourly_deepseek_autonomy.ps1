$ErrorActionPreference = "Stop"

$Repo = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Repo

if (-not $env:FILE_EMAIL_DELIVERY) {
    $env:FILE_EMAIL_DELIVERY = "resend"
}

$LogDir = Join-Path $Repo "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$StdOut = Join-Path $LogDir "hourly_deepseek_autonomy_task_stdout.log"
$StdErr = Join-Path $LogDir "hourly_deepseek_autonomy_task_stderr.log"
$Args = @(
    "src/hourly_deepseek_autonomy_seq001_v001.py",
    "--root", ".",
    "--limit", "8",
    "--timeout-s", "160"
)

& py @Args > $StdOut 2> $StdErr
exit $LASTEXITCODE
