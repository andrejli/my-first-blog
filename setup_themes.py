#!/usr/bin/env python
"""
Setup script to create default themes in the database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from blog.models import SiteTheme

def create_themes():
    """Create default themes if they don't exist"""
    
    themes = [
        {
            'name': 'Terminal Amber',
            'theme_key': 'terminal-amber',
            'display_name': 'Terminal Amber',
            'description': 'Classic amber/orange terminal theme (default)',
            'is_default': True,
            'is_active': True
        },
        {
            'name': 'Dark Blue',
            'theme_key': 'dark-blue',
            'display_name': 'Dark Blue',
            'description': 'Professional dark blue theme',
            'is_default': False,
            'is_active': True
        },
        {
            'name': 'Light Mode',
            'theme_key': 'light',
            'display_name': 'Light',
            'description': 'Light theme for bright environments',
            'is_default': False,
            'is_active': True
        },
        {
            'name': 'Cyberpunk',
            'theme_key': 'cyberpunk',
            'display_name': 'Cyberpunk',
            'description': 'Neon pink and cyan cyberpunk theme',
            'is_default': False,
            'is_active': True
        },
        {
            'name': 'Matrix',
            'theme_key': 'matrix',
            'display_name': 'Matrix',
            'description': 'Green Matrix-style theme',
            'is_default': False,
            'is_active': True
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for theme_data in themes:
        theme, created = SiteTheme.objects.get_or_create(
            theme_key=theme_data['theme_key'],
            defaults=theme_data
        )
        
        if created:
            created_count += 1
            print(f"✓ Created theme: {theme_data['display_name']}")
        else:
            # Update existing theme
            for key, value in theme_data.items():
                setattr(theme, key, value)
            theme.save()
            updated_count += 1
            print(f"✓ Updated theme: {theme_data['display_name']}")
    
    print(f"\n✅ Setup complete!")
    print(f"   Created: {created_count} themes")
    print(f"   Updated: {updated_count} themes")
    print(f"   Total active themes: {SiteTheme.objects.filter(is_active=True).count()}")

if __name__ == '__main__':
    print("Setting up themes...")
    create_themes()
