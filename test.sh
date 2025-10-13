#!/bin/bash
#
# Quick Test Runner for Terminal LMS
# Simple script to run pytest with proper Django settings
#
# Usage: ./test.sh [pytest_args...]
# Examples:
#   ./test.sh                           # Run all tests
#   ./test.sh -m auth                   # Run auth tests
#   ./test.sh --cov=blog               # Run with coverage
#   ./test.sh blog/test_pytest_examples.py::TestAuthentication  # Specific test

# Set Django settings
export DJANGO_SETTINGS_MODULE="mysite.settings"

# Check if virtual environment exists and activate it
if [[ ! "$VIRTUAL_ENV" && -d "venv" ]]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Run pytest with all passed arguments
echo "🧪 Running tests with Django settings: $DJANGO_SETTINGS_MODULE"

if [[ $# -eq 0 ]]; then
    # No arguments, run basic test suite
    python -m pytest
else
    # Pass all arguments to pytest
    python -m pytest "$@"
fi