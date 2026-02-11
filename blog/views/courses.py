"""
Public and course-related views for Django LMS.

This module handles:
- Landing page
- Course listing (public)
- Course details
- Lesson viewing
- Course enrollment/dropping
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.db.models import Count, Q

from blog.models import (
    Post, Course, Lesson, Enrollment, Progress, Assignment, 
    Submission, Quiz, QuizAttempt, Announcement, Event
)


# Legacy blog view (keep for backward compatibility)
def post_list(request):
    """Legacy blog post list view"""
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})


@cache_page(600)  # Cache for 10 minutes
def landing_page(request):
    """Public landing page for the LMS (accessible to all users)"""
    return render(request, 'blog/landing.html')


@cache_page(300)  # Cache for 5 minutes
def course_list(request):
    """
    Display all published courses with upcoming events (public access allowed).
    
    Shows courses with student count and lesson count annotations.
    Includes upcoming events filtered by visibility and user authentication status.
    """
    courses = Course.objects.filter(
        status='published'
    ).select_related(
        'instructor',
        'instructor__userprofile'
    ).prefetch_related(
        'lesson_set'
    ).annotate(
        lesson_count=Count('lesson', filter=Q(lesson__is_published=True)),
        student_count=Count('enrollment', distinct=True)
    ).order_by('-published_date')
    
    # Get upcoming events with visibility filtering
    if request.user.is_authenticated:
        upcoming_events = Event.objects.filter(
            is_published=True,
            start_date__gte=timezone.now(),
            visibility__in=['public', 'registered']
        ).order_by('start_date')[:10]
        
        featured_events = Event.objects.filter(
            is_published=True,
            is_featured=True,
            start_date__gte=timezone.now(),
            visibility__in=['public', 'registered']
        ).order_by('start_date')[:5]
        
        today = timezone.now().date()
        today_events = Event.objects.filter(
            is_published=True,
            start_date__date=today,
            visibility__in=['public', 'registered']
        ).order_by('start_date')
    else:
        upcoming_events = Event.objects.filter(
            is_published=True,
            start_date__gte=timezone.now(),
            visibility='public'
        ).order_by('start_date')[:10]
        
        featured_events = Event.objects.filter(
            is_published=True,
            is_featured=True,
            start_date__gte=timezone.now(),
            visibility='public'
        ).order_by('start_date')[:5]
        
        today = timezone.now().date()
        today_events = Event.objects.filter(
            is_published=True,
            start_date__date=today,
            visibility='public'
        ).order_by('start_date')
    
    context = {
        'courses': courses,
        'upcoming_events': upcoming_events,
        'featured_events': featured_events,
        'today_events': today_events,
    }
    
    return render(request, 'blog/course_list.html', context)


def course_detail(request, course_id):
    """
    Display course details and lessons.
    
    - Instructors can view their own courses in any status
    - Students and public can only view published courses
    - Shows enrollment status, progress, assignments, and quizzes for enrolled students
    """
    # Check access permissions
    course = None
    if request.user.is_authenticated and hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'instructor':
        try:
            course = Course.objects.get(id=course_id, instructor=request.user)
        except Course.DoesNotExist:
            course = get_object_or_404(Course, id=course_id, status='published')
    else:
        course = get_object_or_404(Course, id=course_id, status='published')
    
    lessons = Lesson.objects.filter(course=course, is_published=True).order_by('order')
    
    # Check enrollment status
    is_enrolled = False
    enrollment = None
    user_progress = {}
    next_lesson = None
    assignments = []
    user_submissions = {}
    
    if request.user.is_authenticated:
        try:
            enrollment = Enrollment.objects.get(student=request.user, course=course)
            is_enrolled = True
            
            # Get progress
            progress_queryset = Progress.objects.filter(student=request.user, lesson__course=course)
            user_progress = {p.lesson.pk: p.completed for p in progress_queryset}
            
            # Find next lesson
            for lesson in lessons:
                if not user_progress.get(lesson.pk, False):
                    next_lesson = lesson
                    break
            
            # Get assignments
            assignments = Assignment.objects.filter(course=course, is_published=True).order_by('-due_date')
            for assignment in assignments:
                try:
                    submission = Submission.objects.get(student=request.user, assignment=assignment)
                    user_submissions[assignment.id] = submission
                except Submission.DoesNotExist:
                    user_submissions[assignment.id] = None
                    
        except Enrollment.DoesNotExist:
            pass
    
    # Get quizzes for enrolled students/instructors
    quizzes = []
    quiz_attempts = {}
    if is_enrolled or (request.user.is_authenticated and hasattr(request.user, 'userprofile') and 
                      request.user.userprofile.role == 'instructor' and course.instructor == request.user):
        quizzes = Quiz.objects.filter(course=course, is_published=True).order_by('created_date')
        
        if is_enrolled:
            for quiz in quizzes:
                attempts = QuizAttempt.objects.filter(student=request.user, quiz=quiz).order_by('-started_at')
                if attempts.exists():
                    quiz_attempts[quiz.id] = {
                        'total_attempts': attempts.count(),
                        'last_attempt': attempts.first(),
                        'best_score': max(attempt.score for attempt in attempts if attempt.score is not None) 
                                     if attempts.filter(score__isnull=False).exists() else None,
                        'can_attempt': not quiz.max_attempts or attempts.count() < quiz.max_attempts,
                        'is_available': (not quiz.available_from or quiz.available_from <= timezone.now()) and 
                                       (not quiz.available_until or quiz.available_until >= timezone.now())
                    }
                else:
                    quiz_attempts[quiz.id] = {
                        'total_attempts': 0,
                        'last_attempt': None,
                        'best_score': None,
                        'can_attempt': True,
                        'is_available': (not quiz.available_from or quiz.available_from <= timezone.now()) and 
                                       (not quiz.available_until or quiz.available_until >= timezone.now())
                    }
    
    # Get recent announcements
    recent_announcements = []
    if is_enrolled or (request.user.is_authenticated and hasattr(request.user, 'userprofile') and 
                      request.user.userprofile.role == 'instructor' and course.instructor == request.user):
        if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'instructor' and course.instructor == request.user:
            recent_announcements = Announcement.objects.filter(course=course).order_by('-created_date')[:3]
        elif is_enrolled:
            recent_announcements = Announcement.objects.filter(
                course=course,
                is_published=True
            ).filter(
                Q(scheduled_for__isnull=True) | Q(scheduled_for__lte=timezone.now())
            ).order_by('-created_date')[:3]
    
    is_instructor = (request.user.is_authenticated and hasattr(request.user, 'userprofile') and 
                    request.user.userprofile.role == 'instructor' and course.instructor == request.user)
    
    context = {
        'course': course,
        'lessons': lessons,
        'is_enrolled': is_enrolled,
        'is_instructor': is_instructor,
        'enrollment': enrollment,
        'user_progress': user_progress,
        'next_lesson': next_lesson,
        'total_lessons': lessons.count(),
        'completed_lessons': sum(user_progress.values()) if user_progress else 0,
        'assignments': assignments,
        'user_submissions': user_submissions,
        'quizzes': quizzes,
        'quiz_attempts': quiz_attempts,
        'recent_announcements': recent_announcements,
    }
    
    return render(request, 'blog/course_detail.html', context)


@login_required
def enroll_course(request, course_id):
    """Enroll a student in a course"""
    course = get_object_or_404(Course, id=course_id, status='published')
    
    # Create enrollment if it doesn't exist
    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={'enrollment_date': timezone.now()}
    )
    
    if created:
        messages.success(request, f'You have been enrolled in {course.title}!')
    else:
        messages.info(request, f'You are already enrolled in {course.title}.')
    
    return redirect('course_detail', course_id=course_id)


@login_required
def drop_course(request, course_id):
    """Drop a course (student can unenroll)"""
    course = get_object_or_404(Course, id=course_id)
    
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
        enrollment.delete()
        messages.success(request, f'You have dropped {course.title}.')
    except Enrollment.DoesNotExist:
        messages.error(request, 'You are not enrolled in this course.')
    
    return redirect('course_list')
