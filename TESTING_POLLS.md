# Testing the Secret Chamber Polling System

This document explains how to run tests for the Secret Chamber admin polling system.

## Test Overview

The polling system includes comprehensive tests covering:

- **Model Tests**: AdminPoll, PollOption, AdminVote, AdminPollAudit models
- **View Tests**: Dashboard, poll creation, voting, results display
- **Security Tests**: Access control, poll tampering protection, audit logging
- **Integration Tests**: Complete polling workflows
- **Performance Tests**: Large polls, many voters, stress testing

## Test Files

- `tests/test_polling_system.py` - Main test suite (100+ test cases)
- `test_polling.py` - Dedicated polling test runner
- `test-requirements.txt` - Testing dependencies

## Running Tests

### 1. Install Test Dependencies

```bash
# Install test packages
pip install -r test-requirements.txt

# Or install individually
pip install pytest pytest-django pytest-cov coverage
```

### 2. Run All Tests

#### Using integrated test scripts:

**PowerShell (Windows):**
```powershell
.\test.ps1
```

**Bash (Linux/Mac):**
```bash
./test.sh
```

#### Using dedicated polling test runner:
```bash
python test_polling.py
```

#### Using pytest directly:
```bash
# Run all polling tests
pytest tests/test_polling_system.py -v

# Run with coverage
pytest tests/test_polling_system.py --cov=blog.secret_chamber --cov-report=html
```

### 3. Run Specific Test Categories

```bash
# Model tests only
pytest tests/test_polling_system.py::TestAdminPollModel -v

# View tests only  
pytest tests/test_polling_system.py::TestPollingViews -v

# Security tests only
pytest tests/test_polling_system.py::TestPollingSecurityFeatures -v

# Integration tests only
pytest tests/test_polling_system.py::TestPollingIntegration -v

# Performance tests (marked as slow)
pytest tests/test_polling_system.py::TestPollingPerformance -v -m slow
```

### 4. Run Individual Tests

```bash
# Using the dedicated test runner
python test_polling.py test:TestAdminPollModel::test_poll_creation

# Using pytest directly
pytest tests/test_polling_system.py::TestAdminPollModel::test_poll_creation -v
```

### 5. Generate Coverage Reports

```bash
# HTML coverage report
python test_polling.py coverage

# Or with pytest
pytest tests/test_polling_system.py --cov=blog.secret_chamber --cov-report=html:htmlcov/polling
```

## Test Structure

### Model Tests (`TestAdminPollModel`)
- ✅ Poll creation and validation
- ✅ Date validation (future end dates)
- ✅ Poll state properties (is_open, is_completed)
- ✅ Voting permissions
- ✅ Security validation (tampering protection)
- ✅ Eligible voters calculation
- ✅ Participation rate calculation

### Option Tests (`TestPollOptionModel`)
- ✅ Option creation and ordering
- ✅ Vote counting per option
- ✅ Unique option text validation

### Vote Tests (`TestAdminVoteModel`)
- ✅ Vote creation for different poll types
- ✅ One vote per user per poll enforcement
- ✅ Rating validation (1-10 range)
- ✅ Open response text storage

### View Tests (`TestPollingViews`)
- ✅ Superuser access control
- ✅ Dashboard functionality
- ✅ Poll detail display
- ✅ Poll creation form and submission
- ✅ Voting functionality (all poll types)
- ✅ Double voting prevention
- ✅ Results display

### Security Tests (`TestPollingSecurityFeatures`)
- ✅ Audit log creation
- ✅ Superuser requirement enforcement
- ✅ Poll tampering protection
- ✅ Unauthorized access blocking

### Integration Tests (`TestPollingIntegration`)
- ✅ Complete polling workflow (create → vote → results)
- ✅ Early results with 100% participation
- ✅ Multi-user voting scenarios

### Performance Tests (`TestPollingPerformance`)
- ✅ Large poll creation (100+ options)
- ✅ Many voters performance (50+ users)
- ✅ Vote counting efficiency

## Test Coverage Goals

| Component | Target Coverage | Current Status |
|-----------|----------------|----------------|
| Models    | 90%+          | ✅ Achieved    |
| Views     | 85%+          | ✅ Achieved    |
| Security  | 95%+          | ✅ Achieved    |
| Overall   | 85%+          | ✅ Achieved    |

## Continuous Integration

The tests are integrated into the main test suite and will run automatically:

1. **test.ps1** (PowerShell) - Includes polling tests
2. **test.sh** (Bash) - Includes polling tests  
3. **pytest discovery** - Auto-finds all test files

## Test Data

Tests use Django's test database with:
- Temporary superusers and regular users
- Temporary polls with various configurations
- Isolated test data (cleaned up after each test)

## Debugging Failed Tests

### Common Issues:

1. **Database Errors**: Ensure migrations are up to date
   ```bash
   python manage.py migrate
   ```

2. **Import Errors**: Check that secret_chamber app is in INSTALLED_APPS
   ```python
   # In mysite/settings.py
   INSTALLED_APPS = [
       # ...
       'blog.secret_chamber',
   ]
   ```

3. **Permission Errors**: Tests create temporary superusers automatically

4. **Coverage Issues**: Ensure pytest-cov is installed
   ```bash
   pip install pytest-cov
   ```

### Verbose Output:
```bash
# Get detailed test output
pytest tests/test_polling_system.py -v --tb=long --capture=no
```

### Debug Specific Test:
```bash
# Run single test with detailed output
pytest tests/test_polling_system.py::TestAdminPollModel::test_poll_creation -vvv --tb=long --pdb
```

## Test Environment

- **Python**: 3.13+ required
- **Django**: 5.2+ required  
- **Database**: SQLite (test) / PostgreSQL (production)
- **Dependencies**: See test-requirements.txt

## Contributing

When adding new polling features:

1. **Add corresponding tests** in `tests/test_polling_system.py`
2. **Maintain test coverage** above 85%
3. **Update this documentation** as needed
4. **Run full test suite** before committing

## Performance Benchmarks

Target performance for tests:
- Individual tests: < 5 seconds each
- Full test suite: < 2 minutes
- Coverage report generation: < 30 seconds

Tests marked with `@pytest.mark.slow` may take longer and can be skipped:
```bash
pytest tests/test_polling_system.py -m "not slow"
```