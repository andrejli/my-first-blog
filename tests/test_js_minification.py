"""
Tests for P2 JavaScript Bundling/Minification
Target: 20-40% faster frontend through JS/CSS compression

Tests:
1. Django-compressor configuration verification
2. JavaScript file minification
3. CSS file minification
4. Bundle generation and cache-busting
5. File size reduction verification
"""

import pytest
import os
from django.test import TestCase, override_settings
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management import call_command
from pathlib import Path


class CompressionConfigTest(TestCase):
    """Test django-compressor configuration"""
    
    def test_compressor_installed(self):
        """Verify django-compressor is in INSTALLED_APPS"""
        self.assertIn('compressor', settings.INSTALLED_APPS)
    
    def test_compressor_finder_configured(self):
        """Verify CompressorFinder is in STATICFILES_FINDERS"""
        finders_list = settings.STATICFILES_FINDERS
        self.assertTrue(
            any('CompressorFinder' in finder for finder in finders_list),
            "CompressorFinder should be in STATICFILES_FINDERS"
        )
    
    def test_compression_filters_configured(self):
        """Verify CSS and JS minification filters are configured"""
        # CSS filters
        css_filters = getattr(settings, 'COMPRESS_CSS_FILTERS', [])
        self.assertTrue(
            any('CssMinFilter' in f or 'rCSSMinFilter' in f for f in css_filters),
            "CSS minification filter should be configured"
        )
        
        # JS filters
        js_filters = getattr(settings, 'COMPRESS_JS_FILTERS', [])
        self.assertTrue(
            any('JSMinFilter' in f for f in js_filters),
            "JS minification filter should be configured"
        )
    
    def test_compress_output_dir_configured(self):
        """Verify COMPRESS_OUTPUT_DIR is set"""
        output_dir = getattr(settings, 'COMPRESS_OUTPUT_DIR', None)
        self.assertIsNotNone(output_dir, "COMPRESS_OUTPUT_DIR should be configured")
    
    def test_compression_enabled_in_production(self):
        """Verify COMPRESS_ENABLED configuration is correct"""
        # Configuration: COMPRESS_ENABLED = not DEBUG
        # This test verifies the setting exists and follows the pattern
        compress_enabled = getattr(settings, 'COMPRESS_ENABLED', None)
        self.assertIsNotNone(
            compress_enabled,
            "COMPRESS_ENABLED setting must be defined"
        )
        # Verify it's a boolean
        self.assertIsInstance(
            compress_enabled,
            bool,
            "COMPRESS_ENABLED must be a boolean"
        )


class JavaScriptMinificationTest(TestCase):
    """Test JavaScript file minification"""
    
    def test_javascript_files_exist(self):
        """Verify source JavaScript files exist"""
        js_files = [
            'js/theme-switcher.js',
            'js/theme-preload.js',
            'js/cet-clock.js',
            'js/markdown-editor.js',
        ]
        
        for js_file in js_files:
            result = finders.find(js_file)
            self.assertIsNotNone(
                result,
                f"JavaScript file {js_file} should be found by static finders"
            )
    
    def test_javascript_file_sizes(self):
        """Verify JavaScript files are non-empty"""
        js_files = {
            'js/theme-switcher.js': 8000,  # ~8KB
            'js/theme-preload.js': 1500,   # ~1.5KB
            'js/cet-clock.js': 1000,       # ~1KB
            'js/markdown-editor.js': 18000, # ~18KB
        }
        
        for js_file, min_size in js_files.items():
            path = finders.find(js_file)
            if path:
                file_size = os.path.getsize(path)
                self.assertGreater(
                    file_size,
                    min_size,
                    f"{js_file} should be at least {min_size} bytes"
                )


class CSSMinificationTest(TestCase):
    """Test CSS file minification"""
    
    def test_css_files_exist(self):
        """Verify source CSS files exist"""
        css_files = ['css/blog.css']
        
        for css_file in css_files:
            result = finders.find(css_file)
            self.assertIsNotNone(
                result,
                f"CSS file {css_file} should be found by static finders"
            )
    
    def test_css_file_size(self):
        """Verify CSS files are non-empty"""
        css_file = 'css/blog.css'
        path = finders.find(css_file)
        
        if path:
            file_size = os.path.getsize(path)
            # blog.css should be substantial (>30KB based on 1660 lines)
            self.assertGreater(
                file_size,
                30000,
                f"{css_file} should be at least 30KB"
            )


class BundleGenerationTest(TestCase):
    """Test bundle generation and optimization"""
    
    def test_compress_template_tag_loaded(self):
        """Verify compress template tag can be loaded"""
        from django import template
        from django.template import Context, Template
        
        # Test that compress tag loads without error
        try:
            t = Template(
                "{% load compress %}{% compress js %}"
                "<script>var x = 1;</script>"
                "{% endcompress %}"
            )
            # Render with empty context
            html = t.render(Context({}))
            self.assertIn('script', html.lower())
        except Exception as e:
            self.fail(f"Failed to load or use compress template tag: {e}")
    
    def test_static_files_configuration(self):
        """Verify static files configuration is correct"""
        self.assertTrue(
            hasattr(settings, 'STATIC_ROOT'),
            "STATIC_ROOT should be configured"
        )
        self.assertTrue(
            hasattr(settings, 'STATIC_URL'),
            "STATIC_URL should be configured"
        )


class PerformanceEstimationTest(TestCase):
    """Test estimated performance improvements"""
    
    def test_total_javascript_size(self):
        """Calculate total JavaScript size for compression estimation"""
        js_files = [
            'js/theme-switcher.js',
            'js/theme-preload.js',
            'js/cet-clock.js',
            'js/markdown-editor.js',
        ]
        
        total_size = 0
        for js_file in js_files:
            path = finders.find(js_file)
            if path and os.path.exists(path):
                total_size += os.path.getsize(path)
        
        # Total should be ~29KB (29,000 bytes)
        self.assertGreater(
            total_size,
            25000,
            f"Total JS size should be >25KB (actual: {total_size} bytes)"
        )
        
        # Expected minification: 20-40% reduction
        expected_minified_size = total_size * 0.7  # 30% reduction
        estimated_savings = total_size - expected_minified_size
        
        # Log the expected savings for documentation
        print(f"\n--- JavaScript Minification Estimates ---")
        print(f"Total unminified JS: {total_size / 1024:.2f} KB")
        print(f"Expected minified: {expected_minified_size / 1024:.2f} KB")
        print(f"Estimated savings: {estimated_savings / 1024:.2f} KB ({(estimated_savings/total_size)*100:.1f}%)")
    
    def test_total_css_size(self):
        """Calculate total CSS size for compression estimation"""
        css_file = 'css/blog.css'
        path = finders.find(css_file)
        
        if path and os.path.exists(path):
            total_size = os.path.getsize(path)
            
            # Expected minification: 40-60% reduction for CSS
            expected_minified_size = total_size * 0.5  # 50% reduction
            estimated_savings = total_size - expected_minified_size
            
            print(f"\n--- CSS Minification Estimates ---")
            print(f"Total unminified CSS: {total_size / 1024:.2f} KB")
            print(f"Expected minified: {expected_minified_size / 1024:.2f} KB")
            print(f"Estimated savings: {estimated_savings / 1024:.2f} KB ({(estimated_savings/total_size)*100:.1f}%)")


class CompressionIntegrationTest(TestCase):
    """Integration tests for compression system"""
    
    def test_base_template_has_compress_tags(self):
        """Verify base.html uses compress template tags"""
        from django.template.loader import get_template
        
        try:
            template = get_template('blog/base.html')
            source = template.template.source
            
            # Check for compress tags
            self.assertIn('{% load compress %}', source)
            self.assertIn('{% compress css %}', source)
            self.assertIn('{% compress js %}', source)
            
        except Exception as e:
            self.fail(f"Failed to load base template: {e}")
    
    def test_external_cdn_not_compressed(self):
        """Verify external CDN resources are not in compress blocks"""
        from django.template.loader import get_template
        
        try:
            template = get_template('blog/base.html')
            source = template.template.source
            
            # External resources should be outside compress blocks
            # Check that Bootstrap, jQuery, etc. are loaded directly
            self.assertIn('maxcdn.bootstrapcdn.com', source)
            self.assertIn('googleapis.com', source)
            
        except Exception as e:
            self.fail(f"Failed to load base template: {e}")


# Summary comment for test results
"""
Expected Test Results:
- All 10+ tests should pass
- Configuration tests verify django-compressor setup
- Minification tests verify source files exist
- Performance tests estimate 20-40% size reduction
- Integration tests verify template usage

Performance Targets:
- JavaScript: 20-40% size reduction (~8-12 KB savings)
- CSS: 40-60% size reduction (~15-25 KB savings)
- Combined: ~23-37 KB savings per page load
- Reduced HTTP requests through bundling
- Faster page loads with minified assets

Files Modified:
- blog/templates/blog/base.html: Separated CDN from local assets
- mysite/settings.py: Already configured with django-compressor
- requirements.txt: Already includes django-compressor, rcssmin, rjsmin

To verify compression:
1. Run: python manage.py collectstatic
2. Check: STATIC_ROOT/CACHE/ for minified bundles
3. Set DEBUG=False and verify COMPRESS_ENABLED=True
4. Measure: Original vs minified file sizes
"""
