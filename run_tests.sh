#!/bin/bash
#
# Terminal LMS Test Runner (Bash)
#
# Comprehensive test runner for Terminal LMS Django application.
# Automatically activates virtual environment, sets Django settings, and runs pytest.
#
# Usage:
#   ./run_tests.sh [test_type] [options]
#
# Test Types:
#   all, unit, integration, auth, course, quiz, forum, theme, coverage, quick, models, views
#
# Options:
#   -v, --verbose    : Verbose output
#   -p, --parallel   : Run tests in parallel
#   -c, --coverage   : Generate coverage reports
#   -h, --help       : Show help message
#
# Examples:
#   ./run_tests.sh
#   ./run_tests.sh auth --verbose
#   ./run_tests.sh all --coverage --parallel
#
# Author: Terminal LMS Team
# Version: 1.0
# Requires: Python 3.8+, Django 5.2+, pytest

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    printf "${1}${2}${NC}\n"
}

print_error() {
    print_color "$RED" "❌ $1"
}

print_success() {
    print_color "$GREEN" "✅ $1"
}

print_info() {
    print_color "$CYAN" "ℹ️  $1"
}

print_warning() {
    print_color "$YELLOW" "⚠️  $1"
}

show_help() {
    print_color "$CYAN" "🧪 Terminal LMS Test Runner"
    print_color "$CYAN" "================================"
    echo ""
    print_color "$CYAN" "Usage:"
    echo "  ./run_tests.sh [test_type] [options]"
    echo ""
    print_color "$CYAN" "Test Types:"
    echo "  all         - Run all tests (default)"
    echo "  unit        - Run unit tests only"
    echo "  integration - Run integration tests only"
    echo "  auth        - Run authentication tests"
    echo "  course      - Run course management tests"
    echo "  quiz        - Run quiz system tests"
    echo "  forum       - Run forum system tests"
    echo "  theme       - Run theme system tests"
    echo "  models      - Run model tests"
    echo "  views       - Run view tests"
    echo "  coverage    - Run with comprehensive coverage"
    echo "  quick       - Quick test run (no slow tests)"
    echo ""
    print_color "$CYAN" "Options:"
    echo "  -v, --verbose   - Detailed test output"
    echo "  -p, --parallel  - Run tests in parallel"
    echo "  -c, --coverage  - Generate coverage reports"
    echo "  -h, --help      - Show this help message"
    echo ""
    print_color "$CYAN" "Examples:"
    echo "  ./run_tests.sh"
    echo "  ./run_tests.sh auth --verbose"
    echo "  ./run_tests.sh all --coverage --parallel"
    echo ""
}

# Default values
TEST_TYPE="all"
VERBOSE=""
PARALLEL=""
COVERAGE=""
HELP=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        all|unit|integration|auth|course|quiz|forum|theme|coverage|quick|models|views)
            TEST_TYPE="$1"
            shift
            ;;
        -v|--verbose)
            VERBOSE="true"
            shift
            ;;
        -p|--parallel)
            PARALLEL="true"
            shift
            ;;
        -c|--coverage)
            COVERAGE="true"
            shift
            ;;
        -h|--help)
            HELP="true"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

if [[ "$HELP" == "true" ]]; then
    show_help
    exit 0
fi

print_color "$CYAN" "🚀 Terminal LMS Test Runner Starting..."
print_color "$CYAN" "======================================="

# Check if we're in the correct directory
if [[ ! -f "manage.py" ]]; then
    print_error "manage.py not found. Please run from project root directory."
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    print_error "Virtual environment 'venv' not found."
    print_warning "Please create it with: python -m venv venv"
    exit 1
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

if [[ $? -ne 0 ]]; then
    print_error "Failed to activate virtual environment."
    exit 1
fi

# Set Django settings
export DJANGO_SETTINGS_MODULE="mysite.settings"
print_info "Django settings: $DJANGO_SETTINGS_MODULE"

# Check if pytest is installed
print_info "Checking pytest installation..."
if ! python -m pytest --version > /dev/null 2>&1; then
    print_error "pytest not installed."
    print_warning "Installing pytest and dependencies..."
    python -m pip install pytest pytest-django pytest-cov pytest-xdist pytest-mock
    
    if [[ $? -ne 0 ]]; then
        print_error "Failed to install pytest dependencies."
        exit 1
    fi
fi

PYTEST_VERSION=$(python -m pytest --version 2>/dev/null || echo "Unknown version")
print_success "pytest installed: $PYTEST_VERSION"

# Build pytest command
PYTEST_CMD="python -m pytest"

# Add test selection based on type
case $TEST_TYPE in
    "unit")
        PYTEST_CMD="$PYTEST_CMD -m unit"
        ;;
    "integration")
        PYTEST_CMD="$PYTEST_CMD -m integration"
        ;;
    "auth")
        PYTEST_CMD="$PYTEST_CMD -m auth"
        ;;
    "course")
        PYTEST_CMD="$PYTEST_CMD -m course"
        ;;
    "quiz")
        PYTEST_CMD="$PYTEST_CMD -m quiz"
        ;;
    "forum")
        PYTEST_CMD="$PYTEST_CMD -m forum"
        ;;
    "theme")
        PYTEST_CMD="$PYTEST_CMD -m theme"
        ;;
    "models")
        PYTEST_CMD="$PYTEST_CMD -m models"
        ;;
    "views")
        PYTEST_CMD="$PYTEST_CMD -m views"
        ;;
    "quick")
        PYTEST_CMD="$PYTEST_CMD -m 'not slow'"
        ;;
    "coverage")
        COVERAGE="true"
        PYTEST_CMD="$PYTEST_CMD --cov=blog --cov-report=html:htmlcov --cov-report=term-missing"
        ;;
    "all")
        # Run all tests - no additional markers needed
        ;;
esac

# Add verbose output if requested
if [[ "$VERBOSE" == "true" ]]; then
    PYTEST_CMD="$PYTEST_CMD -v -s"
fi

# Add parallel execution if requested
if [[ "$PARALLEL" == "true" ]]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
    print_info "Running tests in parallel..."
fi

# Add coverage if requested (and not already added)
if [[ "$COVERAGE" == "true" && "$TEST_TYPE" != "coverage" ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov=blog --cov-report=html:htmlcov --cov-report=term-missing"
fi

# Display command being run
print_info "Running: $PYTEST_CMD"
print_info "Test type: $TEST_TYPE"
echo ""

# Run the tests
START_TIME=$(date +%s)

if ! eval $PYTEST_CMD; then
    EXIT_CODE=$?
else
    EXIT_CODE=0
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
print_info "Test execution completed in ${DURATION} seconds"

# Report results
if [[ $EXIT_CODE -eq 0 ]]; then
    print_success "All tests passed!"
    
    if [[ "$COVERAGE" == "true" || "$TEST_TYPE" == "coverage" ]]; then
        print_info "Coverage report generated:"
        print_info "   HTML: htmlcov/index.html"
        print_info "   Terminal output above"
    fi
else
    print_error "Some tests failed (exit code: $EXIT_CODE)"
    print_warning "Tips:"
    print_warning "   - Check test output above for details"
    print_warning "   - Run with --verbose for more information"
    print_warning "   - Run specific test types to isolate issues"
fi

echo ""
print_color "$CYAN" "🎯 Available test commands:"
print_color "$CYAN" "   ./run_tests.sh auth --verbose     # Debug auth tests"
print_color "$CYAN" "   ./run_tests.sh coverage           # Full coverage report"
print_color "$CYAN" "   ./run_tests.sh quick              # Fast test run"
print_color "$CYAN" "   ./run_tests.sh --help             # Show all options"

exit $EXIT_CODE