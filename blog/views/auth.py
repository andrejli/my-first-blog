"""
Authentication views for Django LMS.

This module handles user authentication including:
- Login with role-based redirection
- Logout
- Student registration
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from blog.models import UserProfile


def user_login(request):
    """
    Handle user login with role-based redirection.
    
    Authenticates users and redirects them to appropriate dashboard based on
    their role (admin -> /admin/, instructor -> instructor_dashboard,
    student -> student_dashboard).
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Login page or redirect to appropriate dashboard
        
    POST Parameters:
        username (str): User's username
        password (str): User's password
    """
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
    """
    Handle user logout.
    
    Logs out the current user and redirects to the course list with a
    success message.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponseRedirect: Redirect to course list page
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('course_list')


def user_register(request):
    """
    Handle new student registration.
    
    Creates a new user account with student role. Automatically creates
    a UserProfile with role='student' upon successful registration.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Registration page or redirect to login on success
        
    POST Parameters:
        Form data from UserCreationForm (username, password1, password2)
    """
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
