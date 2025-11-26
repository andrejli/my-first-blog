import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from blog.models import SiteTheme, UserThemePreference
from django.contrib.auth.models import User

print('=== SiteTheme Table ===')
themes = SiteTheme.objects.all()
print(f'Total themes: {themes.count()}\n')

for t in themes:
    print(f'ID {t.id}: {t.theme_key} ({t.display_name})')
    print(f'  Active: {t.is_active}, Default: {t.is_default}')
    print()

print('\n=== UserThemePreference Table ===')
prefs = UserThemePreference.objects.select_related('user', 'theme').all()
print(f'Total preferences: {prefs.count()}\n')

for p in prefs:
    theme_key = p.theme.theme_key if p.theme else 'None'
    print(f'User: {p.user.username} -> Theme: {theme_key}')

print('\n=== Default Theme Check ===')
default_themes = SiteTheme.objects.filter(is_default=True, is_active=True)
print(f'Default themes found: {default_themes.count()}')
for dt in default_themes:
    print(f'  {dt.theme_key} ({dt.display_name})')
