"""
Test Views for Django LMS

This module contains comprehensive tests for all LMS views including:
- Authentication views (login, logout, register)
- Course views (list, detail, enrollment)
- Lesson views (detail, progress tracking)
- Assignment views (list, submit, grade)
- Quiz views (create, take, results)
- Dashboard views (student, instructor)
"""

import pytest
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from blog.models import (
    UserProfile, Course, Enrollment, Lesson, Assignment, 
    Submission, Quiz, Question, Answer, QuizAttempt, QuizResponse
)


# ================================
# AUTHENTICATION VIEW TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.views
@pytest.mark.auth
class TestAuthenticationViews:
    """Test cases for authentication views"""
    
    def test_user_registration_get(self, client):
        """Test GET request to registration page"""
        response = client.get(reverse('register'))
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_user_registration_post_success(self, client):
        """Test successful user registration"""
        user_data = {
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        
        response = client.post(reverse('register'), data=user_data)
        
        # Should redirect to student dashboard
        assert response.status_code == 302
        assert response.url == reverse('student_dashboard')
        
        # User should be created
        user = User.objects.get(username='newuser')
        assert user.is_authenticated
        
        # UserProfile should be created
        profile = UserProfile.objects.get(user=user)
        assert profile.role == 'student'
    
    def test_user_registration_post_invalid(self, client):
        """Test invalid user registration"""
        user_data = {
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'differentpass'  # Passwords don't match
        }
        
        response = client.post(reverse('register'), data=user_data)
        
        # Should stay on registration page
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors
    
    def test_user_login_get(self, client):
        """Test GET request to login page"""
        response = client.get(reverse('login'))
        assert response.status_code == 200
    
    def test_user_login_post_success(self, client):
        """Test successful user login"""
        user = User.objects.create_user(username='testuser', password='testpass123')
        UserProfile.objects.get_or_create(user=user, defaults={'role': 'student'})
        
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = client.post(reverse('login'), data=login_data)
        
        # Should redirect to student dashboard
        assert response.status_code == 302
        assert response.url == reverse('student_dashboard')
    
    def test_user_login_post_invalid(self, client):
        """Test invalid user login"""
        login_data = {
            'username': 'nonexistent',
            'password': 'wrongpass'
        }
        
        response = client.post(reverse('login'), data=login_data)
        
        # Should stay on login page
        assert response.status_code == 200
    
    def test_user_logout(self, authenticated_client):
        """Test user logout"""
        response = authenticated_client.get(reverse('logout'))
        
        # Should redirect to course list
        assert response.status_code == 302
        assert response.url == reverse('course_list')


# ================================
# COURSE VIEW TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.views
@pytest.mark.course
class TestCourseViews:
    """Test cases for course views"""
    
    def test_course_list_view(self, client):
        """Test course list view"""
        instructor = User.objects.create_user(username='prof')
        
        # Create published and draft courses
        published_course = Course.objects.create(
            title='Published Course',
            course_code='PUB101',
            description='Published course description',
            instructor=instructor,
            status='published'
        )
        
        draft_course = Course.objects.create(
            title='Draft Course',
            course_code='DRA101',
            description='Draft course description',
            instructor=instructor,
            status='draft'
        )
        
        response = client.get(reverse('course_list'))
        
        assert response.status_code == 200
        assert published_course in response.context['courses']
        assert draft_course not in response.context['courses']  # Draft courses not shown
    
    def test_course_detail_view_published(self, client):
        """Test course detail view for published course"""
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor,
            status='published'
        )
        
        response = client.get(reverse('course_detail', kwargs={'course_id': course.id}))
        
        assert response.status_code == 200
        assert response.context['course'] == course
        assert response.context['is_enrolled'] is False  # Anonymous user not enrolled
    
    def test_course_detail_view_draft_as_instructor(self, client):
        """Test course detail view for draft course as instructor"""
        instructor = User.objects.create_user(username='prof', password='testpass')
        profile, created = UserProfile.objects.get_or_create(user=instructor, defaults={'role': 'instructor'})
        profile.role = 'instructor'
        profile.save()
        course = Course.objects.create(
            title='Draft Course',
            course_code='DRA101',
            description='Draft description',
            instructor=instructor,
            status='draft'
        )
        
        client.login(username='prof', password='testpass')
        response = client.get(reverse('course_detail', kwargs={'course_id': course.id}))
        
        assert response.status_code == 200
        assert response.context['course'] == course
    
    def test_course_detail_view_draft_as_other_user(self, client):
        """Test course detail view for draft course as non-instructor"""
        instructor = User.objects.create_user(username='prof')
        other_user = User.objects.create_user(username='student', password='testpass')
        UserProfile.objects.get_or_create(user=other_user, defaults={'role': 'student'})
        
        course = Course.objects.create(
            title='Draft Course',
            course_code='DRA101',
            description='Draft description',
            instructor=instructor,
            status='draft'
        )
        
        client.login(username='student', password='testpass')
        response = client.get(reverse('course_detail', kwargs={'course_id': course.id}))
        
        # Should get 404 for draft course
        assert response.status_code == 404
    
    def test_course_detail_with_enrollment(self, client):
        """Test course detail view with enrolled student"""
        instructor = User.objects.create_user(username='prof')
        student = User.objects.create_user(username='student', password='testpass')
        UserProfile.objects.get_or_create(user=student, defaults={'role': 'student'})
        
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor,
            status='published'
        )
        
        # Enroll student
        Enrollment.objects.create(student=student, course=course, status='enrolled')
        
        client.login(username='student', password='testpass')
        response = client.get(reverse('course_detail', kwargs={'course_id': course.id}))
        
        assert response.status_code == 200
        assert response.context['is_enrolled'] is True


# ================================
# LESSON VIEW TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.views
class TestLessonViews:
    """Test cases for lesson views"""
    
    def test_lesson_detail_view_authenticated(self, client):
        """Test lesson detail view for authenticated user"""
        instructor = User.objects.create_user(username='prof')
        student = User.objects.create_user(username='student', password='testpass')
        UserProfile.objects.get_or_create(user=student, defaults={'role': 'student'})
        
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor,
            status='published'
        )
        
        lesson = Lesson.objects.create(
            course=course,
            title='Test Lesson',
            content='Lesson content',
            order=1,
            is_published=True
        )
        
        # Enroll student
        Enrollment.objects.create(student=student, course=course, status='enrolled')
        
        client.login(username='student', password='testpass')
        response = client.get(reverse('lesson_detail', kwargs={'course_id': course.id, 'lesson_id': lesson.id}))
        
        assert response.status_code == 200
        assert response.context['lesson'] == lesson
    
    def test_lesson_detail_view_unauthenticated(self, client):
        """Test lesson detail view for unauthenticated user"""
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        lesson = Lesson.objects.create(
            course=course,
            title='Test Lesson',
            content='Lesson content',
            order=1,
            is_published=True
        )
        
        response = client.get(reverse('lesson_detail', kwargs={'course_id': course.id, 'lesson_id': lesson.id}))
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/login/' in response.url
    
    def test_lesson_detail_not_enrolled(self, client):
        """Test lesson detail view for non-enrolled student"""
        instructor = User.objects.create_user(username='prof')
        student = User.objects.create_user(username='student', password='testpass')
        UserProfile.objects.get_or_create(user=student, defaults={'role': 'student'})
        
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        lesson = Lesson.objects.create(
            course=course,
            title='Test Lesson',
            content='Lesson content',
            order=1,
            is_published=True
        )
        
        client.login(username='student', password='testpass')
        response = client.get(reverse('lesson_detail', kwargs={'course_id': course.id, 'lesson_id': lesson.id}))
        
        # Should redirect to course detail with message
        assert response.status_code == 302


# ================================
# ASSIGNMENT VIEW TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.views
@pytest.mark.assignment
class TestAssignmentViews:
    """Test cases for assignment views"""
    
    def test_assignment_detail_view(self, client):
        """Test assignment detail view"""
        instructor = User.objects.create_user(username='prof')
        student = User.objects.create_user(username='student', password='testpass')
        UserProfile.objects.get_or_create(user=student, defaults={'role': 'student'})
        
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor,
            status='published'
        )
        
        assignment = Assignment.objects.create(
            course=course,
            title='Test Assignment',
            description='Assignment description',
            due_date=timezone.now() + timedelta(days=7),
            max_points=100,
            is_published=True
        )
        
        # Enroll student
        Enrollment.objects.create(student=student, course=course, status='enrolled')
        
        client.login(username='student', password='testpass')
        response = client.get(reverse('assignment_detail', kwargs={'assignment_id': assignment.id}))
        
        assert response.status_code == 200
        assert response.context['assignment'] == assignment
    
    def test_submit_assignment_get(self, client):
        """Test GET request to submit assignment"""
        instructor = User.objects.create_user(username='prof')
        student = User.objects.create_user(username='student', password='testpass')
        UserProfile.objects.get_or_create(user=student, defaults={'role': 'student'})
        
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        assignment = Assignment.objects.create(
            course=course,
            title='Test Assignment',
            description='Assignment description',
            due_date=timezone.now() + timedelta(days=7),
            is_published=True
        )
        
        # Enroll student
        Enrollment.objects.create(student=student, course=course, status='enrolled')
        
        client.login(username='student', password='testpass')
        response = client.get(reverse('submit_assignment', kwargs={'assignment_id': assignment.id}))
        
        assert response.status_code == 200
        assert response.context['assignment'] == assignment
    
    def test_submit_assignment_post(self, client):
        """Test POST request to submit assignment"""
        instructor = User.objects.create_user(username='prof')
        student = User.objects.create_user(username='student', password='testpass')
        UserProfile.objects.get_or_create(user=student, defaults={'role': 'student'})
        
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        assignment = Assignment.objects.create(
            course=course,
            title='Test Assignment',
            description='Assignment description',
            due_date=timezone.now() + timedelta(days=7),
            is_published=True
        )
        
        # Enroll student
        Enrollment.objects.create(student=student, course=course, status='enrolled')
        
        client.login(username='student', password='testpass')
        
        submission_data = {
            'content': 'This is my assignment submission',
            'submit_type': 'submit'  # Actually submit it
        }
        
        response = client.post(
            reverse('submit_assignment', kwargs={'assignment_id': assignment.id}),
            data=submission_data
        )
        
        # Should redirect after successful submission
        assert response.status_code == 302
        
        # Submission should be created
        submission = Submission.objects.get(assignment=assignment, student=student)
        assert submission.text_submission == 'This is my assignment submission'
        assert submission.status == 'submitted'


# ================================
# QUIZ VIEW TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.views
@pytest.mark.quiz
class TestQuizViews:
    """Test cases for quiz views"""
    
    def test_quiz_list_for_students(self, client):
        """Test quiz list view for students"""
        instructor = User.objects.create_user(username='prof')
        student = User.objects.create_user(username='student', password='testpass')
        UserProfile.objects.get_or_create(user=student, defaults={'role': 'student'})
        
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor,
            status='published'
        )
        
        # Create published and unpublished quizzes
        published_quiz = Quiz.objects.create(
            course=course,
            title='Published Quiz',
            is_published=True
        )
        
        unpublished_quiz = Quiz.objects.create(
            course=course,
            title='Unpublished Quiz',
            is_published=False
        )
        
        # Enroll student
        Enrollment.objects.create(student=student, course=course, status='enrolled')
        
        client.login(username='student', password='testpass')
        response = client.get(reverse('student_quiz_list', kwargs={'course_id': course.id}))
        
        assert response.status_code == 200
        assert published_quiz in response.context['quizzes']
        assert unpublished_quiz not in response.context['quizzes']
    
    def test_start_quiz(self, client):
        """Test starting a quiz"""
        instructor = User.objects.create_user(username='prof')
        student = User.objects.create_user(username='student', password='testpass')
        UserProfile.objects.get_or_create(user=student, defaults={'role': 'student'})
        
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        quiz = Quiz.objects.create(
            course=course,
            title='Test Quiz',
            max_attempts=3,
            is_published=True
        )
        
        # Enroll student
        Enrollment.objects.create(student=student, course=course, status='enrolled')
        
        client.login(username='student', password='testpass')
        response = client.post(reverse('start_quiz', kwargs={'quiz_id': quiz.id}))
        
        # Should redirect to take quiz
        assert response.status_code == 302
        
        # Quiz attempt should be created
        attempt = QuizAttempt.objects.get(student=student, quiz=quiz)
        assert attempt.status == 'in_progress'
        assert attempt.attempt_number == 1
    
    def test_start_quiz_max_attempts_reached(self, client):
        """Test starting quiz when max attempts reached"""
        instructor = User.objects.create_user(username='prof')
        student = User.objects.create_user(username='student', password='testpass')
        UserProfile.objects.get_or_create(user=student, defaults={'role': 'student'})
        
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        quiz = Quiz.objects.create(
            course=course,
            title='Test Quiz',
            max_attempts=1,  # Only 1 attempt allowed
            is_published=True
        )
        
        # Enroll student
        Enrollment.objects.create(student=student, course=course, status='enrolled')
        
        # Create a completed attempt
        QuizAttempt.objects.create(
            student=student,
            quiz=quiz,
            attempt_number=1,
            status='completed'
        )
        
        client.login(username='student', password='testpass')
        response = client.post(reverse('start_quiz', kwargs={'quiz_id': quiz.id}))
        
        # Should redirect back to quiz list with error message
        assert response.status_code == 302


# ================================
# DASHBOARD VIEW TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.views
class TestDashboardViews:
    """Test cases for dashboard views"""
    
    def test_student_dashboard(self, client):
        """Test student dashboard view"""
        student = User.objects.create_user(username='student_dashboard', password='testpass')
        UserProfile.objects.get_or_create(user=student, defaults={'role': 'student'})
        
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor,
            status='published'
        )
        
        # Enroll student
        Enrollment.objects.create(student=student, course=course, status='enrolled')
        
        client.login(username='student_dashboard', password='testpass')
        response = client.get(reverse('student_dashboard'))
        
        assert response.status_code == 200
        assert 'course_progress' in response.context
        assert len(response.context['course_progress']) == 1
    
    def test_instructor_dashboard(self, client):
        """Test instructor dashboard view"""
        instructor = User.objects.create_user(username='prof_dashboard', password='testpass')
        profile, created = UserProfile.objects.get_or_create(user=instructor, defaults={'role': 'instructor'})
        if not created:
            profile.role = 'instructor'
            profile.save()
        
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        client.login(username='prof_dashboard', password='testpass')
        response = client.get(reverse('instructor_dashboard'))
        
        assert response.status_code == 200
        assert 'course_stats' in response.context
        # The course should be in the first course_stats entry
        assert len(response.context['course_stats']) == 1
        assert response.context['course_stats'][0]['course'] == course
    
    def test_student_dashboard_no_profile(self, client):
        """Test student dashboard redirect when no profile exists"""
        student = User.objects.create_user(username='student_no_profile', password='testpass')
        # Delete the automatically created profile to test no profile scenario
        UserProfile.objects.filter(user=student).delete()
        
        client.login(username='student_no_profile', password='testpass')
        response = client.get(reverse('student_dashboard'))
        
        # Should redirect to course list with warning
        assert response.status_code == 302
        assert response.url == reverse('course_list')


# ================================
# ENROLLMENT VIEW TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.views
class TestEnrollmentViews:
    """Test cases for enrollment views"""
    
    def test_enroll_in_course(self, client):
        """Test enrolling in a course"""
        student = User.objects.create_user(username='student_enroll', password='testpass')
        UserProfile.objects.get_or_create(user=student, defaults={'role': 'student'})
        
        instructor = User.objects.create_user(username='prof_enroll')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor,
            status='published'
        )
        
        client.login(username='student_enroll', password='testpass')
        response = client.post(reverse('enroll_course', kwargs={'course_id': course.id}))
        
        # Should redirect to course detail
        assert response.status_code == 302
        assert response.url == reverse('course_detail', kwargs={'course_id': course.id})
        
        # Enrollment should be created
        enrollment = Enrollment.objects.get(student=student, course=course)
        assert enrollment.status == 'enrolled'
    
    def test_enroll_already_enrolled(self, client):
        """Test enrolling when already enrolled"""
        student = User.objects.create_user(username='student_already', password='testpass')
        UserProfile.objects.get_or_create(user=student, defaults={'role': 'student'})
        
        instructor = User.objects.create_user(username='prof_already')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor,
            status='published'
        )
        
        # Pre-enroll student
        Enrollment.objects.create(student=student, course=course, status='enrolled')
        
        client.login(username='student', password='testpass')
        response = client.post(reverse('enroll_course', kwargs={'course_id': course.id}))
        
        # Should redirect with message
        assert response.status_code == 302
        
        # Should still only have one enrollment
        assert Enrollment.objects.filter(student=student, course=course).count() == 1
    
    def test_drop_course(self, client):
        """Test dropping from a course"""
        student = User.objects.create_user(username='student_drop', password='testpass')
        UserProfile.objects.get_or_create(user=student, defaults={'role': 'student'})
        
        instructor = User.objects.create_user(username='prof_drop')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor,
            status='published'
        )
        
        # Enroll student first
        Enrollment.objects.create(student=student, course=course, status='enrolled')
        
        client.login(username='student_drop', password='testpass')
        response = client.post(reverse('drop_course', kwargs={'course_id': course.id}))
        
        # Should redirect to course detail
        assert response.status_code == 302
        assert response.url == reverse('course_detail', kwargs={'course_id': course.id})
        
        # Enrollment status should change to dropped
        enrollment = Enrollment.objects.get(student=student, course=course)
        assert enrollment.status == 'dropped'
