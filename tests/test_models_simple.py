"""
Test Models for Django LMS

Simple test module to verify our models work correctly.
"""

import pytest
from django.contrib.auth.models import User
from blog.models import UserProfile, Course


@pytest.mark.django_db
class TestUserProfileModel:
    """Test cases for UserProfile model"""
    
    def test_create_user_profile(self):
        """Test creating a user profile using factories"""
        # Create a user with unique username
        import uuid
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        user = User.objects.create_user(username=username, email=f'{username}@example.com')
        
        # The signal should have automatically created a profile
        profile = UserProfile.objects.get(user=user)
        
        assert profile.user == user
        assert profile.role == 'student'  # Default role
        assert str(profile) == f"{user.username} - {profile.role}"
        
        # Test updating the role
        profile.role = 'instructor'
        profile.save()
        
        assert profile.role == 'instructor'
    
    def test_user_profile_roles(self):
        """Test different user roles"""
        import uuid
        
        # Create users with unique usernames
        user1 = User.objects.create_user(username=f'student_{uuid.uuid4().hex[:8]}')
        user2 = User.objects.create_user(username=f'instructor_{uuid.uuid4().hex[:8]}')
        user3 = User.objects.create_user(username=f'admin_{uuid.uuid4().hex[:8]}')
        
        # Signals automatically create profiles, so let's update them
        profile1 = UserProfile.objects.get(user=user1)
        profile1.role = 'student'
        profile1.save()
        
        profile2 = UserProfile.objects.get(user=user2)
        profile2.role = 'instructor'
        profile2.save()
        
        profile3 = UserProfile.objects.get(user=user3)
        profile3.role = 'admin'
        profile3.save()
        
        assert profile1.role == 'student'
        assert profile2.role == 'instructor'
        assert profile3.role == 'admin'


@pytest.mark.django_db
class TestCourseModel:
    """Test cases for Course model"""
    
    def test_create_course(self):
        """Test creating a course"""
        import uuid
        instructor = User.objects.create_user(username=f'prof_{uuid.uuid4().hex[:8]}')
        
        course = Course.objects.create(
            title='Test Course',
            course_code=f'CS{uuid.uuid4().hex[:3].upper()}',
            description='A test course',
            instructor=instructor
        )
        
        assert course.title == 'Test Course'
        assert course.instructor == instructor
        assert course.status == 'draft'  # Default status
        assert str(course) == f'{course.course_code} - {course.title}'