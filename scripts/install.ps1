<#
  Environment bootstrap — Windows (PowerShell 5.1+)

    .\scripts\install.ps1               # -> report
    .\scripts\install.ps1 bootstrap     # -> install missing + wire every harness found
    .\scripts\install.ps1 wire codex

  Only hard dependency is uv; installed here if missing, then setup.py runs on a
  pinned Python via `uv run --python 3.12`.
#>
$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host 'installing uv ...'
    powershell -ExecutionPolicy Bypass -c 'irm https://astral.sh/uv/install.ps1 | iex'
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

& uv run --python 3.12 "$Repo\scripts\setup.py" @args
exit $LASTEXITCODE
