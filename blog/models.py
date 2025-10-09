from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import os


def course_material_upload_path(instance, filename):
    """Generate upload path for course materials"""
    return f'course_materials/{instance.course.course_code}/{filename}'


def assignment_upload_path(instance, filename):
    """Generate upload path for assignment files"""
    return f'assignments/{instance.course.course_code}/{filename}'


def submission_upload_path(instance, filename):
    """Generate upload path for assignment submissions"""
    return f'submissions/{instance.assignment.course.course_code}/{instance.assignment.id}/{instance.student.username}/{filename}'


# User Profile Models
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    bio = models.TextField(max_length=500, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"


# Course Management Models
class Course(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    course_code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Select an instructor for this course")
    created_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    duration_weeks = models.PositiveIntegerField(default=4)
    max_students = models.PositiveIntegerField(default=30)
    prerequisites = models.TextField(blank=True, help_text="Course requirements")
    
    def publish(self):
        self.published_date = timezone.now()
        self.status = 'published'
        self.save()
    
    def get_enrolled_count(self):
        return self.enrollment_set.filter(status='enrolled').count()
    
    def __str__(self):
        return f"{self.course_code} - {self.title}"


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('pending', 'Pending'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'userprofile__role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_date = models.DateTimeField(default=timezone.now)
    completion_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'course']
    
    def complete_course(self):
        self.completion_date = timezone.now()
        self.status = 'completed'
        self.save()
    
    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.course_code}"


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField(default=1)
    video_url = models.URLField(blank=True, help_text="YouTube or other video link")
    created_date = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.course_code} - Lesson {self.order}: {self.title}"


class CourseMaterial(models.Model):
    """File attachments for courses and lessons"""
    MATERIAL_TYPES = [
        ('pdf', 'PDF Document'),
        ('doc', 'Word Document'),
        ('ppt', 'Presentation'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('other', 'Other'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True, help_text="Optional: attach to specific lesson")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=course_material_upload_path)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES, default='other')
    uploaded_date = models.DateTimeField(default=timezone.now)
    is_required = models.BooleanField(default=False, help_text="Required for course completion")
    
    def __str__(self):
        return f"{self.course.course_code} - {self.title}"
    
    def get_file_size(self):
        """Return file size in MB"""
        if self.file:
            return round(self.file.size / (1024 * 1024), 2)
        return 0
    
    def get_file_extension(self):
        """Return file extension"""
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return ''


class Assignment(models.Model):
    """Course assignments that students can submit"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField(blank=True, help_text="Detailed assignment instructions")
    due_date = models.DateTimeField()
    max_points = models.PositiveIntegerField(default=100)
    file_attachment = models.FileField(upload_to=assignment_upload_path, blank=True, help_text="Optional assignment file")
    allow_file_submission = models.BooleanField(default=True)
    allow_text_submission = models.BooleanField(default=True)
    created_date = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['course', 'due_date']
    
    def __str__(self):
        return f"{self.course.course_code} - {self.title}"
    
    def is_overdue(self):
        """Check if assignment is past due date"""
        return timezone.now() > self.due_date
    
    def get_submission_count(self):
        """Get number of submissions"""
        return self.submission_set.count()


class Submission(models.Model):
    """Student submissions for assignments"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('returned', 'Returned'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'userprofile__role': 'student'})
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    text_submission = models.TextField(blank=True)
    file_submission = models.FileField(upload_to=submission_upload_path, blank=True)
    submitted_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'assignment']
    
    def submit(self):
        """Mark submission as submitted"""
        self.status = 'submitted'
        self.submitted_date = timezone.now()
        self.save()
    
    def is_late(self):
        """Check if submission was late"""
        if self.submitted_date and self.assignment.due_date:
            return self.submitted_date > self.assignment.due_date
        return False
    
    def __str__(self):
        return f"{self.student.username} - {self.assignment.title} ({self.status})"


class Progress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'userprofile__role': 'student'})
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'lesson']
    
    def mark_complete(self):
        self.completed = True
        self.completion_date = timezone.now()
        self.save()
    
    def __str__(self):
        status = "Completed" if self.completed else "In Progress"
        return f"{self.student.username} - {self.lesson.title} ({status})"


# Keep the original Post model for backward compatibility
class Post(models.Model):
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    text = models.TextField()
    create_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title


# Quiz System Models
class Quiz(models.Model):
    """Quiz model for assessments"""
    QUIZ_TYPES = [
        ('practice', 'Practice Quiz'),
        ('graded', 'Graded Quiz'),
        ('exam', 'Exam'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPES, default='practice')
    
    # Timing and attempts
    time_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Time limit in minutes")
    max_attempts = models.PositiveIntegerField(default=1, help_text="Maximum attempts allowed")
    
    # Availability
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)
    
    # Settings
    shuffle_questions = models.BooleanField(default=False)
    show_correct_answers = models.BooleanField(default=True, help_text="Show correct answers after completion")
    immediate_feedback = models.BooleanField(default=False, help_text="Show feedback immediately after each question")
    
    # Grading
    points = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Minimum percentage to pass")
    
    # Status
    is_published = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'title']
    
    def __str__(self):
        return f"{self.course.course_code} - {self.title}"
    
    @property
    def total_questions(self):
        return self.questions.count()
    
    @property
    def is_available(self):
        now = timezone.now()
        if self.available_from and now < self.available_from:
            return False
        if self.available_until and now > self.available_until:
            return False
        return True


class Question(models.Model):
    """Individual quiz question"""
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    points = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    order = models.PositiveIntegerField(default=0)
    
    # Optional explanation
    explanation = models.TextField(blank=True, help_text="Explanation shown after answering")
    
    created_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['quiz', 'order', 'id']
    
    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}: {self.question_text[:50]}..."


class Answer(models.Model):
    """Answer choices for multiple choice and true/false questions"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['question', 'order', 'id']
    
    def __str__(self):
        correct_indicator = "✓" if self.is_correct else "✗"
        return f"{correct_indicator} {self.answer_text}"


class QuizAttempt(models.Model):
    """Student's attempt at taking a quiz"""
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('timed_out', 'Timed Out'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    
    # Attempt info
    attempt_number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    
    # Timing
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken = models.DurationField(null=True, blank=True)
    
    # Scoring
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_points = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        unique_together = ['student', 'quiz', 'attempt_number']
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} (Attempt {self.attempt_number})"
    
    def complete_attempt(self):
        """Mark attempt as completed and calculate score"""
        if self.status == 'completed':
            return
        
        self.completed_at = timezone.now()
        self.time_taken = self.completed_at - self.started_at
        self.status = 'completed'
        
        # Calculate score
        responses = self.responses.all()
        total_score = sum(response.points_earned for response in responses)
        self.score = total_score
        self.total_points = sum(response.question.points for response in responses)
        
        if self.total_points > 0:
            self.percentage = (self.score / self.total_points) * 100
        else:
            self.percentage = 0
        
        self.save()
    
    @property
    def is_passed(self):
        if not self.quiz.passing_score or not self.percentage:
            return None
        return self.percentage >= self.quiz.passing_score


class QuizResponse(models.Model):
    """Student's response to a specific question"""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    
    # Response data
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)  # For MC/TF
    text_answer = models.TextField(blank=True)  # For short answer
    
    # Grading
    is_correct = models.BooleanField(null=True, blank=True)  # Auto-graded for MC/TF
    points_earned = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    feedback = models.TextField(blank=True)  # Manual feedback for short answers
    
    answered_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"{self.attempt.student.username} - {self.question.question_text[:30]}..."
    
    def auto_grade(self):
        """Auto-grade multiple choice and true/false questions"""
        if self.question.question_type in ['multiple_choice', 'true_false']:
            if self.selected_answer and self.selected_answer.is_correct:
                self.is_correct = True
                self.points_earned = self.question.points
            else:
                self.is_correct = False
                self.points_earned = 0
            self.save()


# Course Announcement Models - ACTIVATED
class Announcement(models.Model):
    #Course announcements from instructors to students
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Visibility settings
    is_published = models.BooleanField(default=True)
    is_pinned = models.BooleanField(default=False, help_text="Pinned announcements appear at the top")
    
    # Timestamps
    created_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(null=True, blank=True)
    
    # Optional scheduling
    scheduled_for = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Schedule announcement for future publication"
    )
    
    # Author tracking
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    
    class Meta:
        ordering = ['-is_pinned', '-created_date']
        
    def __str__(self):
        return f"{self.course.course_code}: {self.title}"
    
    def save(self, *args, **kwargs):
        # Set published_date when first published
        if self.is_published and not self.published_date:
            self.published_date = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def is_scheduled(self):
        #Check if announcement is scheduled for future publication
        return self.scheduled_for and self.scheduled_for > timezone.now()
    
    @property
    def should_be_visible(self):
        #Check if announcement should be visible to students
        if not self.is_published:
            return False
        if self.scheduled_for and self.scheduled_for > timezone.now():
            return False
        return True


class AnnouncementRead(models.Model):
    #Track which students have read which announcements
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE)
    read_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['student', 'announcement']
        
    def __str__(self):
        return f"{self.student.username} read {self.announcement.title}"

