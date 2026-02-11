"""
Blog Post Views
---------------
Personal blog posts, viewing, commenting, and management.
"""

import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

from blog.models import BlogPost, BlogComment
from blog.views.helpers import is_content_quarantined, can_view_quarantined_content


@login_required
def user_profile(request, username):
    """Display user profile with their blog posts"""
    profile_user = get_object_or_404(User, username=username)
    user_profile = profile_user.userprofile if hasattr(profile_user, 'userprofile') else None
    
    # Get recent published blog posts by this user
    blog_posts = BlogPost.objects.filter(
        author=profile_user,
        status='published'
    ).order_by('-published_date')[:5]
    
    total_blog_posts = BlogPost.objects.filter(
        author=profile_user,
        status='published'
    ).count()
    
    context = {
        'profile_user': profile_user,
        'user_profile': user_profile,
        'blog_posts': blog_posts,
        'total_blog_posts': total_blog_posts,
    }
    
    return render(request, 'blog/user_profile.html', context)


@login_required
def user_blog_list(request, username):
    """Display all published blog posts by a specific user"""
    profile_user = get_object_or_404(User, username=username)
    
    # Get all published blog posts by this user
    blog_posts = BlogPost.objects.filter(
        author=profile_user,
        status='published'
    ).order_by('-published_date')
    
    # Pagination
    paginator = Paginator(blog_posts, 10)  # 10 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'profile_user': profile_user,
        'page_obj': page_obj,
        'blog_posts': page_obj.object_list,
    }
    
    return render(request, 'blog/user_blog_list.html', context)


@login_required
def blog_post_detail(request, username, slug):
    """Display individual blog post with comments"""
    profile_user = get_object_or_404(User, username=username)
    blog_post = get_object_or_404(
        BlogPost,
        author=profile_user,
        slug=slug,
        status='published'
    )
    
    # Check if post is quarantined
    quarantine = is_content_quarantined(blog_post)
    if quarantine:
        # Only allow admins and author to view
        if not can_view_quarantined_content(blog_post, request.user):
            messages.error(
                request, 
                'This content is currently under review and not available for public viewing.'
            )
            return redirect('user_blog_list', username=username)
    
    # Increment view count
    blog_post.increment_view_count()
    
    # Get approved comments (top-level only)
    comments = BlogComment.objects.filter(
        post=blog_post,
        is_approved=True,
        parent=None
    ).select_related('author').order_by('created_date')
    
    # Handle comment submission
    if request.method == 'POST' and request.user.is_authenticated:
        if blog_post.allow_comments and not quarantine:  # Don't allow comments on quarantined posts
            content = request.POST.get('content', '').strip()
            parent_id = request.POST.get('parent_id')
            
            if content:
                parent_comment = None
                if parent_id:
                    try:
                        parent_comment = BlogComment.objects.get(
                            id=parent_id,
                            post=blog_post,
                            is_approved=True
                        )
                    except BlogComment.DoesNotExist:
                        pass
                
                BlogComment.objects.create(
                    post=blog_post,
                    author=request.user,
                    parent=parent_comment,
                    content=content
                )
                
                messages.success(request, 'Your comment has been posted!')
                return redirect('blog_post_detail', username=username, slug=slug)
            else:
                messages.error(request, 'Comment cannot be empty.')
    
    context = {
        'blog_post': blog_post,
        'profile_user': profile_user,
        'comments': comments,
        'can_comment': request.user.is_authenticated and blog_post.allow_comments and not quarantine,
        'is_quarantined': quarantine is not None,
        'quarantine': quarantine,
    }
    
    return render(request, 'blog/blog_post_detail.html', context)


@login_required
def my_blog_dashboard(request):
    """Dashboard for user's own blog management"""
    # Get user's blog posts
    blog_posts = BlogPost.objects.filter(
        author=request.user
    ).order_by('-created_date')
    
    # Pagination
    paginator = Paginator(blog_posts, 15)  # 15 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_posts = blog_posts.count()
    published_posts = blog_posts.filter(status='published')
    draft_posts = blog_posts.filter(status='draft')
    archived_posts = blog_posts.filter(status='archived')
    
    from django.utils import timezone
    stats = {
        'total_posts': total_posts,
        'published_posts': published_posts.count(),
        'draft_posts': draft_posts.count(),
        'total_views': sum(post.view_count for post in blog_posts),
        'total_comments': sum(post.get_comment_count() for post in blog_posts),
    }
    
    context = {
        'page_obj': page_obj,
        'blog_posts': page_obj.object_list,
        'stats': stats,
        'total_posts': total_posts,
        'total_views': stats['total_views'],
        'total_comments': stats['total_comments'],
        'posts_this_month': blog_posts.filter(
            created_date__month=timezone.now().month,
            created_date__year=timezone.now().year
        ).count(),
        'published_count': stats['published_posts'],
        'draft_count': stats['draft_posts'],
        'archived_count': archived_posts.count(),
        'is_paginated': page_obj.has_other_pages(),
    }
    
    return render(request, 'blog/my_blog_dashboard.html', context)


@login_required
def create_blog_post(request):
    """Create a new blog post"""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        excerpt = request.POST.get('excerpt', '').strip()
        status = request.POST.get('status', 'draft')
        allow_comments = request.POST.get('allow_comments') == 'on'
        
        errors = []
        
        # Validation
        if not title:
            errors.append('Title is required.')
        if not content:
            errors.append('Content is required.')
        if status not in ['draft', 'published']:
            errors.append('Invalid status.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Create blog post
            blog_post = BlogPost.objects.create(
                author=request.user,
                title=title,
                content=content,
                excerpt=excerpt,
                status=status,
                allow_comments=allow_comments
            )
            
            messages.success(request, f'Blog post "{title}" created successfully!')
            return redirect('edit_blog_post', post_id=blog_post.id)
    
    context = {
        'action': 'Create',
    }
    
    return render(request, 'blog/blog_post_form.html', context)


@login_required
def edit_blog_post(request, post_id):
    """Edit an existing blog post"""
    blog_post = get_object_or_404(BlogPost, id=post_id)
    
    # Check permissions
    if not blog_post.can_edit(request.user):
        messages.error(request, 'You do not have permission to edit this blog post.')
        return redirect('my_blog_dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        excerpt = request.POST.get('excerpt', '').strip()
        status = request.POST.get('status', blog_post.status)
        allow_comments = request.POST.get('allow_comments') == 'on'
        
        errors = []
        
        # Validation
        if not title:
            errors.append('Title is required.')
        if not content:
            errors.append('Content is required.')
        if status not in ['draft', 'published', 'archived']:
            errors.append('Invalid status.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Update blog post
            blog_post.title = title
            blog_post.content = content
            blog_post.excerpt = excerpt
            blog_post.status = status
            blog_post.allow_comments = allow_comments
            
            # Regenerate slug if title changed
            if slugify(title) != blog_post.slug:
                base_slug = slugify(title)
                slug = base_slug
                counter = 1
                while BlogPost.objects.filter(slug=slug).exclude(pk=blog_post.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                blog_post.slug = slug
            
            blog_post.save()
            
            messages.success(request, f'Blog post "{title}" updated successfully!')
            
            if status == 'published':
                return redirect('blog_post_detail', username=request.user.username, slug=blog_post.slug)
            else:
                return redirect('my_blog_dashboard')
    
    context = {
        'blog_post': blog_post,
        'action': 'Edit',
    }
    
    return render(request, 'blog/blog_post_form.html', context)


@login_required
def delete_blog_post(request, post_id):
    """Delete a blog post"""
    blog_post = get_object_or_404(BlogPost, id=post_id)
    
    # Check permissions
    if not blog_post.can_edit(request.user):
        messages.error(request, 'You do not have permission to delete this blog post.')
        return redirect('my_blog_dashboard')
    
    if request.method == 'POST':
        title = blog_post.title
        blog_post.delete()
        messages.success(request, f'Blog post "{title}" deleted successfully!')
        return redirect('my_blog_dashboard')
    
    context = {
        'blog_post': blog_post,
    }
    
    return render(request, 'blog/blog_post_confirm_delete.html', context)


@login_required
def delete_blog_comment(request, comment_id):
    """Delete a blog comment"""
    comment = get_object_or_404(BlogComment, id=comment_id)
    
    # Check permissions
    if not comment.can_delete(request.user):
        messages.error(request, 'You do not have permission to delete this comment.')
        return redirect('blog_post_detail', 
                       username=comment.post.author.username, 
                       slug=comment.post.slug)
    
    if request.method == 'POST':
        post = comment.post
        comment.delete()
        messages.success(request, 'Comment deleted successfully!')
        return redirect('blog_post_detail', 
                       username=post.author.username, 
                       slug=post.slug)
    
    context = {
        'comment': comment,
    }
    
    return render(request, 'blog/blog_comment_confirm_delete.html', context)


@cache_page(300)  # Cache for 5 minutes
@vary_on_cookie  # Cache separately per user
@login_required
def all_blogs(request):
    """Display recent blog posts from all users"""
    # Get all published blog posts
    blog_posts = BlogPost.objects.filter(
        status='published'
    ).select_related('author').order_by('-published_date')
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        blog_posts = blog_posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(excerpt__icontains=search_query) |
            Q(author__first_name__icontains=search_query) |
            Q(author__last_name__icontains=search_query) |
            Q(author__username__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(blog_posts, 12)  # 12 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'blog_posts': page_obj.object_list,
        'search_query': search_query,
        'total_posts': paginator.count,
    }
    
    return render(request, 'blog/all_blogs.html', context)


@login_required
def upload_blog_image(request):
    """AJAX view to handle blog image uploads for markdown content"""
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if image.content_type not in allowed_types:
            return JsonResponse({
                'success': False, 
                'error': 'Invalid file type. Please upload JPG, PNG, GIF, or WebP images.'
            })
        
        # Validate file size (max 2MB)
        if image.size > 2 * 1024 * 1024:
            return JsonResponse({
                'success': False, 
                'error': 'File too large. Maximum size is 2MB.'
            })
        
        try:
            import os
            import uuid
            from django.core.files.storage import default_storage
            from blog.utils.image_processing import process_uploaded_image
            
            # Process image to remove EXIF metadata
            processed_image, processing_info = process_uploaded_image(image, strip_exif=True)
            
            # Generate unique filename
            ext = os.path.splitext(image.name)[1].lower()
            filename = f"user_{request.user.id}_{uuid.uuid4().hex[:8]}{ext}"
            
            # Update processed image name
            processed_image.name = filename
            
            # Save to blog_images directory
            file_path = f"blog_images/{filename}"
            saved_path = default_storage.save(file_path, processed_image)
            
            # Get the full URL
            image_url = default_storage.url(saved_path)
            
            # Log EXIF removal for security audit
            if processing_info.get('exif_removed', False):
                exif_summary = processing_info.get('summary', {}).get('exif_summary', {})
                logger = logging.getLogger(__name__)
                logger.info(f"EXIF data stripped from blog image upload: {filename}, "
                           f"GPS={exif_summary.get('gps_data', False)}, "
                           f"Device={exif_summary.get('device_info', False)}, "
                           f"User={request.user.username}")
            
            return JsonResponse({
                'success': True,
                'image_url': image_url,
                'filename': filename,
                'markdown_embed': f'![[{filename}]]',
                'markdown_standard': f'![Image]({image_url})',
                'processing_info': {
                    'exif_removed': processing_info.get('exif_removed', False),
                    'original_size': processing_info.get('summary', {}).get('original_size', 0),
                    'processed_size': processing_info.get('summary', {}).get('processed_size', 0)
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Upload failed: {str(e)}'
            })
    
    return JsonResponse({
        'success': False, 
        'error': 'No image file provided.'
    })
