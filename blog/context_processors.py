"""
Context processors for the blog app
Provides global template variables across all pages
"""

from .models import SiteTheme, UserThemePreference


def theme_context(request):
    """
    Add user's theme preference to template context
    This prevents theme flashing by making theme available immediately
    """
    theme_key = 'terminal-amber'  # Default fallback
    
    if request.user.is_authenticated:
        try:
            # Get user's saved theme preference
            user_preference = UserThemePreference.objects.select_related('theme').get(
                user=request.user
            )
            if user_preference.theme and user_preference.theme.is_active:
                theme_key = user_preference.theme.theme_key
        except UserThemePreference.DoesNotExist:
            # If no preference, try to get default theme
            try:
                default_theme = SiteTheme.objects.get(is_default=True, is_active=True)
                theme_key = default_theme.theme_key
            except SiteTheme.DoesNotExist:
                pass  # Use fallback
    else:
        # For anonymous users, try to get from localStorage via cookie fallback
        theme_from_cookie = request.COOKIES.get('theme_preference', '')
        if theme_from_cookie and SiteTheme.objects.filter(
            theme_key=theme_from_cookie, 
            is_active=True
        ).exists():
            theme_key = theme_from_cookie
    
    return {
        'user_theme': theme_key
    }


def available_themes_context(request):
    """
    Add available themes to template context for theme switcher
    """
    themes = SiteTheme.objects.filter(is_active=True).order_by('display_name')
    theme_choices = [(theme.theme_key, theme.display_name) for theme in themes]
    
    return {
        'available_themes': theme_choices
    }