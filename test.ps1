# Quick Test Runner for Terminal LMS
# Usage: .\test.ps1 [pytest_args...]

# Set Django settings
$env:DJANGO_SETTINGS_MODULE = "mysite.settings"

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV -and (Test-Path "venv")) {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & ".\venv\Scripts\Activate.ps1"
}

# Run pytest with all passed arguments  
Write-Host "Running tests with Django settings: mysite.settings" -ForegroundColor Green

if ($args.Count -eq 0) {
    # No arguments, run basic test suite
    & python -m pytest
} else {
    # Pass all arguments to pytest
    & python -m pytest @args
}