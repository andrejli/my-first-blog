"""
Utility Views
-------------
Theme management, debugging utilities, and other helper views.
"""

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from blog.models import SiteTheme, UserThemePreference


# =============================================================================
# THEME MANAGEMENT VIEWS
# =============================================================================

def get_user_theme(request):
    """Get current user's theme preference"""
    if request.user.is_authenticated:
        try:
            user_preference = UserThemePreference.objects.get(user=request.user)
            theme_key = user_preference.theme.theme_key
        except UserThemePreference.DoesNotExist:
            # Get default theme
            try:
                default_theme = SiteTheme.objects.get(is_default=True, is_active=True)
                theme_key = default_theme.theme_key
            except SiteTheme.DoesNotExist:
                theme_key = 'terminal-amber'  # fallback
    else:
        # For anonymous users, check cookie first, then default
        theme_key = request.COOKIES.get('theme_preference', '')
        if not theme_key or not SiteTheme.objects.filter(theme_key=theme_key, is_active=True).exists():
            try:
                default_theme = SiteTheme.objects.get(is_default=True, is_active=True)
                theme_key = default_theme.theme_key
            except SiteTheme.DoesNotExist:
                theme_key = 'terminal-amber'  # fallback
    
    return JsonResponse({'theme': theme_key})


def set_user_theme(request):
    """Set user's theme preference"""
    if request.method == 'POST':
        theme_key = request.POST.get('theme')
        
        try:
            # Validate theme exists and is active
            theme = SiteTheme.objects.get(theme_key=theme_key, is_active=True)
            
            response = JsonResponse({'success': True, 'theme': theme_key})
            
            if request.user.is_authenticated:
                # Create or update user preference for authenticated users
                user_preference, created = UserThemePreference.objects.get_or_create(
                    user=request.user,
                    defaults={'theme': theme}
                )
                
                if not created:
                    user_preference.theme = theme
                    user_preference.save()
            
            # Always set cookie for immediate persistence and anonymous users
            response.set_cookie(
                'theme_preference', 
                theme_key, 
                max_age=365*24*60*60,  # 1 year
                httponly=False,  # Allow JavaScript access
                samesite='Lax'
            )
            
            return response
            
        except SiteTheme.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid theme'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def list_themes(request):
    """API endpoint to list all available themes"""
    themes = SiteTheme.objects.filter(is_active=True).values(
        'id', 'name', 'display_name', 'theme_key', 'description', 'is_default'
    )
    return JsonResponse(list(themes), safe=False)


# =============================================================================
# DEBUG AND DEVELOPMENT VIEWS
# =============================================================================

def theme_debug_view(request):
    """Debug view to test theme system"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LMS Theme Test</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 40px; 
                background: #000; 
                color: #ffb000;
                padding: 20px;
            }
            .info { 
                background: rgba(255,255,255,0.1); 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 5px; 
            }
            button { 
                padding: 10px 15px; 
                margin: 5px; 
                background: #333; 
                color: #ffb000; 
                border: 1px solid #555; 
                cursor: pointer; 
            }
            [data-theme="dark-blue"] body { background: #1a1a2e; color: #00d4ff; }
            [data-theme="light"] body { background: #f5f5f5; color: #333; }
            [data-theme="cyberpunk"] body { background: linear-gradient(45deg, #0f0f23, #1a0033); color: #ff00ff; }
            [data-theme="matrix"] body { background: #000; color: #00ff00; }
        </style>
    </head>
    <body>
        <h1>🎨 LMS Theme System Test</h1>
        
        <div class="info">
            <h3>Current User: {user}</h3>
            <h3>Server Theme: {theme}</h3>
            <h3>Cookie Theme: {cookie}</h3>
        </div>
        
        <div>
            <h3>Test Theme APIs:</h3>
            <button onclick="testGetTheme()">Get Theme</button>
            <button onclick="testSetTheme('dark-blue')">Set Dark Blue</button>
            <button onclick="testSetTheme('light')">Set Light</button>
            <button onclick="testSetTheme('terminal-amber')">Set Terminal</button>
        </div>
        
        <div class="info" id="results">
            <h3>API Results will appear here...</h3>
        </div>
        
        <script>
            async function testGetTheme() {{
                try {{
                    const response = await fetch('/api/theme/get/');
                    const data = await response.json();
                    document.getElementById('results').innerHTML = 
                        '<h3>✅ Get Theme Result:</h3><pre>' + JSON.stringify(data, null, 2) + '</pre>';
                }} catch (e) {{
                    document.getElementById('results').innerHTML = 
                        '<h3>❌ Get Theme Error:</h3><pre>' + e.message + '</pre>';
                }}
            }}
            
            async function testSetTheme(theme) {{
                try {{
                    const formData = new FormData();
                    formData.append('theme', theme);
                    formData.append('csrfmiddlewaretoken', '{csrf}');
                    
                    const response = await fetch('/api/theme/set/', {{
                        method: 'POST',
                        body: formData
                    }});
                    const data = await response.json();
                    
                    document.getElementById('results').innerHTML = 
                        '<h3>✅ Set Theme Result:</h3><pre>' + JSON.stringify(data, null, 2) + '</pre>';
                        
                    // Apply theme immediately
                    const html = document.documentElement;
                    html.removeAttribute('data-theme');
                    if (theme !== 'terminal-amber') {{
                        html.setAttribute('data-theme', theme);
                    }}
                }} catch (e) {{
                    document.getElementById('results').innerHTML = 
                        '<h3>❌ Set Theme Error:</h3><pre>' + e.message + '</pre>';
                }}
            }}
        </script>
    </body>
    </html>
    """.format(
        user=request.user.username if request.user.is_authenticated else 'Anonymous',
        theme=request.COOKIES.get('theme_preference', 'Not set'),
        cookie=request.COOKIES.get('theme_preference', 'No cookie'),
        csrf=request.META.get('CSRF_COOKIE', 'No CSRF')
    )
    
    return HttpResponse(html_content)
