"""
CLI Browser Detection and Utilities

This module provides utilities for detecting CLI/text-based browsers and
serving appropriate content for optimal CLI browser compatibility.
"""

import re
from django.utils.safestring import mark_safe


def is_cli_browser(request):
    """
    Detect if the request is coming from a CLI/text-based browser.
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        bool: True if CLI browser detected, False otherwise
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    # Known CLI browsers
    cli_browsers = [
        'links',      # Links/Links2
        'w3m',        # w3m
        'elinks',     # ELinks
        'lynx',       # Lynx
        'curl',       # curl (for API access)
        'wget',       # wget
        'httpie',     # HTTPie
        'text',       # Generic text browsers
        'console',    # Console browsers
        'terminal'    # Terminal browsers
    ]
    
    # Check for CLI browser patterns
    for browser in cli_browsers:
        if browser in user_agent:
            return True
    
    # Additional pattern checks for less common CLI browsers
    cli_patterns = [
        r'text/html',           # Text-only browsers
        r'console',             # Console applications
        r'command[\s\-]?line',  # Command line tools
        r'terminal',            # Terminal applications
    ]
    
    for pattern in cli_patterns:
        if re.search(pattern, user_agent):
            return True
    
    return False


def get_browser_type(request):
    """
    Get detailed browser type information.
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        dict: Browser information including type, name, and CLI status
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    browser_info = {
        'is_cli': False,
        'name': 'Unknown',
        'type': 'graphical',
        'supports_js': True,
        'supports_css': True,
        'user_agent': user_agent
    }
    
    # Check for specific CLI browsers
    cli_browser_map = {
        'links': {'name': 'Links', 'supports_css': False, 'supports_js': False},
        'w3m': {'name': 'w3m', 'supports_css': False, 'supports_js': False},
        'elinks': {'name': 'ELinks', 'supports_css': True, 'supports_js': False},
        'lynx': {'name': 'Lynx', 'supports_css': False, 'supports_js': False},
        'curl': {'name': 'cURL', 'supports_css': False, 'supports_js': False},
        'wget': {'name': 'wget', 'supports_css': False, 'supports_js': False},
    }
    
    for browser_key, browser_props in cli_browser_map.items():
        if browser_key in user_agent:
            browser_info.update({
                'is_cli': True,
                'type': 'cli',
                'name': browser_props['name'],
                'supports_css': browser_props['supports_css'],
                'supports_js': browser_props['supports_js']
            })
            break
    
    return browser_info


def cli_friendly_content(cli_content, regular_content=""):
    """
    Return CLI-friendly content when appropriate.
    
    Args:
        cli_content: Content optimized for CLI browsers
        regular_content: Content for regular browsers (optional)
        
    Returns:
        str: Marked safe HTML content
    """
    if regular_content:
        # Return both with noscript wrapper for CLI content
        content = f"""
        <noscript>
        <div class="cli-content" style="background-color: #f8f9fa; padding: 10px; margin: 10px 0; border: 1px solid #dee2e6; border-radius: 4px;">
            {cli_content}
        </div>
        </noscript>
        {regular_content}
        """
    else:
        # Return just CLI content
        content = f"""
        <div class="cli-content" style="background-color: #f8f9fa; padding: 10px; margin: 10px 0; border: 1px solid #dee2e6; border-radius: 4px;">
            {cli_content}
        </div>
        """
    
    return mark_safe(content)


def progress_text_summary(completed, total, label="Progress"):
    """
    Generate text-based progress summary for CLI browsers.
    
    Args:
        completed: Number of completed items
        total: Total number of items
        label: Label for the progress type
        
    Returns:
        str: Text progress summary
    """
    if total == 0:
        percentage = 0
    else:
        percentage = int((completed / total) * 100)
    
    # Visual progress indicator using ASCII
    progress_bars = int(percentage / 10)
    progress_visual = "█" * progress_bars + "░" * (10 - progress_bars)
    
    status_emoji = "✅" if percentage == 100 else "🔄" if percentage > 0 else "📚"
    
    return f"""
    <strong>{label} Summary:</strong><br>
    {status_emoji} {completed} of {total} completed ({percentage}%)<br>
    Progress: [{progress_visual}] {percentage}%
    """


def statistics_summary(stats_dict):
    """
    Generate text-based statistics summary for CLI browsers.
    
    Args:
        stats_dict: Dictionary with statistic labels and values
        
    Returns:
        str: Formatted statistics summary
    """
    summary_lines = ["<strong>Statistics Summary:</strong>"]
    
    for label, value in stats_dict.items():
        summary_lines.append(f"• {label}: {value}")
    
    return "<br>".join(summary_lines)


def format_cli_navigation(nav_items):
    """
    Format navigation items for CLI browsers.
    
    Args:
        nav_items: List of tuples (url, label, description)
        
    Returns:
        str: Formatted navigation HTML
    """
    nav_html = ["<strong>Navigation:</strong>", "<ul style='list-style-type: none; padding: 0;'>"]
    
    for url, label, description in nav_items:
        nav_html.append(
            f"<li style='margin: 5px 0;'>"
            f"<a href='{url}'>[{label.upper()}]</a> - {description}"
            f"</li>"
        )
    
    nav_html.append("</ul>")
    return "".join(nav_html)


# Template context processor to add CLI browser detection to all templates
def cli_browser_context(request):
    """
    Template context processor that adds CLI browser information to all templates.
    
    Usage:
        Add 'blog.utils.cli_browser.cli_browser_context' to TEMPLATES['OPTIONS']['context_processors']
    """
    return {
        'is_cli_browser': is_cli_browser(request),
        'browser_info': get_browser_type(request)
    }