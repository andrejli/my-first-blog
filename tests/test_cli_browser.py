#!/usr/bin/env python
"""
Quick test script for CLI browser detection functionality
"""
import os
import sys
import django

# Add project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from blog.utils.cli_browser import is_cli_browser, get_browser_type
from blog.templatetags.cli_browser_tags import cli_progress_bar, cli_status_emoji

class MockRequest:
    def __init__(self, user_agent):
        self.META = {'HTTP_USER_AGENT': user_agent}

def test_cli_detection():
    """Test CLI browser detection with various user agents"""
    
    test_cases = [
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Chrome", False),
        ("Links (2.25; Linux 5.4.0-74-generic x86_64)", "Links2", True),
        ("w3m/0.5.3+git20210102", "w3m", True),
        ("ELinks/0.12pre6 (textmode; Linux 5.4.0-74-generic x86_64)", "ELinks", True),
        ("Lynx/2.8.9rel.1 libwww-FM/2.14 SSL-MM/1.4.1", "Lynx", True),
        ("curl/7.68.0", "curl", True),
    ]
    
    print("🧪 CLI Browser Detection Test Results:")
    print("=" * 60)
    
    for user_agent, expected_name, should_be_cli in test_cases:
        request = MockRequest(user_agent)
        is_cli = is_cli_browser(request)
        browser_info = get_browser_type(request)
        
        status = "✅" if is_cli == should_be_cli else "❌"
        
        print(f"{status} {expected_name}:")
        print(f"   User Agent: {user_agent[:50]}...")
        print(f"   Detected CLI: {is_cli}")
        print(f"   Browser Name: {browser_info['name']}")
        print(f"   CSS Support: {browser_info['supports_css']}")
        print(f"   JS Support: {browser_info['supports_js']}")
        print()

def test_template_helpers():
    """Test template helper functions"""
    
    print("🎨 Template Helper Test Results:")
    print("=" * 60)
    
    # Test progress bars
    for percentage in [0, 25, 50, 75, 100]:
        progress_bar = cli_progress_bar(percentage)
        status_emoji = cli_status_emoji(percentage)
        print(f"Progress {percentage}%: {progress_bar} {status_emoji}")
    
    print()

if __name__ == "__main__":
    test_cli_detection()
    test_template_helpers()
    print("🎉 All tests completed!")