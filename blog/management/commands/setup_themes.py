from django.core.management.base import BaseCommand
from blog.models import SiteTheme


class Command(BaseCommand):
    help = 'Create default themes for the site'
    
    def handle(self, *args, **options):
        themes_data = [
            {
                'name': 'terminal_green',
                'display_name': 'Terminal Green',
                'theme_key': 'terminal-green',
                'is_default': True,
                'description': 'Classic green terminal theme with retro computing aesthetics'
            },
            {
                'name': 'dark_blue',
                'display_name': 'Dark Blue',
                'theme_key': 'dark-blue',
                'is_default': False,
                'description': 'Professional dark blue theme for focused learning'
            },
            {
                'name': 'light',
                'display_name': 'Light Theme',
                'theme_key': 'light',
                'is_default': False,
                'description': 'Clean light theme for daytime studying'
            },
            {
                'name': 'cyberpunk',
                'display_name': 'Cyberpunk',
                'theme_key': 'cyberpunk',
                'is_default': False,
                'description': 'Futuristic neon cyberpunk theme with electric colors'
            },
            {
                'name': 'matrix',
                'display_name': 'Matrix',
                'theme_key': 'matrix',
                'is_default': False,
                'description': 'Matrix-inspired digital rain theme'
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for theme_data in themes_data:
            theme, created = SiteTheme.objects.get_or_create(
                theme_key=theme_data['theme_key'],
                defaults=theme_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created theme: {theme.display_name}')
                )
            else:
                # Update existing theme if needed
                updated = False
                for field, value in theme_data.items():
                    if getattr(theme, field) != value:
                        setattr(theme, field, value)
                        updated = True
                
                if updated:
                    theme.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated theme: {theme.display_name}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'Theme already exists: {theme.display_name}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSummary: {created_count} created, {updated_count} updated')
        )