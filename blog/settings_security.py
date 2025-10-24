"""
Security configuration for Django LMS
Updates settings to integrate advanced security monitoring
"""

# Add to the bottom of your existing settings.py

# =============================================================================
# ADVANCED SECURITY MONITORING CONFIGURATION
# =============================================================================

# Security middleware (add to MIDDLEWARE list)
SECURITY_MIDDLEWARE = [
    'blog.security_middleware.SecurityMonitoringMiddleware',
    'blog.security_middleware.TorDetectionMiddleware', 
    'blog.security_middleware.AuthenticationMonitoringMiddleware',
]

# Rate limiting settings
SECURITY_RATE_LIMIT_REQUESTS = 100  # Max requests per window
SECURITY_RATE_LIMIT_WINDOW = 3600   # Window in seconds (1 hour)

# Authentication security
SECURITY_MAX_FAILED_ATTEMPTS = 5    # Max failed login attempts
SECURITY_LOCKOUT_DURATION = 3600    # Lockout duration in seconds

# Tor network policy
SECURITY_TOR_POLICY = 'log'         # Options: 'block', 'log', 'allow'

# File upload security (enhanced)
SECURITY_SCAN_UPLOADS = True
SECURITY_MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
SECURITY_ALLOWED_EXTENSIONS = [
    # Documents
    '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
    # Images  
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
    # Archives (with scanning)
    '.zip', '.tar', '.gz',
    # Code files
    '.py', '.js', '.html', '.css', '.json', '.xml'
]

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'DENY'

# Content Security Policy (CSP)
CSP_DEFAULT_SRC = ["'self'"]
CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'", 'cdnjs.cloudflare.com']
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'", 'fonts.googleapis.com']
CSP_FONT_SRC = ["'self'", 'fonts.gstatic.com']
CSP_IMG_SRC = ["'self'", 'data:', 'https:']
CSP_CONNECT_SRC = ["'self'"]

# Security logging
SECURITY_LOG_LEVEL = 'INFO'
SECURITY_LOG_FILE = 'security.log'

# Database connection security
DATABASES_DEFAULT_OPTIONS = {
    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    'charset': 'utf8mb4',
}

# Session security (enhanced)
SESSION_COOKIE_SECURE = True  # Enable in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600  # 1 hour

# CSRF protection (enhanced)  
CSRF_COOKIE_SECURE = True  # Enable in production with HTTPS
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_USE_SESSIONS = True

# Admin security
ADMIN_URL = 'admin/'  # Change this in production
ADMIN_FORCE_ALLAUTH = True

# Password validation (enhanced)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Increased from default
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    # Add custom password validator
    {
        'NAME': 'blog.validators.StrongPasswordValidator',
    },
]

# Security Apps (add to INSTALLED_APPS)
SECURITY_APPS = [
    'django_otp',           # Two-factor authentication
    'django_ratelimit',     # Rate limiting
    'corsheaders',          # CORS headers
    'csp',                  # Content Security Policy
]

# Django OTP (Two-Factor Authentication)
OTP_TOTP_ISSUER = 'Terminal LMS'
OTP_LOGIN_URL = '/2fa/login/'

# Email security
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False  # Use TLS instead
DEFAULT_FROM_EMAIL = 'security@terminallms.com'
SERVER_EMAIL = 'server@terminallms.com'

# Security notifications
SECURITY_NOTIFICATION_EMAIL = 'security@terminallms.com'
SECURITY_NOTIFY_ON_EVENTS = ['high', 'critical']

# Backup and recovery
BACKUP_ENCRYPTION_KEY = None  # Set in production
BACKUP_RETENTION_DAYS = 30

# Security monitoring dashboard
SECURITY_DASHBOARD_ENABLED = True
SECURITY_DASHBOARD_REFRESH_INTERVAL = 30  # seconds

# GeoIP configuration (optional - requires GeoLite2 database)
# GEOIP_PATH = os.path.join(BASE_DIR, 'geoip')

# =============================================================================
# PRODUCTION SECURITY CHECKLIST
# =============================================================================

"""
For production deployment, ensure:

1. Environment Variables:
   - SECRET_KEY from environment
   - DATABASE_URL from environment 
   - DEBUG = False
   - ALLOWED_HOSTS properly configured

2. HTTPS Configuration:
   - SECURE_SSL_REDIRECT = True
   - SESSION_COOKIE_SECURE = True
   - CSRF_COOKIE_SECURE = True
   - SECURE_HSTS_SECONDS = 31536000
   - SECURE_HSTS_INCLUDE_SUBDOMAINS = True
   - SECURE_HSTS_PRELOAD = True

3. Database Security:
   - Use connection pooling
   - Enable SSL for database connections
   - Regular security updates
   - Backup encryption

4. File Security:
   - Separate media server
   - File upload scanning
   - Regular security scans

5. Monitoring:
   - Log aggregation (ELK stack)
   - Real-time alerts
   - Performance monitoring
   - Security incident response plan

6. Infrastructure:
   - Web Application Firewall (WAF)
   - DDoS protection
   - Load balancing
   - Failover systems

7. Updates:
   - Regular Django updates
   - Dependency security scanning
   - OS security patches
   - Security vulnerability monitoring
"""

# =============================================================================
# SECURITY MIDDLEWARE INTEGRATION
# =============================================================================

# To integrate the security middleware, add these to your MIDDLEWARE setting:
MIDDLEWARE_SECURITY_INTEGRATION = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'blog.security_middleware.SecurityMonitoringMiddleware',  # Add this
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'blog.security_middleware.TorDetectionMiddleware',        # Add this  
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'blog.security_middleware.AuthenticationMonitoringMiddleware',  # Add this
    'django_otp.middleware.OTPMiddleware',                    # Add for 2FA
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',                           # Add for CSP
]

# =============================================================================
# INSTALLED APPS INTEGRATION  
# =============================================================================

INSTALLED_APPS_SECURITY_INTEGRATION = [
    'django.contrib.admin',
    'django.contrib.auth', 
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'blog',
    
    # Security apps
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'corsheaders',
    'csp',
]

# =============================================================================
# URL CONFIGURATION INTEGRATION
# =============================================================================

URL_PATTERNS_SECURITY_INTEGRATION = """
# Add to your main urls.py:

from django.contrib import admin
from django.urls import path, include
from blog.admin_security import security_admin_site

urlpatterns = [
    path('admin/', admin.site.urls),
    path('security-admin/', security_admin_site.urls),  # Dedicated security admin
    path('', include('blog.urls')),
    
    # Security URLs
    path('2fa/', include('django_otp.urls')),  # Two-factor authentication
]
"""

# =============================================================================
# CLI COMMANDS AVAILABLE
# =============================================================================

CLI_COMMANDS_HELP = """
Available Security CLI Commands:

1. Security Dashboard:
   python manage.py security_monitor dashboard --hours 24

2. View Security Events:
   python manage.py security_monitor events --severity high --hours 6

3. Threat Management:
   python manage.py security_monitor threats --confidence 80 --auto-block

4. System Metrics:
   python manage.py security_monitor metrics --hours 12

5. Security Analysis:
   python manage.py security_monitor analyze --hours 24

6. Block/Unblock IPs:
   python manage.py security_monitor block --ip 192.168.1.100
   python manage.py security_monitor unblock --ip 192.168.1.100

7. Export Security Data:
   python manage.py security_monitor export --format csv --output security_report.csv

8. Investigate Security Incidents:
   python manage.py security_monitor investigate --ip 192.168.1.100

9. Audit Logs:
   python manage.py security_monitor audit --user admin --hours 48

10. Alert Management:
    python manage.py security_monitor alerts
"""