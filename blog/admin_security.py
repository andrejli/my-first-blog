"""
Security monitoring admin interface for Django LMS
Advanced admin interfaces for security events and system monitoring
"""

from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html
from django.utils import timezone
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from datetime import timedelta
import csv
import json

from .models_security import (
    SecurityEvent, SystemMetrics, ThreatIntelligence, 
    AuditLog, AlertRule
)


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """Advanced admin interface for security events"""
    
    list_display = [
        'timestamp', 'event_type_colored', 'severity_badge', 
        'user_link', 'ip_address_link', 'location', 'blocked_status'
    ]
    
    list_filter = [
        'severity', 'event_type', 'blocked', 'investigated',
        'false_positive', 'timestamp', 'country_code'
    ]
    
    search_fields = [
        'ip_address', 'user__username', 'message', 
        'request_path', 'user_agent'
    ]
    
    readonly_fields = [
        'timestamp', 'ip_address', 'user_agent', 'referer',
        'request_method', 'request_path', 'request_params',
        'response_code', 'country_code', 'city'
    ]
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'severity', 'timestamp', 'message')
        }),
        ('User & Session', {
            'fields': ('user', 'session_key')
        }),
        ('Network Information', {
            'fields': ('ip_address', 'user_agent', 'referer', 'country_code', 'city')
        }),
        ('Request Details', {
            'fields': ('request_method', 'request_path', 'request_params', 'response_code')
        }),
        ('Investigation', {
            'fields': ('investigated', 'false_positive', 'blocked', 'notes'),
            'classes': ('collapse',)
        }),
        ('Additional Data', {
            'fields': ('details',),
            'classes': ('collapse',)
        })
    )
    
    actions = [
        'mark_investigated', 'mark_false_positive', 'block_ip_addresses',
        'export_to_csv', 'create_threat_intelligence'
    ]
    
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def event_type_colored(self, obj):
        colors = {
            'login_failure': 'red',
            'login_brute_force': 'darkred',
            'file_upload_blocked': 'orange',
            'suspicious_request': 'purple',
            'tor_access': 'blue',
            'login_success': 'green',
        }
        color = colors.get(obj.event_type, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.get_event_type_display()
        )
    event_type_colored.short_description = 'Event Type'
    event_type_colored.admin_order_field = 'event_type'
    
    def severity_badge(self, obj):
        colors = {
            'low': 'green',
            'medium': 'orange', 
            'high': 'red',
            'critical': 'darkred'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.severity, 'gray'), obj.severity.upper()
        )
    severity_badge.short_description = 'Severity'
    severity_badge.admin_order_field = 'severity'
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return 'Anonymous'
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def ip_address_link(self, obj):
        """Link IP address to threat intelligence if exists"""
        try:
            threat = ThreatIntelligence.objects.get(ip_address=obj.ip_address)
            url = reverse('admin:blog_threatintelligence_change', args=[threat.pk])
            return format_html(
                '<a href="{}" style="color: red;" title="Known threat">{} ⚠️</a>',
                url, obj.ip_address
            )
        except ThreatIntelligence.DoesNotExist:
            return obj.ip_address
    ip_address_link.short_description = 'IP Address'
    ip_address_link.admin_order_field = 'ip_address'
    
    def location(self, obj):
        return obj.get_location_display()
    location.short_description = 'Location'
    
    def blocked_status(self, obj):
        if obj.blocked:
            return format_html('<span style="color: red;">🛑 BLOCKED</span>')
        return format_html('<span style="color: green;">✅ Allowed</span>')
    blocked_status.short_description = 'Status'
    blocked_status.admin_order_field = 'blocked'
    
    def mark_investigated(self, request, queryset):
        count = queryset.update(investigated=True)
        self.message_user(request, f'{count} events marked as investigated.')
    mark_investigated.short_description = 'Mark as investigated'
    
    def mark_false_positive(self, request, queryset):
        count = queryset.update(false_positive=True, investigated=True)
        self.message_user(request, f'{count} events marked as false positives.')
    mark_false_positive.short_description = 'Mark as false positive'
    
    def block_ip_addresses(self, request, queryset):
        ips = set(queryset.values_list('ip_address', flat=True))
        for ip in ips:
            ThreatIntelligence.objects.get_or_create(
                ip_address=ip,
                defaults={
                    'threat_type': 'malicious_ip',
                    'blocked': True,
                    'confidence': 80,
                    'source': 'manual',
                    'description': f'Blocked via admin action from security events'
                }
            )
        self.message_user(request, f'Blocked {len(ips)} IP addresses.')
    block_ip_addresses.short_description = 'Block IP addresses'
    
    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="security_events.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Timestamp', 'Event Type', 'Severity', 'User', 'IP Address',
            'Message', 'Blocked', 'Investigated'
        ])
        
        for event in queryset:
            writer.writerow([
                event.timestamp.isoformat(),
                event.get_event_type_display(),
                event.severity,
                event.user.username if event.user else 'Anonymous',
                event.ip_address,
                event.message,
                event.blocked,
                event.investigated
            ])
        
        return response
    export_to_csv.short_description = 'Export to CSV'


@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    """Admin interface for system metrics"""
    
    list_display = [
        'timestamp', 'metric_type_colored', 'value_with_unit', 
        'trend_indicator'
    ]
    
    list_filter = ['metric_type', 'timestamp']
    search_fields = ['metric_type']
    readonly_fields = ['timestamp']
    
    date_hierarchy = 'timestamp'
    
    def metric_type_colored(self, obj):
        colors = {
            'cpu_usage': 'blue',
            'memory_usage': 'green',
            'disk_usage': 'orange',
            'error_rate': 'red',
            'request_rate': 'purple'
        }
        color = colors.get(obj.metric_type, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.get_metric_type_display()
        )
    metric_type_colored.short_description = 'Metric Type'
    
    def value_with_unit(self, obj):
        if obj.metric_type in ['cpu_usage', 'memory_usage', 'disk_usage']:
            color = 'red' if obj.value > 80 else 'orange' if obj.value > 60 else 'green'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}{}</span>',
                color, obj.value, obj.unit or '%'
            )
        return f"{obj.value}{obj.unit}"
    value_with_unit.short_description = 'Value'
    
    def trend_indicator(self, obj):
        # Get previous metric of same type
        try:
            previous = SystemMetrics.objects.filter(
                metric_type=obj.metric_type,
                timestamp__lt=obj.timestamp
            ).latest('timestamp')
            
            if obj.value > previous.value:
                return format_html('<span style="color: red;">📈 ↗️</span>')
            elif obj.value < previous.value:
                return format_html('<span style="color: green;">📉 ↘️</span>')
            else:
                return format_html('<span style="color: gray;">➡️</span>')
        except SystemMetrics.DoesNotExist:
            return '-'
    trend_indicator.short_description = 'Trend'


@admin.register(ThreatIntelligence)
class ThreatIntelligenceAdmin(admin.ModelAdmin):
    """Admin interface for threat intelligence"""
    
    list_display = [
        'ip_address_colored', 'threat_type_badge', 'confidence_bar',
        'blocked_status', 'last_seen', 'event_count'
    ]
    
    list_filter = [
        'threat_type', 'blocked', 'whitelisted', 'confidence',
        'source', 'country_code'
    ]
    
    search_fields = ['ip_address', 'description', 'organization']
    
    readonly_fields = ['first_seen', 'last_seen']
    
    actions = [
        'block_threats', 'unblock_threats', 'whitelist_threats',
        'increase_confidence', 'decrease_confidence'
    ]
    
    def ip_address_colored(self, obj):
        color = 'red' if obj.blocked else 'green' if obj.whitelisted else 'black'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.ip_address
        )
    ip_address_colored.short_description = 'IP Address'
    ip_address_colored.admin_order_field = 'ip_address'
    
    def threat_type_badge(self, obj):
        colors = {
            'malicious_ip': 'red',
            'tor_exit_node': 'blue',
            'bot_network': 'purple',
            'scanner': 'orange',
            'brute_force': 'darkred'
        }
        color = colors.get(obj.threat_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            color, obj.get_threat_type_display()
        )
    threat_type_badge.short_description = 'Threat Type'
    
    def confidence_bar(self, obj):
        width = min(obj.confidence, 100)
        color = 'red' if width >= 80 else 'orange' if width >= 50 else 'green'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border: 1px solid #ccc;">'
            '<div style="width: {}px; height: 20px; background-color: {}; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{}%</div></div>',
            width, color, obj.confidence
        )
    confidence_bar.short_description = 'Confidence'
    
    def blocked_status(self, obj):
        if obj.blocked:
            return format_html('<span style="color: red;">🛑 BLOCKED</span>')
        elif obj.whitelisted:
            return format_html('<span style="color: green;">✅ WHITELISTED</span>')
        return format_html('<span style="color: gray;">⚪ MONITORING</span>')
    blocked_status.short_description = 'Status'
    
    def event_count(self, obj):
        """Count related security events"""
        count = SecurityEvent.objects.filter(ip_address=obj.ip_address).count()
        if count > 0:
            url = f"/admin/blog/securityevent/?ip_address={obj.ip_address}"
            return format_html('<a href="{}">{} events</a>', url, count)
        return '0 events'
    event_count.short_description = 'Events'
    
    def block_threats(self, request, queryset):
        count = queryset.update(blocked=True, whitelisted=False)
        self.message_user(request, f'{count} threats blocked.')
    block_threats.short_description = 'Block selected threats'
    
    def unblock_threats(self, request, queryset):
        count = queryset.update(blocked=False)
        self.message_user(request, f'{count} threats unblocked.')
    unblock_threats.short_description = 'Unblock selected threats'
    
    def whitelist_threats(self, request, queryset):
        count = queryset.update(whitelisted=True, blocked=False)
        self.message_user(request, f'{count} threats whitelisted.')
    whitelist_threats.short_description = 'Whitelist selected threats'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for audit logs"""
    
    list_display = [
        'timestamp', 'user_link', 'action_colored', 
        'content_type', 'object_repr_truncated', 'ip_address'
    ]
    
    list_filter = ['action', 'content_type', 'timestamp']
    search_fields = ['user__username', 'object_repr', 'description', 'ip_address']
    readonly_fields = ['timestamp', 'user', 'ip_address', 'user_agent']
    
    date_hierarchy = 'timestamp'
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return 'System'
    user_link.short_description = 'User'
    
    def action_colored(self, obj):
        colors = {
            'create': 'green',
            'read': 'blue',
            'update': 'orange',
            'delete': 'red',
            'login': 'purple',
            'logout': 'gray'
        }
        color = colors.get(obj.action, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_action_display()
        )
    action_colored.short_description = 'Action'
    
    def object_repr_truncated(self, obj):
        return obj.object_repr[:50] + '...' if len(obj.object_repr) > 50 else obj.object_repr
    object_repr_truncated.short_description = 'Object'


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    """Admin interface for alert rules"""
    
    list_display = [
        'name', 'is_active_icon', 'event_type', 'condition_type',
        'alert_severity_badge', 'last_triggered', 'trigger_count'
    ]
    
    list_filter = ['is_active', 'condition_type', 'alert_severity', 'event_type']
    search_fields = ['name', 'description']
    
    actions = ['activate_rules', 'deactivate_rules', 'test_rules']
    
    def is_active_icon(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅</span>')
        return format_html('<span style="color: red;">❌</span>')
    is_active_icon.short_description = 'Active'
    is_active_icon.admin_order_field = 'is_active'
    
    def alert_severity_badge(self, obj):
        colors = {
            'info': 'blue',
            'warning': 'orange',
            'error': 'red', 
            'critical': 'darkred'
        }
        color = colors.get(obj.alert_severity, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            color, obj.alert_severity.upper()
        )
    alert_severity_badge.short_description = 'Severity'
    
    def activate_rules(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} rules activated.')
    activate_rules.short_description = 'Activate selected rules'
    
    def deactivate_rules(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} rules deactivated.')
    deactivate_rules.short_description = 'Deactivate selected rules'


# Custom admin site for security monitoring
class SecurityAdminSite(admin.AdminSite):
    """Dedicated admin site for security monitoring"""
    
    site_header = '🔒 Terminal LMS - Security Monitoring Center'
    site_title = 'Security Admin'
    index_title = 'Security Dashboard'
    
    def index(self, request, extra_context=None):
        """Custom security dashboard"""
        extra_context = extra_context or {}
        
        # Recent security events summary
        recent_events = SecurityEvent.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=24)
        )
        
        extra_context.update({
            'recent_events_count': recent_events.count(),
            'high_severity_events': recent_events.filter(severity__in=['high', 'critical']).count(),
            'blocked_events': recent_events.filter(blocked=True).count(),
            'unique_ips': recent_events.values('ip_address').distinct().count(),
            'threat_count': ThreatIntelligence.objects.filter(blocked=True).count(),
            'active_alerts': AlertRule.objects.filter(is_active=True).count(),
        })
        
        return super().index(request, extra_context)


# Initialize security admin site
security_admin_site = SecurityAdminSite(name='security_admin')

# Register models with security admin site
security_admin_site.register(SecurityEvent, SecurityEventAdmin)
security_admin_site.register(SystemMetrics, SystemMetricsAdmin) 
security_admin_site.register(ThreatIntelligence, ThreatIntelligenceAdmin)
security_admin_site.register(AuditLog, AuditLogAdmin)
security_admin_site.register(AlertRule, AlertRuleAdmin)