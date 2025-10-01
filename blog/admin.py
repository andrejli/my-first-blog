from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from .models import Post, Course, UserProfile, Enrollment, Lesson, Progress


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
    
    def get_enrolled_count(self, obj):
        return obj.get_enrolled_count()
    get_enrolled_count.short_description = 'Enrolled Students'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "instructor":
            # Ensure only instructors are available
            kwargs["queryset"] = User.objects.filter(userprofile__role='instructor')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


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


# Keep the original Post admin
admin.site.register(Post)

