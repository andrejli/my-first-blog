"""
Secret Chamber Apps Configuration
Secure admin-only decision making system
"""
from django.apps import AppConfig


class SecretChamberConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog.secret_chamber'
    verbose_name = 'Secret Chamber'