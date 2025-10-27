"""
Admin Polling System - Phase 1: Simple Admin Interface
Django admin for basic admin polls
"""
from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils import timezone

from .models import AdminPoll, PollOption, AdminVote, AdminPollReport, AdminPollAudit


class PollOptionInline(admin.TabularInline):
    """Inline admin for poll options"""
    model = PollOption
    extra = 2
    fields = ['option_text', 'order']
    ordering = ['order']
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing options for polls with votes"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting options for polls with votes"""
        if not request.user.is_superuser:
            return False
            
        # For inline objects, obj is a PollOption instance
        if obj and hasattr(obj, 'poll'):
            if obj.poll.admin_votes.exists() or obj.poll.is_completed:
                return False
                
        return True
    
    def get_readonly_fields(self, request, obj=None):
        """Make option fields readonly for polls with votes"""
        # obj here is the parent AdminPoll object
        if obj and (obj.admin_votes.exists() or obj.is_completed):
            return ['option_text', 'order']
        return []


@admin.register(AdminPoll)
class AdminPollAdmin(admin.ModelAdmin):
    """Admin interface for Admin Polls - Phase 1"""
    
    list_display = [
        'title', 'poll_type', 'created_by', 'created_at',
        'status_display', 'participation_display', 'is_active'
    ]
    list_filter = [
        'poll_type', 'is_active', 'created_at', 'end_date'
    ]
    search_fields = ['title', 'description', 'created_by__username']
    readonly_fields = ['created_at', 'participation_display', 'status_display']
    
    fieldsets = [
        ('Poll Information', {
            'fields': ['title', 'description', 'poll_type']
        }),
        ('Settings', {
            'fields': ['end_date', 'is_active', 'allow_comments']
        }),
        ('Status', {
            'fields': ['status_display', 'participation_display'],
            'classes': ['collapse']
        })
    ]
    
    inlines = [PollOptionInline]
    
    def get_queryset(self, request):
        """Only superusers can see polls"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs
    
    def has_module_permission(self, request):
        """Only superusers can access"""
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing polls with votes or that are completed - security measure"""
        if not request.user.is_superuser:
            return False
        
        # Allow editing if no object (list view) or new object
        if obj is None:
            return True
            
        # Prevent editing if poll has votes (security: preserve voting integrity)
        if obj.admin_votes.exists():
            return False
            
        # Prevent editing if poll is completed
        if obj.is_completed:
            return False
            
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting polls with votes - security measure"""
        if not request.user.is_superuser:
            return False
            
        # Allow deletion if no object (list view)
        if obj is None:
            return True
            
        # Prevent deletion if poll has votes (security: preserve audit trail)
        if obj.admin_votes.exists():
            return False
            
        return True
    
    def get_readonly_fields(self, request, obj=None):
        """Make fields readonly for polls with votes or completed polls"""
        readonly = list(self.readonly_fields)
        
        if obj and (obj.admin_votes.exists() or obj.is_completed):
            # Make everything readonly except is_active (to allow deactivation)
            readonly.extend([
                'title', 'description', 'poll_type', 'end_date', 'allow_comments'
            ])
            
        return readonly
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Add security warnings for locked polls"""
        extra_context = extra_context or {}
        
        if object_id:
            try:
                obj = self.get_object(request, object_id)
                if obj and (obj.admin_votes.exists() or obj.is_completed):
                    if obj.admin_votes.exists():
                        messages.warning(
                            request, 
                            "🔒 SECURITY LOCK: This poll has received votes and most fields are now "
                            "read-only to preserve voting integrity. Only deactivation is allowed."
                        )
                    elif obj.is_completed:
                        messages.warning(
                            request,
                            "🔒 ARCHIVE LOCK: This poll is completed and locked to maintain audit trail integrity."
                        )
            except:
                pass
                
        return super().changeform_view(request, object_id, form_url, extra_context)
    
    def save_model(self, request, obj, form, change):
        """Set created_by field"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def status_display(self, obj):
        """Display poll status with color coding and security indicators"""
        status_parts = []
        
        if obj.is_open:
            status_parts.append('<span style="color: #28a745;">🗳️ Open</span>')
        elif obj.is_completed:
            status_parts.append('<span style="color: #dc3545;">✅ Closed</span>')
        else:
            status_parts.append('<span style="color: #ffc107;">⏸️ Inactive</span>')
        
        # Add security lock indicators
        if obj.admin_votes.exists():
            status_parts.append('<span style="color: #dc3545; font-size: 0.8em;">🔒 LOCKED</span>')
        
        return format_html(' '.join(status_parts))
    
    status_display.short_description = "Status"
    
    def participation_display(self, obj):
        """Display participation rate"""
        rate = obj.participation_rate
        color = "#28a745" if rate >= 80 else "#ffc107" if rate >= 50 else "#dc3545"
        return format_html(
            f'<span style="color: {color};">{rate:.1f}% ({obj.total_votes}/{obj.eligible_voters.count()})</span>'
        )
    
    participation_display.short_description = "Participation"


@admin.register(AdminVote)
class AdminVoteAdmin(admin.ModelAdmin):
    """Admin interface for votes - read only"""
    
    list_display = [
        'poll', 'voter', 'timestamp', 'vote_summary'
    ]
    list_filter = ['timestamp', 'poll__title']
    readonly_fields = [
        'poll', 'voter', 'timestamp', 'selected_option', 
        'rating_value', 'text_response'
    ]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs
    
    def has_module_permission(self, request):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return False  # Votes created through interface only
    
    def has_change_permission(self, request, obj=None):
        return False  # Votes cannot be modified
    
    def has_delete_permission(self, request, obj=None):
        return False  # Keep audit trail
    
    def vote_summary(self, obj):
        """Show vote summary"""
        if obj.selected_option:
            return f"Selected: {obj.selected_option.option_text[:30]}"
        elif obj.rating_value:
            return f"Rating: {obj.rating_value}/10"
        elif obj.text_response:
            return f"Response: {obj.text_response[:30]}..."
        return "No vote data"
    
    vote_summary.short_description = "Vote"


@admin.register(AdminPollReport)
class AdminPollReportAdmin(admin.ModelAdmin):
    """Admin interface for reports"""
    
    list_display = ['title', 'poll', 'generated_by', 'generated_at']
    list_filter = ['generated_at', 'generated_by']
    readonly_fields = ['generated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs
    
    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(AdminPollAudit)
class AdminPollAuditAdmin(admin.ModelAdmin):
    """Admin interface for audit logs"""
    
    list_display = ['user', 'action', 'poll', 'timestamp']
    list_filter = ['action', 'timestamp']
    readonly_fields = ['user', 'action', 'poll', 'timestamp', 'description']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs
    
    def has_module_permission(self, request):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False