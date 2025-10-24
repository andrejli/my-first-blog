"""
Template tags for CLI browser compatibility
"""

from django import template
from blog.utils.cli_browser import (
    is_cli_browser, 
    get_browser_type,
    cli_friendly_content,
    progress_text_summary,
    statistics_summary,
    format_cli_navigation
)

register = template.Library()


@register.simple_tag(takes_context=True)
def cli_browser_check(context):
    """
    Check if the current request is from a CLI browser.
    
    Usage: {% cli_browser_check as is_cli %}
    """
    request = context['request']
    return is_cli_browser(request)


@register.simple_tag(takes_context=True)
def browser_info(context):
    """
    Get detailed browser information.
    
    Usage: {% browser_info as browser %}
    """
    request = context['request']
    return get_browser_type(request)


@register.simple_tag
def cli_content(cli_text, regular_text=""):
    """
    Generate CLI-friendly content with noscript wrapper.
    
    Usage: {% cli_content "CLI version" "Regular version" %}
    """
    return cli_friendly_content(cli_text, regular_text)


@register.simple_tag
def progress_summary(completed, total, label="Progress"):
    """
    Generate text progress summary for CLI browsers.
    
    Usage: {% progress_summary completed_count total_count "Course Progress" %}
    """
    return progress_text_summary(completed, total, label)


@register.simple_tag
def stats_summary(stats_dict):
    """
    Generate statistics summary for CLI browsers.
    
    Usage: {% stats_summary course_stats %}
    """
    return statistics_summary(stats_dict)


@register.simple_tag
def cli_navigation(nav_items):
    """
    Format navigation for CLI browsers.
    
    Usage: {% cli_navigation navigation_items %}
    """
    return format_cli_navigation(nav_items)


@register.inclusion_tag('blog/cli_browser_info.html', takes_context=True)
def cli_browser_info(context):
    """
    Include CLI browser information widget.
    
    Usage: {% cli_browser_info %}
    """
    request = context['request']
    return {
        'is_cli': is_cli_browser(request),
        'browser': get_browser_type(request)
    }


@register.filter
def cli_progress_bar(percentage):
    """
    Generate ASCII progress bar for CLI browsers.
    
    Usage: {{ progress_percentage|cli_progress_bar }}
    """
    percentage = int(percentage)
    bars = int(percentage / 10)
    return "█" * bars + "░" * (10 - bars) + f" {percentage}%"


@register.filter
def cli_status_emoji(percentage):
    """
    Get status emoji for CLI browsers based on percentage.
    
    Usage: {{ progress_percentage|cli_status_emoji }}
    """
    percentage = int(percentage)
    if percentage == 100:
        return "✅"
    elif percentage > 0:
        return "🔄"
    else:
        return "📚"