"""
Forum Discussion Views
----------------------
Discussion forums for courses and general topics.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

from blog.models import Forum, Topic, ForumPost, Enrollment
from blog.views.helpers import is_content_quarantined, can_view_quarantined_content


@cache_page(300)  # Cache for 5 minutes
@vary_on_cookie  # Cache separately per user
@login_required
def forum_list(request):
    """Display all forums available to the current user"""
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, 'Please complete your profile setup.')
        return redirect('student_dashboard')
    
    profile = request.user.userprofile
    forums = []
    
    # General forum - all students and instructors can access
    general_forum, created = Forum.objects.get_or_create(
        forum_type='general',
        course=None,
        defaults={
            'title': 'General Discussion',
            'description': 'General discussion for all students and instructors'
        }
    )
    forums.append(general_forum)
    
    # Instructor forum - only instructors can access
    if profile.role == 'instructor':
        instructor_forum, created = Forum.objects.get_or_create(
            forum_type='instructor',
            course=None,
            defaults={
                'title': 'Instructor Forum',
                'description': 'Private discussion area for instructors'
            }
        )
        forums.append(instructor_forum)
        
        # Course forums for instructors - show courses they teach
        course_forums = Forum.objects.filter(
            forum_type='course',
            course__instructor=request.user
        ).select_related('course')
        forums.extend(course_forums)
    
    # Course forums for students - show enrolled courses
    if profile.role == 'student':
        enrollments = Enrollment.objects.filter(
            student=request.user,
            status='enrolled'
        ).select_related('course')
        
        for enrollment in enrollments:
            course_forum, created = Forum.objects.get_or_create(
                forum_type='course',
                course=enrollment.course,
                defaults={
                    'title': f'{enrollment.course.course_code} Discussion',
                    'description': f'Discussion forum for {enrollment.course.title}'
                }
            )
            forums.append(course_forum)
    
    context = {
        'forums': forums,
        'user_role': profile.role,
    }
    
    return render(request, 'blog/forum_list.html', context)


@login_required
def forum_detail(request, forum_id):
    """Display topics in a specific forum"""
    forum = get_object_or_404(Forum, id=forum_id)
    
    # Check permissions
    if not forum.can_view(request.user):
        messages.error(request, 'You do not have permission to view this forum.')
        return redirect('forum_list')
    
    # Note: last_post_date already exists on Topic model and is auto-updated
    topics = forum.topics.all().select_related(
        'created_by',
        'created_by__userprofile',
        'last_post_by',
        'last_post_by__userprofile'
    ).annotate(
        post_count=Count('posts')
    ).order_by('-is_pinned', '-last_post_date')
    
    context = {
        'forum': forum,
        'topics': topics,
        'can_post': forum.can_post(request.user),
    }
    
    return render(request, 'blog/forum_detail.html', context)


@login_required
def topic_detail(request, topic_id):
    """Display posts in a specific topic"""
    topic = get_object_or_404(Topic, id=topic_id)
    
    # Check permissions
    if not topic.can_view(request.user):
        messages.error(request, 'You do not have permission to view this topic.')
        return redirect('forum_list')
    
    # Get all posts
    all_posts = topic.posts.all().select_related('author', 'edited_by')
    
    # Filter out quarantined posts (unless user can view them)
    posts = []
    for post in all_posts:
        quarantine = is_content_quarantined(post)
        if quarantine:
            # Only show if user can view quarantined content
            if can_view_quarantined_content(post, request.user):
                posts.append(post)
        else:
            posts.append(post)
    
    # Calculate permissions for each post
    posts_with_permissions = []
    for post in posts:
        quarantine = is_content_quarantined(post)
        posts_with_permissions.append({
            'post': post,
            'can_edit': post.can_edit(request.user),
            'can_delete': post.can_delete(request.user),
            'is_quarantined': quarantine is not None,
            'quarantine': quarantine,
        })
    
    context = {
        'topic': topic,
        'posts': posts,
        'posts_with_permissions': posts_with_permissions,
        'can_reply': topic.can_reply(request.user),
    }
    
    return render(request, 'blog/topic_detail.html', context)


@login_required
def create_topic(request, forum_id):
    """Create a new topic in a forum"""
    forum = get_object_or_404(Forum, id=forum_id)
    
    # Check permissions
    if not forum.can_post(request.user):
        messages.error(request, 'You do not have permission to create topics in this forum.')
        return redirect('forum_detail', forum_id=forum.id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        if not title or not content:
            messages.error(request, 'Both title and content are required.')
        else:
            with transaction.atomic():
                # Create topic
                topic = Topic.objects.create(
                    forum=forum,
                    title=title,
                    created_by=request.user,
                )
                
                # Create first post
                ForumPost.objects.create(
                    topic=topic,
                    author=request.user,
                    content=content,
                    is_first_post=True,
                )
                
                messages.success(request, 'Topic created successfully!')
                return redirect('topic_detail', topic_id=topic.id)
    
    context = {
        'forum': forum,
    }
    
    return render(request, 'blog/create_topic.html', context)


@login_required
def create_post(request, topic_id):
    """Create a new post in a topic"""
    topic = get_object_or_404(Topic, id=topic_id)
    
    # Check permissions
    if not topic.can_reply(request.user):
        messages.error(request, 'You cannot reply to this topic.')
        return redirect('topic_detail', topic_id=topic.id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        
        if not content:
            messages.error(request, 'Content is required.')
        else:
            ForumPost.objects.create(
                topic=topic,
                author=request.user,
                content=content,
            )
            
            messages.success(request, 'Post created successfully!')
            return redirect('topic_detail', topic_id=topic.id)
    
    context = {
        'topic': topic,
    }
    
    return render(request, 'blog/create_post.html', context)


@login_required
def edit_post(request, post_id):
    """Edit an existing forum post"""
    post = get_object_or_404(ForumPost, id=post_id)
    
    # Check permissions
    if not post.can_edit(request.user):
        messages.error(request, 'You do not have permission to edit this post.')
        return redirect('topic_detail', topic_id=post.topic.id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        
        if not content:
            messages.error(request, 'Content is required.')
        else:
            post.content = content
            post.edited_date = timezone.now()
            post.edited_by = request.user
            post.save()
            
            messages.success(request, 'Post updated successfully!')
            return redirect('topic_detail', topic_id=post.topic.id)
    
    context = {
        'post': post,
        'topic': post.topic,
    }
    
    return render(request, 'blog/edit_post.html', context)


@login_required
def delete_post(request, post_id):
    """Delete a forum post"""
    post = get_object_or_404(ForumPost, id=post_id)
    
    # Check permissions
    if not post.can_delete(request.user):
        messages.error(request, 'You do not have permission to delete this post.')
        return redirect('topic_detail', topic_id=post.topic.id)
    
    if request.method == 'POST':
        topic_id = post.topic.id
        
        # If this is the first post, delete the entire topic
        if post.is_first_post:
            post.topic.delete()
            messages.success(request, 'Topic deleted successfully!')
            return redirect('forum_detail', forum_id=post.topic.forum.id)
        else:
            post.delete()
            messages.success(request, 'Post deleted successfully!')
            return redirect('topic_detail', topic_id=topic_id)
    
    context = {
        'post': post,
        'topic': post.topic,
    }
    
    return render(request, 'blog/delete_post.html', context)
