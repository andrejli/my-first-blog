#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Terminal LMS Test Runner (PowerShell)
    
.DESCRIPTION
    Comprehensive test runner for Terminal LMS Django application.
    Automatically activates virtual environment, sets Django settings, and runs pytest.
    
.PARAMETER TestType
    Type of tests to run: all, unit, integration, auth, course, quiz, forum, theme, coverage, quick
    
.PARAMETER Verbose
    Run tests in verbose mode with detailed output
    
.PARAMETER Parallel
    Run tests in parallel using pytest-xdist
    
.PARAMETER Coverage
    Generate coverage reports (HTML and terminal)
    
.EXAMPLE
    .\run_tests.ps1
    .\run_tests.ps1 -TestType auth -Verbose
    .\run_tests.ps1 -TestType all -Coverage -Parallel
    
.NOTES
    Author: Terminal LMS Team
    Version: 1.0
    Requires: Python 3.8+, Django 5.2+, pytest
#>

param(
    [Parameter(Position=0)]
    [ValidateSet("all", "unit", "integration", "auth", "course", "quiz", "forum", "theme", "coverage", "quick", "models", "views")]
    [string]$TestType = "all",
    
    [switch]$VerboseOutput,
    [switch]$Parallel,
    [switch]$Coverage,
    [switch]$Help
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Show-Help {
    Write-ColorOutput "🧪 Terminal LMS Test Runner" $InfoColor
    Write-ColorOutput "================================" $InfoColor
    Write-Host ""
    Write-ColorOutput "Usage:" $InfoColor
    Write-Host "  .\run_tests.ps1 [TestType] [Options]"
    Write-Host ""
    Write-ColorOutput "Test Types:" $InfoColor
    Write-Host "  all         - Run all tests (default)"
    Write-Host "  unit        - Run unit tests only"
    Write-Host "  integration - Run integration tests only"
    Write-Host "  auth        - Run authentication tests"
    Write-Host "  course      - Run course management tests"
    Write-Host "  quiz        - Run quiz system tests"
    Write-Host "  forum       - Run forum system tests"
    Write-Host "  theme       - Run theme system tests"
    Write-Host "  models      - Run model tests"
    Write-Host "  views       - Run view tests"
    Write-Host "  coverage    - Run with comprehensive coverage"
    Write-Host "  quick       - Quick test run (no slow tests)"
    Write-Host ""
    Write-ColorOutput "Options:" $InfoColor
    Write-Host "  -VerboseOutput - Detailed test output"
    Write-Host "  -Parallel   - Run tests in parallel"
    Write-Host "  -Coverage   - Generate coverage reports"
    Write-Host "  -Help       - Show this help message"
    Write-Host ""
    Write-ColorOutput "Examples:" $InfoColor
    Write-Host "  .\run_tests.ps1"
    Write-Host "  .\run_tests.ps1 auth -VerboseOutput"
    Write-Host "  .\run_tests.ps1 all -Coverage -Parallel"
    Write-Host ""
}

if ($Help) {
    Show-Help
    exit 0
}

Write-ColorOutput "🚀 Terminal LMS Test Runner Starting..." $InfoColor
Write-ColorOutput "=======================================" $InfoColor

# Check if we're in the correct directory
if (-not (Test-Path "manage.py")) {
    Write-ColorOutput "❌ Error: manage.py not found. Please run from project root directory." $ErrorColor
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-ColorOutput "❌ Error: Virtual environment 'venv' not found." $ErrorColor
    Write-ColorOutput "Please create it with: python -m venv venv" $WarningColor
    exit 1
}

# Activate virtual environment
Write-ColorOutput "🔧 Activating virtual environment..." $InfoColor
try {
    & ".\venv\Scripts\Activate.ps1"
    if ($LASTEXITCODE -ne 0) {
        throw "Virtual environment activation failed"
    }
} catch {
    Write-ColorOutput "❌ Error: Failed to activate virtual environment." $ErrorColor
    Write-ColorOutput "Try running: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" $WarningColor
    exit 1
}

# Set Django settings
$env:DJANGO_SETTINGS_MODULE = "mysite.settings"
Write-ColorOutput "⚙️ Django settings: $env:DJANGO_SETTINGS_MODULE" $InfoColor

# Check if pytest is installed
Write-ColorOutput "🔍 Checking pytest installation..." $InfoColor
$pytestVersion = & python -m pytest --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput "❌ Error: pytest not installed." $ErrorColor
    Write-ColorOutput "Installing pytest and dependencies..." $WarningColor
    & python -m pip install pytest pytest-django pytest-cov pytest-xdist pytest-mock
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "❌ Error: Failed to install pytest dependencies." $ErrorColor
        exit 1
    }
}

Write-ColorOutput "✅ pytest installed: $pytestVersion" $SuccessColor

# Build pytest command
$pytestCmd = @("python", "-m", "pytest")

# Add test selection based on type
switch ($TestType) {
    "unit" { $pytestCmd += @("-m", "unit") }
    "integration" { $pytestCmd += @("-m", "integration") }
    "auth" { $pytestCmd += @("-m", "auth") }
    "course" { $pytestCmd += @("-m", "course") }
    "quiz" { $pytestCmd += @("-m", "quiz") }
    "forum" { $pytestCmd += @("-m", "forum") }
    "theme" { $pytestCmd += @("-m", "theme") }
    "models" { $pytestCmd += @("-m", "models") }
    "views" { $pytestCmd += @("-m", "views") }
    "quick" { $pytestCmd += @("-m", "not slow") }
    "coverage" { 
        $Coverage = $true
        $pytestCmd += @("--cov=blog", "--cov-report=html:htmlcov", "--cov-report=term-missing")
    }
    "all" { 
        # Run all tests - no additional markers needed
    }
}

# Add verbose output if requested
if ($VerboseOutput) {
    $pytestCmd += @("-v", "-s")
}

# Add parallel execution if requested
if ($Parallel) {
    $pytestCmd += @("-n", "auto")
    Write-ColorOutput "🔄 Running tests in parallel..." $InfoColor
}

# Add coverage if requested (and not already added)
if ($Coverage -and $TestType -ne "coverage") {
    $pytestCmd += @("--cov=blog", "--cov-report=html:htmlcov", "--cov-report=term-missing")
}

# Display command being run
Write-ColorOutput "🧪 Running: $($pytestCmd -join ' ')" $InfoColor
Write-ColorOutput "📁 Test type: $TestType" $InfoColor
Write-Host ""

# Run the tests
$startTime = Get-Date
try {
    & $pytestCmd[0] $pytestCmd[1..($pytestCmd.Length-1)]
    $exitCode = $LASTEXITCODE
} catch {
    Write-ColorOutput "❌ Error running tests: $_" $ErrorColor
    exit 1
}

$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host ""
Write-ColorOutput "🕒 Test execution completed in $($duration.TotalSeconds.ToString('F2')) seconds" $InfoColor

# Report results
if ($exitCode -eq 0) {
    Write-ColorOutput "✅ All tests passed!" $SuccessColor
    
    if ($Coverage -or $TestType -eq "coverage") {
        Write-ColorOutput "📊 Coverage report generated:" $InfoColor
        Write-ColorOutput "   HTML: htmlcov/index.html" $InfoColor
        Write-ColorOutput "   Terminal output above" $InfoColor
    }
} else {
    Write-ColorOutput "❌ Some tests failed (exit code: $exitCode)" $ErrorColor
    Write-ColorOutput "💡 Tips:" $WarningColor
    Write-ColorOutput "   - Check test output above for details" $WarningColor
    Write-ColorOutput "   - Run with -VerboseOutput for more information" $WarningColor
    Write-ColorOutput "   - Run specific test types to isolate issues" $WarningColor
}

Write-Host ""
Write-ColorOutput "🎯 Available test commands:" $InfoColor
Write-ColorOutput "   .\run_tests.ps1 auth -VerboseOutput # Debug auth tests" $InfoColor
Write-ColorOutput "   .\run_tests.ps1 coverage          # Full coverage report" $InfoColor
Write-ColorOutput "   .\run_tests.ps1 quick             # Fast test run" $InfoColor
Write-ColorOutput "   .\run_tests.ps1 -Help             # Show all options" $InfoColor

exit $exitCode