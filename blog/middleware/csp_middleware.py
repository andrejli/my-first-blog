"""
Content Security Policy (CSP) middleware for XSS protection.
Adds nonce to inline scripts and implements strict CSP headers.
"""

import secrets
from django.utils.deprecation import MiddlewareMixin


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
        csp_policies = [
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}' https://ajax.googleapis.com https://code.jquery.com https://cdn.jsdelivr.net https://maxcdn.bootstrapcdn.com",
            "style-src 'self' 'unsafe-inline' https://maxcdn.bootstrapcdn.com https://fonts.googleapis.com https://cdn.jsdelivr.net",
            "font-src 'self' https://fonts.gstatic.com https://maxcdn.bootstrapcdn.com",
            "img-src 'self' data: https:",
            "connect-src 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "object-src 'none'"
        ]
        
        # Join policies with semicolons
        csp_header = "; ".join(csp_policies)
        
        # Add CSP header
        response['Content-Security-Policy'] = csp_header
        
        # Add additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response