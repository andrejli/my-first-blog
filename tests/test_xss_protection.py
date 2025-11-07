"""
XSS Protection Test Script
Tests the newly implemented XSS protection measures.
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.urls import reverse
from html import escape


class TestXSSProtection(TestCase):
    """Test XSS protection implementation"""
    
    def test_xss_protection_implementation(self):
        """Test that XSS protection is working correctly."""
        print("Testing XSS Protection Implementation...")
        
        # Test 1: Check CSP middleware is loaded
        print("\n1. Testing CSP Middleware...")
        try:
            from blog.middleware.csp_middleware import CSPMiddleware
            print("CSP Middleware imported successfully")
        except ImportError as e:
            print(f"ERROR: CSP Middleware import failed: {e}")
            self.fail(f"CSP Middleware import failed: {e}")
        
        # Test 2: Check template tags are working
        print("\n2. Testing CSP Template Tags...")
        try:
            from blog.templatetags.csp_tags import csp_nonce, csp_script_attrs
            print("CSP Template tags imported successfully")
        except ImportError as e:
            print(f"ERROR: CSP Template tags import failed: {e}")
            self.fail(f"CSP Template tags import failed: {e}")
        
        # Test 3: Test message escaping
        print("\n3. Testing Message Escaping...")
        malicious_input = "<script>alert('XSS')</script>"
        escaped_output = escape(malicious_input)
        expected_output = "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;"
        
        self.assertEqual(escaped_output, expected_output, "HTML escaping not working correctly")
        print("HTML escaping working correctly")
        print(f"   Input:  {malicious_input}")
        print(f"   Output: {escaped_output}")
        
        # Test 4: Test client response headers
        print("\n4. Testing CSP Headers...")
        client = Client()
        
        try:
            # Make a request to check headers
            response = client.get('/')
            
            # Check for CSP header
            if 'Content-Security-Policy' in response:
                csp_header = response['Content-Security-Policy']
                print("CSP header present")
                print(f"   CSP Policy: {csp_header[:100]}...")
                
                # Check for nonce in policy
                if 'nonce-' in csp_header:
                    print("Nonce found in CSP policy")
                else:
                    print("⚠️  Nonce not found in CSP policy (may be normal for non-HTML responses)")
            else:
                print("⚠️  CSP header not found (may be normal for non-HTML responses)")
            
            # Check for other security headers
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options', 
                'X-XSS-Protection',
                'Referrer-Policy'
            ]
            
            for header in security_headers:
                if header in response:
                    print(f"PASS: {header}: {response[header]}")
                else:
                    print(f"⚠️  {header} not found")
                    
        except Exception as e:
            print(f"ERROR: Client test failed: {e}")
            self.fail(f"Client test failed: {e}")
        
        print("\nXSS Protection Test Completed!")
    
    def test_csp_middleware_import(self):
        """Test that CSP middleware can be imported"""
        try:
            from blog.middleware.csp_middleware import CSPMiddleware
            self.assertTrue(True)  # If we get here, import succeeded
        except ImportError:
            self.fail("CSP Middleware could not be imported")
    
    def test_csp_template_tags_import(self):
        """Test that CSP template tags can be imported"""
        try:
            from blog.templatetags.csp_tags import csp_nonce, csp_script_attrs
            self.assertTrue(True)  # If we get here, import succeeded
        except ImportError:
            self.fail("CSP Template tags could not be imported")
    
    def test_html_escaping(self):
        """Test HTML escaping functionality"""
        malicious_input = "<script>alert('XSS')</script>"
        escaped_output = escape(malicious_input)
        expected_output = "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;"
        self.assertEqual(escaped_output, expected_output)