"""
Content Security Policy (CSP) middleware for XSS protection.
Adds nonce to inline scripts and implements strict CSP headers.
"""

import secrets
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve


class CSPMiddleware(MiddlewareMixin):
    """
    Middleware to add Content Security Policy headers with nonce for inline scripts.
    This helps prevent XSS attacks by controlling which scripts can execute.
    """
    
    def process_request(self, request):
        """Generate a unique nonce for this request."""
        # Generate a cryptographically secure random nonce
        request.csp_nonce = secrets.token_urlsafe(16)
    
    def process_response(self, request, response):
        """Add CSP headers to the response."""
        # Only add CSP to HTML responses
        content_type = response.get('Content-Type', '')
        if not content_type.startswith('text/html'):
            return response
        
        # Get the nonce from the request
        nonce = getattr(request, 'csp_nonce', None)
        if not nonce:
            nonce = secrets.token_urlsafe(16)
        
        # Build CSP policy
        csp = {
            'default-src': ["'self'"],
            'script-src': [
                "'self'",
                f"'nonce-{nonce}'",
                'https://ajax.googleapis.com',
                'https://code.jquery.com',
                'https://cdn.jsdelivr.net',
                'https://maxcdn.bootstrapcdn.com',
            ],
            'style-src': [
                "'self'",
                "'unsafe-inline'",
                'https://maxcdn.bootstrapcdn.com',
                'https://fonts.googleapis.com',
                'https://cdn.jsdelivr.net',
            ],
            'font-src': [
                "'self'",
                'https://fonts.gstatic.com',
                'https://maxcdn.bootstrapcdn.com',
                'https://cdn.jsdelivr.net',
            ],
            'img-src': ["'self'", 'data:', 'https:'],
            'connect-src': ["'self'"],
            'form-action': ["'self'"],
            'frame-ancestors': ["'none'"],
            'base-uri': ["'self'"],
            'object-src': ["'none'"],
        }
        
        # Check if the current view requires unsafe-inline
        # Note: unsafe-inline is ignored when nonce is present, so we don't need it
        # The templates should use nonce="{{ request.csp_nonce }}" instead

        # Join the CSP directives into a single string
        csp_header = "; ".join([
            f"{key} {' '.join(value)}" for key, value in csp.items()
        ])
        
        response['Content-Security-Policy'] = csp_header
        
        # Add additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response


# Allow unsafe-inline for specific views that require it
# This is a temporary solution. A better long-term fix is to refactor
# the inline scripts into separate .js files.
UNSAFE_INLINE_VIEWS = [
    'blog.views.create_blog_post',
    'blog.views.edit_blog_post',
]