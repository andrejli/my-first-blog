from django import forms
from django.contrib.auth.models import User
from .models import Event, EventType, Course, Lesson


class EventTypeForm(forms.ModelForm):
    """Form for creating and editing custom event types"""
    
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
        slug = self.cleaned_data['slug']
        # Convert to lowercase and replace spaces with hyphens
        slug = slug.lower().replace(' ', '-')
        return slug


class EventForm(forms.ModelForm):
    """Enhanced form for creating and editing events with custom types and colors"""
    
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
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type_new', 'event_type', 'priority', 'visibility',
            'custom_color', 'custom_background', 'start_date', 'end_date', 'all_day',
            'is_published', 'is_featured', 'course', 'linked_lesson', 'obsidian_link', 
            'poster', 'materials'
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customize lesson choices to show course + lesson title
        lessons = Lesson.objects.all().select_related('course').order_by('course__title', 'order', 'title')
        lesson_choices = [('', 'No direct lesson link')]
        for lesson in lessons:
            display_name = f"{lesson.course.title} - {lesson.title}"
            lesson_choices.append((lesson.id, display_name))
        
        self.fields['linked_lesson'].choices = lesson_choices
        
        # Set default values
        self.fields['is_published'].initial = True

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError('End date must be after start date.')
        
        return cleaned_data


class EventFilterForm(forms.Form):
    """Form for filtering events in the management interface"""
    
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