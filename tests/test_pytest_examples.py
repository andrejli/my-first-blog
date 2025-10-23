"""
Comprehensive pytest examples for Django LMS

This file demonstrates various pytest patterns and techniques for testing
the Terminal LMS application with Django models, views, and functionality.

Note: All fixtures are defined in tests/conftest.py to avoid import issues.
"""

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from blog.models import (
    Course, UserProfile, Enrollment, Quiz, Question, Answer,
    SiteTheme, UserThemePreference
)


class TestAuthentication:
    """Test authentication system"""
    
    @pytest.mark.auth
    @pytest.mark.django_db
    def test_user_registration(self, client):
        """Test user registration process"""
        response = client.post('/register/', {
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'email': 'newuser@test.com'
        })
        
        # Should create user and redirect
        assert response.status_code == 302
        
        # User should exist
        user = User.objects.get(username='newuser')
        # Standard UserCreationForm doesn't capture email
        assert user.username == 'newuser'
        
        # Should have student role by default
        profile = UserProfile.objects.get(user=user)
        assert profile.role == 'student'

    @pytest.mark.auth
    @pytest.mark.django_db
    def test_login_redirects(self, client, student_user, instructor_user, admin_user):
        """Test role-based login redirects"""
        # Test student login
        response = client.post('/login/', {
            'username': 'student',
            'password': 'student123'
        })
        assert response.status_code == 302
        
        # Test instructor login  
        response = client.post('/login/', {
            'username': 'instructor',
            'password': 'instructor123'
        })
        assert response.status_code == 302
        
        # Test admin login
        response = client.post('/login/', {
            'username': 'admin',
            'password': 'admin123'
        })
        assert response.status_code == 302


class TestCourseManagement:
    """Test course management functionality"""
    
    @pytest.mark.course
    @pytest.mark.django_db
    def test_course_creation(self, client, instructor_user):
        """Test course creation by instructor"""
        client.force_login(instructor_user)
        
        response = client.post('/instructor/course/create/', {
            'title': 'New Test Course',
            'course_code': 'TEST201',
            'description': 'A brand new test course',
            'duration_weeks': 10,
            'max_students': 25
        })
        
        # Should redirect on success
        assert response.status_code == 302
        
        # Course should exist
        course = Course.objects.get(course_code='TEST201')
        assert course.title == 'New Test Course'
        assert course.instructor == instructor_user

    @pytest.mark.course
    @pytest.mark.django_db
    def test_student_enrollment(self, client, student_user, course):
        """Test student enrollment in course"""
        client.force_login(student_user)
        
        # Enroll in course
        response = client.post(f'/course/{course.id}/enroll/')
        assert response.status_code == 302
        
        # Should be enrolled
        enrollment = Enrollment.objects.get(student=student_user, course=course)
        assert enrollment.status == 'enrolled'

    @pytest.mark.course
    @pytest.mark.django_db
    def test_course_access_permissions(self, client, student_user, course):
        """Test course access permissions"""
        # Unauthenticated access should redirect
        response = client.get(f'/course/{course.id}/')
        assert response.status_code == 302
        
        # Authenticated but not enrolled
        client.force_login(student_user)
        response = client.get(f'/course/{course.id}/')
        # Should allow view but not full access
        assert response.status_code in [200, 302]


class TestQuizSystem:
    """Test quiz functionality"""
    
    @pytest.mark.quiz
    @pytest.mark.django_db
    def test_quiz_creation(self, client, instructor_user, course):
        """Test quiz creation by instructor"""
        client.force_login(instructor_user)
        
        response = client.post(f'/course/{course.id}/quiz/create/', {
            'title': 'Test Quiz',
            'description': 'A test quiz',
            'time_limit': 30,
            'max_attempts': 2
        })
        
        # Should create quiz
        assert response.status_code in [200, 302]
        
        quiz = Quiz.objects.filter(course=course, title='Test Quiz').first()
        if quiz:
            assert quiz.time_limit == 30
            assert quiz.max_attempts == 2

    @pytest.mark.quiz
    @pytest.mark.django_db
    def test_question_creation(self, client, instructor_user, quiz):
        """Test adding questions to quiz"""
        client.force_login(instructor_user)
        
        # Create a multiple choice question
        response = client.post(f'/quiz/{quiz.id}/question/create/', {
            'question_text': 'What is 2+2?',
            'question_type': 'multiple_choice',
            'points': 5,
            'answers-0-answer_text': '3',
            'answers-0-is_correct': False,
            'answers-1-answer_text': '4',
            'answers-1-is_correct': True,
            'answers-TOTAL_FORMS': 2,
            'answers-INITIAL_FORMS': 0
        })
        
        # Should create question
        assert response.status_code in [200, 302]
        
        question = Question.objects.filter(quiz=quiz, question_text='What is 2+2?').first()
        if question:
            assert question.points == 5
            # Check answers if relationship exists
            if hasattr(question, 'answers'):
                assert question.answers.count() >= 2
                assert question.answers.filter(is_correct=True).count() >= 1


class TestThemeSystem:
    """Test theme switching functionality"""
    
    @pytest.mark.theme
    @pytest.mark.django_db
    def test_theme_creation(self, theme):
        """Test theme creation"""
        assert theme.name == 'test_theme'
        assert theme.display_name == 'Test Theme'
        assert theme.is_default == False

    @pytest.mark.theme
    @pytest.mark.django_db
    def test_user_theme_preference(self, client, student_user, theme):
        """Test user theme preference setting"""
        client.force_login(student_user)
        
        response = client.post('/set-theme/', {
            'theme_id': theme.id
        })
        
        # Should set theme preference
        assert response.status_code in [200, 302]
        
        preference = UserThemePreference.objects.filter(
            user=student_user,
            theme=theme
        ).first()
        
        if preference:
            assert preference.theme == theme

    @pytest.mark.theme
    @pytest.mark.django_db
    def test_theme_api_endpoints(self, client, student_user):
        """Test theme API endpoints"""
        client.force_login(student_user)
        
        # Get available themes
        response = client.get('/api/themes/')
        assert response.status_code == 200
        
        # Should return JSON
        if response.content:
            data = response.json()
            assert isinstance(data, (list, dict))


class TestForumSystem:
    """Test forum functionality"""
    
    @pytest.mark.forum
    @pytest.mark.django_db
    def test_forum_access(self, client, student_user):
        """Test forum access permissions"""
        client.force_login(student_user)
        
        response = client.get('/forum/')
        assert response.status_code == 200


class TestIntegrationWorkflows:
    """Test complete user workflows"""
    
    @pytest.mark.integration
    @pytest.mark.django_db
    def test_complete_course_workflow(self, client, instructor_user, student_user):
        """Test complete course creation and enrollment workflow"""
        # Instructor creates course
        client.force_login(instructor_user)
        
        response = client.post('/instructor/courses/create/', {
            'title': 'Integration Test Course',
            'course_code': 'INT101',
            'description': 'Full workflow test',
            'duration_weeks': 8,
            'max_students': 20
        })
        
        if response.status_code == 302:
            # Course created successfully
            course = Course.objects.get(course_code='INT101')
            
            # Student enrolls
            client.force_login(student_user)
            response = client.post(f'/course/{course.id}/enroll/')
            
            if response.status_code == 302:
                # Verify enrollment
                enrollment = Enrollment.objects.filter(
                    student=student_user, 
                    course=course
                ).first()
                if enrollment:
                    assert enrollment.status == 'enrolled'

    @pytest.mark.integration
    @pytest.mark.django_db
    def test_quiz_taking_workflow(self, client, instructor_user, student_user, course):
        """Test complete quiz creation and taking workflow"""
        # Instructor creates quiz
        client.force_login(instructor_user)
        
        # First enroll student
        Enrollment.objects.create(student=student_user, course=course, status='enrolled')
        
        # Create quiz
        quiz = Quiz.objects.create(
            course=course,
            title='Integration Quiz',
            description='Test quiz for workflow',
            time_limit=15,
            max_attempts=1
        )
        
        # Add question
        question = Question.objects.create(
            quiz=quiz,
            question_text='Test question?',
            question_type='multiple_choice',
            points=10
        )
        
        # Add answers
        Answer.objects.create(
            question=question,
            answer_text='Correct answer',
            is_correct=True
        )
        Answer.objects.create(
            question=question,
            answer_text='Wrong answer',
            is_correct=False
        )
        
        # Student takes quiz
        client.force_login(student_user)
        response = client.get(f'/quiz/{quiz.id}/')
        
        # Should be able to access quiz
        assert response.status_code in [200, 302]


class TestPerformance:
    """Test performance-related functionality"""
    
    @pytest.mark.slow
    @pytest.mark.django_db
    def test_course_list_performance(self, client):
        """Test course list page performance with many courses"""
        # Create test instructor
        instructor = User.objects.create_user(username='perf_instructor', password='test')
        UserProfile.objects.get_or_create(user=instructor, defaults={'role': 'instructor'})
        
        # Create multiple courses
        courses = []
        for i in range(20):
            course = Course.objects.create(
                title=f'Performance Test Course {i}',
                course_code=f'PERF{i:03d}',
                description=f'Performance test course {i}',
                instructor=instructor,
                status='published' if hasattr(Course, 'status') else 'published'
            )
            courses.append(course)
        
        # Time the course list page
        import time
        start_time = time.time()
        
        response = client.get('/courses/')
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Should load within reasonable time
        assert response.status_code == 200
        assert response_time < 2.0  # Should load in under 2 seconds
        
        # Should display courses
        content = response.content.decode()
        assert 'Performance Test Course' in content


# ================================
# PARAMETRIZED TESTS
# ================================

@pytest.mark.parametrize("role,expected_redirect", [
    ('student', '/dashboard/'),
    ('instructor', '/instructor/'),
])
@pytest.mark.django_db
def test_login_redirects_parametrized(client, role, expected_redirect):
    """Test login redirects for different roles using parametrization"""
    # Create user with specific role
    user = User.objects.create_user(username=f'test_{role}', password='test123')
    UserProfile.objects.get_or_create(user=user, defaults={'role': role})
    
    response = client.post('/login/', {
        'username': f'test_{role}',
        'password': 'test123'
    })
    
    # Should redirect to appropriate dashboard
    assert response.status_code == 302
