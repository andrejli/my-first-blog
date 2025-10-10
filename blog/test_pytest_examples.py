# Pytest test examples for Terminal LMS
import pytest
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from blog.models import Course, UserProfile, Enrollment, Quiz, Question, Answer, SiteTheme, UserThemePreference


@pytest.fixture
def client():
    """Django test client fixture"""
    return Client()


@pytest.fixture
def admin_user(db):
    """Create admin user for testing"""
    user = User.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='testpass123',
        is_staff=True,
        is_superuser=True
    )
    UserProfile.objects.create(user=user, role='admin')
    return user


@pytest.fixture
def instructor_user(db):
    """Create instructor user for testing"""
    user = User.objects.create_user(
        username='instructor',
        email='instructor@test.com',
        password='testpass123'
    )
    UserProfile.objects.create(user=user, role='instructor')
    return user


@pytest.fixture
def student_user(db):
    """Create student user for testing"""
    user = User.objects.create_user(
        username='student',
        email='student@test.com',
        password='testpass123'
    )
    UserProfile.objects.create(user=user, role='student')
    return user


@pytest.fixture
def course(db, instructor_user):
    """Create test course"""
    return Course.objects.create(
        title='Test Course',
        course_code='TEST101',
        description='A test course',
        instructor=instructor_user,
        status='published'
    )


@pytest.fixture
def theme(db):
    """Create test theme"""
    return SiteTheme.objects.create(
        name='test_theme',
        display_name='Test Theme',
        theme_key='test-theme',
        is_default=True,
        is_active=True
    )


class TestAuthentication:
    """Test authentication system"""
    
    @pytest.mark.auth
    def test_user_registration(self, client, db):
        """Test user registration process"""
        response = client.post('/register/', {
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'testpass123'
        })
        assert response.status_code == 302  # Redirect after successful registration
        assert User.objects.filter(username='newuser').exists()
        
        # Check UserProfile was created with student role
        user = User.objects.get(username='newuser')
        assert hasattr(user, 'userprofile')
        assert user.userprofile.role == 'student'
    
    @pytest.mark.auth
    def test_login_redirects(self, client, admin_user, instructor_user, student_user):
        """Test role-based login redirects"""
        # Test admin redirect
        response = client.post('/login/', {
            'username': 'admin',
            'password': 'testpass123'
        })
        assert response.status_code == 302
        assert '/admin/' in response.url
        
        # Test instructor redirect
        client.logout()
        response = client.post('/login/', {
            'username': 'instructor',
            'password': 'testpass123'
        })
        assert response.status_code == 302
        assert 'instructor' in response.url
        
        # Test student redirect
        client.logout()
        response = client.post('/login/', {
            'username': 'student',
            'password': 'testpass123'
        })
        assert response.status_code == 302
        assert 'student' in response.url


class TestCourseManagement:
    """Test course management functionality"""
    
    @pytest.mark.course
    def test_course_creation(self, instructor_user):
        """Test course creation by instructor"""
        course = Course.objects.create(
            title='New Course',
            course_code='NEW101',
            description='A new course',
            instructor=instructor_user,
            status='draft'
        )
        assert course.title == 'New Course'
        assert course.instructor == instructor_user
        assert course.status == 'draft'
    
    @pytest.mark.course
    def test_student_enrollment(self, client, student_user, course):
        """Test student enrollment in course"""
        client.force_login(student_user)
        response = client.post(f'/course/{course.id}/enroll/')
        
        assert response.status_code == 302
        assert Enrollment.objects.filter(
            student=student_user,
            course=course,
            status='enrolled'
        ).exists()
    
    @pytest.mark.course
    def test_course_access_permissions(self, client, student_user, instructor_user, course):
        """Test course access permissions"""
        # Unenrolled student should not access course details
        client.force_login(student_user)
        response = client.get(f'/course/{course.id}/')
        assert response.status_code == 403 or 'enroll' in response.content.decode()
        
        # Instructor should always access their course
        client.force_login(instructor_user)
        response = client.get(f'/course/{course.id}/')
        assert response.status_code == 200


class TestQuizSystem:
    """Test quiz system functionality"""
    
    @pytest.mark.quiz
    def test_quiz_creation(self, instructor_user, course):
        """Test quiz creation"""
        quiz = Quiz.objects.create(
            course=course,
            title='Test Quiz',
            description='A test quiz',
            time_limit=30,
            max_attempts=3,
            passing_score=70.0,
            is_published=True
        )
        assert quiz.title == 'Test Quiz'
        assert quiz.course == course
        assert quiz.time_limit == 30
    
    @pytest.mark.quiz
    def test_question_creation(self, instructor_user, course):
        """Test quiz question creation"""
        quiz = Quiz.objects.create(
            course=course,
            title='Test Quiz',
            description='A test quiz'
        )
        
        question = Question.objects.create(
            quiz=quiz,
            question_text='What is 2+2?',
            question_type='multiple_choice',
            points=5.0,
            order=1
        )
        
        # Create answer choices
        Answer.objects.create(
            question=question,
            answer_text='3',
            is_correct=False
        )
        Answer.objects.create(
            question=question,
            answer_text='4',
            is_correct=True
        )
        
        assert question.quiz == quiz
        assert question.answers.count() == 2
        assert question.answers.filter(is_correct=True).count() == 1


class TestThemeSystem:
    """Test theme system functionality"""
    
    @pytest.mark.theme
    def test_theme_creation(self, theme):
        """Test theme model creation"""
        assert theme.name == 'test_theme'
        assert theme.is_default is True
        assert theme.is_active is True
    
    @pytest.mark.theme
    def test_user_theme_preference(self, student_user, theme):
        """Test user theme preference creation"""
        preference = UserThemePreference.objects.create(
            user=student_user,
            theme=theme
        )
        assert preference.user == student_user
        assert preference.theme == theme
    
    @pytest.mark.theme
    def test_theme_api_endpoints(self, client, student_user, theme):
        """Test theme API endpoints"""
        client.force_login(student_user)
        
        # Test get theme endpoint
        response = client.get('/api/theme/get/')
        assert response.status_code == 200
        data = response.json()
        assert 'theme' in data
        
        # Test set theme endpoint
        response = client.post('/api/theme/set/', {
            'theme': theme.theme_key
        })
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True


class TestForumSystem:
    """Test forum system functionality"""
    
    @pytest.mark.forum
    def test_forum_access(self, client, student_user, instructor_user):
        """Test forum access permissions"""
        # Student should access general forums
        client.force_login(student_user)
        response = client.get('/forums/')
        assert response.status_code == 200
        
        # Instructor should access instructor forums
        client.force_login(instructor_user)
        response = client.get('/forums/')
        assert response.status_code == 200


@pytest.mark.integration
class TestIntegrationWorkflows:
    """Integration tests for complete workflows"""
    
    def test_complete_course_workflow(self, client, instructor_user, student_user):
        """Test complete course creation and enrollment workflow"""
        # Instructor creates course
        client.force_login(instructor_user)
        response = client.post('/instructor/course/create/', {
            'title': 'Integration Test Course',
            'course_code': 'INT101',
            'description': 'An integration test course',
            'max_students': 30,
            'status': 'published'
        })
        
        course = Course.objects.get(course_code='INT101')
        assert course.instructor == instructor_user
        
        # Student enrolls in course
        client.force_login(student_user)
        response = client.post(f'/course/{course.id}/enroll/')
        assert response.status_code == 302
        
        # Verify enrollment
        assert Enrollment.objects.filter(
            student=student_user,
            course=course
        ).exists()
    
    def test_quiz_taking_workflow(self, client, instructor_user, student_user, course):
        """Test complete quiz creation and taking workflow"""
        # Enroll student first
        Enrollment.objects.create(
            student=student_user,
            course=course,
            status='enrolled'
        )
        
        # Instructor creates quiz
        client.force_login(instructor_user)
        quiz = Quiz.objects.create(
            course=course,
            title='Integration Quiz',
            description='Test quiz',
            is_published=True
        )
        
        # Add question
        question = Question.objects.create(
            quiz=quiz,
            question_text='Test question?',
            question_type='multiple_choice',
            points=10.0
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
        
        # Student should be able to access quiz
        client.force_login(student_user)
        response = client.get(f'/course/{course.id}/quizzes/')
        assert response.status_code == 200
        assert quiz.title in response.content.decode()


# Performance tests
@pytest.mark.slow
class TestPerformance:
    """Performance-related tests"""
    
    def test_course_list_performance(self, client):
        """Test course list page performance with many courses"""
        # Create many courses
        instructor = User.objects.create_user(username='perf_instructor', password='test')
        UserProfile.objects.create(user=instructor, role='instructor')
        
        courses = []
        for i in range(50):
            courses.append(Course(
                title=f'Course {i}',
                course_code=f'PERF{i:03d}',
                description=f'Performance test course {i}',
                instructor=instructor,
                status='published'
            ))
        Course.objects.bulk_create(courses)
        
        # Test page load time
        import time
        start_time = time.time()
        response = client.get('/')
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Should load in under 2 seconds