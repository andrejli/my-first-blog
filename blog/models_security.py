"""
Security monitoring and logging models for Django LMS
Advanced monitoring system with admin interface integration
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

# Use Django's built-in JSONField (available from Django 3.1+)
try:
    from django.db.models import JSONField
except ImportError:
    # Fallback for older Django versions or when postgres is not available
    JSONField = models.TextField  # Store as text and handle JSON manually


class SecurityEvent(models.Model):
    """Log security-related events for monitoring and analysis"""
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'), 
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    EVENT_TYPE_CHOICES = [
        ('login_success', 'Successful Login'),
        ('login_failure', 'Failed Login'),
        ('login_brute_force', 'Brute Force Attempt'),
        ('password_change', 'Password Change'),
        ('account_lockout', 'Account Lockout'),
        ('suspicious_request', 'Suspicious Request'),
        ('file_upload', 'File Upload'),
        ('file_upload_blocked', 'Blocked File Upload'),
        ('tor_access', 'Tor Network Access'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
        ('csrf_failure', 'CSRF Token Failure'),
        ('path_traversal', 'Path Traversal Attempt'),
        ('sql_injection', 'SQL Injection Attempt'),
        ('xss_attempt', 'XSS Attempt'),
        ('admin_access', 'Admin Panel Access'),
        ('privilege_escalation', 'Privilege Escalation Attempt'),
        ('data_export', 'Data Export'),
        ('configuration_change', 'Configuration Change'),
        ('system_error', 'System Error'),
        ('security_scan', 'Security Scan Detected'),
    ]
    
    # Core fields
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, db_index=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium', db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # User and session information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    
    # Network information
    ip_address = models.GenericIPAddressField(db_index=True)
    user_agent = models.TextField(blank=True)
    referer = models.URLField(blank=True)
    
    # Request details
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=500, blank=True, db_index=True)
    request_params = models.TextField(blank=True, help_text="GET/POST parameters (sanitized)")
    
    # Event details
    message = models.TextField(help_text="Human-readable event description")
    details = models.JSONField(default=dict, blank=True, help_text="Additional event metadata")
    
    # Geographic information (optional)
    country_code = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Response and impact
    response_code = models.IntegerField(null=True, blank=True)
    blocked = models.BooleanField(default=False, help_text="Was this request blocked?")
    
    # Investigation and response
    investigated = models.BooleanField(default=False, db_index=True)
    false_positive = models.BooleanField(default=False)
    notes = models.TextField(blank=True, help_text="Investigation notes")
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'severity']),
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['user', 'event_type']),
        ]
        
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.severity.upper()} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def is_recent(self, hours=24):
        """Check if event occurred within specified hours"""
        cutoff = timezone.now() - timezone.timedelta(hours=hours)
        return self.timestamp >= cutoff
    
    def get_user_display(self):
        """Get user display name or anonymous indicator"""
        if self.user:
            return f"{self.user.username} ({self.user.get_full_name() or 'No name'})"
        return "Anonymous"
    
    def get_location_display(self):
        """Get formatted location string"""
        if self.country_code and self.city:
            return f"{self.city}, {self.country_code.upper()}"
        elif self.country_code:
            return self.country_code.upper()
        return "Unknown"


class SystemMetrics(models.Model):
    """System performance and health metrics"""
    
    METRIC_TYPE_CHOICES = [
        ('cpu_usage', 'CPU Usage'),
        ('memory_usage', 'Memory Usage'),
        ('disk_usage', 'Disk Usage'),
        ('database_connections', 'Database Connections'),
        ('active_sessions', 'Active Sessions'),
        ('request_rate', 'Request Rate'),
        ('error_rate', 'Error Rate'),
        ('response_time', 'Response Time'),
        ('file_uploads', 'File Uploads'),
        ('login_rate', 'Login Rate'),
    ]
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPE_CHOICES, db_index=True)
    value = models.FloatField(help_text="Metric value (percentage, count, etc.)")
    unit = models.CharField(max_length=20, blank=True, help_text="Unit of measurement")
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric_type', 'timestamp']),
            models.Index(fields=['timestamp', 'value']),
        ]
    
    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.value}{self.unit} at {self.timestamp.strftime('%H:%M:%S')}"


class ThreatIntelligence(models.Model):
    """Threat intelligence and IP reputation data"""
    
    SOURCE_CHOICES = [
        ('manual', 'Manual Entry'),
        ('automated', 'Automated Detection'),
        ('external_feed', 'External Threat Feed'),
        ('user_report', 'User Report'),
    ]
    
    THREAT_TYPE_CHOICES = [
        ('malicious_ip', 'Malicious IP Address'),
        ('tor_exit_node', 'Tor Exit Node'),
        ('bot_network', 'Bot Network'),
        ('scanner', 'Security Scanner'),
        ('brute_force', 'Brute Force Source'),
        ('spam_source', 'Spam Source'),
        ('phishing', 'Phishing Source'),
        ('malware', 'Malware Distribution'),
    ]
    
    # Threat identification
    ip_address = models.GenericIPAddressField(unique=True, db_index=True)
    threat_type = models.CharField(max_length=50, choices=THREAT_TYPE_CHOICES, db_index=True)
    
    # Threat details
    confidence = models.IntegerField(default=50, help_text="Confidence level (0-100)")
    first_seen = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Source and validation
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='automated')
    description = models.TextField(blank=True)
    
    # Response actions
    blocked = models.BooleanField(default=False, db_index=True)
    whitelisted = models.BooleanField(default=False, db_index=True)
    
    # Additional metadata
    country_code = models.CharField(max_length=2, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-last_seen']
        
    def __str__(self):
        return f"{self.ip_address} - {self.get_threat_type_display()} ({self.confidence}%)"
    
    def update_last_seen(self):
        """Update last seen timestamp"""
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])


class AuditLog(models.Model):
    """Audit log for administrative actions and data changes"""
    
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('config_change', 'Configuration Change'),
        ('permission_change', 'Permission Change'),
    ]
    
    # Action details
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_index=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    
    # Target information
    content_type = models.CharField(max_length=100, blank=True, help_text="Model being acted upon")
    object_id = models.CharField(max_length=50, blank=True, help_text="ID of object being acted upon")
    object_repr = models.CharField(max_length=200, blank=True, help_text="String representation of object")
    
    # Change details
    changes = models.JSONField(default=dict, blank=True, help_text="Before/after values for updates")
    description = models.TextField(help_text="Human-readable description of action")
    
    # Request context
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.user} {self.action} {self.content_type} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class AlertRule(models.Model):
    """Configurable alert rules for security monitoring"""
    
    CONDITION_CHOICES = [
        ('threshold', 'Threshold'),
        ('pattern', 'Pattern Match'),
        ('frequency', 'Frequency'),
        ('anomaly', 'Anomaly Detection'),
    ]
    
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    # Rule configuration
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Trigger conditions
    event_type = models.CharField(max_length=50, blank=True, help_text="Event type to monitor")
    condition_type = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    threshold_value = models.FloatField(null=True, blank=True)
    time_window = models.IntegerField(default=3600, help_text="Time window in seconds")
    
    # Alert configuration
    alert_severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='warning')
    email_notifications = models.BooleanField(default=True)
    
    # Metadata
    created_date = models.DateTimeField(default=timezone.now)
    last_triggered = models.DateTimeField(null=True, blank=True)
    trigger_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
    
    def check_condition(self, events):
        """Check if this rule's conditions are met"""
        # Implementation will be added in the monitoring service
        pass