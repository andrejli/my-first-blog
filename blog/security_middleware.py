"""
Security middleware for real-time monitoring and threat detection
Integrates with security models to log events and enforce policies
"""

import json
import time
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseForbidden, JsonResponse
from django.core.cache import cache
from django.conf import settings
from ipware import get_client_ip
import geoip2.database
import geoip2.errors
from user_agents import parse

from .models_security import SecurityEvent, ThreatIntelligence, SystemMetrics

logger = logging.getLogger(__name__)


class SecurityMonitoringMiddleware:
    """
    Advanced security monitoring middleware
    
    Features:
    - Real-time threat detection
    - Rate limiting
    - Geolocation tracking
    - User agent analysis
    - Automatic IP blocking
    - Security event logging
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Rate limiting settings
        self.rate_limit_requests = getattr(settings, 'SECURITY_RATE_LIMIT_REQUESTS', 100)
        self.rate_limit_window = getattr(settings, 'SECURITY_RATE_LIMIT_WINDOW', 3600)  # 1 hour
        
        # Suspicious patterns
        self.suspicious_paths = [
            '/admin/', '/wp-admin/', '/phpmyadmin/', '/.env', '/config/',
            '/database/', '/backup/', '/shell', '/cmd', '/eval'
        ]
        
        self.suspicious_params = [
            'cmd', 'exec', 'system', 'shell', 'eval', 'base64_decode',
            'file_get_contents', 'curl', 'wget', 'nc', 'netcat'
        ]
        
        # Blocked user agents patterns
        self.blocked_agents = [
            'sqlmap', 'nmap', 'nikto', 'dirb', 'dirbuster', 'gobuster',
            'wpscan', 'masscan', 'zap', 'burp', 'acunetix', 'nessus'
        ]
    
    def __call__(self, request):
        start_time = time.time()
        
        # Get client IP
        client_ip, is_routable = get_client_ip(request)
        if not client_ip:
            client_ip = '127.0.0.1'
        
        # Store IP in request for later use
        request.security_ip = client_ip
        
        # Check if IP is blocked
        if self._is_ip_blocked(client_ip):
            self._log_security_event(
                request, 'blocked_access', 'high',
                f'Access denied for blocked IP: {client_ip}'
            )
            return HttpResponseForbidden('Access denied')
        
        # Rate limiting check
        if self._is_rate_limited(client_ip, request):
            self._log_security_event(
                request, 'rate_limit_exceeded', 'medium',
                f'Rate limit exceeded for IP: {client_ip}'
            )
            return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
        
        # Suspicious request detection
        threat_level = self._detect_suspicious_activity(request)
        
        if threat_level == 'high':
            # Auto-block high threat requests
            self._auto_block_ip(client_ip, 'High threat activity detected')
            self._log_security_event(
                request, 'suspicious_request', 'high',
                'High threat activity - IP auto-blocked'
            )
            return HttpResponseForbidden('Suspicious activity detected')
        elif threat_level == 'medium':
            self._log_security_event(
                request, 'suspicious_request', 'medium',
                'Suspicious activity detected'
            )
        
        # Process request
        response = self.get_response(request)
        
        # Log successful requests for analysis
        self._log_request_metrics(request, response, time.time() - start_time)
        
        return response
    
    def _is_ip_blocked(self, ip_address):
        """Check if IP address is blocked"""
        try:
            threat = ThreatIntelligence.objects.get(ip_address=ip_address)
            return threat.blocked and not threat.whitelisted
        except ThreatIntelligence.DoesNotExist:
            return False
    
    def _is_rate_limited(self, ip_address, request):
        """Check if IP is rate limited"""
        # Skip rate limiting for whitelisted IPs
        try:
            threat = ThreatIntelligence.objects.get(ip_address=ip_address)
            if threat.whitelisted:
                return False
        except ThreatIntelligence.DoesNotExist:
            pass
        
        # Check request count in cache
        cache_key = f'rate_limit_{ip_address}'
        request_count = cache.get(cache_key, 0)
        
        if request_count >= self.rate_limit_requests:
            return True
        
        # Increment counter
        cache.set(cache_key, request_count + 1, self.rate_limit_window)
        return False
    
    def _detect_suspicious_activity(self, request):
        """Detect suspicious request patterns"""
        threat_score = 0
        
        # Check request path
        path = request.path.lower()
        for suspicious_path in self.suspicious_paths:
            if suspicious_path in path:
                threat_score += 30
                break
        
        # Check query parameters
        query_params = ' '.join([
            str(key) + str(value) for key, value in request.GET.items()
        ]).lower()
        
        for suspicious_param in self.suspicious_params:
            if suspicious_param in query_params:
                threat_score += 25
        
        # Check POST data
        if request.method == 'POST':
            try:
                post_data = str(request.POST).lower()
                for suspicious_param in self.suspicious_params:
                    if suspicious_param in post_data:
                        threat_score += 25
            except:
                pass
        
        # Check User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        for blocked_agent in self.blocked_agents:
            if blocked_agent in user_agent:
                threat_score += 50
                break
        
        # Check for common attack patterns
        if any(pattern in path for pattern in ['../', '/./', '/etc/', '/var/', '/root/']):
            threat_score += 40  # Directory traversal
        
        if any(pattern in query_params for pattern in ['union select', 'or 1=1', 'drop table']):
            threat_score += 50  # SQL injection
        
        if any(pattern in query_params for pattern in ['<script', 'javascript:', 'onerror=']):
            threat_score += 35  # XSS attempt
        
        # Determine threat level
        if threat_score >= 75:
            return 'high'
        elif threat_score >= 40:
            return 'medium'
        elif threat_score >= 20:
            return 'low'
        
        return 'none'
    
    def _auto_block_ip(self, ip_address, reason):
        """Automatically block suspicious IP"""
        try:
            threat, created = ThreatIntelligence.objects.get_or_create(
                ip_address=ip_address,
                defaults={
                    'threat_type': 'malicious_ip',
                    'blocked': True,
                    'confidence': 85,
                    'source': 'auto_detection',
                    'description': reason
                }
            )
            
            if not created:
                threat.blocked = True
                threat.confidence = min(threat.confidence + 10, 100)
                threat.save()
            
            logger.warning(f'Auto-blocked IP {ip_address}: {reason}')
            
        except Exception as e:
            logger.error(f'Error auto-blocking IP {ip_address}: {e}')
    
    def _log_security_event(self, request, event_type, severity, message):
        """Log security event"""
        try:
            # Get user
            user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
            
            # Get IP address
            client_ip = getattr(request, 'security_ip', '127.0.0.1')
            
            # Get geolocation data
            country_code = None
            city = None
            try:
                if hasattr(settings, 'GEOIP_PATH'):
                    with geoip2.database.Reader(settings.GEOIP_PATH) as reader:
                        response = reader.city(client_ip)
                        country_code = response.country.iso_code
                        city = response.city.name
            except (geoip2.errors.AddressNotFoundError, FileNotFoundError, AttributeError):
                pass
            
            # Create security event
            SecurityEvent.objects.create(
                event_type=event_type,
                severity=severity,
                message=message,
                user=user,
                ip_address=client_ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                referer=request.META.get('HTTP_REFERER', ''),
                request_method=request.method,
                request_path=request.path,
                request_params=json.dumps(dict(request.GET)),
                session_key=request.session.session_key if hasattr(request, 'session') else None,
                country_code=country_code,
                city=city,
                blocked=(severity in ['high', 'critical']),
                details=json.dumps({
                    'headers': dict(request.headers),
                    'meta': {k: v for k, v in request.META.items() if k.startswith('HTTP_')},
                    'query_params': dict(request.GET),
                })
            )
            
        except Exception as e:
            logger.error(f'Error logging security event: {e}')
    
    def _log_request_metrics(self, request, response, response_time):
        """Log request metrics for performance monitoring"""
        try:
            # Only log every 10th request to avoid overwhelming the database
            if hash(request.path) % 10 == 0:
                SystemMetrics.objects.create(
                    metric_type='response_time',
                    value=response_time * 1000,  # Convert to milliseconds
                    unit='ms',
                    details=json.dumps({
                        'path': request.path,
                        'method': request.method,
                        'status_code': response.status_code,
                        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100],
                    })
                )
        except Exception as e:
            logger.error(f'Error logging request metrics: {e}')


class TorDetectionMiddleware:
    """
    Tor network detection middleware
    Detects and logs Tor exit node access
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.tor_policy = getattr(settings, 'SECURITY_TOR_POLICY', 'log')  # 'block', 'log', 'allow'
    
    def __call__(self, request):
        client_ip, _ = get_client_ip(request)
        
        if client_ip and self._is_tor_exit_node(client_ip):
            # Log Tor access
            self._log_tor_access(request, client_ip)
            
            if self.tor_policy == 'block':
                return HttpResponseForbidden('Tor access not permitted')
        
        return self.get_response(request)
    
    def _is_tor_exit_node(self, ip_address):
        """Check if IP is a Tor exit node"""
        # Simple cache check first
        cache_key = f'tor_check_{ip_address}'
        result = cache.get(cache_key)
        
        if result is not None:
            return result
        
        # Check threat intelligence database
        try:
            threat = ThreatIntelligence.objects.get(
                ip_address=ip_address,
                threat_type='tor_exit_node'
            )
            cache.set(cache_key, True, 3600)  # Cache for 1 hour
            return True
        except ThreatIntelligence.DoesNotExist:
            cache.set(cache_key, False, 3600)
            return False
    
    def _log_tor_access(self, request, ip_address):
        """Log Tor access attempt"""
        try:
            user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
            
            SecurityEvent.objects.create(
                event_type='tor_access',
                severity='medium',
                message=f'Tor exit node access from {ip_address}',
                user=user,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                request_method=request.method,
                request_path=request.path,
                details=json.dumps({
                    'tor_policy': self.tor_policy,
                    'headers': dict(request.headers)
                })
            )
        except Exception as e:
            logger.error(f'Error logging Tor access: {e}')


class AuthenticationMonitoringMiddleware:
    """
    Authentication monitoring middleware
    Tracks login attempts and detects brute force attacks
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.max_failed_attempts = getattr(settings, 'SECURITY_MAX_FAILED_ATTEMPTS', 5)
        self.lockout_duration = getattr(settings, 'SECURITY_LOCKOUT_DURATION', 3600)  # 1 hour
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Monitor login attempts
        if request.path in ['/login/', '/admin/login/'] and request.method == 'POST':
            self._monitor_login_attempt(request, response)
        
        return response
    
    def _monitor_login_attempt(self, request, response):
        """Monitor login attempts for brute force detection"""
        client_ip, _ = get_client_ip(request)
        username = request.POST.get('username', '')
        
        # Check if login was successful (redirect or 200 with success indicators)
        login_successful = (
            response.status_code == 302 or  # Redirect after successful login
            (response.status_code == 200 and 'error' not in str(response.content).lower())
        )
        
        if login_successful:
            # Log successful login
            try:
                SecurityEvent.objects.create(
                    event_type='login_success',
                    severity='low',
                    message=f'Successful login for user: {username}',
                    user_id=request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
                    ip_address=client_ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    request_path=request.path,
                    details=json.dumps({
                        'username': username,
                        'login_time': timezone.now().isoformat()
                    })
                )
                
                # Reset failed attempt counter
                cache_key = f'failed_logins_{client_ip}'
                cache.delete(cache_key)
                
            except Exception as e:
                logger.error(f'Error logging successful login: {e}')
        else:
            # Log failed login attempt
            self._log_failed_login(request, client_ip, username)
    
    def _log_failed_login(self, request, ip_address, username):
        """Log failed login attempt and check for brute force"""
        try:
            # Increment failed attempt counter
            cache_key = f'failed_logins_{ip_address}'
            failed_attempts = cache.get(cache_key, 0) + 1
            cache.set(cache_key, failed_attempts, self.lockout_duration)
            
            # Determine severity based on attempt count
            if failed_attempts >= self.max_failed_attempts:
                severity = 'high'
                event_type = 'login_brute_force'
                message = f'Brute force attack detected from {ip_address} (attempt #{failed_attempts})'
                
                # Auto-block IP after excessive attempts
                if failed_attempts >= self.max_failed_attempts * 2:
                    self._auto_block_brute_force_ip(ip_address)
            else:
                severity = 'medium'
                event_type = 'login_failure'
                message = f'Failed login attempt for user: {username} (attempt #{failed_attempts})'
            
            SecurityEvent.objects.create(
                event_type=event_type,
                severity=severity,
                message=message,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                request_path=request.path,
                details=json.dumps({
                    'username': username,
                    'failed_attempts': failed_attempts,
                    'max_attempts': self.max_failed_attempts
                }),
                blocked=(failed_attempts >= self.max_failed_attempts * 2)
            )
            
        except Exception as e:
            logger.error(f'Error logging failed login: {e}')
    
    def _auto_block_brute_force_ip(self, ip_address):
        """Auto-block IP performing brute force attacks"""
        try:
            threat, created = ThreatIntelligence.objects.get_or_create(
                ip_address=ip_address,
                defaults={
                    'threat_type': 'brute_force',
                    'blocked': True,
                    'confidence': 90,
                    'source': 'auto_brute_force',
                    'description': f'Auto-blocked due to brute force login attempts'
                }
            )
            
            if not created:
                threat.blocked = True
                threat.threat_type = 'brute_force'
                threat.confidence = min(threat.confidence + 15, 100)
                threat.save()
            
            logger.warning(f'Auto-blocked brute force IP: {ip_address}')
            
        except Exception as e:
            logger.error(f'Error auto-blocking brute force IP: {e}')