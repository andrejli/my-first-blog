"""
Assignment and Grading Views
-----------------------------
Assignment submission, grading, and feedback.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from blog.models import Assignment, Course, Enrollment, Submission
from blog.views.helpers import instructor_required


# =============================================================================
# INSTRUCTOR ASSIGNMENT MANAGEMENT VIEWS
# =============================================================================

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


# =============================================================================
# INSTRUCTOR GRADING VIEWS
# =============================================================================

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
        action = request.POST.get('action', request.POST.get('submit_type', 'submit'))
        text_submission = request.POST.get('text_submission', request.POST.get('content', '')).strip() if assignment.allow_text_submission else ''
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
