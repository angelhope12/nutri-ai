$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
py -3.12 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Python 3.12 is required." }
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
Write-Host "Configure .env with your test database and service credentials. See README.md and DEPLOYMENT.md."
