from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse
from .models import Post, Course, Enrollment, Lesson, Progress, UserProfile


# Authentication Views
def user_login(request):
    """Login view for students and instructors"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Redirect based on user role
            try:
                profile = UserProfile.objects.get(user=user)
                if profile.role == 'admin':
                    return redirect('/admin/')
                elif profile.role == 'instructor':
                    return redirect('instructor_dashboard')
                else:  # student
                    return redirect('student_dashboard')
            except UserProfile.DoesNotExist:
                return redirect('course_list')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'blog/login.html')


def user_logout(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('course_list')


def user_register(request):
    """Registration view for new students"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile (signal should handle this, but let's be explicit)
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'student'}
            )
            
            # Log the user in
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome {username}! Your account has been created.')
                return redirect('student_dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'blog/register.html', {'form': form})


# Legacy blog view (keep for backward compatibility)
def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})


# Course listing view
def course_list(request):
    """Display all published courses"""
    courses = Course.objects.filter(status='published').order_by('-published_date')
    return render(request, 'blog/course_list.html', {'courses': courses})


# Course detail view
def course_detail(request, course_id):
    """Display course details and lessons"""
    course = get_object_or_404(Course, id=course_id, status='published')
    lessons = Lesson.objects.filter(course=course, is_published=True).order_by('order')
    
    # Check if user is enrolled (if logged in)
    is_enrolled = False
    enrollment = None
    user_progress = {}
    
    if request.user.is_authenticated:
        try:
            enrollment = Enrollment.objects.get(student=request.user, course=course)
            is_enrolled = True
            
            # Get user progress for each lesson
            progress_queryset = Progress.objects.filter(student=request.user, lesson__course=course)
            user_progress = {p.lesson.pk: p.completed for p in progress_queryset}
            
        except Enrollment.DoesNotExist:
            pass
    
    context = {
        'course': course,
        'lessons': lessons,
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
        'user_progress': user_progress,
        'total_lessons': lessons.count(),
        'completed_lessons': sum(user_progress.values()) if user_progress else 0,
    }
    
    return render(request, 'blog/course_detail.html', context)


# Lesson detail view
@login_required
def lesson_detail(request, course_id, lesson_id):
    """Display individual lesson content"""
    course = get_object_or_404(Course, id=course_id, status='published')
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course, is_published=True)
    
    # Check if user is enrolled
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, 'You must be enrolled in this course to view lessons.')
        return redirect('course_detail', course_id=course_id)
    
    # Get or create progress for this lesson
    progress, created = Progress.objects.get_or_create(
        student=request.user,
        lesson=lesson,
        defaults={'completed': False}
    )
    
    # Get all lessons for navigation
    all_lessons = Lesson.objects.filter(course=course, is_published=True).order_by('order')
    lesson_list = list(all_lessons)
    current_index = lesson_list.index(lesson)
    
    # Previous and next lessons
    prev_lesson = lesson_list[current_index - 1] if current_index > 0 else None
    next_lesson = lesson_list[current_index + 1] if current_index < len(lesson_list) - 1 else None
    
    context = {
        'course': course,
        'lesson': lesson,
        'progress': progress,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'lesson_number': current_index + 1,
        'total_lessons': len(lesson_list),
    }
    
    return render(request, 'blog/lesson_detail.html', context)


# Course enrollment view
@login_required
def enroll_course(request, course_id):
    """Handle course enrollment with capacity and prerequisite checks"""
    course = get_object_or_404(Course, id=course_id, status='published')
    
    # Check if user has a profile
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, 'Please complete your profile setup before enrolling.')
        return redirect('course_detail', course_id=course_id)
    
    # Check if already enrolled
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
        if enrollment.status == 'dropped':
            # Re-enroll if previously dropped
            enrollment.status = 'enrolled'
            enrollment.enrollment_date = timezone.now()
            enrollment.save()
            messages.success(request, f'Successfully re-enrolled in {course.title}!')
        else:
            messages.info(request, f'You are already enrolled in {course.title}.')
        return redirect('course_detail', course_id=course_id)
    except Enrollment.DoesNotExist:
        pass
    
    # Check course capacity
    current_enrollment = course.get_enrolled_count()
    if current_enrollment >= course.max_students:
        messages.error(request, f'Course is full! ({current_enrollment}/{course.max_students} students enrolled)')
        return redirect('course_detail', course_id=course_id)
    
    # Create enrollment
    enrollment = Enrollment.objects.create(
        student=request.user,
        course=course,
        status='enrolled'
    )
    
    messages.success(request, f'Successfully enrolled in {course.title}! ({current_enrollment + 1}/{course.max_students} enrolled)')
    return redirect('course_detail', course_id=course_id)


# Drop course view
@login_required
def drop_course(request, course_id):
    """Handle course withdrawal"""
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        
        try:
            enrollment = Enrollment.objects.get(student=request.user, course=course)
            if enrollment.status == 'enrolled':
                enrollment.status = 'dropped'
                enrollment.save()
                messages.success(request, f'Successfully dropped from {course.title}.')
            else:
                messages.info(request, f'You are not currently enrolled in {course.title}.')
        except Enrollment.DoesNotExist:
            messages.error(request, f'You are not enrolled in {course.title}.')
        
        return redirect('course_detail', course_id=course_id)
    
    return redirect('course_list')


# Student dashboard
@login_required
def student_dashboard(request):
    """Display student's enrolled courses and progress"""
    if not hasattr(request.user, 'userprofile'):
        messages.warning(request, 'Please complete your profile setup.')
        return redirect('course_list')
    
    # Get user's enrollments
    enrollments = Enrollment.objects.filter(
        student=request.user,
        status='enrolled'
    ).select_related('course').order_by('-enrollment_date')
    
    # Calculate progress for each course
    course_progress = []
    for enrollment in enrollments:
        course = enrollment.course
        total_lessons = Lesson.objects.filter(course=course, is_published=True).count()
        completed_lessons = Progress.objects.filter(
            student=request.user,
            lesson__course=course,
            completed=True
        ).count()
        
        progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        course_progress.append({
            'enrollment': enrollment,
            'course': course,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percentage': progress_percentage,
        })
    
    # Get completed courses
    completed_enrollments = Enrollment.objects.filter(
        student=request.user,
        status='completed'
    ).select_related('course').order_by('-completion_date')
    
    context = {
        'course_progress': course_progress,
        'completed_enrollments': completed_enrollments,
        'total_enrolled': enrollments.count(),
        'total_completed': completed_enrollments.count(),
    }
    
    return render(request, 'blog/student_dashboard.html', context)


# Instructor dashboard
@login_required
def instructor_dashboard(request):
    """Display instructor's courses and student management"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'instructor':
        messages.error(request, 'Access denied. Instructor privileges required.')
        return redirect('course_list')
    
    # Get instructor's courses
    courses = Course.objects.filter(instructor=request.user).order_by('-created_date')
    
    # Calculate stats for each course
    course_stats = []
    for course in courses:
        enrolled_count = course.get_enrolled_count()
        total_lessons = Lesson.objects.filter(course=course, is_published=True).count()
        
        # Get recent enrollments
        recent_enrollments = Enrollment.objects.filter(
            course=course,
            status='enrolled'
        ).select_related('student').order_by('-enrollment_date')[:5]
        
        course_stats.append({
            'course': course,
            'enrolled_count': enrolled_count,
            'total_lessons': total_lessons,
            'recent_enrollments': recent_enrollments,
            'capacity_percentage': (enrolled_count / course.max_students * 100) if course.max_students > 0 else 0,
        })
    
    context = {
        'course_stats': course_stats,
        'total_courses': courses.count(),
        'total_students': sum(stat['enrolled_count'] for stat in course_stats),
    }
    
    return render(request, 'blog/instructor_dashboard.html', context)


# My courses view
@login_required
def my_courses(request):
    """Display user's enrolled courses"""
    enrollments = Enrollment.objects.filter(
        student=request.user,
        status__in=['enrolled', 'completed']
    ).select_related('course').order_by('-enrollment_date')
    
    return render(request, 'blog/my_courses.html', {'enrollments': enrollments})


# Course students view (for instructors)
@login_required
def course_students(request, course_id):
    """Display students enrolled in a course (instructor only)"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor
    if request.user != course.instructor:
        messages.error(request, 'Access denied. You are not the instructor of this course.')
        return redirect('course_detail', course_id=course_id)
    
    # Get enrolled students with their progress
    enrollments = Enrollment.objects.filter(
        course=course,
        status='enrolled'
    ).select_related('student', 'student__userprofile').order_by('enrollment_date')
    
    student_progress = []
    total_lessons = Lesson.objects.filter(course=course, is_published=True).count()
    
    for enrollment in enrollments:
        completed_lessons = Progress.objects.filter(
            student=enrollment.student,
            lesson__course=course,
            completed=True
        ).count()
        
        progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        student_progress.append({
            'enrollment': enrollment,
            'student': enrollment.student,
            'completed_lessons': completed_lessons,
            'total_lessons': total_lessons,
            'progress_percentage': progress_percentage,
        })
    
    context = {
        'course': course,
        'student_progress': student_progress,
        'total_students': enrollments.count(),
        'total_lessons': total_lessons,
    }
    
    return render(request, 'blog/course_students.html', context)


# Mark lesson as complete
@login_required
def mark_lesson_complete(request, course_id, lesson_id):
    """Mark a lesson as completed"""
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
        
        # Check enrollment
        try:
            enrollment = Enrollment.objects.get(student=request.user, course=course)
        except Enrollment.DoesNotExist:
            messages.error(request, 'You must be enrolled to mark lessons complete.')
            return redirect('course_detail', course_id=course_id)
        
        # Mark progress
        progress, created = Progress.objects.get_or_create(
            student=request.user,
            lesson=lesson
        )
        
        if not progress.completed:
            progress.mark_complete()
            messages.success(request, f'Lesson "{lesson.title}" marked as complete!')
        
        return redirect('lesson_detail', course_id=course_id, lesson_id=lesson_id)
    
    return redirect('course_list')
