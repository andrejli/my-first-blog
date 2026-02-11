"""
Lesson Views
------------
Lesson detail, navigation, and completion tracking.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from blog.models import Course, Lesson, Enrollment, Progress


@login_required
def lesson_detail(request, course_id, lesson_id):
    """Display individual lesson content"""
    # For instructors: allow viewing their own lessons regardless of publication status
    if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'instructor':
        # Instructors can view their own lessons in any status
        course = get_object_or_404(Course, id=course_id, instructor=request.user)
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
        is_instructor_preview = True
    else:
        # Students can only view published lessons in published courses
        course = get_object_or_404(Course, id=course_id, status='published')
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course, is_published=True)
        is_instructor_preview = False
    
    # For students: check enrollment
    if not is_instructor_preview:
        try:
            enrollment = Enrollment.objects.get(student=request.user, course=course)
        except Enrollment.DoesNotExist:
            messages.error(request, 'You must be enrolled in this course to view lessons.')
            return redirect('course_detail', course_id=course_id)
    else:
        enrollment = None
    
    # Get or create progress for this lesson (only for students)
    progress = None
    if not is_instructor_preview:
        progress, created = Progress.objects.get_or_create(
            student=request.user,
            lesson=lesson,
            defaults={'completed': False}
        )
    
    # Get all lessons for navigation
    if is_instructor_preview:
        # Instructors see all lessons (published and unpublished)
        all_lessons = Lesson.objects.filter(course=course).order_by('order')
    else:
        # Students only see published lessons
        all_lessons = Lesson.objects.filter(course=course, is_published=True).order_by('order')
    
    lesson_list = list(all_lessons)
    
    # Find current lesson index
    try:
        current_index = lesson_list.index(lesson)
    except ValueError:
        # Lesson not in the filtered list (shouldn't happen, but handle gracefully)
        current_index = 0
    
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
        'is_instructor_preview': is_instructor_preview,
    }
    
    return render(request, 'blog/lesson_detail.html', context)


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
