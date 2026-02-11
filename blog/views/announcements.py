"""
Announcement Views
------------------
Course announcements for instructors and students.
"""

from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from blog.models import Announcement, AnnouncementRead, Course, Enrollment


@login_required
def course_announcements(request, course_id):
    """Display all announcements for a course"""
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
    """Create a new announcement for a course (instructors only)"""
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
    """Edit an existing announcement (instructors only)"""
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
    """Delete an announcement (instructors only)"""
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
    """View a single announcement in detail"""
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
