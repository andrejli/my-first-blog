"""
Test Course Import/Export System

This module contains comprehensive tests for the course import/export functionality:
- CourseExporter class tests
- CourseImporter class tests  
- Export/import view tests
- File handling and ZIP creation tests
- Data validation and error handling tests
"""

import pytest
import json
import zipfile
import tempfile
import os
from io import BytesIO
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, Mock

from blog.models import (
    Course, Lesson, Assignment, Quiz, Question, Answer, 
    CourseMaterial, Announcement, Enrollment, UserProfile
)
from blog.course_import_export import CourseExporter, CourseImporter


# ================================
# COURSE EXPORTER TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.import_export
class TestCourseExporter:
    """Test cases for CourseExporter class"""
    
    def test_export_course_metadata(self, instructor_user, sample_course):
        """Test exporting basic course metadata"""
        exporter = CourseExporter(sample_course, include_user_data=False)
        metadata = exporter.export_course_metadata()
        
        assert metadata['title'] == sample_course.title
        assert metadata['course_code'] == sample_course.course_code
        assert metadata['description'] == sample_course.description
        assert metadata['instructor_username'] == instructor_user.username
        assert metadata['instructor_email'] == instructor_user.email
        assert 'created_date' in metadata
        assert 'published_date' in metadata
    
    def test_export_lessons(self, sample_course_with_content):
        """Test exporting course lessons"""
        exporter = CourseExporter(sample_course_with_content, include_user_data=False)
        lessons = exporter.export_lessons()
        
        assert len(lessons) == 3  # From fixture
        lesson = lessons[0]
        assert 'title' in lesson
        assert 'content' in lesson
        assert 'order' in lesson
        assert 'created_date' in lesson
        assert 'is_published' in lesson
    
    def test_export_assignments(self, sample_course_with_content):
        """Test exporting course assignments"""
        exporter = CourseExporter(sample_course_with_content, include_user_data=False)
        assignments = exporter.export_assignments()
        
        assert len(assignments) == 2  # From fixture
        assignment = assignments[0]
        assert 'title' in assignment
        assert 'description' in assignment
        assert 'due_date' in assignment
        assert 'max_points' in assignment
        assert 'allow_file_submission' in assignment
        assert 'allow_text_submission' in assignment
        
    def test_export_quizzes(self, sample_course_with_content):
        """Test exporting course quizzes with questions"""
        exporter = CourseExporter(sample_course_with_content, include_user_data=False)
        quizzes = exporter.export_quizzes()
        
        assert len(quizzes) >= 1  # From fixture
        quiz = quizzes[0]
        assert 'title' in quiz
        assert 'description' in quiz
        assert 'questions' in quiz
        
        if quiz['questions']:
            question = quiz['questions'][0]
            assert 'question_text' in question
            assert 'question_type' in question
            assert 'points' in question
    
    def test_export_announcements(self, sample_course_with_content):
        """Test exporting course announcements"""
        exporter = CourseExporter(sample_course_with_content, include_user_data=False)
        announcements = exporter.export_announcements()
        
        assert isinstance(announcements, list)
        if announcements:
            announcement = announcements[0]
            assert 'title' in announcement
            assert 'content' in announcement
            assert 'priority' in announcement
            assert 'created_date' in announcement
    
    def test_export_without_user_data(self, sample_course_with_content):
        """Test export excludes user data when include_user_data=False"""
        exporter = CourseExporter(sample_course_with_content, include_user_data=False)
        export_data = exporter.generate_export_data()
        
        assert 'enrollments' not in export_data
        assert 'submissions' not in export_data
        assert 'quiz_attempts' not in export_data
        assert 'progress' not in export_data
    
    def test_export_with_user_data(self, sample_course_with_content, student_user):
        """Test export includes user data when include_user_data=True"""
        # Create enrollment for testing
        Enrollment.objects.create(
            student=student_user,
            course=sample_course_with_content,
            enrollment_date=timezone.now()
        )
        
        exporter = CourseExporter(sample_course_with_content, include_user_data=True)
        export_data = exporter.generate_export_data()
        
        assert 'enrollments' in export_data
        assert len(export_data['enrollments']) == 1
        assert export_data['enrollments'][0]['student_username'] == student_user.username
    
    def test_create_zip_export(self, sample_course_with_content):
        """Test creating ZIP file with course data"""
        exporter = CourseExporter(sample_course_with_content, include_user_data=False)
        zip_data = exporter.create_zip_export()
        
        assert isinstance(zip_data, bytes)
        assert len(zip_data) > 0
        
        # Verify ZIP content
        zip_buffer = BytesIO(zip_data)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            assert 'course_data.json' in zip_file.namelist()
            
            # Verify JSON content
            course_json = zip_file.read('course_data.json').decode('utf-8')
            course_data = json.loads(course_json)
            assert 'course' in course_data
            assert 'lessons' in course_data
            assert 'schema_version' in course_data
    
    def test_export_schema_version(self, sample_course_with_content):
        """Test export includes proper schema version"""
        exporter = CourseExporter(sample_course_with_content, include_user_data=False)
        export_data = exporter.generate_export_data()
        
        assert 'schema_version' in export_data
        assert export_data['schema_version'] == '1.0'
        assert 'export_date' in export_data
        assert 'exported_by' in export_data


# ================================
# COURSE IMPORTER TESTS  
# ================================

@pytest.mark.django_db
@pytest.mark.import_export
class TestCourseImporter:
    """Test cases for CourseImporter class"""
    
    def test_import_basic_course(self, instructor_user):
        """Test importing a basic course with minimal data"""
        course_data = {
            'schema_version': '1.0',
            'course': {
                'title': 'Imported Course',
                'description': 'This course was imported from export',
                'duration_weeks': 8,
                'max_students': 25,
                'prerequisites': 'Basic programming knowledge'
            },
            'lessons': []
        }
        
        importer = CourseImporter(course_data, instructor_user, 'IMPORT001')
        imported_course = importer.import_course()
        
        assert imported_course.title == 'Imported Course'
        assert imported_course.course_code == 'IMPORT001'
        assert imported_course.instructor == instructor_user
        assert imported_course.status == 'draft'  # Always import as draft
        assert imported_course.duration_weeks == 8
        assert imported_course.max_students == 25
    
    def test_import_course_with_lessons(self, instructor_user):
        """Test importing course with lessons"""
        course_data = {
            'schema_version': '1.0',
            'course': {
                'title': 'Course with Lessons',
                'description': 'Course description',
                'duration_weeks': 4,
                'max_students': 30
            },
            'lessons': [
                {
                    'title': 'Introduction',
                    'content': '# Welcome to the course\n\nThis is lesson 1.',
                    'order': 1,
                    'video_url': 'https://example.com/video1'
                },
                {
                    'title': 'Advanced Topics',
                    'content': '## Advanced concepts\n\nLesson 2 content.',
                    'order': 2,
                    'video_url': ''
                }
            ]
        }
        
        importer = CourseImporter(course_data, instructor_user, 'LESSON001')
        imported_course = importer.import_course()
        
        lessons = imported_course.lesson_set.all().order_by('order')
        assert len(lessons) == 2
        
        lesson1 = lessons[0]
        assert lesson1.title == 'Introduction'
        assert lesson1.order == 1
        assert lesson1.video_url == 'https://example.com/video1'
        assert not lesson1.is_published  # Import as unpublished
        
        lesson2 = lessons[1]
        assert lesson2.title == 'Advanced Topics'
        assert lesson2.order == 2
        assert lesson2.video_url == ''
    
    def test_import_course_with_assignments(self, instructor_user):
        """Test importing course with assignments"""
        future_date = (timezone.now() + timedelta(days=30)).isoformat()
        
        course_data = {
            'schema_version': '1.0',
            'course': {
                'title': 'Course with Assignments',
                'description': 'Course description',
                'duration_weeks': 4,
                'max_students': 30
            },
            'lessons': [],
            'assignments': [
                {
                    'title': 'Assignment 1',
                    'description': 'First assignment',
                    'instructions': 'Complete all tasks',
                    'due_date': future_date,
                    'max_points': 100,
                    'allow_file_submission': True,
                    'allow_text_submission': False
                }
            ]
        }
        
        importer = CourseImporter(course_data, instructor_user, 'ASSIGN001')
        imported_course = importer.import_course()
        
        assignments = imported_course.assignment_set.all()
        assert len(assignments) == 1
        
        assignment = assignments[0]
        assert assignment.title == 'Assignment 1'
        assert assignment.max_points == 100
        assert assignment.allow_file_submission is True
        assert assignment.allow_text_submission is False
        assert not assignment.is_published  # Import as unpublished
    
    def test_import_course_with_quizzes(self, instructor_user):
        """Test importing course with quizzes and questions"""
        course_data = {
            'schema_version': '1.0',
            'course': {
                'title': 'Course with Quizzes',
                'description': 'Course description',
                'duration_weeks': 4,
                'max_students': 30
            },
            'lessons': [],
            'quizzes': [
                {
                    'title': 'Quiz 1',
                    'description': 'First quiz',
                    'quiz_type': 'practice',
                    'time_limit': 30,
                    'max_attempts': 3,
                    'questions': [
                        {
                            'question_text': 'What is 2+2?',
                            'question_type': 'multiple_choice',
                            'points': 1,
                            'order': 1,
                            'explanation': 'Basic addition',
                            'answers': [
                                {'answer_text': '3', 'is_correct': False, 'order': 1},
                                {'answer_text': '4', 'is_correct': True, 'order': 2},
                                {'answer_text': '5', 'is_correct': False, 'order': 3}
                            ]
                        },
                        {
                            'question_text': 'Explain recursion',
                            'question_type': 'short_answer',
                            'points': 5,
                            'order': 2,
                            'explanation': 'Short answer question'
                        }
                    ]
                }
            ]
        }
        
        importer = CourseImporter(course_data, instructor_user, 'QUIZ001')
        imported_course = importer.import_course()
        
        quizzes = imported_course.quizzes.all()
        assert len(quizzes) == 1
        
        quiz = quizzes[0]
        assert quiz.title == 'Quiz 1'
        assert quiz.time_limit == 30
        assert quiz.max_attempts == 3
        assert not quiz.is_published  # Import as unpublished
        
        questions = quiz.questions.all().order_by('order')
        assert len(questions) == 2
        
        # Test multiple choice question
        mc_question = questions[0]
        assert mc_question.question_text == 'What is 2+2?'
        assert mc_question.question_type == 'multiple_choice'
        assert mc_question.points == 1
        
        answers = mc_question.answers.all().order_by('order')
        assert len(answers) == 3
        assert answers[1].answer_text == '4'
        assert answers[1].is_correct is True
        
        # Test short answer question
        sa_question = questions[1]
        assert sa_question.question_text == 'Explain recursion'
        assert sa_question.question_type == 'short_answer'
        assert sa_question.points == 5
    
    def test_import_course_with_announcements(self, instructor_user):
        """Test importing course with announcements"""
        course_data = {
            'schema_version': '1.0',
            'course': {
                'title': 'Course with Announcements',
                'description': 'Course description',
                'duration_weeks': 4,
                'max_students': 30
            },
            'lessons': [],
            'announcements': [
                {
                    'title': 'Welcome!',
                    'content': 'Welcome to the course!',
                    'priority': 'high',
                    'is_pinned': True
                },
                {
                    'title': 'Assignment Due',
                    'content': 'Don\'t forget the assignment',
                    'priority': 'normal',
                    'is_pinned': False
                }
            ]
        }
        
        importer = CourseImporter(course_data, instructor_user, 'ANNOUNCE001')
        imported_course = importer.import_course()
        
        announcements = imported_course.announcements.all()
        assert len(announcements) == 2
        
        welcome_announcement = announcements.filter(title='Welcome!').first()
        assert welcome_announcement is not None
        assert welcome_announcement.priority == 'high'
        assert welcome_announcement.is_pinned is True
        assert welcome_announcement.author == instructor_user
        assert not welcome_announcement.is_published  # Import as unpublished


# ================================
# EXPORT VIEW TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.import_export
@pytest.mark.views
class TestExportCourseView:
    """Test cases for export_course view"""
    
    def test_export_course_get_request(self, client, instructor_user, sample_course):
        """Test GET request to export course page"""
        client.force_login(instructor_user)
        url = reverse('export_course', kwargs={'course_id': sample_course.id})
        response = client.get(url)
        
        assert response.status_code == 200
        assert b'Export Course' in response.content
        assert sample_course.title.encode() in response.content
    
    def test_export_course_post_request(self, client, instructor_user, sample_course):
        """Test POST request to export course"""
        client.force_login(instructor_user)
        url = reverse('export_course', kwargs={'course_id': sample_course.id})
        
        response = client.post(url, {
            'include_user_data': 'off'
        })
        
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/zip'
        assert 'attachment' in response['Content-Disposition']
        assert sample_course.course_code in response['Content-Disposition']
    
    def test_export_course_unauthorized_access(self, client, student_user, sample_course):
        """Test unauthorized access to export course"""
        client.force_login(student_user)
        url = reverse('export_course', kwargs={'course_id': sample_course.id})
        response = client.get(url)
        
        # Should redirect or return 403 (depends on decorator implementation)
        assert response.status_code in [302, 403]
    
    def test_export_nonexistent_course(self, client, instructor_user):
        """Test exporting non-existent course"""
        client.force_login(instructor_user)
        url = reverse('export_course', kwargs={'course_id': 99999})
        response = client.get(url)
        
        assert response.status_code == 404
    
    def test_export_course_different_instructor(self, client, instructor_user, sample_course):
        """Test instructor cannot export another instructor's course"""
        # Create different instructor
        other_instructor = User.objects.create_user(
            username='other_instructor',
            password='pass123'
        )
        profile, created = UserProfile.objects.get_or_create(
            user=other_instructor, 
            defaults={'role': 'instructor'}
        )
        # Force the role to be instructor (in case it was created already)
        profile.role = 'instructor'
        profile.save()
        
        client.force_login(other_instructor)
        url = reverse('export_course', kwargs={'course_id': sample_course.id})
        response = client.get(url)
        
        assert response.status_code == 404  # Course not found for this instructor


# ================================
# IMPORT VIEW TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.import_export
@pytest.mark.views  
class TestImportCourseView:
    """Test cases for import_course view"""
    
    def test_import_course_get_request(self, client, instructor_user):
        """Test GET request to import course page"""
        client.force_login(instructor_user)
        url = reverse('import_course')
        response = client.get(url)
        
        assert response.status_code == 200
        assert b'Import Course' in response.content
    
    def test_import_course_valid_zip(self, client, instructor_user, sample_export_zip):
        """Test importing valid course ZIP file"""
        client.force_login(instructor_user)
        url = reverse('import_course')
        
        # Create uploaded file
        uploaded_file = SimpleUploadedFile(
            "test_course.zip",
            sample_export_zip,
            content_type="application/zip"
        )
        
        response = client.post(url, {
            'course_file': uploaded_file
        })
        
        assert response.status_code == 200
        assert b'preview' in response.content.lower()
        assert 'course_data' in response.context
    
    def test_import_course_invalid_file_type(self, client, instructor_user):
        """Test importing invalid file type"""
        client.force_login(instructor_user)
        url = reverse('import_course')
        
        # Create non-ZIP file
        uploaded_file = SimpleUploadedFile(
            "test_course.txt",
            b"This is not a ZIP file",
            content_type="text/plain"
        )
        
        response = client.post(url, {
            'course_file': uploaded_file
        })
        
        assert response.status_code == 200
        assert b'valid ZIP file' in response.content
    
    def test_import_course_missing_file(self, client, instructor_user):
        """Test importing without selecting a file"""
        client.force_login(instructor_user)
        url = reverse('import_course')
        
        response = client.post(url, {})
        
        assert response.status_code == 200
        assert b'select a course file' in response.content
    
    def test_import_course_invalid_zip_content(self, client, instructor_user):
        """Test importing ZIP without course_data.json"""
        client.force_login(instructor_user)
        url = reverse('import_course')
        
        # Create ZIP without course_data.json
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.writestr('some_file.txt', 'Invalid content')
        
        uploaded_file = SimpleUploadedFile(
            "invalid_course.zip",
            zip_buffer.getvalue(),
            content_type="application/zip"
        )
        
        response = client.post(url, {
            'course_file': uploaded_file
        })
        
        assert response.status_code == 200
        assert b'missing course_data.json' in response.content
    
    def test_import_course_unauthorized(self, client, student_user):
        """Test unauthorized access to import course"""
        client.force_login(student_user)
        url = reverse('import_course')
        response = client.get(url)
        
        # Should redirect or return 403 (depends on decorator implementation)
        assert response.status_code in [302, 403]


# ================================
# CONFIRM IMPORT TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.import_export
@pytest.mark.views
class TestConfirmImportView:
    """Test cases for confirm_import_course view"""
    
    def test_confirm_import_success(self, client, instructor_user):
        """Test successful course import confirmation"""
        client.force_login(instructor_user)
        
        # Set up session data
        session = client.session
        session['import_data'] = {
            'schema_version': '1.0',
            'course': {
                'title': 'Test Import Course',
                'description': 'Test description',
                'duration_weeks': 4,
                'max_students': 30
            },
            'lessons': []
        }
        session.save()
        
        url = reverse('confirm_import_course')
        response = client.post(url, {
            'course_code': 'TESTIMPORT001',
            'assign_to_me': 'on'
        })
        
        assert response.status_code == 302  # Redirect after success
        
        # Verify course was created
        imported_course = Course.objects.filter(course_code='TESTIMPORT001').first()
        assert imported_course is not None
        assert imported_course.title == 'Test Import Course'
        assert imported_course.instructor == instructor_user
    
    def test_confirm_import_duplicate_course_code(self, client, instructor_user, sample_course):
        """Test import with duplicate course code"""
        client.force_login(instructor_user)
        
        # Set up session data
        session = client.session
        session['import_data'] = {
            'schema_version': '1.0',
            'course': {
                'title': 'Duplicate Course',
                'description': 'Test description',
                'duration_weeks': 4,
                'max_students': 30
            },
            'lessons': []
        }
        session.save()
        
        url = reverse('confirm_import_course')
        response = client.post(url, {
            'course_code': sample_course.course_code,  # Duplicate code
            'assign_to_me': 'on'
        })
        
        assert response.status_code == 302  # Redirect back to import
        assert b'already exists' in client.get(reverse('import_course')).content
    
    def test_confirm_import_missing_session_data(self, client, instructor_user):
        """Test import confirmation without session data"""
        client.force_login(instructor_user)
        
        url = reverse('confirm_import_course')
        response = client.post(url, {
            'course_code': 'TESTCODE001',
            'assign_to_me': 'on'
        })
        
        assert response.status_code == 302  # Redirect back to import
    
    def test_confirm_import_missing_course_code(self, client, instructor_user):
        """Test import confirmation without course code"""
        client.force_login(instructor_user)
        
        # Set up session data
        session = client.session
        session['import_data'] = {
            'schema_version': '1.0',
            'course': {
                'title': 'Test Course',
                'description': 'Test description',
                'duration_weeks': 4,
                'max_students': 30
            },
            'lessons': []
        }
        session.save()
        
        url = reverse('confirm_import_course')
        response = client.post(url, {
            'assign_to_me': 'on'
            # Missing course_code
        })
        
        assert response.status_code == 302  # Redirect back to import


# ================================
# INTEGRATION TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.import_export
@pytest.mark.integration
class TestExportImportIntegration:
    """Integration tests for full export-import cycle"""
    
    def test_full_export_import_cycle(self, instructor_user, sample_course_with_content):
        """Test complete export-import cycle preserves data"""
        # Export course
        exporter = CourseExporter(sample_course_with_content, include_user_data=False)
        export_data = exporter.generate_export_data()
        
        # Import course with new code
        new_instructor = User.objects.create_user(
            username='new_instructor',
            email='new@example.com',
            password='pass123'
        )
        UserProfile.objects.get_or_create(
            user=new_instructor, 
            defaults={'role': 'instructor'}
        )
        
        importer = CourseImporter(export_data, new_instructor, 'IMPORTED001')
        imported_course = importer.import_course()
        
        # Verify course metadata
        assert imported_course.title == sample_course_with_content.title
        assert imported_course.description == sample_course_with_content.description
        assert imported_course.instructor == new_instructor
        assert imported_course.course_code == 'IMPORTED001'
        
        # Verify lessons count
        original_lessons = sample_course_with_content.lesson_set.count()
        imported_lessons = imported_course.lesson_set.count()
        assert imported_lessons == original_lessons
        
        # Verify assignments count
        original_assignments = sample_course_with_content.assignment_set.count()
        imported_assignments = imported_course.assignment_set.count()
        assert imported_assignments == original_assignments
        
        # Verify quizzes count
        original_quizzes = sample_course_with_content.quizzes.count()
        imported_quizzes = imported_course.quizzes.count()
        assert imported_quizzes == original_quizzes
    
    def test_export_import_preserves_quiz_structure(self, instructor_user, sample_quiz):
        """Test that quiz structure is preserved through export-import"""
        course = sample_quiz.course
        
        # Export course with quiz
        exporter = CourseExporter(course, include_user_data=False)
        export_data = exporter.generate_export_data()
        
        # Import course
        new_instructor = User.objects.create_user(
            username='quiz_instructor',
            email='quiz@example.com',
            password='pass123'
        )
        UserProfile.objects.get_or_create(
            user=new_instructor, 
            defaults={'role': 'instructor'}
        )
        
        importer = CourseImporter(export_data, new_instructor, 'QUIZIMPORT001')
        imported_course = importer.import_course()
        
        # Verify quiz structure
        imported_quiz = imported_course.quizzes.first()
        assert imported_quiz is not None
        assert imported_quiz.title == sample_quiz.title
        assert imported_quiz.time_limit == sample_quiz.time_limit
        
        # Verify questions
        original_questions = sample_quiz.questions.count()
        imported_questions = imported_quiz.questions.count()
        assert imported_questions == original_questions
        
        # Verify answers for first question
        original_question = sample_quiz.questions.first()
        imported_question = imported_quiz.questions.first()
        
        if original_question and imported_question:
            original_answers = original_question.answers.count()
            imported_answers = imported_question.answers.count()
            assert imported_answers == original_answers


# ================================
# ERROR HANDLING TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.import_export
@pytest.mark.error_handling
class TestImportExportErrorHandling:
    """Test error handling in import/export operations"""
    
    def test_export_with_missing_files(self, instructor_user, sample_course):
        """Test export handles missing attachment files gracefully"""
        # Create assignment with non-existent file reference
        assignment = Assignment.objects.create(
            course=sample_course,
            title='Test Assignment',
            description='Test description',
            due_date=timezone.now() + timedelta(days=7),
            max_points=100
        )
        
        # Mock file_attachment.path to non-existent file
        with patch.object(assignment, 'file_attachment') as mock_file:
            mock_file.name = 'nonexistent_file.pdf'
            mock_file.path = '/nonexistent/path/file.pdf'
            
            exporter = CourseExporter(sample_course, include_user_data=False)
            # Should not raise exception
            zip_data = exporter.create_zip_export()
            assert isinstance(zip_data, bytes)
    
    def test_import_with_invalid_json_structure(self, instructor_user):
        """Test import handles invalid JSON structure"""
        invalid_course_data = {
            'invalid_schema': True,
            'missing_required_fields': {}
        }
        
        importer = CourseImporter(invalid_course_data, instructor_user, 'INVALID001')
        
        with pytest.raises(KeyError):
            importer.import_course()
    
    def test_import_with_invalid_date_format(self, instructor_user):
        """Test import handles invalid date formats"""
        course_data = {
            'schema_version': '1.0',
            'course': {
                'title': 'Test Course',
                'description': 'Test description',
                'duration_weeks': 4,
                'max_students': 30
            },
            'lessons': [],
            'assignments': [
                {
                    'title': 'Test Assignment',
                    'description': 'Test description',
                    'due_date': 'invalid-date-format',  # Invalid date
                    'max_points': 100
                }
            ]
        }
        
        importer = CourseImporter(course_data, instructor_user, 'BADDATE001')
        
        with pytest.raises(ValueError):
            importer.import_course()


# ================================
# FIXTURES
# ================================

@pytest.fixture
def sample_export_zip(sample_course_with_content):
    """Create a sample export ZIP file for testing"""
    exporter = CourseExporter(sample_course_with_content, include_user_data=False)
    return exporter.create_zip_export()


@pytest.fixture
def sample_course_with_content(instructor_user):
    """Create a sample course with lessons, assignments, and quizzes"""
    course = Course.objects.create(
        title='Complete Sample Course',
        course_code='SAMPLE001',
        description='A course with all content types',
        instructor=instructor_user,
        status='published',
        duration_weeks=8,
        max_students=25
    )
    
    # Add lessons
    for i in range(3):
        Lesson.objects.create(
            course=course,
            title=f'Lesson {i+1}',
            content=f'This is the content for lesson {i+1}.',
            order=i+1,
            is_published=True
        )
    
    # Add assignments
    for i in range(2):
        Assignment.objects.create(
            course=course,
            title=f'Assignment {i+1}',
            description=f'Description for assignment {i+1}',
            due_date=timezone.now() + timedelta(days=7*(i+1)),
            max_points=100,
            is_published=True
        )
    
    # Add quiz with questions
    quiz = Quiz.objects.create(
        course=course,
        title='Sample Quiz',
        description='A sample quiz for testing',
        quiz_type='graded',
        time_limit=30,
        max_attempts=2,
        is_published=True
    )
    
    # Add multiple choice question
    question = Question.objects.create(
        quiz=quiz,
        question_text='What is the capital of France?',
        question_type='multiple_choice',
        points=1,
        order=1
    )
    
    # Add answers
    Answer.objects.create(question=question, answer_text='London', is_correct=False, order=1)
    Answer.objects.create(question=question, answer_text='Paris', is_correct=True, order=2)
    Answer.objects.create(question=question, answer_text='Berlin', is_correct=False, order=3)
    
    # Add announcement
    Announcement.objects.create(
        course=course,
        title='Welcome Announcement',
        content='Welcome to the course!',
        author=instructor_user,
        priority='normal',
        is_published=True
    )
    
    return course


@pytest.fixture
def sample_quiz(sample_course):
    """Create a sample quiz for testing"""
    quiz = Quiz.objects.create(
        course=sample_course,
        title='Test Quiz',
        description='A test quiz',
        quiz_type='practice',
        time_limit=15,
        max_attempts=3,
        is_published=True
    )
    
    # Add a question
    question = Question.objects.create(
        quiz=quiz,
        question_text='Test question?',
        question_type='multiple_choice',
        points=2,
        order=1
    )
    
    # Add answers
    Answer.objects.create(question=question, answer_text='Answer 1', is_correct=False, order=1)
    Answer.objects.create(question=question, answer_text='Answer 2', is_correct=True, order=2)
    
    return quiz