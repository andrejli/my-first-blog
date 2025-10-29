#!/usr/bin/env python
"""
Polling System Test Runner
Specifically tests the Secret Chamber admin polling functionality
"""
import os
import sys
import subprocess
import django
from django.conf import settings
from django.test.utils import get_runner


def run_polling_tests():
    """Run all polling system tests"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    django.setup()
    
    print("🗳️  Secret Chamber Polling System Test Suite")
    print("=" * 50)
    print()
    
    # List of specific test modules/classes to run
    test_targets = [
        # Model tests
        'tests/test_polling_system.py::TestAdminPollModel',
        'tests/test_polling_system.py::TestPollOptionModel', 
        'tests/test_polling_system.py::TestAdminVoteModel',
        
        # View tests
        'tests/test_polling_system.py::TestPollingViews',
        
        # Security tests
        'tests/test_polling_system.py::TestPollingSecurityFeatures',
        
        # Integration tests
        'tests/test_polling_system.py::TestPollingIntegration',
        
        # Performance tests (marked as slow)
        'tests/test_polling_system.py::TestPollingPerformance',
    ]
    
    all_passed = True
    results = {}
    
    for test_target in test_targets:
        print(f"🧪 Running: {test_target.split('::')[-1]}")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            test_target,
            '-v',
            '--tb=short',
            '--disable-warnings',
            '--cov=blog.secret_chamber',
            '--cov-append',
            '--cov-report=term-missing:skip-covered'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                print("   ✅ PASSED")
                results[test_target] = "PASSED"
            else:
                print("   ❌ FAILED")
                print(f"   Error output: {result.stderr[:200]}...")
                results[test_target] = "FAILED"
                all_passed = False
                
        except Exception as e:
            print(f"   💥 ERROR: {e}")
            results[test_target] = "ERROR"
            all_passed = False
        
        print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 50)
    
    for test_target, status in results.items():
        test_name = test_target.split('::')[-1]
        status_icon = "✅" if status == "PASSED" else "❌"
        print(f"   {status_icon} {test_name:<30} {status}")
    
    print()
    
    if all_passed:
        print("🎉 ALL POLLING TESTS PASSED!")
        print("Your Secret Chamber polling system is working perfectly!")
        return 0
    else:
        failed_count = sum(1 for status in results.values() if status != "PASSED")
        print(f"⚠️  {failed_count} test(s) failed")
        print("Please review the failed tests and fix any issues.")
        return 1


def run_specific_test(test_name):
    """Run a specific test by name"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    django.setup()
    
    cmd = [
        sys.executable, '-m', 'pytest',
        f'tests/test_polling_system.py::{test_name}',
        '-v',
        '--tb=long',
        '--cov=blog.secret_chamber',
        '--cov-report=term-missing'
    ]
    
    return subprocess.run(cmd).returncode


def run_coverage_report():
    """Generate detailed coverage report for polling system"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/test_polling_system.py',
        '--cov=blog.secret_chamber',
        '--cov-report=html:htmlcov/polling',
        '--cov-report=term-missing',
        '--cov-report=xml:coverage_polling.xml',
        '-v'
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n📈 Coverage report generated!")
        print("   HTML report: htmlcov/polling/index.html")
        print("   XML report: coverage_polling.xml")
    
    return result.returncode


if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'coverage':
            sys.exit(run_coverage_report())
        elif command.startswith('test:'):
            test_name = command.split(':', 1)[1]
            sys.exit(run_specific_test(test_name))
        else:
            print("Usage:")
            print("  python test_polling.py                    # Run all polling tests")
            print("  python test_polling.py coverage          # Generate coverage report")
            print("  python test_polling.py test:TestName     # Run specific test")
            sys.exit(1)
    else:
        sys.exit(run_polling_tests())