# PowerShell Test Runner for Django LMS
# Run all tests for the my-first-blog Django project

Write-Host "Starting Django LMS Test Suite" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Set up environment
$PROJECT_DIR = "c:\Users\forti\Documents\GitHub\my-first-blog"
$PYTHON_EXE = "$PROJECT_DIR\venv\Scripts\python.exe"

# Change to project directory
Set-Location $PROJECT_DIR

Write-Host "Working Directory: $PROJECT_DIR" -ForegroundColor Cyan
Write-Host "Python Executable: $PYTHON_EXE" -ForegroundColor Cyan
Write-Host ""

# Function to run test and capture results
function Run-Test {
    param(
        [string]$TestName,
        [string]$Command,
        [string]$Description
    )
    
    Write-Host "Running: $TestName" -ForegroundColor Yellow
    Write-Host "Description: $Description" -ForegroundColor Gray
    Write-Host "Command: $Command" -ForegroundColor DarkGray
    
    $startTime = Get-Date
    
    try {
        # Execute the command
        $result = Invoke-Expression $Command
        $exitCode = $LASTEXITCODE
        
        $endTime = Get-Date
        $duration = $endTime - $startTime
        
        if ($exitCode -eq 0) {
            Write-Host "PASSED" -ForegroundColor Green
            Write-Host "Duration: $([math]::Round($duration.TotalSeconds, 2))s" -ForegroundColor Gray
            Write-Host ""
            return $true
        } else {
            Write-Host "FAILED (Exit Code: $exitCode)" -ForegroundColor Red
            Write-Host "Duration: $([math]::Round($duration.TotalSeconds, 2))s" -ForegroundColor Gray
            Write-Host "Output: $result" -ForegroundColor Red
            Write-Host ""
            return $false
        }
    }
    catch {
        $endTime = Get-Date
        $duration = $endTime - $startTime
        Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Duration: $([math]::Round($duration.TotalSeconds, 2))s" -ForegroundColor Gray
        Write-Host ""
        return $false
    }
}

# Test results tracking
$testResults = @()
$totalTests = 0
$passedTests = 0

Write-Host "Pre-flight Checks" -ForegroundColor Magenta
Write-Host "=================" -ForegroundColor Magenta
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "$PROJECT_DIR\venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not found at $PROJECT_DIR\venv" -ForegroundColor Red
    Write-Host "Please create virtual environment first:" -ForegroundColor Yellow
    Write-Host "   python -m venv venv" -ForegroundColor Gray
    Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "   pip install -r requirements.txt" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# Check Django installation
$djangoCheck = & $PYTHON_EXE -c "import django; print(django.get_version())" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Django $djangoCheck detected" -ForegroundColor Green
} else {
    Write-Host "Django not found. Please install requirements:" -ForegroundColor Red
    Write-Host "   pip install -r requirements.txt" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# Check database
& $PYTHON_EXE "manage.py" "check" 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Database configuration OK" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "Database configuration issues detected" -ForegroundColor Red
    Write-Host "Running migrations..." -ForegroundColor Yellow
    Write-Host ""
    & $PYTHON_EXE "manage.py" "migrate"
}

Write-Host "Django Test Suite" -ForegroundColor Magenta
Write-Host "=================" -ForegroundColor Magenta
Write-Host ""

# 1. Django System Check
$totalTests++
if (Run-Test "System Check" "& '$PYTHON_EXE' manage.py check" "Validate Django configuration and models") {
    $passedTests++
}
$testResults += [PSCustomObject]@{Name="System Check"; Passed=($LASTEXITCODE -eq 0)}

# 2. Database Migration Check
$totalTests++
if (Run-Test "Migration Check" "& '$PYTHON_EXE' manage.py showmigrations --plan" "Check database migrations") {
    $passedTests++
}
$testResults += [PSCustomObject]@{Name="Migration Check"; Passed=($LASTEXITCODE -eq 0)}

# 3. Recurring Events Tests
$totalTests++
if (Run-Test "Recurring Events Tests" "& '$PYTHON_EXE' manage.py test tests.test_recurring_events --verbosity=1" "Test recurring events system") {
    $passedTests++
}
$testResults += [PSCustomObject]@{Name="Recurring Events Tests"; Passed=($LASTEXITCODE -eq 0)}

# 4. All Django Tests
$totalTests++
if (Run-Test "All Django Tests" "& '$PYTHON_EXE' manage.py test --verbosity=1" "Run all Django application tests") {
    $passedTests++
}
$testResults += [PSCustomObject]@{Name="All Django Tests"; Passed=($LASTEXITCODE -eq 0)}

# 5. Management Command Tests
$totalTests++
if (Run-Test "Management Commands" "& '$PYTHON_EXE' manage.py generate_recurring_events --dry-run" "Test custom Django management commands") {
    $passedTests++
}
$testResults += [PSCustomObject]@{Name="Management Commands"; Passed=($LASTEXITCODE -eq 0)}

Write-Host "Test Results Summary" -ForegroundColor Green
Write-Host "====================" -ForegroundColor Green
Write-Host ""

# Display results table
$testResults | ForEach-Object {
    $status = if ($_.Passed) { "PASS" } else { "FAIL" }
    $color = if ($_.Passed) { "Green" } else { "Red" }
    Write-Host ("{0,-25} {1}" -f $_.Name, $status) -ForegroundColor $color
}

Write-Host ""
Write-Host "Overall Results:" -ForegroundColor Cyan
$percentage = if ($totalTests -gt 0) { ($passedTests / $totalTests) * 100 } else { 0 }
Write-Host ("Passed: {0}/{1} ({2:F1}%)" -f $passedTests, $totalTests, $percentage) -ForegroundColor $(if ($passedTests -eq $totalTests) { "Green" } else { "Yellow" })

if ($passedTests -eq $totalTests) {
    Write-Host ""
    Write-Host "ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "Your Django LMS is working perfectly!" -ForegroundColor Green
    exit 0
} else {
    $failedTests = $totalTests - $passedTests
    Write-Host ""
    Write-Host "$failedTests TEST(S) FAILED" -ForegroundColor Yellow
    Write-Host "Please review the failed tests above and fix any issues." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Test Suite Completed" -ForegroundColor Green