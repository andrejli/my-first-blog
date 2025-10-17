"""
Test Configuration and Fixtures

This module provides additional test configurations, custom fixtures,
and utility functions for the Django LMS test suite.
"""

import pytest
from django.test import Client
from django.contrib.auth.models import User
from blog.models import UserProfile


# ================================
# CUSTOM FIXTURES
# ================================

@pytest.fixture
def authenticated_client():
    """Fixture providing a client with authenticated student user"""
    client = Client()
    user = User.objects.create_user(username='testuser', password='testpass123')
    UserProfile.objects.get_or_create(user=user, defaults={'role': 'student'})
    client.login(username='testuser', password='testpass123')
    return client


@pytest.fixture
def instructor_client():
    """Fixture providing a client with authenticated instructor user"""
    client = Client()
    user = User.objects.create_user(username='instructor', password='instrpass123')
    UserProfile.objects.get_or_create(user=user, defaults={'role': 'instructor'})
    client.login(username='instructor', password='instrpass123')
    return client


@pytest.fixture
def admin_client():
    """Fixture providing a client with authenticated admin user"""
    client = Client()
    user = User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='adminpass123'
    )
    UserProfile.objects.get_or_create(user=user, defaults={'role': 'admin'})
    client.login(username='admin', password='adminpass123')
    return client


# ================================
# TEST UTILITIES
# ================================

def create_test_course_with_content(instructor):
    """
    Utility function to create a course with lessons, assignments, and quizzes
    for testing purposes.
    """
    from blog.models import Course, Lesson, Assignment, Quiz, Question, Answer
    from django.utils import timezone
    from datetime import timedelta
    
    course = Course.objects.create(
        title='Test Course with Content',
        course_code='TEST101',
        description='A course for testing purposes',
        instructor=instructor,
        status='published'
    )
    
    # Add lessons
    lesson1 = Lesson.objects.create(
        course=course,
        title='Introduction',
        content='Welcome to the course',
        order=1,
        is_published=True
    )
    
    lesson2 = Lesson.objects.create(
        course=course,
        title='Basic Concepts',
        content='Learn the fundamentals',
        order=2,
        is_published=True
    )
    
    # Add assignment
    assignment = Assignment.objects.create(
        course=course,
        title='Practice Assignment',
        description='Complete this assignment for practice',
        due_date=timezone.now() + timedelta(days=7),
        max_points=100,
        is_published=True
    )
    
    # Add quiz with questions
    quiz = Quiz.objects.create(
        course=course,
        title='Knowledge Check',
        description='Test your understanding',
        max_attempts=2,
        is_published=True
    )
    
    question1 = Question.objects.create(
        quiz=quiz,
        text='What is the main topic of this course?',
        question_type='multiple_choice',
        points=10,
        order=1
    )
    
    Answer.objects.create(question=question1, answer_text='Testing', is_correct=True)
    Answer.objects.create(question=question1, answer_text='Cooking', is_correct=False)
    Answer.objects.create(question=question1, answer_text='Sports', is_correct=False)
    
    question2 = Question.objects.create(
        quiz=quiz,
        text='This is a practice course',
        question_type='true_false',
        points=5,
        order=2
    )
    
    Answer.objects.create(question=question2, answer_text='True', is_correct=True)
    Answer.objects.create(question=question2, answer_text='False', is_correct=False)
    
    return {
        'course': course,
        'lessons': [lesson1, lesson2],
        'assignment': assignment,
        'quiz': quiz,
        'questions': [question1, question2]
    }


def enroll_student_in_course(student, course):
    """Utility function to enroll a student in a course"""
    from blog.models import Enrollment
    
    enrollment, created = Enrollment.objects.get_or_create(
        student=student,
        course=course,
        defaults={'status': 'enrolled'}
    )
    return enrollment


def submit_quiz_attempt(student, quiz, answers_dict):
    """
    Utility function to submit a quiz attempt with specified answers
    
    Args:
        student: User object
        quiz: Quiz object
        answers_dict: Dict mapping question_id to answer_id
    
    Returns:
        QuizAttempt object
    """
    from blog.models import QuizAttempt, QuizResponse, Question, Answer
    
    # Create quiz attempt
    attempt = QuizAttempt.objects.create(
        student=student,
        quiz=quiz,
        attempt_number=QuizAttempt.objects.filter(student=student, quiz=quiz).count() + 1,
        status='in_progress'
    )
    
    # Submit responses
    total_score = 0
    for question_id, answer_id in answers_dict.items():
        question = Question.objects.get(id=question_id)
        answer = Answer.objects.get(id=answer_id)
        
        response = QuizResponse.objects.create(
            attempt=attempt,
            question=question,
            selected_answer=answer,
            is_correct=answer.is_correct
        )
        
        if response.is_correct:
            total_score += question.points
    
    # Complete the attempt
    attempt.status = 'completed'
    attempt.score = total_score
    attempt.save()
    
    return attempt


# ================================
# TEST DATA VALIDATORS
# ================================

def validate_course_structure(course):
    """Validate that a course has proper structure"""
    assert course.title
    assert course.course_code
    assert course.instructor
    assert course.status in ['draft', 'published', 'archived']


def validate_quiz_structure(quiz):
    """Validate that a quiz has proper structure"""
    assert quiz.title
    assert quiz.course
    assert quiz.max_attempts >= 1
    
    questions = quiz.questions.all()
    assert questions.count() > 0
    
    for question in questions:
        answers = question.answers.all()
        assert answers.count() >= 2  # At least 2 choices
        assert answers.filter(is_correct=True).count() >= 1  # At least 1 correct


def validate_user_profile(user):
    """Validate that a user has proper profile setup"""
    assert hasattr(user, 'userprofile')
    profile = user.userprofile
    assert profile.role in ['student', 'instructor', 'admin']


# ================================
# PERFORMANCE TEST HELPERS
# ================================

def create_large_dataset(num_courses=10, num_students=50, num_instructors=5):
    """
    Create a large dataset for performance testing
    
    Returns:
        dict: Contains created objects for reference
    """
    from django.contrib.auth.models import User
    from blog.models import UserProfile, Course, Enrollment
    
    # Create instructors
    instructors = []
    for i in range(num_instructors):
        user = User.objects.create_user(
            username=f'instructor_{i}',
            email=f'instructor_{i}@test.com',
            password='testpass123'
        )
        UserProfile.objects.get_or_create(user=user, defaults={'role': 'instructor'})
        instructors.append(user)
    
    # Create students
    students = []
    for i in range(num_students):
        user = User.objects.create_user(
            username=f'student_{i}',
            email=f'student_{i}@test.com',
            password='testpass123'
        )
        UserProfile.objects.get_or_create(user=user, defaults={'role': 'student'})
        students.append(user)
    
    # Create courses
    courses = []
    for i in range(num_courses):
        instructor = instructors[i % num_instructors]
        course = Course.objects.create(
            title=f'Course {i}',
            course_code=f'C{i:03d}',
            description=f'Description for course {i}',
            instructor=instructor,
            status='published'
        )
        courses.append(course)
        
        # Enroll random students (about 30% of students per course)
        import random
        enrolled_students = random.sample(students, k=int(num_students * 0.3))
        for student in enrolled_students:
            Enrollment.objects.create(
                student=student,
                course=course,
                status='enrolled'
            )
    
    return {
        'instructors': instructors,
        'students': students,
        'courses': courses
    }


# ================================
# MOCK DATA GENERATORS
# ================================

def generate_quiz_responses(attempt, score_percentage=0.8):
    """
    Generate quiz responses for an attempt with target score percentage
    
    Args:
        attempt: QuizAttempt object
        score_percentage: Target percentage of correct answers (0.0 to 1.0)
    """
    from blog.models import QuizResponse
    import random
    
    questions = attempt.quiz.questions.all().order_by('order')
    total_questions = questions.count()
    target_correct = int(total_questions * score_percentage)
    
    # Randomly select which questions to answer correctly
    correct_indices = random.sample(range(total_questions), target_correct)
    
    total_score = 0
    for i, question in enumerate(questions):
        is_correct = i in correct_indices
        
        if is_correct:
            answer = question.answers.filter(is_correct=True).first()
            total_score += question.points
        else:
            answer = question.answers.filter(is_correct=False).first()
        
        QuizResponse.objects.create(
            attempt=attempt,
            question=question,
            selected_answer=answer,
            is_correct=is_correct
        )
    
    attempt.score = total_score
    attempt.status = 'completed'
    attempt.save()
    
    return attempt


# ================================
# TEST MARKERS AND CATEGORIES
# ================================

# Performance test thresholds
PERFORMANCE_THRESHOLDS = {
    'page_load_max': 2.0,  # seconds
    'database_query_max': 100,  # number of queries
    'memory_usage_max': 50 * 1024 * 1024,  # 50MB
}

# Test categories for organized test running
TEST_CATEGORIES = {
    'unit': ['models', 'utils', 'forms'],
    'integration': ['views', 'workflows', 'api'],
    'performance': ['load', 'stress', 'database'],
    'security': ['auth', 'permissions', 'validation'],
    'ui': ['templates', 'frontend', 'javascript']
}
