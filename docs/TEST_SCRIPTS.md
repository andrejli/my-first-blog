# Terminal LMS Test Scripts

This directory contains automated test runner scripts that handle Django settings and virtual environment setup automatically.

## 🚀 Quick Start

### PowerShell (Windows)
```powershell
# Simple test runner
.\test.ps1                         # Run all tests
.\test.ps1 -m auth                 # Run auth tests only
.\test.ps1 --cov=blog             # Run with coverage

# Full-featured test runner  
.\run_tests.ps1                   # Run all tests with colors
.\run_tests.ps1 auth -Verbose     # Run auth tests with details
.\run_tests.ps1 coverage -Parallel # Full coverage in parallel
.\run_tests.ps1 -Help             # Show all options
```

### Bash (Linux/Mac/WSL)
```bash
# Make executable (first time only)
chmod +x test.sh run_tests.sh

# Simple test runner
./test.sh                         # Run all tests  
./test.sh -m auth                 # Run auth tests only
./test.sh --cov=blog             # Run with coverage

# Full-featured test runner
./run_tests.sh                    # Run all tests with colors
./run_tests.sh auth --verbose     # Run auth tests with details  
./run_tests.sh coverage --parallel # Full coverage in parallel
./run_tests.sh --help             # Show all options
```

## 📋 What These Scripts Do

### Automatic Setup
- ✅ **Virtual Environment**: Activates `venv/` if not already active
- ✅ **Django Settings**: Sets `DJANGO_SETTINGS_MODULE=mysite.settings`
- ✅ **Dependencies**: Checks and installs pytest if missing
- ✅ **Error Handling**: Clear error messages and helpful tips

### Test Types Available
- `all` - Run all tests (default)
- `unit` - Unit tests only (`-m unit`)
- `integration` - Integration tests only (`-m integration`)
- `auth` - Authentication tests (`-m auth`)
- `course` - Course management tests (`-m course`)
- `quiz` - Quiz system tests (`-m quiz`)
- `forum` - Forum system tests (`-m forum`)
- `theme` - Theme system tests (`-m theme`)
- `models` - Model tests (`-m models`)
- `views` - View tests (`-m views`)
- `quick` - Fast tests only (`-m "not slow"`)
- `coverage` - Full coverage analysis

## 🔧 Script Details

### Simple Scripts (`test.ps1` / `test.sh`)
- Minimal, fast execution
- Pass-through for all pytest arguments
- Good for development workflow

### Full Scripts (`run_tests.ps1` / `run_tests.sh`)
- Comprehensive options and help
- Colored output and progress indicators
- Built-in test type selection
- Parallel execution support
- Coverage reporting
- Error diagnostics

## 📊 Examples

```bash
# Development workflow
./test.sh -x -v                    # Stop on first failure, verbose
./test.sh blog/test_pytest_examples.py::TestAuth  # Specific test

# Pre-commit checks
./run_tests.sh quick               # Fast test run
./run_tests.sh coverage            # Full coverage check

# Debugging specific areas
./run_tests.sh auth --verbose      # Debug auth issues
./run_tests.sh models -v           # Debug model tests

# Performance testing
./run_tests.sh all --parallel      # Fast full test run
./run_tests.sh integration         # Slower integration tests
```

## 🚨 Troubleshooting

### PowerShell Execution Policy
If you get execution policy errors:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Missing Virtual Environment
If `venv/` doesn't exist:
```bash
python -m venv venv
```

### Missing Dependencies
Scripts will auto-install pytest, but you can manually install:
```bash
pip install -r requirements.txt
```

### Django Settings Issues
Scripts automatically set `DJANGO_SETTINGS_MODULE=mysite.settings`. If you have custom settings:
```bash
# Modify the scripts or set manually:
export DJANGO_SETTINGS_MODULE="mysite.production_settings"  # Linux/Mac
$env:DJANGO_SETTINGS_MODULE="mysite.production_settings"   # PowerShell
```

## 🎯 Integration with VS Code

Add these tasks to your `.vscode/tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run Tests",
            "type": "shell",
            "command": "./test.sh",
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "Run Auth Tests",
            "type": "shell", 
            "command": "./run_tests.sh auth --verbose",
            "group": "test"
        }
    ]
}
```

## 📚 More Information

- Full testing guide: [TESTING.md](TESTING.md)
- pytest configuration: [pytest.ini](pytest.ini)
- Test fixtures: [blog/conftest.py](blog/conftest.py)
- Example tests: [blog/test_pytest_examples.py](blog/test_pytest_examples.py)