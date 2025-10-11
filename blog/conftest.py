"""
Django LMS Test Configuration

This module provides fixtures and configuration for pytest-django testing.
"""

import pytest


# ================================
# PYTEST FIXTURES
# ================================

@pytest.fixture
def client():
    """Django test client"""
    from django.test import Client
    return Client()


@pytest.fixture
def admin_user():
    """Create admin user"""
    from django.contrib.auth.models import User
    from blog.models import UserProfile
    
    user = User.objects.create_user(
        username='admin',
        email='admin@lms.com',
        password='admin123',
        is_staff=True,
        is_superuser=True
    )
    
    # Get or update the profile (signal should have created it)
    try:
        profile = user.userprofile
        profile.role = 'admin'
        profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=user, role='admin')
    
    return user


@pytest.fixture
def instructor_user():
    """Create instructor user with profile"""
    from django.contrib.auth.models import User
    from blog.models import UserProfile
    
    user = User.objects.create_user(
        username='instructor',
        email='instructor@lms.com',
        password='instructor123',
        first_name='John',
        last_name='Teacher'
    )
    
    # Get or update the profile (signal should have created it)
    try:
        profile = user.userprofile
        profile.role = 'instructor'
        profile.bio = 'Experienced instructor with 10+ years in computer science.'
        profile.phone = '555-0123'
        profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(
            user=user,
            role='instructor',
            bio='Experienced instructor with 10+ years in computer science.',
            phone='555-0123'
        )
    
    return user


@pytest.fixture
def student_user():
    """Create student user with profile"""
    from django.contrib.auth.models import User
    from blog.models import UserProfile
    
    user = User.objects.create_user(
        username='student',
        email='student@lms.com',
        password='student123',
        first_name='Jane',
        last_name='Student'
    )
    
    # Get or update the profile (signal should have created it)
    try:
        profile = user.userprofile
        profile.role = 'student'
        profile.bio = 'Computer science student interested in web development.'
        profile.phone = '555-0456'
        profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(
            user=user,
            role='student',
            bio='Computer science student interested in web development.',
            phone='555-0456'
        )
    
    return user


@pytest.fixture
def course(instructor_user):
    """Create a test course"""
    from blog.models import Course
    
    return Course.objects.create(
        title='Introduction to Web Development',
        course_code='CS101',
        description='Learn the basics of HTML, CSS, and JavaScript.',
        instructor=instructor_user,
        is_published=True,
        duration_weeks=12,
        max_students=30
    )


@pytest.fixture
def enrolled_student(student_user, course):
    """Create enrollment for student in course"""
    from blog.models import Enrollment
    
    enrollment = Enrollment.objects.create(
        student=student_user,
        course=course,
        status='enrolled'
    )
    return enrollment


@pytest.fixture
def quiz(course):
    """Create a test quiz"""
    from blog.models import Quiz
    from datetime import datetime, timedelta
    
    return Quiz.objects.create(
        course=course,
        title='HTML Knowledge Check',
        description='Test your understanding of HTML basics.',
        time_limit=30,
        max_attempts=3,
        due_date=datetime.now() + timedelta(days=14),
        is_published=True
    )


@pytest.fixture
def theme():
    """Create a test theme"""
    from blog.models import SiteTheme
    
    return SiteTheme.objects.create(
        name='test_theme',
        display_name='Test Theme',
        theme_key='terminal-green',
        description='A theme for testing purposes',
        is_default=False,
        is_active=True
    )