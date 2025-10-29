#!/bin/bash
# Bash Test Runner for Django LMS
# Run all tests for the my-first-blog Django project

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Django LMS Test Suite${NC}"
echo -e "${GREEN}=====================================${NC}\n"

# Set up environment
PROJECT_DIR="/c/Users/forti/Documents/GitHub/my-first-blog"
PYTHON_EXE="$PROJECT_DIR/venv/Scripts/python.exe"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

echo -e "${CYAN}📁 Working Directory: $PROJECT_DIR${NC}"
echo -e "${CYAN}🐍 Python Executable: $PYTHON_EXE${NC}\n"

# Function to run test and capture results
run_test() {
    local test_name="$1"
    local command="$2"
    local description="$3"
    
    echo -e "${YELLOW}🧪 Running: $test_name${NC}"
    echo -e "${GRAY}   Description: $description${NC}"
    echo -e "${GRAY}   Command: $command${NC}"
    
    start_time=$(date +%s.%N)
    
    # Execute the command and capture exit code
    eval "$command" >/dev/null 2>&1
    exit_code=$?
    
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc -l)
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}   ✅ PASSED${NC}"
        echo -e "${GRAY}   Duration: $(printf "%.2f" "$duration")s${NC}\n"
        return 0
    else
        echo -e "${RED}   ❌ FAILED (Exit Code: $exit_code)${NC}"
        echo -e "${GRAY}   Duration: $(printf "%.2f" "$duration")s${NC}\n"
        return 1
    fi
}

# Test results tracking
total_tests=0
passed_tests=0
test_results=()

echo -e "${MAGENTA}🔍 Pre-flight Checks${NC}"
echo -e "${MAGENTA}====================${NC}\n"

# Check if virtual environment exists
if [ ! -f "$PROJECT_DIR/venv/Scripts/python.exe" ]; then
    echo -e "${RED}❌ Virtual environment not found at $PROJECT_DIR/venv${NC}"
    echo -e "${YELLOW}Please create virtual environment first:${NC}"
    echo -e "${GRAY}   python -m venv venv${NC}"
    echo -e "${GRAY}   source venv/Scripts/activate${NC}"
    echo -e "${GRAY}   pip install -r requirements.txt${NC}\n"
    exit 1
fi

# Check Django installation
django_version=$("$PYTHON_EXE" -c "import django; print(f'Django {django.get_version()}')" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ $django_version detected${NC}"
else
    echo -e "${RED}❌ Django not found. Please install requirements:${NC}"
    echo -e "${GRAY}   pip install -r requirements.txt${NC}\n"
    exit 1
fi

# Check database
"$PYTHON_EXE" manage.py check --quiet 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database configuration OK${NC}\n"
else
    echo -e "${RED}❌ Database configuration issues detected${NC}"
    echo -e "${YELLOW}   Running migrations...${NC}\n"
    "$PYTHON_EXE" manage.py migrate --quiet
fi

echo -e "${MAGENTA}🧪 Django Test Suite${NC}"
echo -e "${MAGENTA}====================${NC}\n"

# 1. Django System Check
((total_tests++))
if run_test "System Check" "\"$PYTHON_EXE\" manage.py check --quiet" "Validate Django configuration and models"; then
    ((passed_tests++))
    test_results+=("System Check:PASS")
else
    test_results+=("System Check:FAIL")
fi

# 2. Database Migration Check
((total_tests++))
if run_test "Migration Check" "\"$PYTHON_EXE\" manage.py showmigrations --plan | grep -c blog" "Check database migrations"; then
    ((passed_tests++))
    test_results+=("Migration Check:PASS")
else
    test_results+=("Migration Check:FAIL")
fi

# 3. Recurring Events Tests
((total_tests++))
if run_test "Recurring Events Tests" "\"$PYTHON_EXE\" manage.py test tests.test_recurring_events --verbosity=1" "Test recurring events system"; then
    ((passed_tests++))
    test_results+=("Recurring Events Tests:PASS")
else
    test_results+=("Recurring Events Tests:FAIL")
fi

# 4. All Django Tests
((total_tests++))
if run_test "All Django Tests" "\"$PYTHON_EXE\" manage.py test --verbosity=1" "Run all Django application tests"; then
    ((passed_tests++))
    test_results+=("All Django Tests:PASS")
else
    test_results+=("All Django Tests:FAIL")
fi

# 5. EXIF Removal Tests
((total_tests++))
if run_test "EXIF Removal Tests" "\"$PYTHON_EXE\" manage.py test tests.test_exif_removal --verbosity=1" "Test EXIF metadata removal functionality"; then
    ((passed_tests++))
    test_results+=("EXIF Removal Tests:PASS")
else
    test_results+=("EXIF Removal Tests:FAIL")
fi

# 6. Image Processing Tests
((total_tests++))
if run_test "Image Processing Utils" "\"$PYTHON_EXE\" -c 'import django; django.setup(); from blog.utils.image_processing import is_image_file; print(\"Image utils OK\")'" "Test image processing utilities"; then
    ((passed_tests++))
    test_results+=("Image Processing Utils:PASS")
else
    test_results+=("Image Processing Utils:FAIL")
fi

# 7. Secure Storage Tests
((total_tests++))
if run_test "Secure Storage Backend" "\"$PYTHON_EXE\" -c 'import django; django.setup(); from blog.utils.storage import MediaStorage; s=MediaStorage(); print(\"Storage OK\")'" "Test secure image storage backend"; then
    ((passed_tests++))
    test_results+=("Secure Storage Backend:PASS")
else
    test_results+=("Secure Storage Backend:FAIL")
fi

# 8. EXIF Management Command
((total_tests++))
if run_test "EXIF Management Command" "\"$PYTHON_EXE\" manage.py process_exif_removal --dry-run --verbosity=0" "Test EXIF removal management command"; then
    ((passed_tests++))
    test_results+=("EXIF Management Command:PASS")
else
    test_results+=("EXIF Management Command:FAIL")
fi

# 9. Management Command Tests
((total_tests++))
if run_test "Management Commands" "\"$PYTHON_EXE\" manage.py generate_recurring_events --dry-run --verbosity=0" "Test custom Django management commands"; then
    ((passed_tests++))
    test_results+=("Management Commands:PASS")
else
    test_results+=("Management Commands:FAIL")
fi

# 10. Static Files Collection Test (if collectstatic works)
((total_tests++))
if run_test "Static Files" "\"$PYTHON_EXE\" manage.py collectstatic --noinput --verbosity=0" "Test static files collection"; then
    ((passed_tests++))
    test_results+=("Static Files:PASS")
else
    test_results+=("Static Files:FAIL")
fi

echo -e "${MAGENTA}🧪 Pytest Test Suite${NC}"
echo -e "${MAGENTA}===================${NC}\n"

# 11. Pytest Polling System Tests
((total_tests++))
if run_test "Polling System Tests (pytest)" "\"$PYTHON_EXE\" -m pytest tests/test_polling_system.py -v --tb=short" "Test Secret Chamber polling system with pytest"; then
    ((passed_tests++))
    test_results+=("Polling System Tests (pytest):PASS")
else
    test_results+=("Polling System Tests (pytest):FAIL")
fi

# 12. All Pytest Tests
((total_tests++))
if run_test "All Pytest Tests" "\"$PYTHON_EXE\" -m pytest tests/ -v --tb=short --disable-warnings" "Run all pytest tests"; then
    ((passed_tests++))
    test_results+=("All Pytest Tests:PASS")
else
    test_results+=("All Pytest Tests:FAIL")
fi

# 13. Pytest with Coverage
((total_tests++))
if run_test "Pytest Coverage Report" "\"$PYTHON_EXE\" -m pytest tests/test_polling_system.py --cov=blog.secret_chamber --cov-report=term-missing --tb=short" "Generate coverage report for polling system"; then
    ((passed_tests++))
    test_results+=("Pytest Coverage Report:PASS")
else
    test_results+=("Pytest Coverage Report:FAIL")
fi

echo -e "${GREEN}📊 Test Results Summary${NC}"
echo -e "${GREEN}======================${NC}\n"

# Display results table
for result in "${test_results[@]}"; do
    test_name=$(echo "$result" | cut -d: -f1)
    status=$(echo "$result" | cut -d: -f2)
    
    if [ "$status" = "PASS" ]; then
        printf "   %-25s ${GREEN}✅ PASS${NC}\n" "$test_name"
    else
        printf "   %-25s ${RED}❌ FAIL${NC}\n" "$test_name"
    fi
done

echo ""
percentage=$(echo "scale=1; ($passed_tests / $total_tests) * 100" | bc -l)
echo -e "${CYAN}📈 Overall Results:${NC}"

if [ "$passed_tests" -eq "$total_tests" ]; then
    echo -e "   ${GREEN}Passed: $passed_tests/$total_tests (${percentage}%)${NC}"
    echo ""
    echo -e "${GREEN}🎉 ALL TESTS PASSED! 🎉${NC}"
    echo -e "${GREEN}Your Django LMS is working perfectly!${NC}"
    exit 0
else
    failed_tests=$((total_tests - passed_tests))
    echo -e "   ${YELLOW}Passed: $passed_tests/$total_tests (${percentage}%)${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  $failed_tests TEST(S) FAILED${NC}"
    echo -e "${YELLOW}Please review the failed tests above and fix any issues.${NC}"
    exit 1
fi

echo -e "\n${GREEN}🏁 Test Suite Completed${NC}"