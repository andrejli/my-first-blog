#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from blog.models import Course, UserProfile
from blog.course_import_export import is_instructor

# Test the authentication issue
def test_export_auth_debug():
    client = Client()
    
    # Create instructor 1
    instructor1 = User.objects.create_user(
        username='instructor1',
        password='pass123'
    )
    profile1, created1 = UserProfile.objects.get_or_create(
        user=instructor1, 
        defaults={'role': 'instructor'}
    )
    profile1.role = 'instructor'
    profile1.save()
    
    # Create instructor 2
    instructor2 = User.objects.create_user(
        username='instructor2',
        password='pass123'
    )
    profile2, created2 = UserProfile.objects.get_or_create(
        user=instructor2, 
        defaults={'role': 'instructor'}
    )
    profile2.role = 'instructor'
    profile2.save()
    
    # Create a course for instructor1
    course = Course.objects.create(
        title="Test Course",
        course_code="TEST001",
        description="Test description",
        instructor=instructor1
    )
    
    print(f"Instructor1 ID: {instructor1.id}")
    print(f"Instructor1 Profile: {profile1.role}")
    print(f"Instructor1 is_instructor check: {is_instructor(instructor1)}")
    
    print(f"Instructor2 ID: {instructor2.id}")
    print(f"Instructor2 Profile: {profile2.role}")
    print(f"Instructor2 is_instructor check: {is_instructor(instructor2)}")
    
    print(f"Course ID: {course.id}")
    print(f"Course instructor ID: {course.instructor.id}")
    
    # Test access with instructor2 (should fail)
    client.force_login(instructor2)
    url = reverse('export_course', kwargs={'course_id': course.id})
    print(f"URL: {url}")
    
    response = client.get(url)
    print(f"Response status: {response.status_code}")
    if hasattr(response, 'url'):
        print(f"Redirect URL: {response.url}")

if __name__ == '__main__':
    test_export_auth_debug()