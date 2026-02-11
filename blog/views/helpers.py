"""
Helper functions and decorators for Django LMS views.

This module contains shared utilities used across multiple view modules:
- Quarantine checking functions
- Custom decorators for role-based access
- Common utility functions
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from blog.models import ContentQuarantine, UserProfile


# =============================================================================
# QUARANTINE HELPER FUNCTIONS
# =============================================================================

def is_content_quarantined(content_object):
    """
    Check if content is currently quarantined.
    
    Args:
        content_object: Django model instance (ForumPost, BlogPost, etc.)
        
    Returns:
        ContentQuarantine instance if quarantined, None otherwise
    """
    ct = ContentType.objects.get_for_model(content_object)
    return ContentQuarantine.objects.filter(
        content_type=ct,
        object_id=content_object.id,
        status='ACTIVE'
    ).first()


def can_view_quarantined_content(content_object, user):
    """
    Check if user can view quarantined content.
    
    Only admins and content authors can view quarantined content.
    
    Args:
        content_object: The quarantined content
        user: User requesting access
        
    Returns:
        bool: True if user can view, False otherwise
    """
    if not user.is_authenticated:
        return False
    
    # Admins can always view
    if user.is_superuser or user.is_staff:
        return True
    
    # Check if user is the author
    if hasattr(content_object, 'author'):
        return content_object.author == user
    elif hasattr(content_object, 'user'):
        return content_object.user == user
    
    return False


# =============================================================================
# CUSTOM DECORATORS
# =============================================================================

def instructor_required(view_func):
    """
    Decorator to require instructor or admin role.
    
    Args:
        view_func: The view function to wrap
        
    Returns:
        Wrapped function that checks for instructor/admin role
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to access this page.')
            return redirect('user_login')
        
        try:
            profile = UserProfile.objects.get(user=request.user)
            if profile.role not in ['instructor', 'admin']:
                messages.error(request, 'You must be an instructor or admin to access this page.')
                return redirect('landing_page')
        except UserProfile.DoesNotExist:
            messages.error(request, 'Profile not found.')
            return redirect('landing_page')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """
    Decorator to require admin role.
    
    Args:
        view_func: The view function to wrap
        
    Returns:
        Wrapped function that checks for admin role
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to access this page.')
            return redirect('user_login')
        
        if not request.user.is_superuser:
            messages.error(request, 'You must be an admin to access this page.')
            return redirect('landing_page')
        
        return view_func(request, *args, **kwargs)
    return wrapper
