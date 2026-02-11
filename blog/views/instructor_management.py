"""
Instructor Course Management Views
-----------------------------------
Course creation, editing, lesson management, and materials.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from blog.models import Course, Lesson, CourseMaterial
from blog.views.helpers import instructor_required


@login_required
def instructor_course_detail(request, course_id):
    """Enhanced course management for instructors"""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    # Get enrollment statistics
    total_students = course.get_enrolled_count()
    
    # Optimize: annotate lessons with completion counts in single query
    lessons = Lesson.objects.filter(
        course=course
    ).annotate(
        completed_count=Count(
            'progress',
            filter=Q(progress__completed=True)
        )
    ).order_by('order')
    
    # Build lessons stats (no additional queries)
    lessons_stats = [
        {
            'lesson': lesson,
            'completed_count': lesson.completed_count,
            'completion_rate': (
                lesson.completed_count / total_students * 100
            ) if total_students > 0 else 0,
        }
        for lesson in lessons
    ]
    
    # Calculate counts from already-fetched lessons
    total_lessons_count = len(lessons)
    published_lessons_count = sum(1 for lesson in lessons if lesson.is_published)
    
    context = {
        'course': course,
        'lessons_stats': lessons_stats,
        'total_students': total_students,
        'total_lessons': total_lessons_count,
        'published_lessons': published_lessons_count,
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
