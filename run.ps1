$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    py -3.11 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.11, then run this script again.' }
}
# Check/install even when a previous installation left an incomplete virtual environment.
& $pythonPath -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Rerun this script to retry.' }
if (-not (Test-Path -LiteralPath 'models\supportflow.joblib')) {
    & $pythonPath -m supportflow.train
    if ($LASTEXITCODE -ne 0) { throw 'Training failed. Check your internet connection and try again.' }
}
& $pythonPath -m streamlit run app.py
if ($LASTEXITCODE -ne 0) { throw 'The app could not start. Check whether port 8501 is already in use.' }
