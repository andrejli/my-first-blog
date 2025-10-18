# Quick Test Runner for Django LMS
# Usage: .\test.ps1 [test_args...]
#
# Examples:
#   .\test.ps1                          # Run all 26 tests (event/calendar + markdown)
#   .\test.ps1 blog.tests               # Run only event/calendar tests (11 tests)
#   .\test.ps1 tests.test_enhanced_markdown  # Run only markdown tests (15 tests)
#   .\test.ps1 blog.tests.EventModelTest     # Run specific test class

# Set Django settings
$env:DJANGO_SETTINGS_MODULE = "mysite.settings"

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV -and (Test-Path "venv")) {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & ".\venv\Scripts\Activate.ps1"
}

# Run Django tests with all passed arguments  
Write-Host "Running Django tests with settings: mysite.settings" -ForegroundColor Green

if ($args.Count -eq 0) {
    # No arguments, run ALL Django tests
    Write-Host "Running ALL Django tests (event/calendar + markdown + more)..." -ForegroundColor Yellow
    & python manage.py test -v 2
} else {
    # Pass all arguments to Django test runner
    & python manage.py test @args
}