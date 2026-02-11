"""
Dashboard Views
---------------
Student and instructor dashboards with progress tracking.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

from blog.models import (
    Course, Lesson, Enrollment, Progress, Assignment, 
    Submission, UserProfile
)


@login_required
def student_dashboard(request):
    """Display student's enrolled courses and progress"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Please complete your profile setup.')
        return redirect('course_list')
    
    # Get user's enrollments with optimized queries
    enrollments = Enrollment.objects.filter(
        student=request.user,
        status='enrolled'
    ).select_related(
        'course',
        'course__instructor',
        'course__instructor__userprofile'
    ).annotate(
        total_lessons=Count(
            'course__lesson',
            filter=Q(course__lesson__is_published=True)
        ),
        completed_lessons_count=Count(
            'course__lesson__progress',
            filter=Q(
                course__lesson__progress__student=request.user,
                course__lesson__progress__completed=True
            )
        )
    ).order_by('-enrollment_date')
    
    # Calculate progress for each course (now using annotated values)
    course_progress = []
    for enrollment in enrollments:
        total_lessons = enrollment.total_lessons
        completed_lessons = enrollment.completed_lessons_count
        progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        course_progress.append({
            'enrollment': enrollment,
            'course': enrollment.course,
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


@cache_page(300)  # Cache for 5 minutes
@vary_on_cookie  # Cache separately per instructor
@login_required
def instructor_dashboard(request):
    """Display instructor's courses and student management"""
    try:
        profile = request.user.userprofile
        if profile.role != 'instructor':
            messages.error(request, 'Access denied. Instructor privileges required.')
            return redirect('course_list')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Access denied. Instructor privileges required.')
        return redirect('course_list')
    
    # Get instructor's courses with optimized queries
    # Prefetch recent enrollments efficiently
    recent_enrollments_prefetch = Prefetch(
        'enrollment_set',
        queryset=Enrollment.objects.filter(
            status='enrolled'
        ).select_related('student', 'student__userprofile').order_by('-enrollment_date')[:5],
        to_attr='recent_enrollments_list'
    )
    
    courses = Course.objects.filter(
        instructor=request.user
    ).annotate(
        enrolled_count=Count('enrollment', filter=Q(enrollment__status='enrolled'), distinct=True),
        published_lessons_count=Count('lesson', filter=Q(lesson__is_published=True)),
        total_assignments=Count('assignment', distinct=True),
        pending_grading_count=Count(
            'assignment__submission',
            filter=Q(assignment__submission__status='submitted'),
            distinct=True
        )
    ).prefetch_related(
        recent_enrollments_prefetch
    ).order_by('-created_date')
    
    # Get pending submissions across all courses
    pending_submissions = Submission.objects.filter(
        assignment__course__instructor=request.user,
        status='submitted'
    ).select_related(
        'student',
        'student__userprofile',
        'assignment',
        'assignment__course'
    ).order_by('-submitted_date')[:10]
    
    # Calculate stats for each course (now using annotated values)
    course_stats = []
    for course in courses:
        enrolled_count = course.enrolled_count
        
        course_stats.append({
            'course': course,
            'enrolled_count': enrolled_count,
            'total_lessons': course.published_lessons_count,
            'total_assignments': course.total_assignments,
            'pending_grading': course.pending_grading_count,
            'recent_enrollments': course.recent_enrollments_list,
            'capacity_percentage': (enrolled_count / course.max_students * 100) if course.max_students > 0 else 0,
        })
    
    context = {
        'course_stats': course_stats,
        'pending_submissions': pending_submissions,
        'total_courses': len(courses),  # Use len() on already-fetched queryset
        'total_students': sum(stat['enrolled_count'] for stat in course_stats),
        'total_pending_grading': sum(stat['pending_grading'] for stat in course_stats),
    }
    
    return render(request, 'blog/instructor_dashboard.html', context)


@cache_page(300)  # Cache for 5 minutes
@vary_on_cookie  # Cache separately per user
@login_required
def my_courses(request):
    """Display user's enrolled courses"""
    enrollments = Enrollment.objects.filter(
        student=request.user,
        status__in=['enrolled', 'completed']
    ).select_related('course').order_by('-enrollment_date')
    
    # Separate enrolled and completed courses
    enrolled_courses = enrollments.filter(status='enrolled')
    completed_courses = enrollments.filter(status='completed')
    
    # Get recent progress (last 5 completed lessons)
    recent_progress = Progress.objects.filter(
        student=request.user,
        completed=True,
        completion_date__isnull=False
    ).select_related('lesson', 'lesson__course').order_by('-completion_date')[:5]
    
    context = {
        'enrollments': enrollments,
        'enrolled_courses': enrolled_courses,
        'completed_courses': completed_courses,
        'recent_progress': recent_progress,
    }
    
    return render(request, 'blog/my_courses.html', context)


@login_required
def course_students(request, course_id):
    """Display students enrolled in a course (instructor only)"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor
    if request.user != course.instructor:
        messages.error(request, 'Access denied. You are not the instructor of this course.')
        return redirect('course_detail', course_id=course_id)
    
    # Get enrolled students with their progress (optimized with annotations)
    # Get total lessons count once
    total_lessons = Lesson.objects.filter(course=course, is_published=True).count()
    
    # Optimize: annotate enrollments with completed lesson counts in single query
    enrollments = Enrollment.objects.filter(
        course=course,
        status='enrolled'
    ).select_related(
        'student',
        'student__userprofile'
    ).annotate(
        completed_lessons_count=Count(
            'student__progress',
            filter=Q(
                student__progress__lesson__course=course,
                student__progress__completed=True
            )
        )
    ).order_by('enrollment_date')
    
    # Build student progress list (no additional queries)
    student_progress = []
    for enrollment in enrollments:
        progress_percentage = (
            enrollment.completed_lessons_count / total_lessons * 100
        ) if total_lessons > 0 else 0
        
        student_progress.append({
            'enrollment': enrollment,
            'student': enrollment.student,
            'completed_lessons': enrollment.completed_lessons_count,
            'total_lessons': total_lessons,
            'progress_percentage': progress_percentage,
        })
    
    context = {
        'course': course,
        'student_progress': student_progress,
        'total_students': len(enrollments),  # Use len() instead of .count() on already-fetched queryset
        'total_lessons': total_lessons,
    }
    
    return render(request, 'blog/course_students.html', context)
