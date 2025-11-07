"""
Template tags for Content Security Policy (CSP) nonce support.
Provides easy access to CSP nonce in templates for inline scripts.
"""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def csp_nonce(context):
    """
    Return the CSP nonce for the current request.
    Usage in templates: {% csp_nonce %}
    """
    request = context.get('request')
    if request:
        return getattr(request, 'csp_nonce', '')
    return ''


@register.inclusion_tag('blog/security/csp_script_tag.html', takes_context=True)
def csp_script(context, content=''):
    """
    Render a script tag with CSP nonce.
    Usage: {% csp_script %}...javascript code...{% endcsp_script %}
    """
    request = context.get('request')
    nonce = ''
    if request:
        nonce = getattr(request, 'csp_nonce', '')
    
    return {
        'nonce': nonce,
        'content': content
    }


@register.simple_tag(takes_context=True)
def csp_script_attrs(context):
    """
    Return the nonce attribute for script tags.
    Usage: <script {% csp_script_attrs %}>...javascript...</script>
    """
    request = context.get('request')
    if request:
        nonce = getattr(request, 'csp_nonce', '')
        if nonce:
            return f'nonce="{nonce}"'
    return ''