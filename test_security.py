#!/usr/bin/env python
"""
Test script to demonstrate secure file upload validation
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from blog.validators import validate_assignment_file
from django.core.exceptions import ValidationError

def test_file_validation():
    """Test the file validation system with various file types"""
    
    print("🔒 FILE UPLOAD SECURITY VALIDATION TEST")
    print("=" * 50)
    
    # Test cases: (filename, content, should_pass, description)
    test_cases = [
        # SAFE FILES - Should pass
        ("hello.py", b"print('Hello World!')", True, "Python source code"),
        ("main.go", b"package main\nfunc main() {}", True, "Go source code"),
        ("lib.rs", b"fn main() { println!(\"Hello\"); }", True, "Rust source code"),
        ("app.js", b"console.log('Hello World');", True, "JavaScript code"),
        ("program.cpp", b"#include <iostream>\nint main() {}", True, "C++ source code"),
        ("README.md", b"# Project Title", True, "Markdown documentation"),
        ("notes.txt", b"This is a text file", True, "Plain text file"),
        
        # DANGEROUS FILES - Should fail
        ("virus.exe", b"MZ\x90\x00", False, "Windows executable"),
        ("script.bat", b"@echo off", False, "Batch script"),
        ("malware.sh", b"#!/bin/bash\nrm -rf /", False, "Shell script"),
        ("hack.ps1", b"Remove-Item", False, "PowerShell script"),
        ("", b"content", False, "Empty filename"),
        ("file", b"content", False, "No extension"),
    ]
    
    passed = 0
    failed = 0
    
    for filename, content, should_pass, description in test_cases:
        try:
            uploaded_file = SimpleUploadedFile(filename, content)
            validate_assignment_file(uploaded_file)
            
            if should_pass:
                print(f"✅ PASS: {description} ({filename})")
                passed += 1
            else:
                print(f"❌ FAIL: {description} ({filename}) - Should have been blocked!")
                failed += 1
                
        except ValidationError as e:
            if not should_pass:
                print(f"🛡️  BLOCK: {description} ({filename}) - {str(e)}")
                passed += 1
            else:
                print(f"❌ FAIL: {description} ({filename}) - Incorrectly blocked: {str(e)}")
                failed += 1
        except Exception as e:
            print(f"💥 ERROR: {description} ({filename}) - {str(e)}")
            failed += 1
    
    print(f"\n📊 Results: ✅ {passed} passed, ❌ {failed} failed")
    return failed == 0

if __name__ == "__main__":
    test_file_validation()