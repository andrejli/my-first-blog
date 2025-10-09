"""
Django LMS Test Configuration

This module provides fixtures and configuration for pytest-django testing.
It includes factory classes for creating test data and common test utilities.
"""

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.core.management import call_command
import factory
from factory.django import DjangoModelFactory
from blog.models import (
    UserProfile, Course, Enrollment, Lesson, Assignment, 
    Submission, Quiz, Question, Answer, QuizAttempt, QuizResponse
)


# ================================
# PYTEST FIXTURES
# ================================

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Loads initial data for the entire test session
    """
    with django_db_blocker.unblock():
        # Load any fixtures or initial data here if needed
        pass


@pytest.fixture
def client():
    """Django test client"""
    return Client()


@pytest.fixture
def authenticated_client(client, student_user):
    """Client with authenticated student user"""
    client.force_login(student_user)
    return client


@pytest.fixture
def instructor_client(client, instructor_user):
    """Client with authenticated instructor user"""
    client.force_login(instructor_user)
    return client


# ================================
# FACTORY CLASSES
# ================================

class UserFactory(DjangoModelFactory):
    """Factory for creating User instances"""
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True


class UserProfileFactory(DjangoModelFactory):
    """Factory for creating UserProfile instances"""
    class Meta:
        model = UserProfile
    
    user = factory.SubFactory(UserFactory)
    role = 'student'
    bio = factory.Faker('text', max_nb_chars=200)
    phone = factory.Faker('phone_number')
    date_of_birth = factory.Faker('date_of_birth', minimum_age=18, maximum_age=65)


class InstructorProfileFactory(UserProfileFactory):
    """Factory for creating instructor UserProfile instances"""
    role = 'instructor'


class StudentProfileFactory(UserProfileFactory):
    """Factory for creating student UserProfile instances"""
    role = 'student'


class CourseFactory(DjangoModelFactory):
    """Factory for creating Course instances"""
    class Meta:
        model = Course
    
    title = factory.Faker('catch_phrase')
    course_code = factory.Sequence(lambda n: f"CS{n:03d}")
    description = factory.Faker('text', max_nb_chars=500)
    instructor = factory.SubFactory(UserFactory)
    status = 'published'
    duration_weeks = factory.Faker('random_int', min=4, max=16)
    max_students = factory.Faker('random_int', min=10, max=50)
    prerequisites = factory.Faker('text', max_nb_chars=200)
    
    @factory.post_generation
    def create_instructor_profile(self, create, extracted, **kwargs):
        """Ensure instructor has correct profile"""
        if not create:
            return
        
        profile, created = UserProfile.objects.get_or_create(
            user=self.instructor,
            defaults={'role': 'instructor'}
        )
        if not created and profile.role != 'instructor':
            profile.role = 'instructor'
            profile.save()


class LessonFactory(DjangoModelFactory):
    """Factory for creating Lesson instances"""
    class Meta:
        model = Lesson
    
    course = factory.SubFactory(CourseFactory)
    title = factory.Faker('sentence', nb_words=4)
    content = factory.Faker('text', max_nb_chars=1000)
    order = factory.Sequence(lambda n: n + 1)
    video_url = factory.Faker('url')
    is_published = True


class EnrollmentFactory(DjangoModelFactory):
    """Factory for creating Enrollment instances"""
    class Meta:
        model = Enrollment
    
    student = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
    status = 'enrolled'
    
    @factory.post_generation
    def create_student_profile(self, create, extracted, **kwargs):
        """Ensure student has correct profile"""
        if not create:
            return
        
        profile, created = UserProfile.objects.get_or_create(
            user=self.student,
            defaults={'role': 'student'}
        )


class AssignmentFactory(DjangoModelFactory):
    """Factory for creating Assignment instances"""
    class Meta:
        model = Assignment
    
    course = factory.SubFactory(CourseFactory)
    title = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('text', max_nb_chars=500)
    due_date = factory.Faker('future_datetime', end_date='+30d')
    max_points = factory.Faker('random_int', min=50, max=100)
    is_published = True


class SubmissionFactory(DjangoModelFactory):
    """Factory for creating Submission instances"""
    class Meta:
        model = Submission
    
    assignment = factory.SubFactory(AssignmentFactory)
    student = factory.SubFactory(UserFactory)
    content = factory.Faker('text', max_nb_chars=1000)
    status = 'submitted'
    
    @factory.post_generation
    def ensure_enrollment(self, create, extracted, **kwargs):
        """Ensure student is enrolled in the course"""
        if not create:
            return
        
        EnrollmentFactory(student=self.student, course=self.assignment.course)


class QuizFactory(DjangoModelFactory):
    """Factory for creating Quiz instances"""
    class Meta:
        model = Quiz
    
    course = factory.SubFactory(CourseFactory)
    title = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('text', max_nb_chars=300)
    quiz_type = 'graded'
    time_limit = factory.Faker('random_int', min=15, max=120)
    max_attempts = factory.Faker('random_int', min=1, max=3)
    show_correct_answers = True
    is_published = True


class QuestionFactory(DjangoModelFactory):
    """Factory for creating Question instances"""
    class Meta:
        model = Question
    
    quiz = factory.SubFactory(QuizFactory)
    question_text = factory.Faker('sentence', nb_words=8, variable_nb_words=True)
    question_type = 'multiple_choice'
    points = factory.Faker('random_int', min=1, max=5)
    order = factory.Sequence(lambda n: n)


class AnswerFactory(DjangoModelFactory):
    """Factory for creating Answer instances"""
    class Meta:
        model = Answer
    
    question = factory.SubFactory(QuestionFactory)
    answer_text = factory.Faker('sentence', nb_words=5)
    is_correct = False
    order = factory.Sequence(lambda n: n)


class QuizAttemptFactory(DjangoModelFactory):
    """Factory for creating QuizAttempt instances"""
    class Meta:
        model = QuizAttempt
    
    student = factory.SubFactory(UserFactory)
    quiz = factory.SubFactory(QuizFactory)
    attempt_number = 1
    status = 'in_progress'
    
    @factory.post_generation
    def ensure_enrollment(self, create, extracted, **kwargs):
        """Ensure student is enrolled in the course"""
        if not create:
            return
        
        EnrollmentFactory(student=self.student, course=self.quiz.course)


# ================================
# USER FIXTURES
# ================================

@pytest.fixture
def student_user():
    """Create a student user with profile"""
    profile = StudentProfileFactory()
    return profile.user


@pytest.fixture
def instructor_user():
    """Create an instructor user with profile"""
    profile = InstructorProfileFactory()
    return profile.user


@pytest.fixture
def admin_user():
    """Create an admin user"""
    user = UserFactory(is_staff=True, is_superuser=True)
    UserProfile.objects.create(user=user, role='admin')
    return user


# ================================
# COURSE FIXTURES
# ================================

@pytest.fixture
def course(instructor_user):
    """Create a basic course"""
    return CourseFactory(instructor=instructor_user)


@pytest.fixture
def course_with_lessons(course):
    """Create a course with lessons"""
    lessons = LessonFactory.create_batch(3, course=course)
    return course


@pytest.fixture
def enrolled_student(student_user, course):
    """Create an enrolled student"""
    EnrollmentFactory(student=student_user, course=course)
    return student_user


# ================================
# QUIZ FIXTURES
# ================================

@pytest.fixture
def quiz(course):
    """Create a basic quiz"""
    return QuizFactory(course=course)


@pytest.fixture
def quiz_with_questions(quiz):
    """Create a quiz with multiple choice questions"""
    for i in range(3):
        question = QuestionFactory(quiz=quiz, question_type='multiple_choice')
        # Create 4 answers, one correct
        AnswerFactory.create_batch(3, question=question, is_correct=False)
        AnswerFactory(question=question, is_correct=True)
    return quiz


@pytest.fixture
def quiz_attempt(enrolled_student, quiz):
    """Create a quiz attempt"""
    return QuizAttemptFactory(student=enrolled_student, quiz=quiz)


# ================================
# ASSIGNMENT FIXTURES
# ================================

@pytest.fixture
def assignment(course):
    """Create a basic assignment"""
    return AssignmentFactory(course=course)


@pytest.fixture
def submission(enrolled_student, assignment):
    """Create a submission"""
    return SubmissionFactory(student=enrolled_student, assignment=assignment)