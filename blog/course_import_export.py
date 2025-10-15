import json
import os
import zipfile
from datetime import datetime
from io import BytesIO
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth.models import User

from .models import (
    Course, Lesson, CourseMaterial, Assignment, Quiz, Question, Answer,
    Announcement, Enrollment, Progress, Submission, QuizAttempt, QuizResponse
)


def is_instructor(user):
    """Check if user is an instructor"""
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'instructor'


def is_admin(user):
    """Check if user is an admin"""
    return user.is_authenticated and (user.is_superuser or (hasattr(user, 'userprofile') and user.userprofile.role == 'admin'))


class CourseExporter:
    """Handle course export to JSON/ZIP format"""
    
    def __init__(self, course, include_user_data=False):
        self.course = course
        self.include_user_data = include_user_data
        self.export_data = {}
        self.files_to_include = []
    
    def export_course_metadata(self):
        """Export basic course information"""
        return {
            'title': self.course.title,
            'course_code': self.course.course_code,
            'description': self.course.description,
            'instructor_username': self.course.instructor.username,
            'instructor_email': self.course.instructor.email,
            'instructor_first_name': self.course.instructor.first_name,
            'instructor_last_name': self.course.instructor.last_name,
            'created_date': self.course.created_date.isoformat(),
            'published_date': self.course.published_date.isoformat() if self.course.published_date else None,
            'status': self.course.status,
            'duration_weeks': self.course.duration_weeks,
            'max_students': self.course.max_students,
            'prerequisites': self.course.prerequisites,
        }
    
    def export_lessons(self):
        """Export all course lessons"""
        lessons = []
        for lesson in self.course.lesson_set.all().order_by('order'):
            lessons.append({
                'title': lesson.title,
                'content': lesson.content,
                'order': lesson.order,
                'video_url': lesson.video_url,
                'created_date': lesson.created_date.isoformat(),
                'is_published': lesson.is_published,
            })
        return lessons
    
    def export_materials(self):
        """Export course materials with file references"""
        materials = []
        for material in self.course.coursematerial_set.all():
            material_data = {
                'title': material.title,
                'description': material.description,
                'material_type': material.material_type,
                'uploaded_date': material.uploaded_date.isoformat(),
                'is_required': material.is_required,
                'lesson_order': material.lesson.order if material.lesson else None,
                'file_name': os.path.basename(material.file.name) if material.file else None,
                'file_path': material.file.name if material.file else None,
            }
            
            # Add file to inclusion list if it exists
            if material.file and os.path.exists(material.file.path):
                self.files_to_include.append({
                    'source_path': material.file.path,
                    'archive_path': f'materials/{os.path.basename(material.file.name)}',
                    'material_title': material.title
                })
            
            materials.append(material_data)
        return materials
    
    def export_assignments(self):
        """Export course assignments"""
        assignments = []
        for assignment in self.course.assignment_set.all():
            assignment_data = {
                'title': assignment.title,
                'description': assignment.description,
                'instructions': assignment.instructions,
                'due_date': assignment.due_date.isoformat(),
                'max_points': assignment.max_points,
                'allow_file_submission': assignment.allow_file_submission,
                'allow_text_submission': assignment.allow_text_submission,
                'created_date': assignment.created_date.isoformat(),
                'is_published': assignment.is_published,
                'file_name': os.path.basename(assignment.file_attachment.name) if assignment.file_attachment else None,
                'file_path': assignment.file_attachment.name if assignment.file_attachment else None,
            }
            
            # Add attachment file to inclusion list if it exists
            if assignment.file_attachment and os.path.exists(assignment.file_attachment.path):
                self.files_to_include.append({
                    'source_path': assignment.file_attachment.path,
                    'archive_path': f'assignments/{os.path.basename(assignment.file_attachment.name)}',
                    'assignment_title': assignment.title
                })
            
            assignments.append(assignment_data)
        return assignments
    
    def export_quizzes(self):
        """Export course quizzes with questions and answers"""
        quizzes = []
        for quiz in self.course.quizzes.all():
            questions = []
            for question in quiz.questions.all().order_by('order'):
                question_data = {
                    'question_text': question.question_text,
                    'question_type': question.question_type,
                    'points': float(question.points),
                    'order': question.order,
                    'explanation': question.explanation,
                    'created_date': question.created_date.isoformat(),
                }
                
                # Export answers for multiple choice and true/false questions
                if question.question_type in ['multiple_choice', 'true_false']:
                    answers = []
                    for answer in question.answers.all().order_by('order'):
                        answers.append({
                            'answer_text': answer.answer_text,
                            'is_correct': answer.is_correct,
                            'order': answer.order,
                        })
                    question_data['answers'] = answers
                
                questions.append(question_data)
            
            quiz_data = {
                'title': quiz.title,
                'description': quiz.description,
                'quiz_type': quiz.quiz_type,
                'time_limit': quiz.time_limit,
                'max_attempts': quiz.max_attempts,
                'available_from': quiz.available_from.isoformat() if quiz.available_from else None,
                'available_until': quiz.available_until.isoformat() if quiz.available_until else None,
                'shuffle_questions': quiz.shuffle_questions,
                'show_correct_answers': quiz.show_correct_answers,
                'immediate_feedback': quiz.immediate_feedback,
                'points': float(quiz.points),
                'passing_score': float(quiz.passing_score) if quiz.passing_score else None,
                'is_published': quiz.is_published,
                'created_date': quiz.created_date.isoformat(),
                'questions': questions,
            }
            quizzes.append(quiz_data)
        return quizzes
    
    def export_announcements(self):
        """Export course announcements"""
        announcements = []
        for announcement in self.course.announcements.all():
            announcements.append({
                'title': announcement.title,
                'content': announcement.content,
                'priority': announcement.priority,
                'is_published': announcement.is_published,
                'is_pinned': announcement.is_pinned,
                'created_date': announcement.created_date.isoformat(),
                'published_date': announcement.published_date.isoformat() if announcement.published_date else None,
                'scheduled_for': announcement.scheduled_for.isoformat() if announcement.scheduled_for else None,
                'author_username': announcement.author.username,
            })
        return announcements
    
    def export_enrollment_data(self):
        """Export enrollment and progress data (only if include_user_data=True)"""
        if not self.include_user_data:
            return None
        
        enrollments = []
        for enrollment in self.course.enrollment_set.all():
            enrollment_data = {
                'student_username': enrollment.student.username,
                'student_email': enrollment.student.email,
                'enrollment_date': enrollment.enrollment_date.isoformat(),
                'completion_date': enrollment.completion_date.isoformat() if enrollment.completion_date else None,
                'status': enrollment.status,
                'grade': float(enrollment.grade) if enrollment.grade else None,
            }
            
            # Export student progress
            progress_data = []
            for lesson in self.course.lesson_set.all():
                try:
                    progress = Progress.objects.get(student=enrollment.student, lesson=lesson)
                    progress_data.append({
                        'lesson_order': lesson.order,
                        'completed': progress.completed,
                        'completion_date': progress.completion_date.isoformat() if progress.completion_date else None,
                    })
                except Progress.DoesNotExist:
                    pass
            
            enrollment_data['progress'] = progress_data
            enrollments.append(enrollment_data)
        
        return enrollments
    
    def generate_export_data(self):
        """Generate complete export data structure"""
        self.export_data = {
            'schema_version': '1.0',
            'export_date': datetime.now().isoformat(),
            'exported_by': 'System',
            'export_info': {
                'exported_at': datetime.now().isoformat(),
                'exported_by': 'System',
                'lms_version': '1.0',
                'export_format_version': '1.0',
                'include_user_data': self.include_user_data,
            },
            'course': self.export_course_metadata(),
            'lessons': self.export_lessons(),
            'materials': self.export_materials(),
            'assignments': self.export_assignments(),
            'quizzes': self.export_quizzes(),
            'announcements': self.export_announcements(),
        }
        
        # Add enrollment data if requested
        if self.include_user_data:
            self.export_data['enrollments'] = self.export_enrollment_data()
        
        return self.export_data
    
    def create_zip_export(self):
        """Create ZIP file with course data and files"""
        # Generate export data
        export_data = self.generate_export_data()
        
        # Create in-memory ZIP file
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add course data JSON
            course_json = json.dumps(export_data, indent=2, ensure_ascii=False)
            zip_file.writestr('course_data.json', course_json)
            
            # Add files
            for file_info in self.files_to_include:
                try:
                    zip_file.write(file_info['source_path'], file_info['archive_path'])
                except Exception as e:
                    # Log missing file but continue export
                    print(f"Warning: Could not include file {file_info['source_path']}: {e}")
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()


@user_passes_test(is_instructor)
def export_course(request, course_id):
    """Export a course to ZIP format"""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    if request.method == 'POST':
        include_user_data = request.POST.get('include_user_data') == 'on'
        
        try:
            # Create exporter and generate ZIP
            exporter = CourseExporter(course, include_user_data=include_user_data)
            zip_data = exporter.create_zip_export()
            
            # Create HTTP response with ZIP file
            response = HttpResponse(zip_data, content_type='application/zip')
            filename = f"{course.course_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            messages.success(request, f'Course "{course.title}" exported successfully!')
            return response
            
        except Exception as e:
            messages.error(request, f'Export failed: {str(e)}')
            return redirect('instructor_course_detail', course_id=course.id)
    
    # GET request - show export form
    context = {
        'course': course,
        'enrolled_count': course.get_enrolled_count(),
        'lesson_count': course.lesson_set.count(),
        'assignment_count': course.assignment_set.count(),
        'quiz_count': course.quizzes.count(),
        'material_count': course.coursematerial_set.count(),
        'announcement_count': course.announcements.count(),
    }
    
    return render(request, 'blog/export_course.html', context)


@user_passes_test(is_instructor)
def import_course(request):
    """Import a course from ZIP format"""
    if request.method == 'POST':
        uploaded_file = request.FILES.get('course_file')
        
        if not uploaded_file:
            messages.error(request, 'Please select a course file to import.')
            return render(request, 'blog/import_course.html')
        
        if not uploaded_file.name.endswith('.zip'):
            messages.error(request, 'Please upload a valid ZIP file.')
            return render(request, 'blog/import_course.html')
        
        try:
            # Extract and validate ZIP file
            with zipfile.ZipFile(uploaded_file, 'r') as zip_file:
                # Check for required files
                if 'course_data.json' not in zip_file.namelist():
                    messages.error(request, 'Invalid course file: missing course_data.json')
                    return render(request, 'blog/import_course.html')
                
                # Load course data
                course_json = zip_file.read('course_data.json').decode('utf-8')
                course_data = json.loads(course_json)
                
                # Validate course data structure
                if not all(key in course_data for key in ['course', 'lessons']):
                    messages.error(request, 'Invalid course file: missing required data')
                    return render(request, 'blog/import_course.html')
                
                # Show import preview
                context = {
                    'course_data': course_data,
                    'preview': True,
                    'zip_file_name': uploaded_file.name,
                    'file_list': [f for f in zip_file.namelist() if f != 'course_data.json'],
                }
                
                # Store uploaded file temporarily (in session or temp file)
                request.session['import_file_name'] = uploaded_file.name
                request.session['import_data'] = course_data
                
                return render(request, 'blog/import_course.html', context)
                
        except Exception as e:
            messages.error(request, f'Error reading course file: {str(e)}')
            return render(request, 'blog/import_course.html')
    
    return render(request, 'blog/import_course.html')


@user_passes_test(is_instructor)
@require_POST
def confirm_import_course(request):
    """Confirm and execute course import"""
    course_data = request.session.get('import_data')
    
    if not course_data:
        messages.error(request, 'No import data found. Please start import process again.')
        return redirect('import_course')
    
    new_course_code = request.POST.get('course_code', '').strip()
    assign_to_me = request.POST.get('assign_to_me') == 'on'
    
    if not new_course_code:
        messages.error(request, 'Course code is required.')
        return redirect('import_course')
    
    # Check for course code conflicts
    if Course.objects.filter(course_code=new_course_code).exists():
        messages.error(request, f'Course code "{new_course_code}" already exists.')
        return redirect('import_course')
    
    try:
        with transaction.atomic():
            # Import course using CourseImporter
            importer = CourseImporter(course_data, request.user, new_course_code)
            imported_course = importer.import_course()
            
            # Clear session data
            if 'import_data' in request.session:
                del request.session['import_data']
            if 'import_file_name' in request.session:
                del request.session['import_file_name']
            
            messages.success(request, f'Course "{imported_course.title}" imported successfully!')
            return redirect('instructor_course_detail', course_id=imported_course.id)
            
    except Exception as e:
        messages.error(request, f'Import failed: {str(e)}')
        return redirect('import_course')


class CourseImporter:
    """Handle course import from exported data"""
    
    def __init__(self, course_data, instructor, new_course_code):
        self.course_data = course_data
        self.instructor = instructor
        self.new_course_code = new_course_code
        self.course = None
    
    def import_course(self):
        """Import complete course from data"""
        # Create course
        course_info = self.course_data['course']
        self.course = Course.objects.create(
            title=course_info['title'],
            course_code=self.new_course_code,
            description=course_info['description'],
            instructor=self.instructor,
            status='draft',  # Always import as draft
            duration_weeks=course_info.get('duration_weeks', 4),
            max_students=course_info.get('max_students', 30),
            prerequisites=course_info.get('prerequisites', ''),
        )
        
        # Import lessons
        self.import_lessons()
        
        # Import assignments
        if 'assignments' in self.course_data:
            self.import_assignments()
        
        # Import quizzes
        if 'quizzes' in self.course_data:
            self.import_quizzes()
        
        # Import announcements
        if 'announcements' in self.course_data:
            self.import_announcements()
        
        # Note: Materials would require file handling which we'll skip for now
        # import_materials() would go here
        
        return self.course
    
    def import_lessons(self):
        """Import course lessons"""
        for lesson_data in self.course_data.get('lessons', []):
            Lesson.objects.create(
                course=self.course,
                title=lesson_data['title'],
                content=lesson_data['content'],
                order=lesson_data['order'],
                video_url=lesson_data.get('video_url', ''),
                is_published=False,  # Import as unpublished for review
            )
    
    def import_assignments(self):
        """Import course assignments"""
        for assignment_data in self.course_data.get('assignments', []):
            Assignment.objects.create(
                course=self.course,
                title=assignment_data['title'],
                description=assignment_data['description'],
                instructions=assignment_data.get('instructions', ''),
                due_date=datetime.fromisoformat(assignment_data['due_date'].replace('Z', '+00:00')),
                max_points=assignment_data.get('max_points', 100),
                allow_file_submission=assignment_data.get('allow_file_submission', True),
                allow_text_submission=assignment_data.get('allow_text_submission', True),
                is_published=False,  # Import as unpublished for review
            )
    
    def import_quizzes(self):
        """Import course quizzes with questions and answers"""
        for quiz_data in self.course_data.get('quizzes', []):
            # Create quiz
            quiz = Quiz.objects.create(
                course=self.course,
                title=quiz_data['title'],
                description=quiz_data.get('description', ''),
                quiz_type=quiz_data.get('quiz_type', 'practice'),
                time_limit=quiz_data.get('time_limit'),
                max_attempts=quiz_data.get('max_attempts', 1),
                shuffle_questions=quiz_data.get('shuffle_questions', False),
                show_correct_answers=quiz_data.get('show_correct_answers', True),
                immediate_feedback=quiz_data.get('immediate_feedback', False),
                points=quiz_data.get('points', 0),
                passing_score=quiz_data.get('passing_score'),
                is_published=False,  # Import as unpublished for review
            )
            
            # Import questions
            for question_data in quiz_data.get('questions', []):
                question = Question.objects.create(
                    quiz=quiz,
                    question_text=question_data['question_text'],
                    question_type=question_data['question_type'],
                    points=question_data.get('points', 1),
                    order=question_data.get('order', 0),
                    explanation=question_data.get('explanation', ''),
                )
                
                # Import answers for multiple choice and true/false questions
                if question_data.get('answers'):
                    for answer_data in question_data['answers']:
                        Answer.objects.create(
                            question=question,
                            answer_text=answer_data['answer_text'],
                            is_correct=answer_data['is_correct'],
                            order=answer_data.get('order', 0),
                        )
    
    def import_announcements(self):
        """Import course announcements"""
        for announcement_data in self.course_data.get('announcements', []):
            Announcement.objects.create(
                course=self.course,
                title=announcement_data['title'],
                content=announcement_data['content'],
                priority=announcement_data.get('priority', 'normal'),
                is_published=False,  # Import as unpublished for review
                is_pinned=announcement_data.get('is_pinned', False),
                author=self.instructor,
            )