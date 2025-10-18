from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from .models import (
    Post, Course, UserProfile, Enrollment, Lesson, Progress, 
    CourseMaterial, Assignment, Submission,
    Quiz, Question, Answer, QuizAttempt, QuizResponse,
    Announcement, AnnouncementRead,
    Forum, Topic, ForumPost, SiteTheme, UserThemePreference,
    Event
)


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


# Event Administration
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'start_date', 'end_date', 'priority', 'visibility', 'is_published', 'is_featured', 'has_poster', 'has_materials', 'created_by', 'course']
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
        ('Files & Materials', {
            'fields': ('poster', 'materials'),
            'description': 'Upload event poster and materials (admin only)'
        }),
        ('Visibility', {
            'fields': ('is_published', 'is_featured', 'course')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]
    
    def has_poster(self, obj):
        return obj.has_poster
    has_poster.boolean = True
    has_poster.short_description = 'Poster'
    
    def has_materials(self, obj):
        return obj.has_materials
    has_materials.boolean = True
    has_materials.short_description = 'Materials'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new event
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'course')

