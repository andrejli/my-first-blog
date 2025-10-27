"""
Secret Chamber Forms
Forms for poll creation, voting, and administration
"""
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from .models import SecretPoll, PollOption, AnonymousVote


class PollCreationForm(forms.ModelForm):
    """Form for creating new polls"""
    
    # Additional fields for poll options
    option_1 = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Option 1 (required for multiple choice polls)'
        })
    )
    option_2 = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Option 2'
        })
    )
    option_3 = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Option 3'
        })
    )
    option_4 = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Option 4'
        })
    )
    option_5 = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Option 5'
        })
    )
    
    class Meta:
        model = SecretPoll
        fields = [
            'title', 'description', 'poll_type', 'start_date', 'end_date',
            'anonymity_level', 'quorum_required', 'require_all_admins',
            'allow_comments', 'results_public'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter poll title/question'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide context and background for this decision...'
            }),
            'poll_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'anonymity_level': forms.Select(attrs={'class': 'form-control'}),
            'quorum_required': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '0 (no minimum)'
            }),
            'require_all_admins': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'results_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default dates
        now = timezone.now()
        self.fields['start_date'].initial = now
        self.fields['end_date'].initial = now + timedelta(days=7)
        
        # Add help text
        self.fields['title'].help_text = "Clear, concise question for admins to vote on"
        self.fields['description'].help_text = "Detailed context, background, and any relevant information"
        self.fields['anonymity_level'].help_text = "Level of voter anonymity for this poll"
        self.fields['quorum_required'].help_text = "Minimum number of votes required (0 = no minimum)"
        self.fields['require_all_admins'].help_text = "Poll auto-completes when all admins vote"
        self.fields['allow_comments'].help_text = "Allow voters to add optional comments"
        self.fields['results_public'].help_text = "Show results during voting (not recommended for sensitive topics)"
    
    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        
        # Validate dates
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("End date must be after start date")
            
            if end_date <= timezone.now():
                raise ValidationError("End date must be in the future")
            
            # Check minimum duration (at least 1 hour)
            if (end_date - start_date).total_seconds() < 3600:
                raise ValidationError("Poll must be open for at least 1 hour")
        
        # Validate poll options for multiple choice polls
        poll_type = cleaned_data.get('poll_type')
        if poll_type in ['multiple_choice', 'ranking', 'approval']:
            options = []
            for i in range(1, 6):
                option = cleaned_data.get(f'option_{i}', '').strip()
                if option:
                    options.append(option)
            
            if poll_type in ['multiple_choice', 'ranking'] and len(options) < 2:
                raise ValidationError(f"{poll_type.replace('_', ' ').title()} polls require at least 2 options")
        
        return cleaned_data


class VoteForm(forms.Form):
    """Base form for voting"""
    
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional comment (will be included anonymously)...'
        }),
        help_text="Optional anonymous comment about your vote"
    )
    
    def __init__(self, poll, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.poll = poll
        
        # Add poll-specific fields
        if poll.poll_type == 'multiple_choice':
            choices = [(opt.id, opt.option_text) for opt in poll.options.all()]
            self.fields['option'] = forms.ChoiceField(
                choices=choices,
                widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                required=True
            )
        
        elif poll.poll_type == 'rating':
            self.fields['rating'] = forms.IntegerField(
                min_value=1,
                max_value=10,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'min': 1,
                    'max': 10,
                    'step': 1
                }),
                help_text="Rate from 1 (strongly disagree) to 10 (strongly agree)"
            )
        
        elif poll.poll_type == 'open_response':
            self.fields['response'] = forms.CharField(
                widget=forms.Textarea(attrs={
                    'class': 'form-control',
                    'rows': 5,
                    'placeholder': 'Enter your detailed response...'
                }),
                required=True,
                help_text="Provide your detailed thoughts and reasoning"
            )
        
        elif poll.poll_type == 'ranking':
            # Create ranking fields for each option
            for option in poll.options.all():
                field_name = f'rank_{option.id}'
                self.fields[field_name] = forms.IntegerField(
                    min_value=1,
                    max_value=poll.options.count(),
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control ranking-input',
                        'min': 1,
                        'max': poll.options.count()
                    }),
                    label=f"Rank for: {option.option_text}",
                    required=True
                )
        
        elif poll.poll_type == 'approval':
            self.fields['approval'] = forms.ChoiceField(
                choices=[
                    ('approve', 'Approve'),
                    ('reject', 'Reject'),
                    ('abstain', 'Abstain')
                ],
                widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                required=True
            )
        
        elif poll.poll_type == 'budget':
            # Budget allocation fields
            total_budget = 100  # Percentage
            for option in poll.options.all():
                field_name = f'budget_{option.id}'
                self.fields[field_name] = forms.IntegerField(
                    min_value=0,
                    max_value=100,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control budget-input',
                        'min': 0,
                        'max': 100,
                        'step': 1
                    }),
                    label=f"% for: {option.option_text}",
                    required=True,
                    initial=0
                )
        
        # Hide comment field if not allowed
        if not poll.allow_comments:
            del self.fields['comment']
    
    def clean(self):
        """Validate vote data"""
        cleaned_data = super().clean()
        
        # Validate ranking (no duplicates)
        if self.poll.poll_type == 'ranking':
            ranks = []
            for field_name, value in cleaned_data.items():
                if field_name.startswith('rank_') and value is not None:
                    ranks.append(value)
            
            if len(ranks) != len(set(ranks)):
                raise ValidationError("Each option must have a unique rank")
            
            expected_ranks = list(range(1, len(ranks) + 1))
            if sorted(ranks) != expected_ranks:
                raise ValidationError("Ranks must be consecutive starting from 1")
        
        # Validate budget allocation (must sum to 100%)
        elif self.poll.poll_type == 'budget':
            budget_total = 0
            for field_name, value in cleaned_data.items():
                if field_name.startswith('budget_') and value is not None:
                    budget_total += value
            
            if budget_total != 100:
                raise ValidationError(f"Budget allocation must total 100% (currently {budget_total}%)")
        
        return cleaned_data


class CommentForm(forms.Form):
    """Form for adding comments to polls"""
    
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Share your thoughts (will be posted anonymously)...'
        }),
        help_text="Your comment will be posted anonymously"
    )


class PollFilterForm(forms.Form):
    """Form for filtering polls in list view"""
    
    STATUS_CHOICES = [
        ('', 'All Polls'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('scheduled', 'Scheduled'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    poll_type = forms.ChoiceField(
        choices=[('', 'All Types')] + SecretPoll.POLL_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search polls...'
        })
    )


class ReportGenerationForm(forms.Form):
    """Form for generating decision reports"""
    
    REPORT_TYPES = [
        ('poll_results', 'Poll Results Report'),
        ('decision_analysis', 'Decision Analysis'),
        ('governance_report', 'Governance Summary'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    include_comments = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Include anonymous comments in the report"
    )
    
    include_statistics = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Include detailed statistical analysis"
    )
    
    mark_confidential = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Mark report as confidential (admin-only access)"
    )