from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    Post, BlogPost, Course, UserProfile, Enrollment, Lesson, Progress, 
    CourseMaterial, Assignment, Submission,
    Quiz, Question, Answer, QuizAttempt, QuizResponse,
    Announcement, AnnouncementRead,
    Forum, Topic, ForumPost, SiteTheme, UserThemePreference,
    Event
)
from .forms import WeekdayMultipleChoiceField
from .utils.image_processing import process_uploaded_image, get_image_info
import logging


# Custom form for Course to handle instructor selection
class CourseAdminForm(forms.ModelForm):
    instructor = forms.ModelChoiceField(
        queryset=User.objects.filter(userprofile__role='instructor').order_by('first_name', 'last_name'),
        empty_label="Select an instructor",
        help_text="Only users with instructor role are shown"
    )
    
    class Meta:
        model = Course
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Refresh the queryset to ensure we get current instructors
        self.fields['instructor'].queryset = User.objects.filter(
            userprofile__role='instructor'
        ).order_by('first_name', 'last_name')


# Custom form for Event to handle recurrence_days checkboxes
class EventAdminForm(forms.ModelForm):
    recurrence_days = WeekdayMultipleChoiceField(
        required=False,
        help_text="Select which days of the week this event should repeat"
    )
    
    class Meta:
        model = Event
        fields = '__all__'


# User Profile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_date']
    list_filter = ['role', 'created_date']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    
    def get_queryset(self, request):
        # Make sure we can see all profiles
        return super().get_queryset(request).select_related('user')


# Course Admin
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    form = CourseAdminForm  # Use custom form
    list_display = ['course_code', 'title', 'instructor', 'status', 'created_date', 'get_enrolled_count']
    list_filter = ['status', 'created_date', 'instructor']
    search_fields = ['title', 'course_code', 'description', 'instructor__first_name', 'instructor__last_name']
    readonly_fields = ['created_date']
    actions = ['export_courses', 'export_courses_with_data']
    
    def get_enrolled_count(self, obj):
        return obj.get_enrolled_count()
    get_enrolled_count.short_description = 'Enrolled Students'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "instructor":
            # Ensure only instructors are available
            kwargs["queryset"] = User.objects.filter(userprofile__role='instructor')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def export_courses(self, request, queryset):
        """Export selected courses without student data"""
        from .course_import_export import CourseExporter
        import zipfile
        from io import BytesIO
        from django.http import HttpResponse
        import json
        from datetime import datetime
        
        if queryset.count() == 1:
            # Single course export
            course = queryset.first()
            exporter = CourseExporter(course, include_user_data=False)
            zip_data = exporter.create_zip_export()
            
            response = HttpResponse(zip_data, content_type='application/zip')
            filename = f"{course.course_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            # Batch export
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as batch_zip:
                for course in queryset:
                    exporter = CourseExporter(course, include_user_data=False)
                    course_zip_data = exporter.create_zip_export()
                    course_filename = f"{course.course_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                    batch_zip.writestr(f"courses/{course_filename}", course_zip_data)
            
            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            filename = f"course_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    
    export_courses.short_description = "Export selected courses (template only)"
    
    def export_courses_with_data(self, request, queryset):
        """Export selected courses with student data"""
        from .course_import_export import CourseExporter
        import zipfile
        from io import BytesIO
        from django.http import HttpResponse
        import json
        from datetime import datetime
        
        if queryset.count() == 1:
            # Single course export
            course = queryset.first()
            exporter = CourseExporter(course, include_user_data=True)
            zip_data = exporter.create_zip_export()
            
            response = HttpResponse(zip_data, content_type='application/zip')
            filename = f"{course.course_code}_FULL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            # Batch export
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as batch_zip:
                for course in queryset:
                    exporter = CourseExporter(course, include_user_data=True)
                    course_zip_data = exporter.create_zip_export()
                    course_filename = f"{course.course_code}_FULL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                    batch_zip.writestr(f"courses/{course_filename}", course_zip_data)
            
            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            filename = f"course_batch_FULL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    
    export_courses_with_data.short_description = "Export selected courses (with student data)"


# Enrollment Admin
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'enrollment_date', 'grade']
    list_filter = ['status', 'enrollment_date', 'course']
    search_fields = ['student__username', 'course__title', 'course__course_code']


# Lesson Admin
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'is_published', 'created_date']
    list_filter = ['course', 'is_published', 'created_date']
    search_fields = ['title', 'course__title']
    ordering = ['course', 'order']


# Progress Admin
@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'completed', 'completion_date']
    list_filter = ['completed', 'lesson__course', 'completion_date']
    search_fields = ['student__username', 'lesson__title']


# Course Material Admin
@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'lesson', 'material_type', 'get_file_size', 'is_required', 'uploaded_date']
    list_filter = ['material_type', 'is_required', 'course', 'uploaded_date']
    search_fields = ['title', 'course__title', 'lesson__title']
    
    def get_file_size(self, obj):
        return f"{obj.get_file_size()} MB"
    get_file_size.short_description = 'File Size'


# Assignment Admin
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'due_date', 'max_points', 'is_published', 'get_submission_count']
    list_filter = ['course', 'is_published', 'due_date', 'created_date']
    search_fields = ['title', 'course__title', 'description']
    
    def get_submission_count(self, obj):
        return obj.get_submission_count()
    get_submission_count.short_description = 'Submissions'


# Submission Admin
@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'assignment', 'status', 'submitted_date', 'grade', 'is_late']
    list_filter = ['status', 'assignment__course', 'submitted_date', 'graded_date']
    search_fields = ['student__username', 'assignment__title']
    
    def is_late(self, obj):
        return obj.is_late()
    is_late.boolean = True
    is_late.short_description = 'Late Submission'


# Keep the original Post admin
admin.site.register(Post)


# Quiz System Admin

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2
    fields = ['answer_text', 'is_correct', 'order']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'question_type', 'truncated_text', 'points', 'order']
    list_filter = ['question_type', 'quiz__course', 'quiz']
    search_fields = ['question_text', 'quiz__title']
    inlines = [AnswerInline]
    
    def truncated_text(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    truncated_text.short_description = 'Question Text'


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'quiz_type', 'total_questions', 'points', 'is_published']
    list_filter = ['quiz_type', 'is_published', 'course', 'created_date']
    search_fields = ['title', 'description', 'course__title']
    readonly_fields = ['created_date', 'updated_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'title', 'description', 'quiz_type')
        }),
        ('Timing & Attempts', {
            'fields': ('time_limit', 'max_attempts', 'available_from', 'available_until'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('shuffle_questions', 'show_correct_answers', 'immediate_feedback'),
            'classes': ('collapse',)
        }),
        ('Grading', {
            'fields': ('points', 'passing_score'),
            'classes': ('collapse',)
        }),
        ('Publication', {
            'fields': ('is_published', 'created_date', 'updated_date'),
        }),
    )


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'quiz', 'attempt_number', 'status', 'score', 'percentage', 'started_at', 'completed_at']
    list_filter = ['status', 'quiz__course', 'started_at']
    search_fields = ['student__username', 'quiz__title']
    readonly_fields = ['started_at', 'completed_at', 'time_taken']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'quiz', 'quiz__course')


@admin.register(QuizResponse)
class QuizResponseAdmin(admin.ModelAdmin):
    list_display = ['attempt_student', 'question_text', 'is_correct', 'points_earned', 'answered_at']
    list_filter = ['is_correct', 'question__question_type', 'attempt__quiz__course']
    search_fields = ['attempt__student__username', 'question__question_text']
    
    def attempt_student(self, obj):
        return obj.attempt.student.username
    attempt_student.short_description = 'Student'
    
    def question_text(self, obj):
        return obj.question.question_text[:50] + "..." if len(obj.question.question_text) > 50 else obj.question.question_text
    question_text.short_description = 'Question'


# Course Announcement Admin - ACTIVATED
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'author', 'priority', 'is_published', 'is_pinned', 'created_date']
    list_filter = ['priority', 'is_published', 'is_pinned', 'course', 'created_date']
    search_fields = ['title', 'content', 'course__title', 'course__course_code']
    ordering = ['-created_date']
    readonly_fields = ['created_date', 'published_date']
    
    fieldsets = (
        ('Announcement Details', {
            'fields': ('course', 'title', 'content')
        }),
        ('Settings', {
            'fields': ('priority', 'is_published', 'is_pinned', 'scheduled_for')
        }),
        ('Metadata', {
            'fields': ('author', 'created_date', 'published_date'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new announcement
            obj.author = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Non-superusers can only see announcements for courses they teach
        return qs.filter(course__instructor=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'course':
            if not request.user.is_superuser:
                # Non-superusers can only select courses they teach
                kwargs['queryset'] = Course.objects.filter(instructor=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(AnnouncementRead)
class AnnouncementReadAdmin(admin.ModelAdmin):
    list_display = ['student', 'announcement_title', 'announcement_course', 'read_date']
    list_filter = ['announcement__course', 'read_date']
    search_fields = ['student__username', 'announcement__title']
    readonly_fields = ['read_date']
    
    def announcement_title(self, obj):
        return obj.announcement.title
    announcement_title.short_description = 'Announcement'
    
    def announcement_course(self, obj):
        return obj.announcement.course.course_code
    announcement_course.short_description = 'Course'


# Register remaining models without custom admin
admin.site.register(Answer)


# ================================
# DISCUSSION FORUM ADMIN - Phase 4 Point 2
# ================================

@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ['title', 'forum_type', 'course', 'is_active', 'created_date']
    list_filter = ['forum_type', 'is_active', 'created_date']
    search_fields = ['title', 'description']
    ordering = ['forum_type', 'title']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course')


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'forum', 'created_by', 'created_date', 'is_pinned', 'is_locked', 'post_count']
    list_filter = ['forum', 'is_pinned', 'is_locked', 'created_date']
    search_fields = ['title', 'created_by__username']
    ordering = ['-created_date']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('forum', 'created_by')


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ['topic', 'author', 'created_date', 'is_first_post']
    list_filter = ['topic__forum', 'is_first_post', 'created_date']
    search_fields = ['topic__title', 'author__username', 'content']
    ordering = ['-created_date']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('topic', 'author')


# Site Theme Administration
@admin.register(SiteTheme)
class SiteThemeAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'theme_key', 'is_default', 'is_active', 'created_date']
    list_filter = ['is_default', 'is_active', 'theme_key']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['display_name']
    
    fieldsets = (
        ('Theme Information', {
            'fields': ('name', 'display_name', 'theme_key', 'description')
        }),
        ('Settings', {
            'fields': ('is_default', 'is_active')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Ensure only one default theme
        if obj.is_default:
            SiteTheme.objects.filter(is_default=True).exclude(pk=obj.pk).update(is_default=False)
        super().save_model(request, obj, form, change)


@admin.register(UserThemePreference)
class UserThemePreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'theme', 'created_date', 'updated_date']
    list_filter = ['theme', 'created_date', 'updated_date']
    search_fields = ['user__username', 'user__email', 'theme__display_name']
    ordering = ['-updated_date']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'theme')


# BlogPost Administration with EXIF processing
@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'created_date', 'published_date', 'has_featured_image', 'image_security_status']
    list_filter = ['status', 'created_date', 'published_date', 'author']
    search_fields = ['title', 'content', 'excerpt', 'author__username', 'author__first_name', 'author__last_name']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['-created_date']
    date_hierarchy = 'created_date'
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'author', 'content', 'excerpt')
        }),
        ('Publication', {
            'fields': ('status', 'featured_image', 'published_date'),
            'description': 'Featured images automatically have EXIF metadata removed for privacy protection.'
        }),
        ('Settings', {
            'fields': ('allow_comments',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('view_count', 'created_date', 'updated_date'),
            'classes': ('collapse',),
            'description': 'Read-only fields for tracking and statistics.'
        })
    )
    
    readonly_fields = ['created_date', 'updated_date', 'view_count']
    actions = ['process_featured_images', 'make_published', 'make_draft']
    
    def has_featured_image(self, obj):
        """Display if blog post has a featured image."""
        return bool(obj.featured_image)
    has_featured_image.boolean = True
    has_featured_image.short_description = 'Featured Image'
    
    def image_security_status(self, obj):
        """Display security status of featured image."""
        if not obj.featured_image:
            return format_html('<span style="color: gray;">No Image</span>')
        
        try:
            # Check if image has EXIF data
            obj.featured_image.seek(0)
            image_info = get_image_info(obj.featured_image)
            if image_info.get('has_exif', False):
                return format_html('<span style="color: red;">⚠️ Has EXIF</span>')
            else:
                return format_html('<span style="color: green;">✓ Clean</span>')
        except Exception:
            return format_html('<span style="color: orange;">Unknown</span>')
    image_security_status.short_description = 'Image Security'
    
    def process_featured_images(self, request, queryset):
        """Admin action to process featured images and remove EXIF data."""
        processed_count = 0
        error_count = 0
        
        for blog_post in queryset:
            if blog_post.featured_image:
                try:
                    # Process the image
                    blog_post.featured_image.seek(0)
                    processed_image, processing_info = process_uploaded_image(
                        blog_post.featured_image, 
                        strip_exif=True
                    )
                    
                    if processing_info.get('exif_removed', False):
                        # Save the processed image
                        blog_post.featured_image.save(
                            blog_post.featured_image.name,
                            processed_image,
                            save=True
                        )
                        processed_count += 1
                        
                        # Log the processing
                        logger = logging.getLogger(__name__)
                        logger.info(f"Admin EXIF removal: {blog_post.title} (ID: {blog_post.id}) processed by {request.user.username}")
                    
                except Exception as e:
                    error_count += 1
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to process featured image for {blog_post.title}: {str(e)}")
        
        if processed_count > 0:
            self.message_user(
                request,
                f'Successfully processed {processed_count} featured images. EXIF metadata removed.',
                level='SUCCESS'
            )
        if error_count > 0:
            self.message_user(
                request,
                f'Failed to process {error_count} images. Check logs for details.',
                level='WARNING'
            )
        if processed_count == 0 and error_count == 0:
            self.message_user(
                request,
                'No images found to process or all images are already clean.',
                level='INFO'
            )
    
    process_featured_images.short_description = "Remove EXIF metadata from featured images"
    
    def make_published(self, request, queryset):
        """Admin action to publish selected blog posts."""
        updated = queryset.update(status='published')
        self.message_user(
            request,
            f'{updated} blog posts were successfully published.',
            level='SUCCESS'
        )
    make_published.short_description = "Mark selected posts as published"
    
    def make_draft(self, request, queryset):
        """Admin action to set selected blog posts as draft."""
        updated = queryset.update(status='draft')
        self.message_user(
            request,
            f'{updated} blog posts were set to draft status.',
            level='SUCCESS'
        )
    make_draft.short_description = "Mark selected posts as draft"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author')


# Event Administration
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm  # Use custom form for checkboxes
    list_display = ['title', 'event_type', 'start_date', 'end_date', 'priority', 'visibility', 'is_published', 'is_featured', 'has_poster', 'has_materials', 'has_zoom', 'created_by', 'course']
    list_filter = ['event_type', 'priority', 'visibility', 'is_published', 'is_featured', 'start_date', 'created_by']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'
    
    fieldsets = [
        ('Event Information', {
            'fields': ('title', 'description', 'event_type', 'priority', 'visibility')
        }),
        ('Date & Time', {
            'fields': ('start_date', 'end_date', 'all_day')
        }),
        ('Zoom Meeting Integration', {
            'fields': ('zoom_meeting_url', 'zoom_meeting_id', 'zoom_meeting_password', 'zoom_webinar_url'),
            'description': 'Add Zoom meeting or webinar links for virtual events'
        }),
        ('Files & Materials', {
            'fields': ('poster', 'materials'),
            'description': 'Upload event poster and materials (admin only)'
        }),
        ('Course Integration', {
            'fields': ('course', 'linked_lesson', 'obsidian_link'),
            'classes': ('collapse',),
            'description': 'Link event to course content'
        }),
        ('Visibility & Publishing', {
            'fields': ('is_published', 'is_featured')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]
    
    actions = ['process_poster_images', 'export_to_ical', 'show_import_instructions', 'go_to_import_export_interface']
    
    def has_poster(self, obj):
        return obj.has_poster
    has_poster.boolean = True
    has_poster.short_description = 'Poster'
    
    def has_materials(self, obj):
        return obj.has_materials
    has_materials.boolean = True
    has_materials.short_description = 'Materials'
    
    def has_zoom(self, obj):
        return obj.has_zoom_info
    has_zoom.boolean = True
    has_zoom.short_description = 'Zoom'
    
    def go_to_import_export_interface(self, request, queryset=None):
        """Redirect to dedicated import/export interface."""
        from django.shortcuts import redirect
        return redirect('ical_import_export_page')
    go_to_import_export_interface.short_description = "🚀 Go to iCal Import/Export Interface"
    
    def show_import_instructions(self, request, queryset=None):
        """Show import instructions without requiring event selection."""
        from django.contrib import messages
        
        instructions = """
        📅 EASY iCal Import/Export - Multiple Options Available:
        
        🌟 OPTION 1: WEB INTERFACE (Recommended)
        Click "🚀 Go to iCal Import/Export Interface" action above for easy web-based import/export
        
        🔧 OPTION 2: Management Commands
        Open terminal in project folder and run:
        
        📥 IMPORT:
        python manage.py import_ical your_file.ics --dry-run --creator=admin
        python manage.py import_ical your_file.ics --creator=admin --default-course=CS101
        
        📤 EXPORT: 
        python manage.py export_ical events.ics --published-only
        python manage.py export_ical events.ics --course=CS101 --start-date=2024-01-01
        
        ✅ SUPPORTED: Google Calendar, Outlook, Apple Calendar
        🔍 FEATURES: Duplicate detection, course assignment, date filtering
        """
        
        self.message_user(
            request,
            instructions,
            level=messages.INFO
        )
        
        # Additional success message
        self.message_user(
            request,
            '💡 Use the web interface for the easiest import/export experience!',
            level=messages.SUCCESS
        )
    show_import_instructions.short_description = "📋 Show iCal Import/Export Instructions"
    
    def export_to_ical(self, request, queryset):
        """Export selected events to iCal format."""
        import io
        from django.http import HttpResponse
        from datetime import datetime
        
        # Create iCal content
        ical_content = self._create_ical_content(queryset)
        
        # Create HTTP response
        response = HttpResponse(ical_content, content_type='text/calendar')
        response['Content-Disposition'] = f'attachment; filename="events_{datetime.now().strftime("%Y%m%d")}.ics"'
        
        self.message_user(
            request,
            f'Exported {queryset.count()} events to iCal format.',
            level='SUCCESS'
        )
        
        return response
    export_to_ical.short_description = "📤 Export selected events to iCal (.ics)"
    
    def _create_ical_content(self, queryset):
        """Create iCal content from event queryset."""
        from datetime import datetime
        
        lines = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//FORTIS AURIS LMS//Event Calendar//EN',
            'CALSCALE:GREGORIAN',
            'METHOD:PUBLISH',
        ]
        
        for event in queryset:
            # Format dates for iCal
            start_dt = event.start_date.strftime('%Y%m%dT%H%M%S')
            end_dt = event.end_date.strftime('%Y%m%dT%H%M%S') if event.end_date else start_dt
            created_dt = event.created_at.strftime('%Y%m%dT%H%M%SZ')
            
            lines.extend([
                'BEGIN:VEVENT',
                f'UID:{event.id}@fortisauris.lms',
                f'DTSTART:{start_dt}',
                f'DTEND:{end_dt}',
                f'DTSTAMP:{created_dt}',
                f'SUMMARY:{event.title}',
                f'DESCRIPTION:{event.description or ""}',
                f'LOCATION:{event.course.title if event.course else ""}',
                f'CATEGORIES:{event.get_event_type_display()}',
                f'PRIORITY:{self._get_ical_priority(event.priority)}',
                'END:VEVENT',
            ])
        
        lines.append('END:VCALENDAR')
        return '\r\n'.join(lines)
    
    def _get_ical_priority(self, priority):
        """Convert LMS priority to iCal priority (1=high, 5=medium, 9=low)."""
        priority_map = {
            'urgent': '1',
            'high': '3', 
            'normal': '5',
            'low': '9'
        }
        return priority_map.get(priority, '5')
    
    def process_poster_images(self, request, queryset):
        """Admin action to process poster images and remove EXIF data."""
        processed_count = 0
        error_count = 0
        
        for event in queryset:
            if event.poster:
                try:
                    # Process the poster image
                    event.poster.seek(0)
                    processed_image, processing_info = process_uploaded_image(
                        event.poster, 
                        strip_exif=True
                    )
                    
                    if processing_info.get('exif_removed', False):
                        # Save the processed image
                        event.poster.save(
                            event.poster.name,
                            processed_image,
                            save=True
                        )
                        processed_count += 1
                        
                        # Log the processing
                        logger = logging.getLogger(__name__)
                        logger.info(f"Admin EXIF removal: Event '{event.title}' (ID: {event.id}) poster processed by {request.user.username}")
                    
                except Exception as e:
                    error_count += 1
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to process poster image for event '{event.title}': {str(e)}")
        
        if processed_count > 0:
            self.message_user(
                request,
                f'Successfully processed {processed_count} event posters. EXIF metadata removed.',
                level='SUCCESS'
            )
        if error_count > 0:
            self.message_user(
                request,
                f'Failed to process {error_count} poster images. Check logs for details.',
                level='WARNING'
            )
        if processed_count == 0 and error_count == 0:
            self.message_user(
                request,
                'No poster images found to process or all images are already clean.',
                level='INFO'
            )
    
    process_poster_images.short_description = "Remove EXIF metadata from poster images"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new event
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        
        # Auto-generate recurring instances if this is a new recurring event
        if obj.is_recurring and not change:
            instances = obj.generate_recurring_events()
            if instances:
                self.message_user(
                    request,
                    f'Created recurring event with {len(instances)} instances.',
                    level='SUCCESS'
                )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'course')


# =============================================================================
# SECURITY MONITORING ADMIN - Import from separate admin file
# =============================================================================

# Import security admin classes (they self-register)
from .admin_security import *

