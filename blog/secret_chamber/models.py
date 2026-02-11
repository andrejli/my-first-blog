"""
Admin Polling System - Phase 1: Basic Models
Simple admin-only polling system to be enhanced to Secret Chamber
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
import json


"""
Admin Polling System - Phase 1: Basic Models
Simple admin-only polling system to be enhanced to Secret Chamber
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError


class AdminPoll(models.Model):
    """Simple admin poll - Phase 1 implementation"""
    
    POLL_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('yes_no', 'Yes/No Vote'),
        ('rating', 'Rating (1-10)'),
        ('open_response', 'Open Response'),
    ]
    
    title = models.CharField(max_length=200, help_text="Poll question")
    description = models.TextField(blank=True, help_text="Additional context")
    poll_type = models.CharField(max_length=20, choices=POLL_TYPES, default='multiple_choice')
    
    # Basic timing
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_admin_polls')
    created_at = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(help_text="When voting closes")
    
    # Simple settings
    is_active = models.BooleanField(default=True)
    allow_comments = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Admin Poll"
        verbose_name_plural = "Admin Polls"
    
    def __str__(self):
        return self.title
    
    def clean(self):
        """Enhanced validation with security measures"""
        # Basic date validation
        if self.end_date and self.end_date <= timezone.now():
            raise ValidationError("End date must be in the future")
        
        # Security: Prevent modification of polls with votes
        if self.pk and self.admin_votes.exists():
            # Check if any critical fields are being changed
            if hasattr(self, '_state') and self._state.db:
                original = AdminPoll.objects.get(pk=self.pk)
                if (self.title != original.title or 
                    self.description != original.description or 
                    self.poll_type != original.poll_type or 
                    self.end_date != original.end_date):
                    raise ValidationError(
                        "Cannot modify poll details after voting has started. "
                        "This restriction protects voting integrity and security."
                    )
        
        # Security: Prevent modification of completed polls
        if self.pk and self.is_completed:
            if hasattr(self, '_state') and self._state.db:
                original = AdminPoll.objects.get(pk=self.pk)
                if (self.title != original.title or 
                    self.description != original.description or 
                    self.poll_type != original.poll_type):
                    raise ValidationError(
                        "Cannot modify completed poll details. "
                        "This restriction maintains audit trail integrity."
                    )
    
    @property
    def is_open(self):
        """Check if voting is open"""
        if not self.end_date:
            return self.is_active
        return self.is_active and timezone.now() <= self.end_date
    
    @property
    def is_completed(self):
        """Check if poll is completed"""
        if not self.end_date:
            return not self.is_active or self.all_admins_voted
        return timezone.now() > self.end_date or not self.is_active or self.all_admins_voted
    
    @property
    def all_admins_voted(self):
        """Check if all eligible admins have voted"""
        eligible_count = self.eligible_voters.count()
        if eligible_count == 0:
            return False
        return self.total_votes >= eligible_count
    
    @property
    def can_view_results(self):
        """Check if results can be viewed (poll ended or all admins voted)"""
        return self.is_completed or self.all_admins_voted
    
    @property
    def total_votes(self):
        """Get total votes"""
        return self.admin_votes.count()
    
    @property
    def eligible_voters(self):
        """Get all superusers"""
        return User.objects.filter(is_superuser=True, is_active=True)
    
    @property
    def participation_rate(self):
        """Calculate participation percentage"""
        eligible = self.eligible_voters.count()
        if eligible == 0:
            return 0
        return (self.total_votes / eligible) * 100
    
    def can_user_vote(self, user):
        """Check if user can vote"""
        if not (user.is_authenticated and user.is_superuser):
            return False
        
        if not self.is_open:
            return False
        
        # Check if already voted
        return not self.admin_votes.filter(voter=user).exists()


class PollOption(models.Model):
    """Options for multiple choice polls"""
    
    poll = models.ForeignKey(AdminPoll, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=300)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'id']
        unique_together = ['poll', 'option_text']
    
    def __str__(self):
        return f"{self.poll.title}: {self.option_text[:50]}"
    
    @property
    def vote_count(self):
        """Count votes for this option"""
        return self.poll.admin_votes.filter(selected_option=self).count()


class AdminVote(models.Model):
    """Simple admin vote - no encryption in Phase 1"""
    
    poll = models.ForeignKey(AdminPoll, on_delete=models.CASCADE, related_name='admin_votes')
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_votes')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Vote content (simple, no encryption)
    selected_option = models.ForeignKey(PollOption, on_delete=models.CASCADE, null=True, blank=True)
    rating_value = models.IntegerField(null=True, blank=True, help_text="1-10 rating")
    text_response = models.TextField(blank=True, help_text="Open response or comment")
    
    class Meta:
        unique_together = ['poll', 'voter']  # One vote per user per poll
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.voter.username} voted on {self.poll.title}"
    
    def clean(self):
        """Validate vote content based on poll type"""
        if self.poll.poll_type == 'multiple_choice' and not self.selected_option:
            raise ValidationError("Multiple choice polls require a selected option")
        
        if self.poll.poll_type == 'rating':
            if not self.rating_value or not (1 <= self.rating_value <= 10):
                raise ValidationError("Rating must be between 1 and 10")


class AdminPollReport(models.Model):
    """Simple reports for admin polls"""
    
    poll = models.OneToOneField(AdminPoll, on_delete=models.CASCADE, related_name='report')
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Report content in markdown")
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"Report: {self.poll.title}"


class AdminPollAudit(models.Model):
    """Basic audit log for admin polling"""
    
    ACTION_TYPES = [
        ('poll_created', 'Poll Created'),
        ('vote_cast', 'Vote Cast'),
        ('poll_closed', 'Poll Closed'),
        ('report_generated', 'Report Generated'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    poll = models.ForeignKey(AdminPoll, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=200)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"