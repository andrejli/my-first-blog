#!/bin/bash
#
# Quick Test Runner for Django LMS
# Simple script to run Django tests with proper settings
#
# Usage: ./test.sh [test_args...]
# Examples:
#   ./test.sh                                # Run all 26 tests (event/calendar + markdown)
#   ./test.sh blog.tests                     # Run only event/calendar tests (11 tests)
#   ./test.sh tests.test_enhanced_markdown   # Run only markdown tests (15 tests)
#   ./test.sh blog.tests.EventModelTest      # Run specific test class
#   ./test.sh -v 2                           # Run with verbose output

# Set Django settings
export DJANGO_SETTINGS_MODULE="mysite.settings"

# Check if virtual environment exists and activate it
if [[ ! "$VIRTUAL_ENV" && -d "venv" ]]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Run Django tests with all passed arguments
echo "🧪 Running Django tests with settings: $DJANGO_SETTINGS_MODULE"

if [[ $# -eq 0 ]]; then
    # No arguments, run ALL Django tests
    echo "🧪 Running ALL Django tests (event/calendar + markdown + more)..."
    python manage.py test -v 2
else
    # Pass all arguments to Django test runner
    python manage.py test "$@"
fi