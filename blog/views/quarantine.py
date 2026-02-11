"""
Content Quarantine Management Views
------------------------------------
Admin/staff views for quarantining and managing problematic content.
"""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from blog.models import (
    BlogPost,
    ContentQuarantine,
    ForumPost,
    QuarantineDecision
)
from blog.views.helpers import is_content_quarantined


# =============================================================================
# CONTENT QUARANTINE MANAGEMENT VIEWS
# =============================================================================

@staff_member_required
def quarantine_forum_post(request, post_id):
    """
    Quarantine a forum post (Admin/Staff only).
    
    Hides the post from public view and creates a record for resolution.
    """
    post = get_object_or_404(ForumPost, id=post_id)
    
    # Check if already quarantined
    existing_quarantine = is_content_quarantined(post)
    if existing_quarantine:
        messages.warning(request, 'This post is already quarantined.')
        return redirect('topic_detail', topic_id=post.topic.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        
        if not reason:
            messages.error(request, 'Please provide a reason for quarantine.')
        else:
            # Create quarantine record
            ct = ContentType.objects.get_for_model(post)
            
            quarantine = ContentQuarantine.objects.create(
                content_type=ct,
                object_id=post.id,
                quarantined_by=request.user,
                quarantine_reason=reason,
                status='ACTIVE',
                resolution_deadline=timezone.now() + timezone.timedelta(days=7)
            )
            
            # Create Secret Chamber poll for democratic resolution
            try:
                from blog.secret_chamber.models import AdminPoll, PollOption
                
                poll = AdminPoll.objects.create(
                    title=f"Quarantine Resolution: Forum Post #{post.id}",
                    description=f"**Reason for Quarantine:** {reason}\n\n**Content Preview:** {post.content[:200]}...\n\n**Author:** {post.author.username}\n**Topic:** {post.topic.title}\n\n**Decision Required:** Should this content be restored or deleted?",
                    poll_type='multiple_choice',
                    created_by=request.user,
                    end_date=timezone.now() + timezone.timedelta(days=7),
                    is_active=True,
                    allow_comments=True
                )
                
                # Create poll options
                PollOption.objects.create(poll=poll, option_text='RESTORE - Content is acceptable, restore to public view', order=1)
                PollOption.objects.create(poll=poll, option_text='DELETE - Content violates policy, permanently remove', order=2)
                PollOption.objects.create(poll=poll, option_text='EXTEND - Need more time to decide, extend deadline', order=3)
                
                # Link poll to quarantine
                quarantine.linked_poll = poll
                quarantine.save()
                
                messages.success(
                    request, 
                    f'Forum post quarantined and Secret Chamber poll created. '
                    f'Resolution deadline: {quarantine.resolution_deadline.strftime("%B %d, %Y at %I:%M %p")}'
                )
            except Exception as e:
                messages.warning(request, f'Content quarantined but poll creation failed: {str(e)}')
            
            return redirect('topic_detail', topic_id=post.topic.id)
    
    context = {
        'post': post,
        'content_type': 'Forum Post',
        'return_url': request.META.get('HTTP_REFERER', '/')
    }
    
    return render(request, 'blog/quarantine_form.html', context)


@staff_member_required
def quarantine_blog_post(request, post_id):
    """
    Quarantine a blog post (Admin/Staff only).
    
    Hides the blog post from public view and creates a record for resolution.
    """
    post = get_object_or_404(BlogPost, id=post_id)
    
    # Check if already quarantined
    existing_quarantine = is_content_quarantined(post)
    if existing_quarantine:
        messages.warning(request, 'This blog post is already quarantined.')
        return redirect('blog_post_detail', username=post.author.username, slug=post.slug)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        
        if not reason:
            messages.error(request, 'Please provide a reason for quarantine.')
        else:
            # Create quarantine record
            ct = ContentType.objects.get_for_model(post)
            
            quarantine = ContentQuarantine.objects.create(
                content_type=ct,
                object_id=post.id,
                quarantined_by=request.user,
                quarantine_reason=reason,
                status='ACTIVE',
                resolution_deadline=timezone.now() + timezone.timedelta(days=7)
            )
            
            # Create Secret Chamber poll for democratic resolution
            try:
                from blog.secret_chamber.models import AdminPoll, PollOption
                
                poll = AdminPoll.objects.create(
                    title=f"Quarantine Resolution: Blog Post #{post.id}",
                    description=f"**Reason for Quarantine:** {reason}\n\n**Content Preview:** {post.content[:200]}...\n\n**Author:** {post.author.username}\n**Title:** {post.title}\n\n**Decision Required:** Should this content be restored or deleted?",
                    poll_type='multiple_choice',
                    created_by=request.user,
                    end_date=timezone.now() + timezone.timedelta(days=7),
                    is_active=True,
                    allow_comments=True
                )
                
                # Create poll options
                PollOption.objects.create(poll=poll, option_text='RESTORE - Content is acceptable, restore to public view', order=1)
                PollOption.objects.create(poll=poll, option_text='DELETE - Content violates policy, permanently remove', order=2)
                PollOption.objects.create(poll=poll, option_text='EXTEND - Need more time to decide, extend deadline', order=3)
                
                # Link poll to quarantine
                quarantine.linked_poll = poll
                quarantine.save()
                
                messages.success(
                    request,
                    f'Blog post quarantined and Secret Chamber poll created. '
                    f'Resolution deadline: {quarantine.resolution_deadline.strftime("%B %d, %Y at %I:%M %p")}'
                )
            except Exception as e:
                messages.warning(request, f'Content quarantined but poll creation failed: {str(e)}')
            
            return redirect('blog_post_detail', username=post.author.username, slug=post.slug)
    
    context = {
        'post': post,
        'content_type': 'Blog Post',
        'return_url': request.META.get('HTTP_REFERER', '/')
    }
    
    return render(request, 'blog/quarantine_form.html', context)


@staff_member_required
def resolve_quarantine(request, quarantine_id):
    """
    Resolve a quarantine (Admin/Staff only).
    
    Options: RESTORE, DELETE, EXTEND
    """
    quarantine = get_object_or_404(ContentQuarantine, id=quarantine_id)
    
    if quarantine.status != 'ACTIVE':
        messages.warning(request, 'This quarantine has already been resolved.')
        return redirect('quarantine_dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '').strip()
        
        if action == 'RESTORE':
            quarantine.status = 'RESOLVED_RESTORE'
            quarantine.save()
            
            # Create decision record
            QuarantineDecision.objects.create(
                quarantine=quarantine,
                poll_result='RESTORE',
                action_taken='RESTORED',
                decision_notes=notes or 'Content manually restored by administrator',
                decided_by=request.user
            )
            
            messages.success(request, 'Content has been restored and is now visible to all users.')
            
        elif action == 'DELETE':
            quarantine.status = 'RESOLVED_DELETE'
            quarantine.save()
            
            # Create decision record
            QuarantineDecision.objects.create(
                quarantine=quarantine,
                poll_result='DELETE',
                action_taken='DELETED',
                decision_notes=notes or 'Content manually deleted by administrator',
                decided_by=request.user
            )
            
            # Optionally delete the actual content
            try:
                content = quarantine.content_object
                if content:
                    content.delete()
                    messages.success(request, 'Content has been permanently deleted.')
                else:
                    messages.success(request, 'Quarantine resolved. Content was already removed.')
            except Exception as e:
                messages.warning(request, f'Quarantine marked as deleted, but content removal failed: {str(e)}')
                
        elif action == 'EXTEND':
            # Extend deadline by 7 days
            if quarantine.resolution_deadline:
                quarantine.resolution_deadline = quarantine.resolution_deadline + timezone.timedelta(days=7)
            else:
                quarantine.resolution_deadline = timezone.now() + timezone.timedelta(days=7)
            quarantine.save()
            
            messages.success(
                request,
                f'Quarantine extended. New deadline: {quarantine.resolution_deadline.strftime("%B %d, %Y at %I:%M %p")}'
            )
        else:
            messages.error(request, 'Invalid action specified.')
        
        return redirect('quarantine_dashboard')
    
    context = {
        'quarantine': quarantine,
    }
    
    return render(request, 'blog/resolve_quarantine.html', context)


@staff_member_required
def quarantine_dashboard(request):
    """
    Dashboard for managing quarantined content (Admin/Staff only).
    
    Shows all active and resolved quarantines with filtering options.
    """
    # Get filter parameters
    status_filter = request.GET.get('status', 'ACTIVE')
    content_type_filter = request.GET.get('content_type', 'all')
    
    # Base queryset
    quarantines = ContentQuarantine.objects.select_related(
        'quarantined_by', 'content_type', 'linked_poll'
    ).order_by('-quarantine_date')
    
    # Apply filters
    if status_filter != 'all':
        quarantines = quarantines.filter(status=status_filter)
    
    if content_type_filter != 'all':
        if content_type_filter == 'forum':
            ct = ContentType.objects.get_for_model(ForumPost)
            quarantines = quarantines.filter(content_type=ct)
        elif content_type_filter == 'blog':
            ct = ContentType.objects.get_for_model(BlogPost)
            quarantines = quarantines.filter(content_type=ct)
    
    # Get statistics
    stats = {
        'total_active': ContentQuarantine.objects.filter(status='ACTIVE').count(),
        'total_resolved': ContentQuarantine.objects.filter(status__startswith='RESOLVED').count(),
        'total_forum_posts': ContentQuarantine.objects.filter(
            content_type=ContentType.objects.get_for_model(ForumPost)
        ).count(),
        'total_blog_posts': ContentQuarantine.objects.filter(
            content_type=ContentType.objects.get_for_model(BlogPost)
        ).count(),
    }
    
    # Pagination
    paginator = Paginator(quarantines, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'quarantines': page_obj.object_list,
        'stats': stats,
        'status_filter': status_filter,
        'content_type_filter': content_type_filter,
    }
    
    return render(request, 'blog/quarantine_dashboard.html', context)
