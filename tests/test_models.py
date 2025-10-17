"""
Test Models for Django LMS

This module contains comprehensive tests for all LMS models including:
- UserProfile model with different roles
- Course model with enrollment management  
- Assignment and Submission models
- Quiz, Question, Answer, and QuizAttempt models
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from blog.models import (
    UserProfile, Course, Enrollment, Lesson, Assignment, 
    Submission, Quiz, Question, Answer, QuizAttempt, QuizResponse
)


# ================================
# USER PROFILE MODEL TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.models
class TestUserProfileModel:
    """Test cases for UserProfile model"""
    
    def test_create_user_profile(self, user_factory, user_profile_factory):
        """Test creating a user profile"""
        user = user_factory()
        profile = user_profile_factory(user=user, role='student')
        
        assert profile.user == user
        assert profile.role == 'student'
        assert str(profile) == f"{user.username} - {profile.role}"


# ================================
# USER PROFILE MODEL TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.models
class TestUserProfileModel:
    """Test cases for UserProfile model"""
    
    def test_create_user_profile(self):
        """Test creating a user profile"""
        user = User.objects.create_user(username='testuser', email='test@example.com')
        # Signal automatically creates profile, so get it
        profile = user.userprofile
        profile.role = 'student'
        profile.save()
        
        assert profile.user == user
        assert profile.role == 'student'
        assert str(profile) == 'testuser - student'
    
    def test_user_profile_roles(self, user_factory, user_profile_factory):
        """Test different user roles"""
        student_user = user_factory(username='student')
        instructor_user = user_factory(username='instructor') 
        admin_user = user_factory(username='admin')
        
        student_profile = user_profile_factory(user=student_user, role='student')
        instructor_profile = user_profile_factory(user=instructor_user, role='instructor')
        admin_profile = user_profile_factory(user=admin_user, role='admin')
        
        assert student_profile.role == 'student'
        assert instructor_profile.role == 'instructor'
        assert admin_profile.role == 'admin'
    
    def test_user_profile_default_role(self):
        """Test default role is student"""
        user = User.objects.create_user(username='testuser')
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        assert profile.role == 'student'
    
    def test_user_profile_one_to_one_relationship(self):
        """Test one-to-one relationship with User"""
        user = User.objects.create_user(username='testuser')
        UserProfile.objects.get_or_create(user=user, defaults={'role': 'student'})
        
        # Trying to create another profile for same user should fail
        with pytest.raises(IntegrityError):
            UserProfile.objects.get_or_create(user=user, defaults={'role': 'instructor'})


# ================================
# COURSE MODEL TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.models
@pytest.mark.course
class TestCourseModel:
    """Test cases for Course model"""
    
    def test_create_course(self):
        """Test creating a course"""
        instructor = User.objects.create_user(username='prof')
        UserProfile.objects.get_or_create(user=instructor, defaults={'role': 'instructor'})
        
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        assert course.title == 'Test Course'
        assert course.course_code == 'CS101'
        assert course.instructor == instructor
        assert course.status == 'draft'  # default status
        assert str(course) == 'CS101 - Test Course'
    
    def test_course_unique_code(self):
        """Test course codes must be unique"""
        instructor1 = User.objects.create_user(username='prof1')
        instructor2 = User.objects.create_user(username='prof2')
        
        Course.objects.create(
            title='Course 1',
            course_code='CS101',
            description='Description 1',
            instructor=instructor1
        )
        
        # Creating another course with same code should fail
        with pytest.raises(IntegrityError):
            Course.objects.create(
                title='Course 2',
                course_code='CS101',
                description='Description 2',
                instructor=instructor2
            )
    
    def test_course_publish(self):
        """Test course publish functionality"""
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        assert course.status == 'draft'
        assert course.published_date is None
        
        course.publish()
        
        assert course.status == 'published'
        assert course.published_date is not None
    
    def test_course_enrollment_count(self):
        """Test get_enrolled_count method"""
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        # Initially no enrollments
        assert course.get_enrolled_count() == 0
        
        # Create some enrollments
        student1 = User.objects.create_user(username='student1')
        student2 = User.objects.create_user(username='student2')
        student3 = User.objects.create_user(username='student3')
        
        Enrollment.objects.create(student=student1, course=course, status='enrolled')
        Enrollment.objects.create(student=student2, course=course, status='enrolled')
        Enrollment.objects.create(student=student3, course=course, status='dropped')
        
        # Should count only enrolled students
        assert course.get_enrolled_count() == 2


# ================================
# ENROLLMENT MODEL TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.models
class TestEnrollmentModel:
    """Test cases for Enrollment model"""
    
    def test_create_enrollment(self):
        """Test creating an enrollment"""
        student = User.objects.create_user(username='student')
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        enrollment = Enrollment.objects.create(student=student, course=course)
        
        assert enrollment.student == student
        assert enrollment.course == course
        assert enrollment.status == 'enrolled'  # default status
        assert enrollment.enrollment_date is not None
        assert str(enrollment) == 'student enrolled in CS101'
    
    def test_enrollment_unique_together(self):
        """Test student can only enroll once per course"""
        student = User.objects.create_user(username='student')
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        Enrollment.objects.create(student=student, course=course)
        
        # Creating another enrollment for same student-course should fail
        with pytest.raises(IntegrityError):
            Enrollment.objects.create(student=student, course=course)
    
    def test_enrollment_statuses(self):
        """Test different enrollment statuses"""
        student = User.objects.create_user(username='student')
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        enrollment = Enrollment.objects.create(
            student=student, 
            course=course, 
            status='waitlisted'
        )
        
        assert enrollment.status == 'waitlisted'


# ================================
# LESSON MODEL TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.models
class TestLessonModel:
    """Test cases for Lesson model"""
    
    def test_create_lesson(self):
        """Test creating a lesson"""
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        lesson = Lesson.objects.create(
            course=course,
            title='Lesson 1',
            content='Lesson content',
            order=1
        )
        
        assert lesson.course == course
        assert lesson.title == 'Lesson 1'
        assert lesson.order == 1
        assert lesson.is_published is False  # default
        assert str(lesson) == 'CS101 - Lesson 1: Lesson 1'
    
    def test_lesson_ordering(self):
        """Test lesson ordering"""
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        lesson2 = Lesson.objects.create(course=course, title='Lesson 2', order=2)
        lesson1 = Lesson.objects.create(course=course, title='Lesson 1', order=1)
        lesson3 = Lesson.objects.create(course=course, title='Lesson 3', order=3)
        
        # Should be ordered by course, then order
        lessons = list(Lesson.objects.all())
        assert lessons == [lesson1, lesson2, lesson3]


# ================================
# ASSIGNMENT MODEL TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.models
@pytest.mark.assignment
class TestAssignmentModel:
    """Test cases for Assignment model"""
    
    def test_create_assignment(self):
        """Test creating an assignment"""
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        future_date = timezone.now() + timedelta(days=7)
        assignment = Assignment.objects.create(
            course=course,
            title='Test Assignment',
            description='Assignment description',
            due_date=future_date,
            max_points=100
        )
        
        assert assignment.course == course
        assert assignment.title == 'Test Assignment'
        assert assignment.max_points == 100
        assert assignment.is_published is False  # default
        assert str(assignment) == 'CS101 - Test Assignment'
    
    def test_assignment_is_overdue(self):
        """Test is_overdue property"""
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        # Past due date
        past_date = timezone.now() - timedelta(days=1)
        overdue_assignment = Assignment.objects.create(
            course=course,
            title='Overdue Assignment',
            due_date=past_date
        )
        
        # Future due date
        future_date = timezone.now() + timedelta(days=7)
        future_assignment = Assignment.objects.create(
            course=course,
            title='Future Assignment',
            due_date=future_date
        )
        
        assert overdue_assignment.is_overdue is True
        assert future_assignment.is_overdue is False


# ================================
# SUBMISSION MODEL TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.models
@pytest.mark.assignment
class TestSubmissionModel:
    """Test cases for Submission model"""
    
    def test_create_submission(self):
        """Test creating a submission"""
        student = User.objects.create_user(username='student')
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        assignment = Assignment.objects.create(
            course=course,
            title='Test Assignment',
            due_date=timezone.now() + timedelta(days=7)
        )
        
        submission = Submission.objects.create(
            assignment=assignment,
            student=student,
            text_submission='Submission content'
        )
        
        assert submission.assignment == assignment
        assert submission.student == student
        assert submission.status == 'draft'  # default
        assert submission.submitted_date is None  # not submitted yet
        assert str(submission) == 'student - Test Assignment (draft)'
    
    def test_submission_unique_together(self):
        """Test student can only submit once per assignment"""
        student = User.objects.create_user(username='student')
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        assignment = Assignment.objects.create(
            course=course,
            title='Test Assignment',
            due_date=timezone.now() + timedelta(days=7)
        )
        
        Submission.objects.create(assignment=assignment, student=student)
        
        # Creating another submission for same student-assignment should fail
        with pytest.raises(IntegrityError):
            Submission.objects.create(assignment=assignment, student=student)


# ================================
# QUIZ MODEL TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.models
@pytest.mark.quiz
class TestQuizModel:
    """Test cases for Quiz model"""
    
    def test_create_quiz(self):
        """Test creating a quiz"""
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        quiz = Quiz.objects.create(
            course=course,
            title='Test Quiz',
            description='Quiz description',
            quiz_type='graded',
            time_limit=60,
            max_attempts=2
        )
        
        assert quiz.course == course
        assert quiz.title == 'Test Quiz'
        assert quiz.quiz_type == 'graded'
        assert quiz.time_limit == 60
        assert quiz.max_attempts == 2
        assert quiz.is_published is False  # default
        assert str(quiz) == 'CS101 - Test Quiz'
    
    def test_quiz_availability(self):
        """Test quiz availability checking"""
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        
        # Quiz available now
        current_quiz = Quiz.objects.create(
            course=course,
            title='Available Quiz',
            available_from=timezone.now() - timedelta(hours=1),
            available_until=timezone.now() + timedelta(hours=1)
        )
        
        # Quiz not yet available
        future_quiz = Quiz.objects.create(
            course=course,
            title='Future Quiz',
            available_from=timezone.now() + timedelta(hours=1),
            available_until=timezone.now() + timedelta(hours=2)
        )
        
        # Quiz no longer available
        past_quiz = Quiz.objects.create(
            course=course,
            title='Past Quiz',
            available_from=timezone.now() - timedelta(hours=2),
            available_until=timezone.now() - timedelta(hours=1)
        )
        
        assert current_quiz.is_available is True
        assert future_quiz.is_available is False
        assert past_quiz.is_available is False
    
    def test_quiz_total_questions(self):
        """Test total_questions property"""
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        quiz = Quiz.objects.create(course=course, title='Test Quiz')
        
        # Initially no questions
        assert quiz.total_questions == 0
        
        # Add some questions
        Question.objects.create(quiz=quiz, question_text='Question 1', question_type='multiple_choice')
        Question.objects.create(quiz=quiz, question_text='Question 2', question_type='true_false')
        
        assert quiz.total_questions == 2


# ================================
# QUESTION MODEL TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.models
@pytest.mark.quiz
class TestQuestionModel:
    """Test cases for Question model"""
    
    def test_create_question(self):
        """Test creating a question"""
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        quiz = Quiz.objects.create(course=course, title='Test Quiz')
        
        question = Question.objects.create(
            quiz=quiz,
            question_text='What is 2+2?',
            question_type='multiple_choice',
            points=Decimal('5.00'),
            order=1
        )
        
        assert question.quiz == quiz
        assert question.question_text == 'What is 2+2?'
        assert question.question_type == 'multiple_choice'
        assert question.points == Decimal('5.00')
        assert str(question) == 'CS101 - Test Quiz - Q1: What is 2+2?...'
    
    def test_question_types(self):
        """Test different question types"""
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        quiz = Quiz.objects.create(course=course, title='Test Quiz')
        
        mc_question = Question.objects.create(
            quiz=quiz,
            question_text='Multiple choice question',
            question_type='multiple_choice'
        )
        
        tf_question = Question.objects.create(
            quiz=quiz,
            question_text='True/false question',
            question_type='true_false'
        )
        
        sa_question = Question.objects.create(
            quiz=quiz,
            question_text='Short answer question',
            question_type='short_answer'
        )
        
        assert mc_question.question_type == 'multiple_choice'
        assert tf_question.question_type == 'true_false'
        assert sa_question.question_type == 'short_answer'


# ================================
# ANSWER MODEL TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.models
@pytest.mark.quiz
class TestAnswerModel:
    """Test cases for Answer model"""
    
    def test_create_answer(self):
        """Test creating an answer"""
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        quiz = Quiz.objects.create(course=course, title='Test Quiz')
        question = Question.objects.create(
            quiz=quiz,
            question_text='What is 2+2?',
            question_type='multiple_choice'
        )
        
        answer = Answer.objects.create(
            question=question,
            answer_text='4',
            is_correct=True,
            order=1
        )
        
        assert answer.question == question
        assert answer.answer_text == '4'
        assert answer.is_correct is True
        assert str(answer) == '✓ 4'
    
    def test_answer_string_representation(self):
        """Test answer string representation with correct/incorrect indicators"""
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        quiz = Quiz.objects.create(course=course, title='Test Quiz')
        question = Question.objects.create(
            quiz=quiz,
            question_text='What is 2+2?',
            question_type='multiple_choice'
        )
        
        correct_answer = Answer.objects.create(
            question=question,
            answer_text='4',
            is_correct=True
        )
        
        incorrect_answer = Answer.objects.create(
            question=question,
            answer_text='5',
            is_correct=False
        )
        
        assert str(correct_answer) == '✓ 4'
        assert str(incorrect_answer) == '✗ 5'


# ================================
# QUIZ ATTEMPT MODEL TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.models
@pytest.mark.quiz
class TestQuizAttemptModel:
    """Test cases for QuizAttempt model"""
    
    def test_create_quiz_attempt(self):
        """Test creating a quiz attempt"""
        student = User.objects.create_user(username='student')
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        quiz = Quiz.objects.create(course=course, title='Test Quiz')
        
        attempt = QuizAttempt.objects.create(
            student=student,
            quiz=quiz,
            attempt_number=1
        )
        
        assert attempt.student == student
        assert attempt.quiz == quiz
        assert attempt.status == 'in_progress'  # default
        assert attempt.started_at is not None
        assert str(attempt) == 'student - Test Quiz (Attempt 1) - in_progress'
    
    def test_quiz_attempt_completion(self):
        """Test quiz attempt completion"""
        student = User.objects.create_user(username='student')
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        quiz = Quiz.objects.create(course=course, title='Test Quiz')
        
        attempt = QuizAttempt.objects.create(
            student=student,
            quiz=quiz
        )
        
        # Initially in progress
        assert attempt.status == 'in_progress'
        assert attempt.completed_at is None
        
        # Complete the attempt
        attempt.complete_attempt()
        
        assert attempt.status == 'completed'
        assert attempt.completed_at is not None
        assert attempt.time_taken is not None
    
    def test_quiz_attempt_passing_score(self):
        """Test is_passed property"""
        student = User.objects.create_user(username='student')
        instructor = User.objects.create_user(username='prof')
        course = Course.objects.create(
            title='Test Course',
            course_code='CS101',
            description='Test description',
            instructor=instructor
        )
        quiz = Quiz.objects.create(
            course=course, 
            title='Test Quiz',
            passing_score=Decimal('70.00')
        )
        
        # Passing attempt
        passing_attempt = QuizAttempt.objects.create(
            student=student,
            quiz=quiz,
            percentage=Decimal('80.00')
        )
        
        # Failing attempt
        failing_attempt = QuizAttempt.objects.create(
            student=student,
            quiz=quiz,
            percentage=Decimal('60.00')
        )
        
        assert passing_attempt.is_passed is True
        assert failing_attempt.is_passed is False
        
        # Test with no passing score set
        quiz.passing_score = None
        quiz.save()
        
        assert passing_attempt.is_passed is False  # Should be False when no passing score
