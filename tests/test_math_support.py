#!/usr/bin/env python
"""
Test script to verify math equation support works without markdown-math package
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

from blog.templatetags.markdown_extras import obsidian_markdown

def test_math_rendering():
    """Test that math equations are preserved for MathJax rendering"""
    
    test_content = """
# Math Test

Inline math: $E = mc^2$ and $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$

Display math:
$$\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$$

Complex equation:
$$\\sum_{n=1}^\\infty \\frac{1}{n^2} = \\frac{\\pi^2}{6}$$

Regular text with **bold** and *italic* formatting.
"""
    
    print("🧪 Testing Math Equation Support")
    print("=" * 50)
    
    # Process the content through our markdown system
    result = obsidian_markdown(test_content)
    
    print("Input content:")
    print(test_content)
    print("\nProcessed HTML:")
    print(result)
    
    # Check that math delimiters are preserved
    math_checks = [
        ('$E = mc^2$' in result, "Inline math preserved"),
        ('$$\\int_0^\\infty' in result, "Display math preserved"),
        ('<strong>bold</strong>' in result, "Markdown formatting works"),
        ('<em>italic</em>' in result, "Italic formatting works")
    ]
    
    print("\n🔍 Math Preservation Checks:")
    for check, description in math_checks:
        status = "✅" if check else "❌"
        print(f"{status} {description}")
    
    print("\n📝 Note: Math rendering happens in the browser via MathJax")
    print("Server-side markdown processing preserves math syntax for frontend rendering")

if __name__ == "__main__":
    test_math_rendering()