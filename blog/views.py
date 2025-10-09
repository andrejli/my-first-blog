from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse
from django.db import transaction
from .models import Post, Course, Enrollment, Lesson, Progress, UserProfile, CourseMaterial, Assignment, Submission, Quiz, Question, Answer, QuizAttempt, QuizResponse, Announcement, AnnouncementRead


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
    # Try to get the course - allow instructors to view their own courses regardless of status
    # and allow everyone to view published courses
    course = None
    
    if request.user.is_authenticated and hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'instructor':
        # Try to get the course if the instructor owns it (any status)
        try:
            course = Course.objects.get(id=course_id, instructor=request.user)
        except Course.DoesNotExist:
            # If not their course, try to get it if it's published
            course = get_object_or_404(Course, id=course_id, status='published')
    else:
        # Students and anonymous users can only view published courses
        course = get_object_or_404(Course, id=course_id, status='published')
    
    lessons = Lesson.objects.filter(course=course, is_published=True).order_by('order')
    
    # Check if user is enrolled (if logged in)
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
            
            # Get user progress for each lesson
            progress_queryset = Progress.objects.filter(student=request.user, lesson__course=course)
            user_progress = {p.lesson.pk: p.completed for p in progress_queryset}
            
            # Find the next lesson to continue
            for lesson in lessons:
                if not user_progress.get(lesson.pk, False):
                    next_lesson = lesson
                    break
            
            # Get course assignments for enrolled students
            assignments = Assignment.objects.filter(course=course, is_published=True).order_by('-due_date')
            
            # Get user's submissions for these assignments
            for assignment in assignments:
                try:
                    submission = Submission.objects.get(student=request.user, assignment=assignment)
                    user_submissions[assignment.id] = submission
                except Submission.DoesNotExist:
                    user_submissions[assignment.id] = None
            
        except Enrollment.DoesNotExist:
            pass
    
    # Get course quizzes for enrolled students or instructors
    quizzes = []
    quiz_attempts = {}
    if is_enrolled or (request.user.is_authenticated and hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'instructor' and course.instructor == request.user):
        from django.utils import timezone
        quizzes = Quiz.objects.filter(course=course, is_published=True).order_by('created_date')
        
        # For students, get their quiz attempts
        if is_enrolled:
            for quiz in quizzes:
                attempts = QuizAttempt.objects.filter(student=request.user, quiz=quiz).order_by('-started_at')
                if attempts.exists():
                    quiz_attempts[quiz.id] = {
                        'total_attempts': attempts.count(),
                        'last_attempt': attempts.first(),
                        'best_score': max(attempt.score for attempt in attempts if attempt.score is not None) if attempts.filter(score__isnull=False).exists() else None,
                        'can_attempt': not quiz.max_attempts or attempts.count() < quiz.max_attempts,
                        'is_available': (not quiz.available_from or quiz.available_from <= timezone.now()) and (not quiz.available_until or quiz.available_until >= timezone.now())
                    }
                else:
                    quiz_attempts[quiz.id] = {
                        'total_attempts': 0,
                        'last_attempt': None,
                        'best_score': None,
                        'can_attempt': True,
                        'is_available': (not quiz.available_from or quiz.available_from <= timezone.now()) and (not quiz.available_until or quiz.available_until >= timezone.now())
                    }
    
    # Get recent announcements for enrolled students or instructors
    recent_announcements = []
    if is_enrolled or (request.user.is_authenticated and hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'instructor' and course.instructor == request.user):
        if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'instructor' and course.instructor == request.user:
            # Instructors can see all announcements for their courses
            recent_announcements = Announcement.objects.filter(course=course).order_by('-created_date')[:3]
        elif is_enrolled:
            # Students can only see published, visible announcements
            from django.utils import timezone
            from django.db.models import Q
            recent_announcements = Announcement.objects.filter(
                course=course,
                is_published=True
            ).filter(
                Q(scheduled_for__isnull=True) | Q(scheduled_for__lte=timezone.now())
            ).order_by('-created_date')[:3]

    context = {
        'course': course,
        'lessons': lessons,
        'is_enrolled': is_enrolled,
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


# Lesson detail view
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
    
    # Get pending submissions across all courses
    from blog.models import Submission
    pending_submissions = Submission.objects.filter(
        assignment__course__instructor=request.user,
        status='submitted'
    ).select_related('student', 'assignment', 'assignment__course').order_by('-submitted_date')[:10]
    
    # Calculate stats for each course
    course_stats = []
    for course in courses:
        enrolled_count = course.get_enrolled_count()
        total_lessons = Lesson.objects.filter(course=course, is_published=True).count()
        
        # Get assignment stats for this course
        course_assignments = Assignment.objects.filter(course=course)
        total_assignments = course_assignments.count()
        pending_grading = Submission.objects.filter(
            assignment__course=course,
            status='submitted'
        ).count()
        
        # Get recent enrollments
        recent_enrollments = Enrollment.objects.filter(
            course=course,
            status='enrolled'
        ).select_related('student').order_by('-enrollment_date')[:5]
        
        course_stats.append({
            'course': course,
            'enrolled_count': enrolled_count,
            'total_lessons': total_lessons,
            'total_assignments': total_assignments,
            'pending_grading': pending_grading,
            'recent_enrollments': recent_enrollments,
            'capacity_percentage': (enrolled_count / course.max_students * 100) if course.max_students > 0 else 0,
        })
    
    context = {
        'course_stats': course_stats,
        'pending_submissions': pending_submissions,
        'total_courses': courses.count(),
        'total_students': sum(stat['enrolled_count'] for stat in course_stats),
        'total_pending_grading': sum(stat['pending_grading'] for stat in course_stats),
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


# Phase 2: Enhanced Instructor Lesson Management Views

def instructor_required(view_func):
    """Decorator to ensure user is an instructor"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'instructor':
            messages.error(request, 'Access denied. Instructor privileges required.')
            return redirect('course_list')
        return view_func(request, *args, **kwargs)
    return wrapper


@instructor_required
def instructor_course_detail(request, course_id):
    """Enhanced course management for instructors"""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    # Get lessons ordered by order field
    lessons = Lesson.objects.filter(course=course).order_by('order')
    
    # Get enrollment statistics
    total_students = course.get_enrolled_count()
    lessons_stats = []
    
    for lesson in lessons:
        completed_count = Progress.objects.filter(
            lesson=lesson,
            completed=True
        ).count()
        
        lessons_stats.append({
            'lesson': lesson,
            'completed_count': completed_count,
            'completion_rate': (completed_count / total_students * 100) if total_students > 0 else 0,
        })
    
    context = {
        'course': course,
        'lessons_stats': lessons_stats,
        'total_students': total_students,
        'total_lessons': lessons.count(),
        'published_lessons': lessons.filter(is_published=True).count(),
    }
    
    return render(request, 'blog/instructor_course_detail.html', context)


@instructor_required
def create_lesson(request, course_id):
    """Create a new lesson for a course"""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        video_url = request.POST.get('video_url', '').strip()
        is_published = request.POST.get('is_published') == 'on'
        
        if not title or not content:
            messages.error(request, 'Title and content are required.')
        else:
            # Get next order number
            last_lesson = Lesson.objects.filter(course=course).order_by('-order').first()
            next_order = (last_lesson.order + 1) if last_lesson else 1
            
            lesson = Lesson.objects.create(
                course=course,
                title=title,
                content=content,
                video_url=video_url,
                order=next_order,
                is_published=is_published
            )
            
            messages.success(request, f'Lesson "{lesson.title}" created successfully!')
            return redirect('instructor_course_detail', course_id=course_id)
    
    context = {
        'course': course,
        'action': 'Create',
    }
    
    return render(request, 'blog/lesson_form.html', context)


@instructor_required
def edit_lesson(request, lesson_id):
    """Edit an existing lesson"""
    lesson = get_object_or_404(Lesson, id=lesson_id, course__instructor=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        video_url = request.POST.get('video_url', '').strip()
        is_published = request.POST.get('is_published') == 'on'
        
        if not title or not content:
            messages.error(request, 'Title and content are required.')
        else:
            lesson.title = title
            lesson.content = content
            lesson.video_url = video_url
            lesson.is_published = is_published
            lesson.save()
            
            messages.success(request, f'Lesson "{lesson.title}" updated successfully!')
            return redirect('instructor_course_detail', course_id=lesson.course.id)
    
    context = {
        'course': lesson.course,
        'lesson': lesson,
        'action': 'Edit',
    }
    
    return render(request, 'blog/lesson_form.html', context)


@instructor_required
def delete_lesson(request, lesson_id):
    """Delete a lesson"""
    lesson = get_object_or_404(Lesson, id=lesson_id, course__instructor=request.user)
    course_id = lesson.course.id
    
    if request.method == 'POST':
        lesson_title = lesson.title
        lesson.delete()
        messages.success(request, f'Lesson "{lesson_title}" deleted successfully!')
        return redirect('instructor_course_detail', course_id=course_id)
    
    context = {
        'lesson': lesson,
        'course': lesson.course,
    }
    
    return render(request, 'blog/lesson_confirm_delete.html', context)


@instructor_required
def reorder_lessons(request, course_id):
    """Reorder lessons in a course"""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    if request.method == 'POST':
        lesson_orders = request.POST.getlist('lesson_order')
        
        # Use a transaction to prevent integrity errors
        try:
            with transaction.atomic():
                # First, set all lesson orders to negative values to avoid conflicts
                lessons_to_update = Lesson.objects.filter(course=course)
                for lesson in lessons_to_update:
                    lesson.order = -lesson.id  # Use negative ID to ensure uniqueness
                    lesson.save()
                
                # Then, set the correct order values
                for i, lesson_id in enumerate(lesson_orders):
                    try:
                        lesson = Lesson.objects.get(id=lesson_id, course=course)
                        lesson.order = i + 1
                        lesson.save()
                    except Lesson.DoesNotExist:
                        continue
            
            messages.success(request, 'Lesson order updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating lesson order: {str(e)}')
    
    return redirect('instructor_course_detail', course_id=course_id)


@instructor_required
def create_course(request):
    """Create a new course for an instructor"""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        course_code = request.POST.get('course_code', '').strip()
        description = request.POST.get('description', '').strip()
        duration_weeks = request.POST.get('duration_weeks', '4')
        max_students = request.POST.get('max_students', '30')
        prerequisites = request.POST.get('prerequisites', '').strip()
        status = request.POST.get('status', 'draft')
        
        # Validation
        errors = []
        if not title:
            errors.append('Course title is required.')
        if not course_code:
            errors.append('Course code is required.')
        elif Course.objects.filter(course_code=course_code).exists():
            errors.append('Course code already exists. Please choose a different one.')
        if not description:
            errors.append('Course description is required.')
        
        try:
            duration_weeks = int(duration_weeks)
            if duration_weeks < 1:
                errors.append('Duration must be at least 1 week.')
        except ValueError:
            errors.append('Duration must be a valid number.')
            
        try:
            max_students = int(max_students)
            if max_students < 1:
                errors.append('Maximum students must be at least 1.')
        except ValueError:
            errors.append('Maximum students must be a valid number.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            course = Course.objects.create(
                title=title,
                course_code=course_code,
                description=description,
                instructor=request.user,
                duration_weeks=duration_weeks,
                max_students=max_students,
                prerequisites=prerequisites,
                status=status
            )
            
            if status == 'published':
                course.publish()
            
            messages.success(request, f'Course "{course.title}" created successfully!')
            return redirect('instructor_course_detail', course_id=course.id)
    
    context = {
        'action': 'Create',
    }
    
    return render(request, 'blog/course_form.html', context)


@instructor_required
def edit_course(request, course_id):
    """Edit an existing course"""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        course_code = request.POST.get('course_code', '').strip()
        description = request.POST.get('description', '').strip()
        duration_weeks = request.POST.get('duration_weeks', '4')
        max_students = request.POST.get('max_students', '30')
        prerequisites = request.POST.get('prerequisites', '').strip()
        status = request.POST.get('status', 'draft')
        
        # Validation
        errors = []
        if not title:
            errors.append('Course title is required.')
        if not course_code:
            errors.append('Course code is required.')
        elif Course.objects.filter(course_code=course_code).exclude(id=course.id).exists():
            errors.append('Course code already exists. Please choose a different one.')
        if not description:
            errors.append('Course description is required.')
        
        try:
            duration_weeks = int(duration_weeks)
            if duration_weeks < 1:
                errors.append('Duration must be at least 1 week.')
        except ValueError:
            errors.append('Duration must be a valid number.')
            
        try:
            max_students = int(max_students)
            if max_students < 1:
                errors.append('Maximum students must be at least 1.')
        except ValueError:
            errors.append('Maximum students must be a valid number.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            course.title = title
            course.course_code = course_code
            course.description = description
            course.duration_weeks = duration_weeks
            course.max_students = max_students
            course.prerequisites = prerequisites
            course.status = status
            course.save()
            
            if status == 'published' and not course.published_date:
                course.publish()
            
            messages.success(request, f'Course "{course.title}" updated successfully!')
            return redirect('instructor_course_detail', course_id=course.id)
    
    context = {
        'course': course,
        'action': 'Edit',
    }
    
    return render(request, 'blog/course_form.html', context)


# Phase 2.2: Content Upload System Views

@instructor_required
def course_materials(request, course_id):
    """Manage course materials"""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    materials = CourseMaterial.objects.filter(course=course).order_by('-uploaded_date')
    
    context = {
        'course': course,
        'materials': materials,
    }
    
    return render(request, 'blog/course_materials.html', context)


@instructor_required
def upload_material(request, course_id):
    """Upload course material"""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        material_type = request.POST.get('material_type', 'other')
        is_required = request.POST.get('is_required') == 'on'
        lesson_id = request.POST.get('lesson_id')
        file = request.FILES.get('file')
        
        errors = []
        if not title:
            errors.append('Title is required.')
        if not file:
            errors.append('File is required.')
        
        # File size validation (10MB limit)
        if file and file.size > 10 * 1024 * 1024:
            errors.append('File size must be less than 10MB.')
        
        lesson = None
        if lesson_id:
            try:
                lesson = Lesson.objects.get(id=lesson_id, course=course)
            except Lesson.DoesNotExist:
                errors.append('Invalid lesson selected.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            material = CourseMaterial.objects.create(
                course=course,
                lesson=lesson,
                title=title,
                description=description,
                file=file,
                material_type=material_type,
                is_required=is_required
            )
            
            messages.success(request, f'Material "{material.title}" uploaded successfully!')
            return redirect('course_materials', course_id=course_id)
    
    # Get lessons for selection
    lessons = Lesson.objects.filter(course=course).order_by('order')
    
    context = {
        'course': course,
        'lessons': lessons,
    }
    
    return render(request, 'blog/upload_material.html', context)


@instructor_required
def delete_material(request, material_id):
    """Delete course material"""
    material = get_object_or_404(CourseMaterial, id=material_id, course__instructor=request.user)
    course_id = material.course.id
    
    if request.method == 'POST':
        # Delete the file from filesystem
        if material.file:
            import os
            if os.path.exists(material.file.path):
                os.remove(material.file.path)
        
        material_title = material.title
        material.delete()
        messages.success(request, f'Material "{material_title}" deleted successfully!')
        return redirect('course_materials', course_id=course_id)
    
    context = {
        'material': material,
        'course': material.course,
    }
    
    return render(request, 'blog/material_confirm_delete.html', context)


# Assignment Management Views

@instructor_required
def course_assignments(request, course_id):
    """Manage course assignments"""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    assignments = Assignment.objects.filter(course=course).order_by('-due_date')
    
    context = {
        'course': course,
        'assignments': assignments,
    }
    
    return render(request, 'blog/course_assignments.html', context)


@instructor_required
def create_assignment(request, course_id):
    """Create a new assignment"""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        instructions = request.POST.get('instructions', '').strip()
        due_date = request.POST.get('due_date')
        max_points = request.POST.get('max_points', '100')
        allow_file_submission = request.POST.get('allow_file_submission') == 'on'
        allow_text_submission = request.POST.get('allow_text_submission') == 'on'
        is_published = request.POST.get('is_published') == 'on'
        file_attachment = request.FILES.get('file_attachment')
        
        errors = []
        if not title:
            errors.append('Title is required.')
        if not description:
            errors.append('Description is required.')
        if not due_date:
            errors.append('Due date is required.')
        
        try:
            max_points = int(max_points)
            if max_points < 1:
                errors.append('Maximum points must be at least 1.')
        except ValueError:
            errors.append('Maximum points must be a valid number.')
        
        if not allow_file_submission and not allow_text_submission:
            errors.append('At least one submission type must be allowed.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            assignment = Assignment.objects.create(
                course=course,
                title=title,
                description=description,
                instructions=instructions,
                due_date=due_date,
                max_points=max_points,
                allow_file_submission=allow_file_submission,
                allow_text_submission=allow_text_submission,
                is_published=is_published,
                file_attachment=file_attachment
            )
            
            messages.success(request, f'Assignment "{assignment.title}" created successfully!')
            return redirect('course_assignments', course_id=course_id)
    
    context = {
        'course': course,
        'action': 'Create',
    }
    
    return render(request, 'blog/assignment_form.html', context)


@instructor_required
def edit_assignment(request, assignment_id):
    """Edit an existing assignment"""
    assignment = get_object_or_404(Assignment, id=assignment_id, course__instructor=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        instructions = request.POST.get('instructions', '').strip()
        due_date = request.POST.get('due_date')
        max_points = request.POST.get('max_points', '100')
        allow_file_submission = request.POST.get('allow_file_submission') == 'on'
        allow_text_submission = request.POST.get('allow_text_submission') == 'on'
        is_published = request.POST.get('is_published') == 'on'
        file_attachment = request.FILES.get('file_attachment')
        
        errors = []
        if not title:
            errors.append('Title is required.')
        if not description:
            errors.append('Description is required.')
        if not due_date:
            errors.append('Due date is required.')
        
        try:
            max_points = int(max_points)
            if max_points < 1:
                errors.append('Maximum points must be at least 1.')
        except ValueError:
            errors.append('Maximum points must be a valid number.')
        
        if not allow_file_submission and not allow_text_submission:
            errors.append('At least one submission type must be allowed.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            assignment.title = title
            assignment.description = description
            assignment.instructions = instructions
            assignment.due_date = due_date
            assignment.max_points = max_points
            assignment.allow_file_submission = allow_file_submission
            assignment.allow_text_submission = allow_text_submission
            assignment.is_published = is_published
            
            if file_attachment:
                assignment.file_attachment = file_attachment
            
            assignment.save()
            
            messages.success(request, f'Assignment "{assignment.title}" updated successfully!')
            return redirect('course_assignments', course_id=assignment.course.id)
    
    context = {
        'course': assignment.course,
        'assignment': assignment,
        'action': 'Edit',
    }
    
    return render(request, 'blog/assignment_form.html', context)


@instructor_required
def delete_assignment(request, assignment_id):
    """Delete an assignment"""
    assignment = get_object_or_404(Assignment, id=assignment_id, course__instructor=request.user)
    course_id = assignment.course.id
    
    if request.method == 'POST':
        assignment_title = assignment.title
        assignment.delete()
        messages.success(request, f'Assignment "{assignment_title}" deleted successfully!')
        return redirect('course_assignments', course_id=course_id)
    
    context = {
        'assignment': assignment,
        'course': assignment.course,
    }
    
    return render(request, 'blog/assignment_confirm_delete.html', context)


@instructor_required
def assignment_submissions(request, assignment_id):
    """View all submissions for an assignment"""
    assignment = get_object_or_404(Assignment, id=assignment_id, course__instructor=request.user)
    submissions = Submission.objects.filter(assignment=assignment).select_related('student').order_by('-submitted_date')
    
    context = {
        'assignment': assignment,
        'submissions': submissions,
        'course': assignment.course,
    }
    
    return render(request, 'blog/assignment_submissions.html', context)


@instructor_required
def grade_submission(request, submission_id):
    """Grade a student submission"""
    submission = get_object_or_404(Submission, id=submission_id, assignment__course__instructor=request.user)
    
    if request.method == 'POST':
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback', '').strip()
        
        try:
            grade = float(grade) if grade else None
            if grade is not None and (grade < 0 or grade > submission.assignment.max_points):
                messages.error(request, f'Grade must be between 0 and {submission.assignment.max_points}.')
            else:
                submission.grade = grade
                submission.feedback = feedback
                submission.status = 'graded'
                submission.graded_date = timezone.now()
                submission.save()
                
                messages.success(request, f'Submission graded successfully!')
                return redirect('assignment_submissions', assignment_id=submission.assignment.id)
        except ValueError:
            messages.error(request, 'Invalid grade value.')
    
    context = {
        'submission': submission,
        'assignment': submission.assignment,
        'course': submission.assignment.course,
    }
    
    return render(request, 'blog/grade_submission.html', context)


# Student Assignment Views

@login_required
def student_assignments(request, course_id):
    """View assignments for a course (student view)"""
    course = get_object_or_404(Course, id=course_id, status='published')
    
    # Check enrollment
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, 'You must be enrolled in this course to view assignments.')
        return redirect('course_detail', course_id=course_id)
    
    assignments = Assignment.objects.filter(course=course, is_published=True).order_by('-due_date')
    
    # Get student's submissions
    submissions = {}
    for assignment in assignments:
        try:
            submission = Submission.objects.get(student=request.user, assignment=assignment)
            submissions[assignment.id] = submission
        except Submission.DoesNotExist:
            pass
    
    context = {
        'course': course,
        'assignments': assignments,
        'submissions': submissions,
    }
    
    return render(request, 'blog/student_assignments.html', context)


@login_required
def assignment_detail(request, assignment_id):
    """View assignment details and submit"""
    assignment = get_object_or_404(Assignment, id=assignment_id, is_published=True)
    
    # Check enrollment
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=assignment.course)
    except Enrollment.DoesNotExist:
        messages.error(request, 'You must be enrolled in this course to view assignments.')
        return redirect('course_detail', course_id=assignment.course.id)
    
    # Get or create submission
    submission, created = Submission.objects.get_or_create(
        student=request.user,
        assignment=assignment,
        defaults={'status': 'draft'}
    )
    
    context = {
        'assignment': assignment,
        'submission': submission,
        'course': assignment.course,
    }
    
    return render(request, 'blog/assignment_detail.html', context)


@login_required
def submit_assignment(request, assignment_id):
    """Submit an assignment"""
    assignment = get_object_or_404(Assignment, id=assignment_id, is_published=True)
    
    # Check enrollment
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=assignment.course)
    except Enrollment.DoesNotExist:
        messages.error(request, 'You must be enrolled in this course to submit assignments.')
        return redirect('course_detail', course_id=assignment.course.id)
    
    # Get or create submission
    submission, created = Submission.objects.get_or_create(
        student=request.user,
        assignment=assignment,
        defaults={'status': 'draft'}
    )
    
    if request.method == 'POST':
        action = request.POST.get('action', 'submit')
        text_submission = request.POST.get('text_submission', '').strip() if assignment.allow_text_submission else ''
        file_submission = request.FILES.get('file_submission') if assignment.allow_file_submission else None
        
        errors = []
        
        # Validate submission only if submitting (not for drafts)
        if action == 'submit':
            if not text_submission and not file_submission:
                errors.append('Please provide either text or file submission.')
        
        if file_submission and file_submission.size > 10 * 1024 * 1024:
            errors.append('File size must be less than 10MB.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            submission.text_submission = text_submission
            if file_submission:
                submission.file_submission = file_submission
            
            if action == 'submit':
                submission.submit()
                messages.success(request, f'Assignment "{assignment.title}" submitted successfully!')
                return redirect('assignment_detail', assignment_id=assignment_id)
            else:
                # Save as draft
                submission.save()
                messages.success(request, 'Draft saved successfully!')
                return redirect('assignment_detail', assignment_id=assignment_id)
    
    context = {
        'assignment': assignment,
        'submission': submission,
        'course': assignment.course,
    }
    
    return render(request, 'blog/submit_assignment.html', context)


@login_required
def edit_submission(request, submission_id):
    """Edit a draft submission"""
    submission = get_object_or_404(Submission, id=submission_id, student=request.user)
    
    if submission.status != 'draft':
        messages.error(request, 'Cannot edit a submitted assignment.')
        return redirect('assignment_detail', assignment_id=submission.assignment.id)
    
    assignment = submission.assignment
    
    if request.method == 'POST':
        text_submission = request.POST.get('text_submission', '').strip() if assignment.allow_text_submission else ''
        file_submission = request.FILES.get('file_submission') if assignment.allow_file_submission else None
        
        submission.text_submission = text_submission
        if file_submission:
            submission.file_submission = file_submission
        submission.save()
        
        messages.success(request, 'Submission updated successfully!')
        return redirect('assignment_detail', assignment_id=assignment.id)
    
    context = {
        'assignment': assignment,
        'submission': submission,
        'course': assignment.course,
    }
    
    return render(request, 'blog/edit_submission.html', context)


# Quiz Management Views

@instructor_required
def course_quizzes(request, course_id):
    """View all quizzes for a course"""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    quizzes = course.quizzes.all().order_by('-created_date')
    
    context = {
        'course': course,
        'quizzes': quizzes,
    }
    
    return render(request, 'blog/course_quizzes.html', context)


@instructor_required
def create_quiz(request, course_id):
    """Create a new quiz"""
    from blog.models import Quiz
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        quiz_type = request.POST.get('quiz_type', 'practice')
        time_limit = request.POST.get('time_limit')
        max_attempts = request.POST.get('max_attempts', 1)
        points = request.POST.get('points', 0)
        passing_score = request.POST.get('passing_score')
        
        # Boolean fields
        shuffle_questions = request.POST.get('shuffle_questions') == 'on'
        show_correct_answers = request.POST.get('show_correct_answers') == 'on'
        immediate_feedback = request.POST.get('immediate_feedback') == 'on'
        is_published = request.POST.get('is_published') == 'on'
        
        errors = []
        
        # Validation
        if not title:
            errors.append('Quiz title is required.')
        
        if Quiz.objects.filter(course=course, title=title).exists():
            errors.append('A quiz with this title already exists in this course.')
        
        try:
            max_attempts = int(max_attempts) if max_attempts else 1
            if max_attempts < 1:
                errors.append('Maximum attempts must be at least 1.')
        except ValueError:
            errors.append('Invalid maximum attempts value.')
        
        try:
            points = float(points) if points else 0
            if points < 0:
                errors.append('Points cannot be negative.')
        except ValueError:
            errors.append('Invalid points value.')
        
        if time_limit:
            try:
                time_limit = int(time_limit)
                if time_limit < 1:
                    errors.append('Time limit must be at least 1 minute.')
            except ValueError:
                errors.append('Invalid time limit value.')
        else:
            time_limit = None
        
        if passing_score:
            try:
                passing_score = float(passing_score)
                if passing_score < 0 or passing_score > 100:
                    errors.append('Passing score must be between 0 and 100.')
            except ValueError:
                errors.append('Invalid passing score value.')
        else:
            passing_score = None
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Create quiz
            quiz = Quiz.objects.create(
                course=course,
                title=title,
                description=description,
                quiz_type=quiz_type,
                time_limit=time_limit,
                max_attempts=max_attempts,
                points=points,
                passing_score=passing_score,
                shuffle_questions=shuffle_questions,
                show_correct_answers=show_correct_answers,
                immediate_feedback=immediate_feedback,
                is_published=is_published,
            )
            
            messages.success(request, f'Quiz "{title}" created successfully!')
            return redirect('quiz_detail', quiz_id=quiz.id)
    
    context = {
        'course': course,
    }
    
    return render(request, 'blog/create_quiz.html', context)


@instructor_required  
def quiz_detail(request, quiz_id):
    """View quiz details and manage questions"""
    from blog.models import Quiz
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    questions = quiz.questions.all().order_by('order', 'id')
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'course': quiz.course,
    }
    
    return render(request, 'blog/quiz_detail.html', context)


@instructor_required
def edit_quiz(request, quiz_id):
    """Edit quiz settings"""
    from blog.models import Quiz
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        quiz_type = request.POST.get('quiz_type', 'practice')
        time_limit = request.POST.get('time_limit')
        max_attempts = request.POST.get('max_attempts', 1)
        points = request.POST.get('points', 0)
        passing_score = request.POST.get('passing_score')
        
        # Boolean fields
        shuffle_questions = request.POST.get('shuffle_questions') == 'on'
        show_correct_answers = request.POST.get('show_correct_answers') == 'on'
        immediate_feedback = request.POST.get('immediate_feedback') == 'on'
        is_published = request.POST.get('is_published') == 'on'
        
        errors = []
        
        # Validation
        if not title:
            errors.append('Quiz title is required.')
        
        if Quiz.objects.filter(course=quiz.course, title=title).exclude(id=quiz.id).exists():
            errors.append('A quiz with this title already exists in this course.')
        
        try:
            max_attempts = int(max_attempts) if max_attempts else 1
            if max_attempts < 1:
                errors.append('Maximum attempts must be at least 1.')
        except ValueError:
            errors.append('Invalid maximum attempts value.')
        
        try:
            points = float(points) if points else 0
            if points < 0:
                errors.append('Points cannot be negative.')
        except ValueError:
            errors.append('Invalid points value.')
        
        if time_limit:
            try:
                time_limit = int(time_limit)
                if time_limit < 1:
                    errors.append('Time limit must be at least 1 minute.')
            except ValueError:
                errors.append('Invalid time limit value.')
        else:
            time_limit = None
        
        if passing_score:
            try:
                passing_score = float(passing_score)
                if passing_score < 0 or passing_score > 100:
                    errors.append('Passing score must be between 0 and 100.')
            except ValueError:
                errors.append('Invalid passing score value.')
        else:
            passing_score = None
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Update quiz
            quiz.title = title
            quiz.description = description
            quiz.quiz_type = quiz_type
            quiz.time_limit = time_limit
            quiz.max_attempts = max_attempts
            quiz.points = points
            quiz.passing_score = passing_score
            quiz.shuffle_questions = shuffle_questions
            quiz.show_correct_answers = show_correct_answers
            quiz.immediate_feedback = immediate_feedback
            quiz.is_published = is_published
            quiz.save()
            
            messages.success(request, f'Quiz "{title}" updated successfully!')
            return redirect('quiz_detail', quiz_id=quiz.id)
    
    context = {
        'quiz': quiz,
        'course': quiz.course,
    }
    
    return render(request, 'blog/edit_quiz.html', context)


@instructor_required
def toggle_quiz_publish(request, quiz_id):
    """Toggle quiz published status"""
    from blog.models import Quiz
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    
    if request.method == 'POST':
        quiz.is_published = not quiz.is_published
        quiz.save()
        
        status = "published" if quiz.is_published else "unpublished"
        messages.success(request, f'Quiz "{quiz.title}" has been {status}.')
        
        return redirect('quiz_detail', quiz_id=quiz.id)
    
    return redirect('quiz_detail', quiz_id=quiz.id)


# Question Management Views

@instructor_required
def add_question(request, quiz_id):
    """Add a new question to a quiz"""
    from blog.models import Quiz, Question, Answer
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    
    if request.method == 'POST':
        # Get form data
        question_text = request.POST.get('question_text', '').strip()
        question_type = request.POST.get('question_type', 'multiple_choice')
        points = request.POST.get('points', 1)
        explanation = request.POST.get('explanation', '').strip()
        
        errors = []
        
        # Validation
        if not question_text:
            errors.append('Question text is required.')
        
        try:
            points = float(points) if points else 1
            if points <= 0:
                errors.append('Points must be greater than 0.')
        except ValueError:
            errors.append('Invalid points value.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Create question
            question = Question.objects.create(
                quiz=quiz,
                question_text=question_text,
                question_type=question_type,
                points=points,
                explanation=explanation,
                order=quiz.questions.count() + 1
            )
            
            # Create answer choices for multiple choice and true/false questions
            if question_type == 'multiple_choice':
                # Get answer choices from form
                answer_texts = []
                correct_answers = []
                
                for i in range(1, 6):  # Support up to 5 answer choices
                    answer_text = request.POST.get(f'answer_{i}', '').strip()
                    if answer_text:
                        answer_texts.append(answer_text)
                        if request.POST.get(f'correct_{i}') == 'on':
                            correct_answers.append(len(answer_texts) - 1)
                
                if len(answer_texts) < 2:
                    messages.error(request, 'Multiple choice questions must have at least 2 answer choices.')
                    question.delete()
                elif len(correct_answers) == 0:
                    messages.error(request, 'Please select at least one correct answer.')
                    question.delete()
                else:
                    # Create answer objects
                    for i, answer_text in enumerate(answer_texts):
                        Answer.objects.create(
                            question=question,
                            answer_text=answer_text,
                            is_correct=(i in correct_answers),
                            order=i + 1
                        )
                    messages.success(request, f'Question added successfully!')
                    return redirect('quiz_detail', quiz_id=quiz.id)
            
            elif question_type == 'true_false':
                # Create True/False answers
                correct_answer = request.POST.get('tf_correct', 'true')
                Answer.objects.create(
                    question=question,
                    answer_text='True',
                    is_correct=(correct_answer == 'true'),
                    order=1
                )
                Answer.objects.create(
                    question=question,
                    answer_text='False',
                    is_correct=(correct_answer == 'false'),
                    order=2
                )
                messages.success(request, f'Question added successfully!')
                return redirect('quiz_detail', quiz_id=quiz.id)
            
            else:  # short_answer
                messages.success(request, f'Question added successfully!')
                return redirect('quiz_detail', quiz_id=quiz.id)
    
    context = {
        'quiz': quiz,
        'course': quiz.course,
    }
    
    return render(request, 'blog/add_question.html', context)


@instructor_required
def edit_question(request, question_id):
    """Edit an existing question"""
    from blog.models import Question, Answer
    question = get_object_or_404(Question, id=question_id, quiz__course__instructor=request.user)
    quiz = question.quiz
    
    if request.method == 'POST':
        # Get form data
        question_text = request.POST.get('question_text', '').strip()
        question_type = request.POST.get('question_type', question.question_type)
        points = request.POST.get('points', question.points)
        explanation = request.POST.get('explanation', '').strip()
        
        errors = []
        
        # Validation
        if not question_text:
            errors.append('Question text is required.')
        
        try:
            points = float(points) if points else 1
            if points <= 0:
                errors.append('Points must be greater than 0.')
        except ValueError:
            errors.append('Invalid points value.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Update question
            question.question_text = question_text
            question.question_type = question_type
            question.points = points
            question.explanation = explanation
            question.save()
            
            # Handle answer choices
            if question_type in ['multiple_choice', 'true_false']:
                # Delete existing answers
                question.answers.all().delete()
                
                if question_type == 'multiple_choice':
                    # Get answer choices from form
                    answer_texts = []
                    correct_answers = []
                    
                    for i in range(1, 6):  # Support up to 5 answer choices
                        answer_text = request.POST.get(f'answer_{i}', '').strip()
                        if answer_text:
                            answer_texts.append(answer_text)
                            if request.POST.get(f'correct_{i}') == 'on':
                                correct_answers.append(len(answer_texts) - 1)
                    
                    if len(answer_texts) < 2:
                        messages.error(request, 'Multiple choice questions must have at least 2 answer choices.')
                    elif len(correct_answers) == 0:
                        messages.error(request, 'Please select at least one correct answer.')
                    else:
                        # Create answer objects
                        for i, answer_text in enumerate(answer_texts):
                            Answer.objects.create(
                                question=question,
                                answer_text=answer_text,
                                is_correct=(i in correct_answers),
                                order=i + 1
                            )
                        messages.success(request, f'Question updated successfully!')
                        return redirect('quiz_detail', quiz_id=quiz.id)
                
                elif question_type == 'true_false':
                    # Create True/False answers
                    correct_answer = request.POST.get('tf_correct', 'true')
                    Answer.objects.create(
                        question=question,
                        answer_text='True',
                        is_correct=(correct_answer == 'true'),
                        order=1
                    )
                    Answer.objects.create(
                        question=question,
                        answer_text='False',
                        is_correct=(correct_answer == 'false'),
                        order=2
                    )
                    messages.success(request, f'Question updated successfully!')
                    return redirect('quiz_detail', quiz_id=quiz.id)
            else:
                messages.success(request, f'Question updated successfully!')
                return redirect('quiz_detail', quiz_id=quiz.id)
    
    context = {
        'question': question,
        'quiz': quiz,
        'course': quiz.course,
        'answers': question.answers.all().order_by('order'),
    }
    
    return render(request, 'blog/edit_question.html', context)


@instructor_required
def delete_question(request, question_id):
    """Delete a question from a quiz"""
    from blog.models import Question
    question = get_object_or_404(Question, id=question_id, quiz__course__instructor=request.user)
    quiz = question.quiz
    
    if request.method == 'POST':
        question_text = question.question_text[:50] + "..." if len(question.question_text) > 50 else question.question_text
        question.delete()
        messages.success(request, f'Question "{question_text}" deleted successfully!')
        return redirect('quiz_detail', quiz_id=quiz.id)
    
    context = {
        'question': question,
        'quiz': quiz,
        'course': quiz.course,
    }
    
    return render(request, 'blog/delete_question.html', context)


@instructor_required
def reorder_questions(request, quiz_id):
    """Reorder questions in a quiz"""
    from blog.models import Quiz, Question
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    
    if request.method == 'POST':
        question_ids = request.POST.getlist('question_order')
        
        for i, question_id in enumerate(question_ids):
            try:
                question = Question.objects.get(id=question_id, quiz=quiz)
                question.order = i + 1
                question.save()
            except Question.DoesNotExist:
                continue
        
        messages.success(request, 'Questions reordered successfully!')
        return redirect('quiz_detail', quiz_id=quiz.id)
    
    questions = quiz.questions.all().order_by('order', 'id')
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'course': quiz.course,
    }
    
    return render(request, 'blog/reorder_questions.html', context)


# Student Quiz Taking Views

def quiz_list_for_students(request, course_id):
    """List all available quizzes for students in a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if student is enrolled in the course
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'student':
        messages.error(request, 'Only students can take quizzes.')
        return redirect('course_list')
    
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.error(request, 'You must be enrolled in this course to view quizzes.')
        return redirect('course_detail', course_id=course_id)
    
    # Get published quizzes that are available
    from blog.models import Quiz, QuizAttempt
    quizzes = Quiz.objects.filter(
        course=course, 
        is_published=True
    ).select_related('course').prefetch_related('attempts').order_by('-created_date')
    
    # Add attempt information for each quiz
    quiz_data = []
    for quiz in quizzes:
        user_attempts = quiz.attempts.filter(student=request.user).order_by('-started_at')
        
        quiz_info = {
            'quiz': quiz,
            'total_attempts': user_attempts.count(),
            'max_attempts': quiz.max_attempts,
            'can_attempt': user_attempts.count() < quiz.max_attempts if quiz.max_attempts else True,
            'best_score': None,
            'last_attempt': user_attempts.first() if user_attempts.exists() else None,
            'is_available': quiz.is_available,
        }
        
        # Calculate best score
        completed_attempts = user_attempts.filter(status='completed')
        if completed_attempts.exists():
            quiz_info['best_score'] = max(attempt.percentage or 0 for attempt in completed_attempts)
        
        quiz_data.append(quiz_info)
    
    context = {
        'course': course,
        'quiz_data': quiz_data,
    }
    
    return render(request, 'blog/student_quiz_list.html', context)


def start_quiz(request, quiz_id):
    """Start a new quiz attempt"""
    from blog.models import Quiz, QuizAttempt
    quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)
    
    # Check if student is enrolled
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'student':
        messages.error(request, 'Only students can take quizzes.')
        return redirect('course_list')
    
    if not Enrollment.objects.filter(student=request.user, course=quiz.course).exists():
        messages.error(request, 'You must be enrolled in this course to take quizzes.')
        return redirect('course_detail', course_id=quiz.course.id)
    
    # Check quiz availability
    if not quiz.is_available:
        messages.error(request, 'This quiz is not currently available.')
        return redirect('student_quiz_list', course_id=quiz.course.id)
    
    # Check if quiz has questions
    if quiz.total_questions == 0:
        messages.error(request, 'This quiz has no questions and cannot be taken.')
        return redirect('student_quiz_list', course_id=quiz.course.id)
    
    # Check attempt limits
    existing_attempts = QuizAttempt.objects.filter(student=request.user, quiz=quiz)
    if quiz.max_attempts and existing_attempts.count() >= quiz.max_attempts:
        messages.error(request, f'You have reached the maximum number of attempts ({quiz.max_attempts}) for this quiz.')
        return redirect('student_quiz_list', course_id=quiz.course.id)
    
    # Check for existing in-progress attempt
    in_progress_attempt = existing_attempts.filter(status='in_progress').first()
    if in_progress_attempt:
        return redirect('take_quiz', attempt_id=in_progress_attempt.id)
    
    # Create new attempt
    attempt_number = existing_attempts.count() + 1
    attempt = QuizAttempt.objects.create(
        student=request.user,
        quiz=quiz,
        attempt_number=attempt_number
    )
    
    messages.success(request, f'Quiz attempt started! You have {attempt_number} of {quiz.max_attempts or "unlimited"} attempts.')
    return redirect('take_quiz', attempt_id=attempt.id)


def take_quiz(request, attempt_id):
    """Take a quiz - show questions and collect answers"""
    from blog.models import QuizAttempt, QuizResponse, Question, Answer
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    
    if attempt.status != 'in_progress':
        messages.error(request, 'This quiz attempt is no longer active.')
        return redirect('quiz_results', attempt_id=attempt.id)
    
    quiz = attempt.quiz
    questions = quiz.questions.all().order_by('order', 'id')
    
    # Shuffle questions if enabled
    if quiz.shuffle_questions:
        questions = list(questions)
        import random
        random.shuffle(questions)
    
    if request.method == 'POST':
        # Process quiz submission
        for question in questions:
            response, created = QuizResponse.objects.get_or_create(
                attempt=attempt,
                question=question,
                defaults={'answered_at': timezone.now()}
            )
            
            if question.question_type == 'multiple_choice':
                answer_id = request.POST.get(f'question_{question.id}')
                if answer_id:
                    try:
                        selected_answer = Answer.objects.get(id=answer_id, question=question)
                        response.selected_answer = selected_answer
                        response.text_answer = ''
                    except Answer.DoesNotExist:
                        pass
            
            elif question.question_type == 'true_false':
                answer_value = request.POST.get(f'question_{question.id}')
                if answer_value in ['True', 'False']:
                    # For true/false questions, store the text value
                    response.text_answer = answer_value
                    response.selected_answer = None
                    # Try to find matching answer for auto-grading
                    try:
                        matching_answer = Answer.objects.get(
                            question=question, 
                            answer_text__iexact=answer_value
                        )
                        response.selected_answer = matching_answer
                    except Answer.DoesNotExist:
                        pass
            
            elif question.question_type == 'short_answer':
                text_answer = request.POST.get(f'question_{question.id}', '').strip()
                response.text_answer = text_answer
                response.selected_answer = None
            
            response.answered_at = timezone.now()
            response.save()
            
            # Auto-grade MC and T/F questions
            if question.question_type in ['multiple_choice', 'true_false']:
                response.auto_grade()
        
        # Complete the attempt
        attempt.complete_attempt()
        messages.success(request, 'Quiz submitted successfully!')
        return redirect('quiz_results', attempt_id=attempt.id)
    
    # Get existing responses
    responses = {r.question_id: r for r in QuizResponse.objects.filter(attempt=attempt)}
    
    # Add response data to questions
    for question in questions:
        question.current_response = responses.get(question.id)
        # For now, we'll use the original order of answers
        # Answer shuffling can be added as a future feature
        question.shuffled_answers = question.answers.all().order_by('order')
    
    context = {
        'attempt': attempt,
        'quiz': quiz,
        'questions': questions,
        'responses': responses,
    }
    
    return render(request, 'blog/take_quiz.html', context)


def quiz_results(request, attempt_id):
    """Show quiz results to student"""
    from blog.models import QuizAttempt
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    
    if attempt.status == 'in_progress':
        messages.warning(request, 'Quiz is still in progress.')
        return redirect('take_quiz', attempt_id=attempt.id)
    
    quiz = attempt.quiz
    responses = attempt.responses.all().select_related('question', 'selected_answer')
    
    # Calculate statistics
    total_questions = responses.count()
    correct_answers = responses.filter(is_correct=True).count()
    
    context = {
        'attempt': attempt,
        'quiz': quiz,
        'responses': responses,
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'show_correct_answers': quiz.show_correct_answers,
    }
    
    return render(request, 'blog/quiz_results.html', context)


# Instructor Quiz Grading Views

@instructor_required
def quiz_attempts(request, quiz_id):
    """View all attempts for a quiz (instructor)"""
    from blog.models import Quiz, QuizAttempt
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    
    attempts = QuizAttempt.objects.filter(quiz=quiz).select_related(
        'student', 'student__userprofile'
    ).order_by('-started_at')
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        attempts = attempts.filter(status=status_filter)
    
    # Statistics
    total_attempts = attempts.count()
    completed_attempts = attempts.filter(status='completed')
    average_score = None
    if completed_attempts.exists():
        scores = [attempt.percentage for attempt in completed_attempts if attempt.percentage is not None]
        if scores:
            average_score = sum(scores) / len(scores)
    
    context = {
        'quiz': quiz,
        'attempts': attempts,
        'total_attempts': total_attempts,
        'completed_attempts': completed_attempts.count(),
        'average_score': average_score,
        'status_filter': status_filter,
    }
    
    return render(request, 'blog/quiz_attempts.html', context)


@instructor_required
def grade_quiz_attempt(request, attempt_id):
    """Grade a specific quiz attempt (instructor)"""
    from blog.models import QuizAttempt, QuizResponse
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, quiz__course__instructor=request.user)
    
    responses = QuizResponse.objects.filter(attempt=attempt).select_related(
        'question', 'selected_answer'
    ).order_by('question__order', 'question__id')
    
    if request.method == 'POST':
        # Process grading for short answer questions
        for response in responses:
            if response.question.question_type == 'short_answer':
                points_key = f'points_{response.id}'
                feedback_key = f'feedback_{response.id}'
                
                points = request.POST.get(points_key, '0')
                feedback = request.POST.get(feedback_key, '').strip()
                
                try:
                    points = float(points)
                    points = max(0, min(points, float(response.question.points)))  # Clamp between 0 and max points
                    response.points_earned = points
                    response.is_correct = points > 0
                except ValueError:
                    response.points_earned = 0
                    response.is_correct = False
                
                response.feedback = feedback
                response.save()
        
        # Recalculate attempt score
        attempt.complete_attempt()
        messages.success(request, 'Quiz graded successfully!')
        return redirect('quiz_attempts', quiz_id=attempt.quiz.id)
    
    # Separate responses by type
    auto_graded = responses.filter(question__question_type__in=['multiple_choice', 'true_false'])
    manual_graded = responses.filter(question__question_type='short_answer')
    
    context = {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'responses': responses,
        'auto_graded': auto_graded,
        'manual_graded': manual_graded,
    }
    
    return render(request, 'blog/grade_quiz_attempt.html', context)


# ================================
# ANNOUNCEMENT VIEWS - Phase 4 - ACTIVATED
# ================================

from django.db.models import Q

@login_required
def course_announcements(request, course_id):
    #Display all announcements for a course
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user has access to this course
    if hasattr(request.user, 'userprofile'):
        profile = request.user.userprofile
        
        # Instructors can see all announcements for their courses
        if profile.role == 'instructor' and course.instructor == request.user:
            announcements = course.announcements.all()
        # Students can only see published, visible announcements for enrolled courses
        elif profile.role == 'student':
            if not Enrollment.objects.filter(student=request.user, course=course, status='enrolled').exists():
                messages.error(request, 'You must be enrolled in this course to view announcements.')
                return redirect('course_detail', course_id=course.id)
            
            announcements = course.announcements.filter(
                is_published=True
            ).filter(
                Q(scheduled_for__isnull=True) | Q(scheduled_for__lte=timezone.now())
            )
        else:
            messages.error(request, 'You do not have permission to view announcements for this course.')
            return redirect('course_list')
    else:
        messages.error(request, 'You must complete your profile to view announcements.')
        return redirect('course_list')
    
    # Mark announcements as read for students
    if profile.role == 'student':
        for announcement in announcements:
            AnnouncementRead.objects.get_or_create(
                student=request.user,
                announcement=announcement
            )
    
    context = {
        'course': course,
        'announcements': announcements,
        'is_instructor': profile.role == 'instructor' and course.instructor == request.user,
    }
    
    return render(request, 'blog/course_announcements.html', context)


@login_required
def create_announcement(request, course_id):
    #Create a new announcement for a course (instructors only)
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor for this course
    if not hasattr(request.user, 'userprofile') or \
       request.user.userprofile.role != 'instructor' or \
       course.instructor != request.user:
        messages.error(request, 'You do not have permission to create announcements for this course.')
        return redirect('course_detail', course_id=course.id)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        priority = request.POST.get('priority', 'normal')
        is_published = request.POST.get('is_published') == 'on'
        is_pinned = request.POST.get('is_pinned') == 'on'
        scheduled_for = request.POST.get('scheduled_for')
        
        if not title or not content:
            messages.error(request, 'Title and content are required.')
            return render(request, 'blog/create_announcement.html', {
                'course': course,
                'title': title,
                'content': content,
                'priority': priority,
                'is_published': is_published,
                'is_pinned': is_pinned,
                'scheduled_for': scheduled_for,
            })
        
        # Parse scheduled_for if provided
        scheduled_datetime = None
        if scheduled_for:
            try:
                from datetime import datetime
                scheduled_datetime = datetime.fromisoformat(scheduled_for.replace('T', ' '))
                # Convert to timezone-aware datetime
                scheduled_datetime = timezone.make_aware(scheduled_datetime)
            except ValueError:
                messages.error(request, 'Invalid scheduled date format.')
                return render(request, 'blog/create_announcement.html', {
                    'course': course,
                    'title': title,
                    'content': content,
                    'priority': priority,
                    'is_published': is_published,
                    'is_pinned': is_pinned,
                    'scheduled_for': scheduled_for,
                })
        
        # Create the announcement
        announcement = Announcement.objects.create(
            course=course,
            title=title,
            content=content,
            priority=priority,
            is_published=is_published,
            is_pinned=is_pinned,
            scheduled_for=scheduled_datetime,
            author=request.user
        )
        
        messages.success(request, f'Announcement "{title}" created successfully!')
        return redirect('course_announcements', course_id=course.id)
    
    context = {
        'course': course,
    }
    
    return render(request, 'blog/create_announcement.html', context)


@login_required
def edit_announcement(request, announcement_id):
    #Edit an existing announcement (instructors only)
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    # Check if user is the instructor for this course or the announcement author
    if not hasattr(request.user, 'userprofile') or \
       request.user.userprofile.role != 'instructor' or \
       (announcement.course.instructor != request.user and announcement.author != request.user):
        messages.error(request, 'You do not have permission to edit this announcement.')
        return redirect('course_announcements', course_id=announcement.course.id)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        priority = request.POST.get('priority', 'normal')
        is_published = request.POST.get('is_published') == 'on'
        is_pinned = request.POST.get('is_pinned') == 'on'
        scheduled_for = request.POST.get('scheduled_for')
        
        if not title or not content:
            messages.error(request, 'Title and content are required.')
            return render(request, 'blog/edit_announcement.html', {
                'announcement': announcement,
                'title': title,
                'content': content,
                'priority': priority,
                'is_published': is_published,
                'is_pinned': is_pinned,
                'scheduled_for': scheduled_for,
            })
        
        # Parse scheduled_for if provided
        scheduled_datetime = None
        if scheduled_for:
            try:
                from datetime import datetime
                scheduled_datetime = datetime.fromisoformat(scheduled_for.replace('T', ' '))
                scheduled_datetime = timezone.make_aware(scheduled_datetime)
            except ValueError:
                messages.error(request, 'Invalid scheduled date format.')
                return render(request, 'blog/edit_announcement.html', {
                    'announcement': announcement,
                    'title': title,
                    'content': content,
                    'priority': priority,
                    'is_published': is_published,
                    'is_pinned': is_pinned,
                    'scheduled_for': scheduled_for,
                })
        
        # Update the announcement
        announcement.title = title
        announcement.content = content
        announcement.priority = priority
        announcement.is_published = is_published
        announcement.is_pinned = is_pinned
        announcement.scheduled_for = scheduled_datetime
        announcement.save()
        
        messages.success(request, f'Announcement "{title}" updated successfully!')
        return redirect('course_announcements', course_id=announcement.course.id)
    
    context = {
        'announcement': announcement,
        'scheduled_for_formatted': announcement.scheduled_for.strftime('%Y-%m-%dT%H:%M') if announcement.scheduled_for else '',
    }
    
    return render(request, 'blog/edit_announcement.html', context)


@login_required
def delete_announcement(request, announcement_id):
    #Delete an announcement (instructors only)
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    # Check if user is the instructor for this course or the announcement author
    if not hasattr(request.user, 'userprofile') or \
       request.user.userprofile.role != 'instructor' or \
       (announcement.course.instructor != request.user and announcement.author != request.user):
        messages.error(request, 'You do not have permission to delete this announcement.')
        return redirect('course_announcements', course_id=announcement.course.id)
    
    course_id = announcement.course.id
    title = announcement.title
    
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, f'Announcement "{title}" deleted successfully!')
        return redirect('course_announcements', course_id=course_id)
    
    context = {
        'announcement': announcement,
    }
    
    return render(request, 'blog/delete_announcement.html', context)


@login_required
def announcement_detail(request, announcement_id):
    #View a single announcement in detail
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    # Check if user has access to this announcement
    if hasattr(request.user, 'userprofile'):
        profile = request.user.userprofile
        
        # Instructors can see all announcements for their courses
        if profile.role == 'instructor' and announcement.course.instructor == request.user:
            pass  # Access granted
        # Students can only see published, visible announcements for enrolled courses
        elif profile.role == 'student':
            if not Enrollment.objects.filter(student=request.user, course=announcement.course, status='enrolled').exists():
                messages.error(request, 'You must be enrolled in this course to view this announcement.')
                return redirect('course_detail', course_id=announcement.course.id)
            
            if not announcement.should_be_visible:
                messages.error(request, 'This announcement is not available.')
                return redirect('course_announcements', course_id=announcement.course.id)
            
            # Mark as read
            AnnouncementRead.objects.get_or_create(
                student=request.user,
                announcement=announcement
            )
        else:
            messages.error(request, 'You do not have permission to view this announcement.')
            return redirect('course_list')
    else:
        messages.error(request, 'You must complete your profile to view announcements.')
        return redirect('course_list')
    
    # Check if student has read this announcement
    is_read = False
    if profile.role == 'student':
        is_read = AnnouncementRead.objects.filter(
            student=request.user,
            announcement=announcement
        ).exists()
    
    context = {
        'announcement': announcement,
        'is_instructor': profile.role == 'instructor' and announcement.course.instructor == request.user,
        'is_read': is_read,
    }
    
    return render(request, 'blog/announcement_detail.html', context)
