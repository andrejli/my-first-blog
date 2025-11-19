"""
Django forms for the FORTIS AURIS LMS (Learning Management System).

This module contains form classes for:
- Event management (creation, editing, filtering)
- Custom event types
- Calendar functionality with recurring events
- Course and lesson linking
- Custom widgets for weekday selection

The forms include comprehensive validation and custom widgets for enhanced
user experience, especially for recurring event management.
"""

from django import forms
from django.contrib.auth.models import User
from .models import Event, EventType, Course, Lesson


class WeekdayCheckboxWidget(forms.CheckboxSelectMultiple):
    """
    Custom widget for selecting weekdays with checkboxes.
    
    Provides a user-friendly checkbox interface for selecting multiple
    weekdays for recurring events. Handles conversion between list format
    (for display) and comma-separated string format (for storage).
    
    Attributes:
        template_name (str): Django template for checkbox group rendering
        option_template_name (str): Django template for individual checkbox rendering
    """
    template_name = 'django/forms/widgets/checkbox_select.html'
    option_template_name = 'django/forms/widgets/checkbox_option.html'
    
    def __init__(self, attrs=None):
        """
        Initialize weekday choices.
        
        Args:
            attrs (dict, optional): HTML attributes for the widget
        """
        weekday_choices = [
            (0, 'Monday'),
            (1, 'Tuesday'), 
            (2, 'Wednesday'),
            (3, 'Thursday'),
            (4, 'Friday'),
            (5, 'Saturday'),
            (6, 'Sunday'),
        ]
        super().__init__(attrs=attrs, choices=weekday_choices)
        
    def optgroups(self, name, value, attrs=None):
        """
        Override to handle comma-separated string values.
        
        Converts stored comma-separated string back to list of integers
        for proper checkbox rendering.
        
        Args:
            name (str): Field name
            value (str or list): Current field value
            attrs (dict, optional): HTML attributes
            
        Returns:
            list: Option groups for rendering
        """
        if isinstance(value, str) and value:
            # Convert comma-separated string to list of integers for rendering
            try:
                value = [int(day.strip()) for day in value.split(',') if day.strip().isdigit()]
            except (ValueError, AttributeError):
                value = []
        return super().optgroups(name, value, attrs)
        
    def value_from_datadict(self, data, files, name):
        """
        Extract the value from form data.
        
        Handles both QueryDict (web requests) and regular dict (tests).
        
        Args:
            data (QueryDict or dict): Form data
            files (MultiValueDict): Uploaded files
            name (str): Field name
            
        Returns:
            list: List of selected weekday integers
        """
        if hasattr(data, 'getlist'):
            values = data.getlist(name)
        else:
            # Handle regular dict (in tests)
            value = data.get(name, [])
            values = value if isinstance(value, list) else [value] if value else []
        
        if values:
            try:
                return [int(val) for val in values if val != '' and val is not None]
            except (ValueError, TypeError):
                return []
        return []


class WeekdayMultipleChoiceField(forms.MultipleChoiceField):
    """
    Custom field for selecting multiple weekdays.
    
    Stores selected weekdays as comma-separated string (e.g., "0,2,4" for
    Monday, Wednesday, Friday). Provides validation and conversion between
    display format (list) and storage format (string).
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize weekday multiple choice field.
        
        Sets up weekday choices (0-6 for Monday-Sunday) and custom widget.
        
        Args:
            *args: Positional arguments passed to parent
            **kwargs: Keyword arguments passed to parent
        """
        weekday_choices = [
            (0, 'Monday'),
            (1, 'Tuesday'), 
            (2, 'Wednesday'),
            (3, 'Thursday'),
            (4, 'Friday'),
            (5, 'Saturday'),
            (6, 'Sunday'),
        ]
        kwargs['choices'] = weekday_choices
        kwargs['widget'] = WeekdayCheckboxWidget(attrs={'class': 'form-check-input'})
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        """
        Convert to comma-separated string for storage.
        
        Args:
            value (list or str or None): Selected weekdays
            
        Returns:
            str: Comma-separated string of day numbers (e.g., "0,2,4")
        """
        if value is None or value == '' or value == []:
            return ''
        # Convert list of strings/integers to list of integers, then to comma-separated string
        try:
            if isinstance(value, (list, tuple)):
                # Filter out empty strings but keep 0 values
                day_numbers = [int(day) for day in value if day != '' and day is not None]
            else:
                # Single value
                day_numbers = [int(value)] if value != '' and value is not None else []
            return ','.join(map(str, sorted(day_numbers)))
        except (ValueError, TypeError):
            return ''
    
    def prepare_value(self, value):
        """
        Convert stored comma-separated string back to list for display.
        
        Args:
            value (str or list): Stored weekday data
            
        Returns:
            list: List of weekday integers for checkbox rendering
        """
        if not value:
            return []
        try:
            if isinstance(value, str):
                return [int(day.strip()) for day in value.split(',') if day.strip().isdigit()]
            return value
        except (ValueError, AttributeError):
            return []
    
    def validate(self, value):
        """
        Override validation to handle comma-separated string.
        
        Ensures all selected days are valid (0-6) and at least one day
        is selected when required.
        
        Args:
            value (str or list): Value to validate
            
        Raises:
            ValidationError: If value contains invalid day numbers
        """
        # Skip the parent's validation since we're using a different format
        if value and isinstance(value, str):
            # Our format is comma-separated, parent expects individual choices
            try:
                days = [int(day.strip()) for day in value.split(',') if day.strip()]
                for day in days:
                    if day not in [choice[0] for choice in self.choices]:
                        raise forms.ValidationError(f'Invalid day: {day}')
            except (ValueError, AttributeError):
                raise forms.ValidationError('Invalid day format')
        elif value:
            # Normal list format, use parent validation
            super().validate(value)


class EventTypeForm(forms.ModelForm):
    """
    Form for creating and editing custom event types.
    
    Allows administrators to create custom event categories with:
    - Custom colors and icons
    - Slug for URL-friendly identification
    - Sort order for display prioritization
    - Active/inactive status
    """
    
    class Meta:
        model = EventType
        fields = ['name', 'slug', 'color', 'background_color', 'icon', 'description', 'is_active', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Workshop, Seminar, Conference'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., workshop, seminar, conference'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color',
                'value': '#32cd32'
            }),
            'background_color': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color',
                'value': '#0f1419'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., fas fa-laptop-code, fas fa-graduation-cap'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of this event type...'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'value': 0
            }),
        }

    def clean_slug(self):
        """
        Normalize slug to lowercase with hyphens.
        
        Returns:
            str: Cleaned slug (lowercase, spaces replaced with hyphens)
        """
        slug = self.cleaned_data['slug']
        # Convert to lowercase and replace spaces with hyphens
        slug = slug.lower().replace(' ', '-')
        return slug


class EventForm(forms.ModelForm):
    """
    Enhanced form for creating and editing events.
    
    Comprehensive event management form supporting:
    - Custom event types with colors and icons
    - Course and lesson linking
    - Obsidian-style wiki links
    - Zoom integration (meetings and webinars)
    - Recurring event patterns (daily, weekly, biweekly, monthly, yearly)
    - File attachments (posters, materials)
    - Priority and visibility settings
    - Holiday and weekend exclusion for recurring events
    """
    
    event_type_new = forms.ModelChoiceField(
        queryset=EventType.objects.filter(is_active=True).order_by('sort_order', 'name'),
        required=False,
        empty_label="Choose custom event type...",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    course = forms.ModelChoiceField(
        queryset=Course.objects.all().order_by('title'),
        required=False,
        empty_label="No course (general event)",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    linked_lesson = forms.ModelChoiceField(
        queryset=Lesson.objects.all().select_related('course').order_by('course__title', 'order', 'title'),
        required=False,
        empty_label="No direct lesson link",
        widget=forms.Select(attrs={'class': 'form-control lesson-select'})
    )
    
    recurrence_days = WeekdayMultipleChoiceField(
        required=False,
        help_text="Select which days of the week this event should repeat"
    )
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type_new', 'event_type', 'priority', 'visibility',
            'custom_color', 'custom_background', 'start_date', 'end_date', 'all_day',
            'is_published', 'is_featured', 'course', 'linked_lesson', 'obsidian_link', 
            'poster', 'materials', 'zoom_meeting_url', 'zoom_meeting_id', 'zoom_meeting_password',
            'zoom_webinar_url', 'is_recurring', 'recurrence_pattern', 'recurrence_interval',
            'recurrence_days', 'recurrence_end_date', 'max_occurrences', 'exclude_weekends',
            'exclude_holidays'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Event title (max 128 characters)',
                'maxlength': 128
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Event description...'
            }),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'visibility': forms.Select(attrs={'class': 'form-control'}),
            'custom_color': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color',
                'placeholder': 'Optional: Override event type color'
            }),
            'custom_background': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color',
                'placeholder': 'Optional: Override background color'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'all_day': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'linked_lesson': forms.Select(attrs={'class': 'form-control lesson-select'}),
            'obsidian_link': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '[[Course Name - Lesson Title]] or lesson title',
                'data-toggle': 'tooltip',
                'title': 'Use Obsidian-style links like [[Python Basics - Variables and Data Types]]'
            }),
            'poster': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'materials': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt'
            }),
            'zoom_meeting_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://zoom.us/j/1234567890 (complete Zoom meeting join URL)'
            }),
            'zoom_meeting_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 123-456-7890 or 1234567890'
            }),
            'zoom_meeting_password': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Meeting password (optional)'
            }),
            'zoom_webinar_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://zoom.us/webinar/register/... (webinar registration URL)'
            }),
            'is_recurring': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_is_recurring'
            }),
            'recurrence_pattern': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_recurrence_pattern'
            }),
            'recurrence_interval': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 30,
                'placeholder': 'e.g., 1 for every week, 2 for every 2 weeks'
            }),
            'recurrence_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'max_occurrences': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 365,
                'placeholder': 'Maximum number of occurrences'
            }),
            'exclude_weekends': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'exclude_holidays': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize event form with customized choices and defaults.
        
        Sets up:
        - Formatted lesson choices showing "Course - Lesson" format
        - Default values for common fields
        - Help text for recurring event fields
        """
        super().__init__(*args, **kwargs)
        
        # Customize lesson choices to show course + lesson title
        lessons = Lesson.objects.all().select_related('course').order_by('course__title', 'order', 'title')
        lesson_choices = [('', 'No direct lesson link')]
        for lesson in lessons:
            display_name = f"{lesson.course.title} - {lesson.title}"
            lesson_choices.append((lesson.pk, display_name))
        
        self.fields['linked_lesson'].choices = lesson_choices
        
        # Set default values
        self.fields['is_published'].initial = True
        self.fields['recurrence_interval'].initial = 1
        
        # Add help text for recurring fields
        self.fields['recurrence_days'].help_text = (
            "For weekly/biweekly patterns: Enter days of week as numbers "
            "(0=Monday, 1=Tuesday, ... 6=Sunday). Example: 0,2,4 for Mon, Wed, Fri"
        )
        self.fields['recurrence_pattern'].help_text = (
            "Choose how often this event should repeat"
        )
        self.fields['max_occurrences'].help_text = (
            "Maximum number of event instances to create (alternative to end date)"
        )

    def clean(self):
        """
        Comprehensive validation for event data.
        
        Validates:
        - End date is after start date
        - Recurring events have required fields (pattern, end date or max occurrences)
        - Recurrence end date is after start date
        - Weekly/biweekly events have selected weekdays
        - Max occurrences doesn't exceed 365
        
        Returns:
            dict: Cleaned form data
            
        Raises:
            ValidationError: If validation fails
        """
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_recurring = cleaned_data.get('is_recurring', False)
        recurrence_pattern = cleaned_data.get('recurrence_pattern')
        recurrence_end_date = cleaned_data.get('recurrence_end_date')
        max_occurrences = cleaned_data.get('max_occurrences')
        recurrence_days = cleaned_data.get('recurrence_days')
        
        # Basic date validation
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError('End date must be after start date.')
        
        # Recurring event validation
        if is_recurring:
            if not recurrence_pattern:
                raise forms.ValidationError('Recurrence pattern is required for recurring events.')
            
            if not recurrence_end_date and not max_occurrences:
                raise forms.ValidationError('Either end date or maximum occurrences must be specified for recurring events.')
            
            if recurrence_end_date and start_date:
                # Convert both to dates for comparison
                recurrence_date = recurrence_end_date.date() if hasattr(recurrence_end_date, 'date') else recurrence_end_date
                start_date_only = start_date.date() if hasattr(start_date, 'date') else start_date
                if recurrence_date <= start_date_only:
                    raise forms.ValidationError('Recurrence end date must be after the event start date.')
            
            # Validate recurrence_days format for weekly patterns
            if recurrence_pattern in ['weekly', 'biweekly']:
                if not recurrence_days:  # Empty or None
                    raise forms.ValidationError('Please select at least one day of the week for weekly/biweekly events.')
                
                # The recurrence_days field now returns a comma-separated string
                # so we can validate it directly
                if isinstance(recurrence_days, str):
                    try:
                        days = [int(day.strip()) for day in recurrence_days.split(',') if day.strip()]
                        if not all(0 <= day <= 6 for day in days):
                            raise ValueError()
                        if not days:  # Empty list
                            raise ValueError()
                    except (ValueError, AttributeError):
                        raise forms.ValidationError('Please select at least one day of the week for weekly/biweekly events.')
                else:
                    raise forms.ValidationError('Please select at least one day of the week for weekly/biweekly events.')
            
            # Validate max_occurrences
            if max_occurrences and max_occurrences > 365:
                raise forms.ValidationError('Maximum occurrences cannot exceed 365.')
        
        return cleaned_data


class EventFilterForm(forms.Form):
    """
    Form for filtering events in the management interface.
    
    Provides filtering by:
    - Publication status (all, published, draft, featured)
    - Custom event type
    - Legacy event type
    - Priority level
    - Associated course
    """
    
    STATUS_CHOICES = [
        ('', 'All Events'),
        ('published', 'Published'),
        ('draft', 'Draft'),
        ('featured', 'Featured'),
    ]
    
    PRIORITY_CHOICES = [
        ('', 'All Priorities'),
    ] + Event.PRIORITY_CHOICES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    event_type_new = forms.ModelChoiceField(
        queryset=EventType.objects.filter(is_active=True).order_by('sort_order', 'name'),
        required=False,
        empty_label='All Custom Types',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    event_type = forms.ChoiceField(
        choices=[('', 'All Legacy Types')] + Event.EVENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    course = forms.ModelChoiceField(
        queryset=Course.objects.all().order_by('title'),
        required=False,
        empty_label='All Courses',
        widget=forms.Select(attrs={'class': 'form-control'})
    )