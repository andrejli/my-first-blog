from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

# Import security admin site (uncomment after installing dependencies)
# from blog.admin_security import security_admin_site

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Dedicated security monitoring admin (uncomment after setup)
    # path('security-admin/', security_admin_site.urls),
    
    path('', include('blog.urls')),
    
    # Two-factor authentication URLs (uncomment after installing django-otp)
    # path('2fa/', include('django_otp.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'blog.views.custom_404'
