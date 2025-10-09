"""
Integration Tests for Django LMS

This module contains end-to-end integration tests for complex user workflows:
- Complete student enrollment and course completion workflow
- Quiz taking end-to-end process
- Assignment submission and grading workflow
- Instructor course management workflow
- Multi-user interaction scenarios
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
# STUDENT ENROLLMENT WORKFLOW
# ================================

@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.slow
class TestStudentEnrollmentWorkflow:
    """Test complete student enrollment and course participation workflow"""
    
    def test_complete_student_journey(self, client):
        """Test complete student journey from registration to course completion"""
        # Create instructor and course
        instructor = User.objects.create_user(username='prof', password='profpass')
        UserProfile.objects.create(user=instructor, role='instructor')
        
        course = Course.objects.create(
            title='Introduction to Python',
            course_code='CS101',
            description='Learn Python programming',
            instructor=instructor,
            status='published'
        )
        
        # Create course content
        lesson1 = Lesson.objects.create(
            course=course,
            title='Python Basics',
            content='Introduction to Python syntax',
            order=1,
            is_published=True
        )
        
        lesson2 = Lesson.objects.create(
            course=course,
            title='Variables and Data Types',
            content='Understanding Python variables',
            order=2,
            is_published=True
        )
        
        assignment = Assignment.objects.create(
            course=course,
            title='Hello World Program',
            description='Write a hello world program',
            due_date=timezone.now() + timedelta(days=7),
            max_points=100,
            is_published=True
        )
        
        # Create quiz with questions
        quiz = Quiz.objects.create(
            course=course,
            title='Python Basics Quiz',
            description='Test your Python knowledge',
            max_attempts=2,
            is_published=True
        )
        
        question1 = Question.objects.create(
            quiz=quiz,
            text='What is Python?',
            question_type='multiple_choice',
            points=10,
            order=1
        )
        
        Answer.objects.create(
            question=question1,
            text='A programming language',
            is_correct=True
        )
        Answer.objects.create(
            question=question1,
            text='A snake',
            is_correct=False
        )
        
        question2 = Question.objects.create(
            quiz=quiz,
            text='Python is case-sensitive',
            question_type='true_false',
            points=5,
            order=2
        )
        
        Answer.objects.create(
            question=question2,
            text='True',
            is_correct=True
        )
        Answer.objects.create(
            question=question2,
            text='False',
            is_correct=False
        )
        
        # Step 1: Student Registration
        registration_data = {
            'username': 'student1',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        
        response = client.post(reverse('register'), data=registration_data)
        assert response.status_code == 302  # Redirect to dashboard
        
        # Verify user and profile created
        student = User.objects.get(username='student1')
        profile = UserProfile.objects.get(user=student)
        assert profile.role == 'student'
        
        # Step 2: Browse Courses
        response = client.get(reverse('course_list'))
        assert response.status_code == 200
        assert course in response.context['courses']
        
        # Step 3: View Course Detail
        response = client.get(reverse('course_detail', kwargs={'course_id': course.id}))
        assert response.status_code == 200
        assert response.context['is_enrolled'] is False
        
        # Step 4: Enroll in Course
        response = client.post(reverse('enroll_course', kwargs={'course_id': course.id}))
        assert response.status_code == 302
        
        # Verify enrollment
        enrollment = Enrollment.objects.get(student=student, course=course)
        assert enrollment.status == 'enrolled'
        
        # Step 5: Access Course Content
        response = client.get(reverse('course_detail', kwargs={'course_id': course.id}))
        assert response.context['is_enrolled'] is True
        
        # Step 6: View Lessons
        response = client.get(reverse('lesson_detail', kwargs={'lesson_id': lesson1.id}))
        assert response.status_code == 200
        
        response = client.get(reverse('lesson_detail', kwargs={'lesson_id': lesson2.id}))
        assert response.status_code == 200
        
        # Step 7: Submit Assignment
        response = client.get(reverse('submit_assignment', kwargs={'assignment_id': assignment.id}))
        assert response.status_code == 200
        
        submission_data = {
            'content': 'print("Hello, World!")\n# This is my first Python program',
            'submit_type': 'submit'
        }
        
        response = client.post(
            reverse('submit_assignment', kwargs={'assignment_id': assignment.id}),
            data=submission_data
        )
        assert response.status_code == 302
        
        # Verify submission
        submission = Submission.objects.get(assignment=assignment, student=student)
        assert submission.status == 'submitted'
        
        # Step 8: Take Quiz
        response = client.post(reverse('start_quiz', kwargs={'quiz_id': quiz.id}))
        assert response.status_code == 302
        
        # Verify quiz attempt created
        attempt = QuizAttempt.objects.get(student=student, quiz=quiz)
        assert attempt.status == 'in_progress'
        
        # Answer quiz questions
        quiz_data = {
            f'question_{question1.id}': Answer.objects.filter(question=question1, is_correct=True).first().id,
            f'question_{question2.id}': Answer.objects.filter(question=question2, is_correct=True).first().id,
        }
        
        response = client.post(
            reverse('take_quiz', kwargs={'attempt_id': attempt.id}),
            data=quiz_data
        )
        assert response.status_code == 302
        
        # Verify quiz responses and completion
        attempt.refresh_from_db()
        assert attempt.status == 'completed'
        assert attempt.score == 15  # Full score (10 + 5)
        
        quiz_responses = QuizResponse.objects.filter(attempt=attempt)
        assert quiz_responses.count() == 2
        
        # Step 9: Check Student Dashboard
        response = client.get(reverse('student_dashboard'))
        assert response.status_code == 200
        
        # Verify course appears in progress
        course_progress = response.context['course_progress']
        assert len(course_progress) == 1
        assert course_progress[0]['course'] == course


# ================================
# INSTRUCTOR WORKFLOW
# ================================

@pytest.mark.django_db
@pytest.mark.integration
class TestInstructorWorkflow:
    """Test complete instructor workflow for course management"""
    
    def test_instructor_course_creation_and_management(self, client):
        """Test instructor creating and managing a complete course"""
        # Step 1: Instructor Registration/Login
        instructor = User.objects.create_user(username='prof', password='profpass')
        UserProfile.objects.create(user=instructor, role='instructor')
        
        client.login(username='prof', password='profpass')
        
        # Step 2: Create Course
        course_data = {
            'title': 'Advanced Web Development',
            'course_code': 'WEB301',
            'description': 'Learn advanced web development techniques',
            'status': 'draft'
        }
        
        response = client.post(reverse('create_course'), data=course_data)
        assert response.status_code == 302
        
        course = Course.objects.get(course_code='WEB301')
        assert course.instructor == instructor
        assert course.status == 'draft'
        
        # Step 3: Add Lessons
        lesson_data = {
            'title': 'JavaScript ES6 Features',
            'content': 'Learn about arrow functions, destructuring, and more',
            'order': 1,
            'is_published': True
        }
        
        response = client.post(
            reverse('create_lesson', kwargs={'course_id': course.id}),
            data=lesson_data
        )
        assert response.status_code == 302
        
        lesson = Lesson.objects.get(course=course, title='JavaScript ES6 Features')
        assert lesson.is_published is True
        
        # Step 4: Create Assignment
        assignment_data = {
            'title': 'Build a Single Page Application',
            'description': 'Create a SPA using modern JavaScript',
            'due_date': (timezone.now() + timedelta(days=14)).strftime('%Y-%m-%d %H:%M'),
            'max_points': 150,
            'is_published': True
        }
        
        response = client.post(
            reverse('create_assignment', kwargs={'course_id': course.id}),
            data=assignment_data
        )
        assert response.status_code == 302
        
        assignment = Assignment.objects.get(course=course, title='Build a Single Page Application')
        assert assignment.max_points == 150
        
        # Step 5: Create Quiz with Questions
        quiz_data = {
            'title': 'JavaScript Knowledge Check',
            'description': 'Test your JavaScript skills',
            'max_attempts': 3,
            'is_published': False  # Keep as draft initially
        }
        
        response = client.post(
            reverse('create_quiz', kwargs={'course_id': course.id}),
            data=quiz_data
        )
        assert response.status_code == 302
        
        quiz = Quiz.objects.get(course=course, title='JavaScript Knowledge Check')
        assert quiz.is_published is False
        
        # Add questions to quiz
        question_data = {
            'text': 'What does "const" keyword do in JavaScript?',
            'question_type': 'multiple_choice',
            'points': 10,
            'order': 1,
            'answers': [
                {'text': 'Creates a constant variable', 'is_correct': True},
                {'text': 'Creates a mutable variable', 'is_correct': False},
                {'text': 'Defines a function', 'is_correct': False},
            ]
        }
        
        response = client.post(
            reverse('add_question', kwargs={'quiz_id': quiz.id}),
            data=question_data
        )
        assert response.status_code == 302
        
        question = Question.objects.get(quiz=quiz, text__contains='const keyword')
        assert question.points == 10
        
        answers = Answer.objects.filter(question=question)
        assert answers.count() == 3
        assert answers.filter(is_correct=True).count() == 1
        
        # Step 6: Publish Quiz
        response = client.post(reverse('publish_quiz', kwargs={'quiz_id': quiz.id}))
        assert response.status_code == 302
        
        quiz.refresh_from_db()
        assert quiz.is_published is True
        
        # Step 7: Publish Course
        response = client.post(reverse('publish_course', kwargs={'course_id': course.id}))
        assert response.status_code == 302
        
        course.refresh_from_db()
        assert course.status == 'published'
        
        # Step 8: View Instructor Dashboard
        response = client.get(reverse('instructor_dashboard'))
        assert response.status_code == 200
        assert course in response.context['courses']
        
        # Step 9: Monitor Student Enrollments (simulate students enrolling)
        student1 = User.objects.create_user(username='student1', password='pass123')
        UserProfile.objects.create(user=student1, role='student')
        Enrollment.objects.create(student=student1, course=course, status='enrolled')
        
        student2 = User.objects.create_user(username='student2', password='pass123')
        UserProfile.objects.create(user=student2, role='student')
        Enrollment.objects.create(student=student2, course=course, status='enrolled')
        
        response = client.get(reverse('course_enrollments', kwargs={'course_id': course.id}))
        assert response.status_code == 200
        
        enrollments = response.context['enrollments']
        assert enrollments.count() == 2


# ================================
# QUIZ TAKING WORKFLOW
# ================================

@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.quiz
class TestQuizTakingWorkflow:
    """Test complete quiz taking workflow with multiple attempts"""
    
    def test_multiple_quiz_attempts_and_grading(self, client):
        """Test student taking quiz multiple times with different scores"""
        # Setup
        instructor = User.objects.create_user(username='prof')
        student = User.objects.create_user(username='student', password='testpass')
        UserProfile.objects.create(user=student, role='student')
        
        course = Course.objects.create(
            title='Test Course',
            course_code='TST101',
            instructor=instructor,
            status='published'
        )
        
        Enrollment.objects.create(student=student, course=course, status='enrolled')
        
        # Create quiz with multiple questions
        quiz = Quiz.objects.create(
            course=course,
            title='Math Quiz',
            max_attempts=3,
            is_published=True
        )
        
        # Question 1: Multiple choice
        q1 = Question.objects.create(
            quiz=quiz,
            text='What is 2 + 2?',
            question_type='multiple_choice',
            points=10,
            order=1
        )
        
        Answer.objects.create(question=q1, text='3', is_correct=False)
        correct_answer_q1 = Answer.objects.create(question=q1, text='4', is_correct=True)
        Answer.objects.create(question=q1, text='5', is_correct=False)
        
        # Question 2: True/False
        q2 = Question.objects.create(
            quiz=quiz,
            text='The square root of 16 is 4',
            question_type='true_false',
            points=5,
            order=2
        )
        
        correct_answer_q2 = Answer.objects.create(question=q2, text='True', is_correct=True)
        Answer.objects.create(question=q2, text='False', is_correct=False)
        
        client.login(username='student', password='testpass')
        
        # Attempt 1: Get one question wrong
        response = client.post(reverse('start_quiz', kwargs={'quiz_id': quiz.id}))
        assert response.status_code == 302
        
        attempt1 = QuizAttempt.objects.get(student=student, quiz=quiz, attempt_number=1)
        
        # Submit answers (wrong answer for q1, correct for q2)
        wrong_answer_q1 = Answer.objects.filter(question=q1, is_correct=False).first()
        quiz_data = {
            f'question_{q1.id}': wrong_answer_q1.id,
            f'question_{q2.id}': correct_answer_q2.id,
        }
        
        response = client.post(
            reverse('take_quiz', kwargs={'attempt_id': attempt1.id}),
            data=quiz_data
        )
        assert response.status_code == 302
        
        attempt1.refresh_from_db()
        assert attempt1.status == 'completed'
        assert attempt1.score == 5  # Only q2 correct (5 points)
        
        # Verify responses
        responses = QuizResponse.objects.filter(attempt=attempt1)
        assert responses.count() == 2
        
        response_q1 = responses.get(question=q1)
        assert response_q1.selected_answer == wrong_answer_q1
        assert not response_q1.is_correct
        
        response_q2 = responses.get(question=q2)
        assert response_q2.selected_answer == correct_answer_q2
        assert response_q2.is_correct
        
        # Attempt 2: Get both questions correct
        response = client.post(reverse('start_quiz', kwargs={'quiz_id': quiz.id}))
        assert response.status_code == 302
        
        attempt2 = QuizAttempt.objects.get(student=student, quiz=quiz, attempt_number=2)
        
        # Submit all correct answers
        quiz_data = {
            f'question_{q1.id}': correct_answer_q1.id,
            f'question_{q2.id}': correct_answer_q2.id,
        }
        
        response = client.post(
            reverse('take_quiz', kwargs={'attempt_id': attempt2.id}),
            data=quiz_data
        )
        assert response.status_code == 302
        
        attempt2.refresh_from_db()
        assert attempt2.status == 'completed'
        assert attempt2.score == 15  # Both questions correct (10 + 5)
        
        # Verify best score is recorded
        best_attempt = QuizAttempt.objects.filter(
            student=student, quiz=quiz, status='completed'
        ).order_by('-score').first()
        
        assert best_attempt == attempt2
        assert best_attempt.score == 15
        
        # Attempt 3: Reach max attempts
        response = client.post(reverse('start_quiz', kwargs={'quiz_id': quiz.id}))
        assert response.status_code == 302
        
        attempt3 = QuizAttempt.objects.get(student=student, quiz=quiz, attempt_number=3)
        
        # Submit answers
        quiz_data = {
            f'question_{q1.id}': correct_answer_q1.id,
            f'question_{q2.id}': correct_answer_q2.id,
        }
        
        response = client.post(
            reverse('take_quiz', kwargs={'attempt_id': attempt3.id}),
            data=quiz_data
        )
        assert response.status_code == 302
        
        # Try to start attempt 4 (should fail)
        response = client.post(reverse('start_quiz', kwargs={'quiz_id': quiz.id}))
        assert response.status_code == 302  # Redirected with error message
        
        # Verify only 3 attempts exist
        attempts = QuizAttempt.objects.filter(student=student, quiz=quiz)
        assert attempts.count() == 3


# ================================
# ASSIGNMENT GRADING WORKFLOW
# ================================

@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.assignment
class TestAssignmentGradingWorkflow:
    """Test complete assignment submission and grading workflow"""
    
    def test_assignment_submission_and_instructor_grading(self, client):
        """Test student submitting assignment and instructor grading it"""
        # Setup
        instructor = User.objects.create_user(username='prof', password='profpass')
        UserProfile.objects.create(user=instructor, role='instructor')
        
        student = User.objects.create_user(username='student', password='studpass')
        UserProfile.objects.create(user=student, role='student')
        
        course = Course.objects.create(
            title='Programming Course',
            course_code='PRG101',
            instructor=instructor,
            status='published'
        )
        
        Enrollment.objects.create(student=student, course=course, status='enrolled')
        
        assignment = Assignment.objects.create(
            course=course,
            title='Calculator Program',
            description='Write a calculator program in Python',
            due_date=timezone.now() + timedelta(days=7),
            max_points=100,
            is_published=True
        )
        
        # Student submits assignment
        client.login(username='student', password='studpass')
        
        submission_data = {
            'content': '''
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b != 0:
        return a / b
    else:
        return "Cannot divide by zero"

# Test the functions
print(add(5, 3))
print(subtract(10, 4))
print(multiply(6, 7))
print(divide(15, 3))
            ''',
            'submit_type': 'submit'
        }
        
        response = client.post(
            reverse('submit_assignment', kwargs={'assignment_id': assignment.id}),
            data=submission_data
        )
        assert response.status_code == 302
        
        submission = Submission.objects.get(assignment=assignment, student=student)
        assert submission.status == 'submitted'
        assert submission.submitted_at is not None
        
        # Switch to instructor to grade
        client.login(username='prof', password='profpass')
        
        # View submissions
        response = client.get(reverse('assignment_submissions', kwargs={'assignment_id': assignment.id}))
        assert response.status_code == 200
        assert submission in response.context['submissions']
        
        # Grade the submission
        grade_data = {
            'score': '85',
            'feedback': 'Good work! The calculator functions are well implemented. Consider adding input validation for better error handling.',
            'status': 'graded'
        }
        
        response = client.post(
            reverse('grade_submission', kwargs={'submission_id': submission.id}),
            data=grade_data
        )
        assert response.status_code == 302
        
        submission.refresh_from_db()
        assert submission.score == Decimal('85')
        assert submission.status == 'graded'
        assert 'Good work!' in submission.feedback
        assert submission.graded_at is not None
        
        # Student views graded assignment
        client.login(username='student', password='studpass')
        
        response = client.get(reverse('student_assignments', kwargs={'course_id': course.id}))
        assert response.status_code == 200
        
        # Check that student can see their grade
        response = client.get(reverse('assignment_detail', kwargs={'assignment_id': assignment.id}))
        assert response.status_code == 200
        
        # Verify grade appears in student dashboard
        response = client.get(reverse('student_dashboard'))
        assert response.status_code == 200


# ================================
# MULTI-USER INTERACTION SCENARIOS
# ================================

@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.slow
class TestMultiUserInteractions:
    """Test scenarios involving multiple users interacting with the system"""
    
    def test_multiple_students_same_course(self, client):
        """Test multiple students enrolled in the same course"""
        # Setup
        instructor = User.objects.create_user(username='prof')
        UserProfile.objects.create(user=instructor, role='instructor')
        
        course = Course.objects.create(
            title='Data Science',
            course_code='DS101',
            instructor=instructor,
            status='published'
        )
        
        quiz = Quiz.objects.create(
            course=course,
            title='Statistics Quiz',
            max_attempts=1,
            is_published=True
        )
        
        question = Question.objects.create(
            quiz=quiz,
            text='What is the mean of [1, 2, 3, 4, 5]?',
            question_type='multiple_choice',
            points=10,
            order=1
        )
        
        correct_answer = Answer.objects.create(question=question, text='3', is_correct=True)
        Answer.objects.create(question=question, text='2.5', is_correct=False)
        Answer.objects.create(question=question, text='4', is_correct=False)
        
        # Create multiple students
        students = []
        for i in range(3):
            student = User.objects.create_user(
                username=f'student{i+1}',
                password=f'pass{i+1}'
            )
            UserProfile.objects.create(user=student, role='student')
            Enrollment.objects.create(student=student, course=course, status='enrolled')
            students.append(student)
        
        # Each student takes the quiz
        for i, student in enumerate(students):
            client.login(username=f'student{i+1}', password=f'pass{i+1}')
            
            # Start quiz
            response = client.post(reverse('start_quiz', kwargs={'quiz_id': quiz.id}))
            assert response.status_code == 302
            
            attempt = QuizAttempt.objects.get(student=student, quiz=quiz)
            
            # Student 1 gets it right, students 2 and 3 get it wrong
            if i == 0:
                selected_answer = correct_answer
            else:
                selected_answer = Answer.objects.filter(question=question, is_correct=False).first()
            
            quiz_data = {f'question_{question.id}': selected_answer.id}
            
            response = client.post(
                reverse('take_quiz', kwargs={'attempt_id': attempt.id}),
                data=quiz_data
            )
            assert response.status_code == 302
            
            attempt.refresh_from_db()
            assert attempt.status == 'completed'
            
            if i == 0:
                assert attempt.score == 10  # Correct answer
            else:
                assert attempt.score == 0   # Wrong answer
        
        # Verify all attempts recorded
        attempts = QuizAttempt.objects.filter(quiz=quiz, status='completed')
        assert attempts.count() == 3
        
        # Check score distribution
        high_scores = attempts.filter(score=10).count()
        low_scores = attempts.filter(score=0).count()
        
        assert high_scores == 1
        assert low_scores == 2
    
    def test_instructor_managing_multiple_courses(self, client):
        """Test instructor managing multiple courses with different students"""
        instructor = User.objects.create_user(username='prof', password='profpass')
        UserProfile.objects.create(user=instructor, role='instructor')
        
        # Create multiple courses
        course1 = Course.objects.create(
            title='Python Basics',
            course_code='PY101',
            instructor=instructor,
            status='published'
        )
        
        course2 = Course.objects.create(
            title='Advanced Python',
            course_code='PY201',
            instructor=instructor,
            status='published'
        )
        
        # Create assignments for each course
        assignment1 = Assignment.objects.create(
            course=course1,
            title='Variables and Functions',
            description='Basic Python assignment',
            due_date=timezone.now() + timedelta(days=7),
            max_points=50,
            is_published=True
        )
        
        assignment2 = Assignment.objects.create(
            course=course2,
            title='Object-Oriented Programming',
            description='Advanced OOP assignment',
            due_date=timezone.now() + timedelta(days=10),
            max_points=100,
            is_published=True
        )
        
        # Create students for different courses
        student1 = User.objects.create_user(username='student1', password='pass1')
        UserProfile.objects.create(user=student1, role='student')
        Enrollment.objects.create(student=student1, course=course1, status='enrolled')
        
        student2 = User.objects.create_user(username='student2', password='pass2')
        UserProfile.objects.create(user=student2, role='student')
        Enrollment.objects.create(student=student2, course=course2, status='enrolled')
        
        student3 = User.objects.create_user(username='student3', password='pass3')
        UserProfile.objects.create(user=student3, role='student')
        # Student 3 enrolled in both courses
        Enrollment.objects.create(student=student3, course=course1, status='enrolled')
        Enrollment.objects.create(student=student3, course=course2, status='enrolled')
        
        # Students submit assignments
        # Student 1 submits to course 1
        client.login(username='student1', password='pass1')
        response = client.post(
            reverse('submit_assignment', kwargs={'assignment_id': assignment1.id}),
            data={'content': 'Basic Python code', 'submit_type': 'submit'}
        )
        
        # Student 2 submits to course 2  
        client.login(username='student2', password='pass2')
        response = client.post(
            reverse('submit_assignment', kwargs={'assignment_id': assignment2.id}),
            data={'content': 'Advanced Python code', 'submit_type': 'submit'}
        )
        
        # Student 3 submits to both courses
        client.login(username='student3', password='pass3')
        response = client.post(
            reverse('submit_assignment', kwargs={'assignment_id': assignment1.id}),
            data={'content': 'Student 3 basic code', 'submit_type': 'submit'}
        )
        response = client.post(
            reverse('submit_assignment', kwargs={'assignment_id': assignment2.id}),
            data={'content': 'Student 3 advanced code', 'submit_type': 'submit'}
        )
        
        # Instructor views dashboard
        client.login(username='prof', password='profpass')
        response = client.get(reverse('instructor_dashboard'))
        assert response.status_code == 200
        
        courses = response.context['courses']
        assert course1 in courses
        assert course2 in courses
        
        # Check submissions for each course
        response = client.get(reverse('assignment_submissions', kwargs={'assignment_id': assignment1.id}))
        assert response.status_code == 200
        submissions_course1 = response.context['submissions']
        assert submissions_course1.count() == 2  # Student 1 and 3
        
        response = client.get(reverse('assignment_submissions', kwargs={'assignment_id': assignment2.id}))
        assert response.status_code == 200
        submissions_course2 = response.context['submissions']
        assert submissions_course2.count() == 2  # Student 2 and 3
        
        # Verify total submissions across all courses
        total_submissions = Submission.objects.filter(
            assignment__course__instructor=instructor
        ).count()
        assert total_submissions == 4