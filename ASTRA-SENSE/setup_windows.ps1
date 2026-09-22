$ErrorActionPreference = "Stop"
Write-Host "ASTRA-SENSE setup" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    $created = $false
    foreach ($version in @("3.14", "3.13", "3.12", "3.11", "3.10")) {
        try {
            & py "-$version" -m venv .venv
            if ($LASTEXITCODE -eq 0) {
                $created = $true
                break
            }
        } catch {}
    }
    if (-not $created) {
        throw "Python 3.10 or newer is required. Install Python and enable the py launcher."
    }
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
Write-Host "Setup complete. Run: .\.venv\Scripts\python.exe main.py" -ForegroundColor Green
