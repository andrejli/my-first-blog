from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from .validators import validate_assignment_file
from .utils.storage import MediaStorage
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


# Site Configuration Models
class SiteTheme(models.Model):
    THEME_CHOICES = [
        ('terminal-amber', 'Terminal Amber'),
        ('dark-blue', 'Dark Blue'),
        ('light', 'Light'),
        ('cyberpunk', 'Cyberpunk'),
        ('matrix', 'Matrix'),
    ]
    
    name = models.CharField(max_length=50, unique=True, help_text="Theme identifier")
    display_name = models.CharField(max_length=100, help_text="Human-readable theme name")
    theme_key = models.CharField(max_length=20, choices=THEME_CHOICES, unique=True)
    is_default = models.BooleanField(default=False, help_text="Set as default theme for new users")
    is_active = models.BooleanField(default=True, help_text="Theme is available for selection")
    description = models.TextField(blank=True, help_text="Theme description")
    created_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Site Theme"
        verbose_name_plural = "Site Themes"
    
    def __str__(self):
        default_text = " (Default)" if self.is_default else ""
        return f"{self.display_name}{default_text}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default theme
        if self.is_default:
            SiteTheme.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class UserThemePreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='theme_preference')
    theme = models.ForeignKey(SiteTheme, on_delete=models.CASCADE, limit_choices_to={'is_active': True})
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Theme Preference"
        verbose_name_plural = "User Theme Preferences"
    
    def __str__(self):
        return f"{self.user.username} - {self.theme.display_name}"


# Course Management Models
class Course(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200, db_index=True)
    course_code = models.CharField(max_length=20, unique=True, db_index=True)
    description = models.TextField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True, help_text="Select an instructor for this course")
    created_date = models.DateTimeField(default=timezone.now, db_index=True)
    published_date = models.DateTimeField(blank=True, null=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    duration_weeks = models.PositiveIntegerField(default=4)
    max_students = models.PositiveIntegerField(default=30)
    prerequisites = models.TextField(blank=True, help_text="Course requirements")
    
    class Meta:
        ordering = ['-created_date', 'title']
        indexes = [
            models.Index(fields=['status', 'published_date']),
            models.Index(fields=['instructor', 'status']),
            models.Index(fields=['created_date', 'status']),
        ]
    
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
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True, limit_choices_to={'userprofile__role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, db_index=True)
    enrollment_date = models.DateTimeField(default=timezone.now, db_index=True)
    completion_date = models.DateTimeField(null=True, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled', db_index=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enrollment_date']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
            models.Index(fields=['enrollment_date', 'status']),
        ]
    
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
    file = models.FileField(
        upload_to=course_material_upload_path,
        validators=[validate_assignment_file],
        help_text="Educational materials: documents, source code, images, videos. Max 50MB."
    )
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
    course = models.ForeignKey(Course, on_delete=models.CASCADE, db_index=True)
    title = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    instructions = models.TextField(blank=True, help_text="Detailed assignment instructions")
    due_date = models.DateTimeField(db_index=True)
    max_points = models.PositiveIntegerField(default=100)
    file_attachment = models.FileField(
        upload_to=assignment_upload_path, 
        blank=True, 
        validators=[validate_assignment_file],
        help_text="Optional assignment file (instructions, templates, etc.)"
    )
    allow_file_submission = models.BooleanField(default=True)
    allow_text_submission = models.BooleanField(default=True)
    created_date = models.DateTimeField(default=timezone.now, db_index=True)
    is_published = models.BooleanField(default=False, db_index=True)
    
    class Meta:
        ordering = ['course', 'due_date']
        indexes = [
            models.Index(fields=['course', 'is_published']),
            models.Index(fields=['due_date', 'is_published']),
            models.Index(fields=['created_date', 'course']),
        ]
    
    def __str__(self):
        return f"{self.course.course_code} - {self.title}"
    
    @property
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
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True, limit_choices_to={'userprofile__role': 'student'})
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, db_index=True)
    text_submission = models.TextField(blank=True)
    file_submission = models.FileField(
        upload_to=submission_upload_path, 
        blank=True,
        validators=[validate_assignment_file],
        help_text="Allowed: Source code (.py, .go, .rs, .js, .java, .cpp), documents (.pdf, .txt, .md), images, archives (.zip). Max 50MB."
    )
    submitted_date = models.DateTimeField(null=True, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_date = models.DateTimeField(null=True, blank=True, db_index=True)
    
    class Meta:
        unique_together = ['student', 'assignment']
        ordering = ['-submitted_date', '-graded_date']
        indexes = [
            models.Index(fields=['assignment', 'status']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['submitted_date', 'status']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(grade__gte=0) | models.Q(grade__isnull=True),
                name='non_negative_grade'
            ),
        ]
    
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
        return f"{self.quiz.course.course_code} - {self.quiz.title} - Q{self.order}: {self.question_text[:50]}..."


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
        indexes = [
            models.Index(fields=['student', 'quiz']),
            models.Index(fields=['quiz', 'status']),
            models.Index(fields=['started_at', 'status']),
            models.Index(fields=['student', 'status']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(attempt_number__gte=1),
                name='positive_attempt_number'
            ),
            models.CheckConstraint(
                condition=models.Q(score__gte=0) | models.Q(score__isnull=True),
                name='non_negative_score'
            ),
            models.CheckConstraint(
                condition=models.Q(percentage__gte=0, percentage__lte=100) | models.Q(percentage__isnull=True),
                name='valid_percentage_range'
            ),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} (Attempt {self.attempt_number}) - {self.status}"
    
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


# ================================
# DISCUSSION FORUM MODELS - Phase 4 Point 2
# ================================

class Forum(models.Model):
    """
    Forum categories for organizing discussions
    """
    FORUM_TYPES = [
        ('general', 'General Forum'),
        ('course', 'Course Forum'),
        ('instructor', 'Instructor Forum'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    forum_type = models.CharField(max_length=20, choices=FORUM_TYPES, default='general')
    course = models.OneToOneField(Course, on_delete=models.CASCADE, null=True, blank=True, 
                                  help_text="Leave blank for general forum")
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['forum_type', 'title']
    
    def __str__(self):
        if self.course:
            return f"{self.course.course_code} - {self.title}"
        return self.title
    
    def can_view(self, user):
        """Check if user can view this forum"""
        if not user.is_authenticated:
            return False
            
        if self.forum_type == 'general':
            return hasattr(user, 'userprofile') and user.userprofile.role in ['student', 'instructor']
        elif self.forum_type == 'course' and self.course:
            # Students must be enrolled, instructors must be course instructor
            if hasattr(user, 'userprofile'):
                if user.userprofile.role == 'instructor' and self.course.instructor == user:
                    return True
                elif user.userprofile.role == 'student':
                    return Enrollment.objects.filter(student=user, course=self.course, status='enrolled').exists()
        elif self.forum_type == 'instructor':
            return hasattr(user, 'userprofile') and user.userprofile.role == 'instructor'
        
        return False
    
    def can_post(self, user):
        """Check if user can create topics in this forum"""
        return self.can_view(user)


class Topic(models.Model):
    """
    Discussion topics within forums
    """
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_topics')
    created_date = models.DateTimeField(default=timezone.now)
    is_pinned = models.BooleanField(default=False, help_text="Pinned topics appear at the top")
    is_locked = models.BooleanField(default=False, help_text="Locked topics cannot receive new posts")
    last_post_date = models.DateTimeField(default=timezone.now)
    last_post_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='last_posts')
    
    class Meta:
        ordering = ['-is_pinned', '-last_post_date']
    
    def __str__(self):
        return f"{self.forum.title} - {self.title}"
    
    def post_count(self):
        """Return total number of posts in this topic"""
        return self.posts.count()
    
    def can_view(self, user):
        """Check if user can view this topic"""
        return self.forum.can_view(user)
    
    def can_reply(self, user):
        """Check if user can reply to this topic"""
        if self.is_locked:
            return False
        return self.forum.can_post(user)


class ForumPost(models.Model):
    """
    Individual posts within topics
    """
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    content = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    edited_date = models.DateTimeField(null=True, blank=True)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_posts')
    is_first_post = models.BooleanField(default=False, help_text="True if this is the first post in the topic")
    
    class Meta:
        ordering = ['created_date']
    
    def __str__(self):
        return f"{self.topic.title} - Post by {self.author.username}"
    
    def can_edit(self, user):
        """Check if user can edit this post"""
        if not user.is_authenticated:
            return False
        
        # Authors can edit their own posts
        if self.author == user:
            return True
        
        # Instructors can edit posts in their course forums
        if hasattr(user, 'userprofile') and user.userprofile.role == 'instructor':
            if self.topic.forum.forum_type == 'course' and self.topic.forum.course:
                return self.topic.forum.course.instructor == user
        
        return False
    
    def can_delete(self, user):
        """Check if user can delete this post"""
        return self.can_edit(user)
    
    def save(self, *args, **kwargs):
        """Update topic's last post info when saving"""
        super().save(*args, **kwargs)
        self.topic.last_post_date = self.created_date
        self.topic.last_post_by = self.author
        self.topic.save(update_fields=['last_post_date', 'last_post_by'])


# Individual User Blog Models
class BlogPost(models.Model):
    """Individual blog posts by users - separate from courses"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    # Core fields
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField(help_text="Supports Obsidian markdown: [[links]], callouts, math equations")
    excerpt = models.TextField(max_length=300, blank=True, help_text="Brief description of the post")
    
    # Publication settings
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    featured_image = models.ImageField(
        upload_to='blog_images/', 
        blank=True, 
        null=True,
        storage=MediaStorage(),
        help_text="Blog featured image (EXIF metadata will be automatically removed for privacy)"
    )
    
    # Metadata
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    published_date = models.DateTimeField(null=True, blank=True)
    
    # Settings
    allow_comments = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-published_date', '-created_date']
        indexes = [
            models.Index(fields=['-published_date']),
            models.Index(fields=['author', '-published_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.author.get_full_name() or self.author.username}"
    
    def save(self, *args, **kwargs):
        """Set published_date when status changes to published"""
        if self.status == 'published' and not self.published_date:
            self.published_date = timezone.now()
        elif self.status != 'published':
            self.published_date = None
        
        # Generate slug if not provided
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Return URL for this blog post"""
        return f"/user/{self.author.username}/blog/{self.slug}/"
    
    def get_comment_count(self):
        """Return number of approved comments"""
        return self.comments.filter(is_approved=True).count()
    
    def is_published(self):
        """Check if post is published"""
        return self.status == 'published' and self.published_date is not None
    
    def can_edit(self, user):
        """Check if user can edit this post"""
        return user == self.author or (hasattr(user, 'userprofile') and user.userprofile.role == 'admin')
    
    def increment_view_count(self):
        """Increment view count (thread-safe)"""
        BlogPost.objects.filter(pk=self.pk).update(view_count=models.F('view_count') + 1)


class BlogComment(models.Model):
    """Comments on blog posts with moderation"""
    
    # Relationships
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Content
    content = models.TextField(max_length=1000, help_text="Share your thoughts on this blog post")
    
    # Moderation
    is_approved = models.BooleanField(default=True, help_text="Approved comments are visible to all users")
    is_flagged = models.BooleanField(default=False, help_text="Flagged comments require admin review")
    
    # Metadata
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_date']
        indexes = [
            models.Index(fields=['post', 'created_date']),
            models.Index(fields=['author', 'created_date']),
            models.Index(fields=['is_approved']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.get_full_name() or self.author.username} on {self.post.title}"
    
    def can_edit(self, user):
        """Check if user can edit this comment"""
        # Author can edit within 30 minutes of posting
        if user == self.author:
            time_limit = timezone.now() - timezone.timedelta(minutes=30)
            return self.created_date > time_limit
        
        # Admin can always edit
        return hasattr(user, 'userprofile') and user.userprofile.role == 'admin'
    
    def can_delete(self, user):
        """Check if user can delete this comment"""
        # Author can delete their own comments
        if user == self.author:
            return True
        
        # Blog post author can delete comments on their posts
        if user == self.post.author:
            return True
        
        # Admin can delete any comment
        return hasattr(user, 'userprofile') and user.userprofile.role == 'admin'
    
    def get_reply_count(self):
        """Return number of approved replies"""
        return self.replies.filter(is_approved=True).count()
    
    def is_reply(self):
        """Check if this is a reply to another comment"""
        return self.parent is not None


# Calendar Event Models
class EventType(models.Model):
    """Customizable event types with colors"""
    name = models.CharField(max_length=50, unique=True, help_text="Event type name")
    slug = models.SlugField(max_length=50, unique=True, help_text="URL-friendly identifier")
    color = models.CharField(max_length=7, default='#32cd32', help_text="Hex color code (e.g., #32cd32)")
    background_color = models.CharField(max_length=7, default='#0f1419', help_text="Background hex color")
    icon = models.CharField(max_length=50, default='fas fa-calendar', help_text="FontAwesome icon class")
    description = models.TextField(blank=True, help_text="Description of this event type")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0, help_text="Display order")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'name']
        
    def __str__(self):
        return self.name
    
    def get_css_variables(self):
        """Generate CSS custom properties for this event type"""
        return {
            f'--event-{self.slug}-color': self.color,
            f'--event-{self.slug}-bg': self.background_color,
        }


class Event(models.Model):
    """Calendar events for the LMS homepage"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Legacy event type choices - kept for migration compatibility
    EVENT_TYPE_CHOICES = [
        ('general', 'General'),
        ('deadline', 'Assignment Deadline'),
        ('exam', 'Exam'),
        ('holiday', 'Holiday'),
        ('maintenance', 'System Maintenance'),
        ('meeting', 'Meeting'),
        ('workshop', 'Workshop'),
        ('announcement', 'Announcement'),
    ]
    
    VISIBILITY_CHOICES = [
        ('public', 'Public - Visible to everyone'),
        ('registered', 'Registered Users Only - Login required'),
    ]

    title = models.CharField(max_length=128, help_text="Event name (max 128 characters)")
    description = models.TextField(blank=True)
    
    # New customizable event type system
    event_type_new = models.ForeignKey(EventType, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='events', help_text="Customizable event type")
    # Legacy event type field - kept for backward compatibility
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='general',
                                 help_text="Legacy event type (use event_type_new for custom types)")
    
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    visibility = models.CharField(max_length=15, choices=VISIBILITY_CHOICES, default='registered',
                                 help_text="Who can view this event")
    
    # Custom colors (overrides event type colors if set)
    custom_color = models.CharField(max_length=7, blank=True, help_text="Custom hex color (overrides event type)")
    custom_background = models.CharField(max_length=7, blank=True, help_text="Custom background color")
    
    # Date and time
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)
    
    # Recurring Event Fields
    is_recurring = models.BooleanField(default=False, help_text="Create recurring events")
    recurrence_pattern = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly (Every 2 weeks)'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom Pattern'),
    ], blank=True, help_text="How often should this event repeat?")
    
    recurrence_interval = models.PositiveIntegerField(default=1, 
        help_text="Repeat every N intervals (e.g., every 2 weeks)")
    
    # Days of the week for weekly/biweekly patterns (stored as comma-separated)
    # Format: "mon,wed,fri" or "1,3,5" (1=Monday, 7=Sunday)
    recurrence_days = models.CharField(max_length=50, blank=True,
        help_text="Days of week for recurring events (mon,tue,wed,thu,fri,sat,sun)")
    
    # End conditions for recurring events
    recurrence_end_date = models.DateTimeField(null=True, blank=True,
        help_text="When should recurring events stop?")
    max_occurrences = models.PositiveIntegerField(null=True, blank=True,
        help_text="Maximum number of occurrences (alternative to end date)")
    
    # Recurring event management
    parent_event = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='recurring_instances', help_text="Parent event for recurring series")
    occurrence_date = models.DateField(null=True, blank=True, 
        help_text="Original date for this occurrence (for modified instances)")
    
    # Academic calendar integration
    exclude_holidays = models.BooleanField(default=True,
        help_text="Skip events that fall on holidays")
    exclude_weekends = models.BooleanField(default=False,
        help_text="Skip weekend occurrences (for daily patterns)")
    
    # Visibility and permissions
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Show on homepage")
    
    # Relations
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, 
                              help_text="Link to specific course (optional)")
    
    # Lesson linking with Obsidian-style syntax
    linked_lesson = models.ForeignKey('Lesson', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='linked_events', help_text="Direct lesson link")
    obsidian_link = models.CharField(max_length=255, blank=True,
                                    help_text="Obsidian-style link: [[Course Name - Lesson Title]] or lesson URL")
    
    # File uploads for posters and materials (admin only)
    poster = models.ImageField(
        upload_to='event_posters/', 
        null=True, 
        blank=True,
        storage=MediaStorage(),
        help_text="Event poster image (JPG, PNG) - EXIF metadata will be automatically removed for privacy"
    )
    materials = models.FileField(upload_to='event_materials/', null=True, blank=True,
                                help_text="Event materials (PDF, DOC, etc.)")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_date', 'title']
        indexes = [
            models.Index(fields=['start_date', 'is_published']),
            models.Index(fields=['event_type', 'priority']),
            models.Index(fields=['is_featured', 'start_date']),
            models.Index(fields=['course', 'start_date']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.start_date.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_upcoming(self):
        """Check if event is in the future"""
        from django.utils import timezone
        return self.start_date > timezone.now()
    
    @property
    def is_today(self):
        """Check if event is today"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date.date() == today
    
    @property
    def is_ongoing(self):
        """Check if event is currently happening"""
        from django.utils import timezone
        now = timezone.now()
        if self.end_date:
            return self.start_date <= now <= self.end_date
        return self.is_today
    
    def get_duration(self):
        """Get event duration in a human-readable format"""
        if not self.end_date:
            return "No end time specified"
        
        delta = self.end_date - self.start_date
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days} day{'s' if days > 1 else ''}"
        elif hours > 0:
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        else:
            return f"{minutes}m"
    
    @property
    def has_poster(self):
        """Check if event has a poster uploaded"""
        return bool(self.poster and self.poster.name)
    
    @property
    def has_materials(self):
        """Check if event has materials uploaded"""
        return bool(self.materials and self.materials.name)
    
    @property
    def get_poster_url(self):
        """Get poster URL if exists"""
        return self.poster.url if self.has_poster else None
    
    @property
    def get_materials_url(self):
        """Get materials URL if exists"""
        return self.materials.url if self.has_materials else None
    
    def get_display_color(self):
        """Get the display color for this event (custom or event type)"""
        if self.custom_color:
            return self.custom_color
        elif self.event_type_new:
            return self.event_type_new.color
        else:
            # Fallback to legacy color mapping
            color_map = {
                'general': '#007bff',      # Blue
                'deadline': '#dc3545',     # Red
                'exam': '#fd7e14',         # Orange
                'holiday': '#28a745',      # Green
                'maintenance': '#6c757d',  # Gray
                'meeting': '#17a2b8',      # Cyan
                'workshop': '#6f42c1',     # Purple
                'announcement': '#20c997',  # Teal
            }
            return color_map.get(self.event_type, '#32cd32')  # Default terminal green
    
    def get_display_background(self):
        """Get the background color for this event"""
        if self.custom_background:
            return self.custom_background
        elif self.event_type_new:
            return self.event_type_new.background_color
        else:
            return '#0f1419'  # Default dark background
    
    def get_display_name(self):
        """Get the display name for the event type"""
        if self.event_type_new:
            return self.event_type_new.name
        else:
            return dict(self.EVENT_TYPE_CHOICES).get(self.event_type, 'General')
    
    def get_display_icon(self):
        """Get the icon for this event type"""
        if self.event_type_new:
            return self.event_type_new.icon
        else:
            # Fallback icon mapping
            icon_map = {
                'general': 'fas fa-calendar',
                'deadline': 'fas fa-exclamation-triangle',
                'exam': 'fas fa-graduation-cap',
                'holiday': 'fas fa-gift',
                'maintenance': 'fas fa-tools',
                'meeting': 'fas fa-users',
                'workshop': 'fas fa-laptop-code',
                'announcement': 'fas fa-bullhorn',
            }
            return icon_map.get(self.event_type, 'fas fa-calendar')
    
    def get_css_style(self):
        """Generate CSS style string for this event"""
        color = self.get_display_color()
        background = self.get_display_background()
        return f"color: {color}; background-color: {background}; border-color: {color};"
    
    def parse_obsidian_link(self):
        """Parse Obsidian-style link to find matching lesson"""
        if not self.obsidian_link:
            return None
            
        link = self.obsidian_link.strip()
        
        # Handle Obsidian-style [[Course Name - Lesson Title]] format
        if link.startswith('[[') and link.endswith(']]'):
            content = link[2:-2].strip()  # Remove [[ ]]
            
            # Try to split by ' - ' to separate course and lesson
            if ' - ' in content:
                course_name, lesson_title = content.split(' - ', 1)
                course_name = course_name.strip()
                lesson_title = lesson_title.strip()
                
                try:
                    # Find course by title (case-insensitive)
                    course = Course.objects.filter(title__icontains=course_name).first()
                    if course:
                        # Find lesson in that course (case-insensitive)
                        lesson = Lesson.objects.filter(
                            course=course, 
                            title__icontains=lesson_title
                        ).first()
                        return lesson
                except Exception:
                    pass
            else:
                # Just lesson title, search across all courses
                try:
                    lesson = Lesson.objects.filter(title__icontains=content).first()
                    return lesson
                except Exception:
                    pass
        
        # Handle direct lesson title (without brackets)
        elif link:
            try:
                lesson = Lesson.objects.filter(title__icontains=link).first()
                return lesson
            except Exception:
                pass
        
        return None
    
    def get_linked_lesson(self):
        """Get the linked lesson (direct or via Obsidian link)"""
        if self.linked_lesson:
            return self.linked_lesson
        return self.parse_obsidian_link()
    
    def get_lesson_url(self):
        """Get URL to the linked lesson"""
        lesson = self.get_linked_lesson()
        if lesson:
            from django.urls import reverse
            return reverse('lesson_detail', kwargs={
                'course_id': lesson.course.id,
                'lesson_id': lesson.id
            })
        return None
    
    def get_lesson_display(self):
        """Get display text for the linked lesson"""
        lesson = self.get_linked_lesson()
        if lesson:
            return f"{lesson.course.title} - {lesson.title}"
        elif self.obsidian_link:
            return self.obsidian_link.replace('[[', '').replace(']]', '')
        return None
    
    @property
    def has_lesson_link(self):
        """Check if event has a lesson link"""
        return bool(self.linked_lesson or self.obsidian_link)
    
    # ==========================================
    # RECURRING EVENTS METHODS
    # ==========================================
    
    @property
    def is_recurring_parent(self):
        """Check if this is the parent event of a recurring series"""
        return self.is_recurring and self.parent_event is None
    
    @property
    def is_recurring_instance(self):
        """Check if this is an instance of a recurring series"""
        return self.parent_event is not None
    
    def get_recurrence_days_list(self):
        """Convert recurrence_days string to list of day names"""
        if not self.recurrence_days:
            return []
        
        day_map = {
            'mon': 'Monday', 'tue': 'Tuesday', 'wed': 'Wednesday',
            'thu': 'Thursday', 'fri': 'Friday', 'sat': 'Saturday', 'sun': 'Sunday',
            '1': 'Monday', '2': 'Tuesday', '3': 'Wednesday',
            '4': 'Thursday', '5': 'Friday', '6': 'Saturday', '7': 'Sunday'
        }
        
        days = []
        for day in self.recurrence_days.split(','):
            day = day.strip().lower()
            if day in day_map:
                days.append(day_map[day])
        return days
    
    def get_next_occurrence_date(self, from_date=None):
        """Calculate the next occurrence date based on recurrence pattern"""
        from datetime import timedelta
        import calendar
        
        if not self.is_recurring:
            return None
        
        if from_date is None:
            from_date = self.start_date.date()
        
        if self.recurrence_pattern == 'daily':
            return from_date + timedelta(days=self.recurrence_interval)
            
        elif self.recurrence_pattern == 'weekly':
            return from_date + timedelta(weeks=self.recurrence_interval)
            
        elif self.recurrence_pattern == 'biweekly':
            return from_date + timedelta(weeks=2 * self.recurrence_interval)
            
        elif self.recurrence_pattern == 'monthly':
            # Add months (approximate)
            try:
                if from_date.month == 12:
                    return from_date.replace(year=from_date.year + 1, month=1)
                else:
                    return from_date.replace(month=from_date.month + self.recurrence_interval)
            except ValueError:
                # Handle month overflow (e.g., Jan 31 + 1 month)
                import calendar
                next_month = from_date.month + self.recurrence_interval
                year = from_date.year
                while next_month > 12:
                    next_month -= 12
                    year += 1
                
                # Handle day overflow (e.g., Jan 31 -> Feb 28)
                max_day = calendar.monthrange(year, next_month)[1]
                day = min(from_date.day, max_day)
                return from_date.replace(year=year, month=next_month, day=day)
        
        return None
    
    def generate_recurring_events(self, save=True):
        """Generate all recurring event instances"""
        from datetime import datetime, timedelta
        
        if not self.is_recurring or self.parent_event is not None:
            return []
        
        instances = []
        current_date = self.start_date
        count = 0
        
        # Determine end condition
        max_count = self.max_occurrences or 100  # Safety limit
        end_date = self.recurrence_end_date or (self.start_date + timedelta(days=365))  # 1 year max
        
        # Generate occurrences
        while count < max_count and current_date.date() <= end_date.date():
            # Skip the original event (count = 0)
            if count > 0:
                # Create new instance
                instance = Event(
                    title=self.title,
                    description=self.description,
                    event_type_new=self.event_type_new,
                    event_type=self.event_type,
                    priority=self.priority,
                    visibility=self.visibility,
                    custom_color=self.custom_color,
                    custom_background=self.custom_background,
                    start_date=current_date,
                    end_date=current_date + (self.end_date - self.start_date) if self.end_date else None,
                    all_day=self.all_day,
                    is_published=self.is_published,
                    is_featured=False,  # Only parent should be featured
                    created_by=self.created_by,
                    course=self.course,
                    linked_lesson=self.linked_lesson,
                    obsidian_link=self.obsidian_link,
                    parent_event=self,
                    occurrence_date=current_date.date(),
                    # Recurring fields should be False for instances
                    is_recurring=False,
                )
                
                if save:
                    instance.save()
                instances.append(instance)
            
            # Calculate next occurrence
            if self.recurrence_pattern == 'daily':
                current_date += timedelta(days=self.recurrence_interval)
                
                # Skip weekends if specified
                if self.exclude_weekends and current_date.weekday() >= 5:
                    days_to_add = 7 - current_date.weekday()  # Skip to Monday
                    current_date += timedelta(days=days_to_add)
                    
            elif self.recurrence_pattern == 'weekly':
                # Handle specific days of the week
                if self.recurrence_days:
                    target_days = []
                    try:
                        # Parse comma-separated day numbers (0=Monday, 6=Sunday)
                        for day in self.recurrence_days.split(','):
                            day = day.strip()
                            if day.isdigit():
                                day_num = int(day)
                                if 0 <= day_num <= 6:
                                    target_days.append(day_num)
                    except (ValueError, AttributeError):
                        # Fallback to weekly interval if parsing fails
                        current_date += timedelta(weeks=self.recurrence_interval)
                        count += 1
                        continue
                    
                    if target_days:
                        target_days = sorted(target_days)
                        current_weekday = current_date.weekday()
                        next_day = None
                        
                        # Look for next target day in current week
                        for day in target_days:
                            if day > current_weekday:
                                next_day = day
                                break
                        
                        if next_day is not None:
                            # Next occurrence is in current week
                            days_ahead = next_day - current_weekday
                            current_date += timedelta(days=days_ahead)
                        else:
                            # Go to next week, first target day
                            days_ahead = 7 - current_weekday + min(target_days)
                            current_date += timedelta(days=days_ahead)
                    else:
                        # No valid days, just weekly
                        current_date += timedelta(weeks=self.recurrence_interval)
                else:
                    current_date += timedelta(weeks=self.recurrence_interval)
                    
            elif self.recurrence_pattern == 'biweekly':
                # Handle specific days of the week for biweekly pattern
                if self.recurrence_days:
                    target_days = []
                    try:
                        # Parse comma-separated day numbers (0=Monday, 6=Sunday)
                        for day in self.recurrence_days.split(','):
                            day = day.strip()
                            if day.isdigit():
                                day_num = int(day)
                                if 0 <= day_num <= 6:
                                    target_days.append(day_num)
                    except (ValueError, AttributeError):
                        # Fallback to biweekly interval if parsing fails
                        current_date += timedelta(weeks=2 * self.recurrence_interval)
                        count += 1
                        continue
                    
                    if target_days:
                        target_days = sorted(target_days)
                        current_weekday = current_date.weekday()
                        next_day = None
                        
                        # Look for next target day in current week
                        for day in target_days:
                            if day > current_weekday:
                                next_day = day
                                break
                        
                        if next_day is not None:
                            # Next occurrence is in current week
                            days_ahead = next_day - current_weekday
                            current_date += timedelta(days=days_ahead)
                        else:
                            # Go to next occurrence in 2 weeks, first target day
                            days_ahead = 14 - current_weekday + min(target_days)
                            current_date += timedelta(days=days_ahead)
                    else:
                        # No valid days, just biweekly
                        current_date += timedelta(weeks=2 * self.recurrence_interval)
                else:
                    current_date += timedelta(weeks=2 * self.recurrence_interval)
                
            elif self.recurrence_pattern == 'custom':
                # Handle custom pattern with specific weekdays
                if self.recurrence_days:
                    target_days = []
                    try:
                        # Parse comma-separated day numbers (0=Monday, 6=Sunday)
                        for day in self.recurrence_days.split(','):
                            day = day.strip()
                            if day.isdigit():
                                day_num = int(day)
                                if 0 <= day_num <= 6:
                                    target_days.append(day_num)
                    except (ValueError, AttributeError):
                        # Fallback - just advance one day if parsing fails
                        current_date += timedelta(days=1)
                        count += 1
                        continue
                    
                    if target_days:
                        target_days = sorted(target_days)
                        current_weekday = current_date.weekday()
                        next_day = None
                        
                        # Look for next target day in current week
                        for day in target_days:
                            if day > current_weekday:
                                next_day = day
                                break
                        
                        if next_day is not None:
                            # Next occurrence is in current week
                            days_ahead = next_day - current_weekday
                            current_date += timedelta(days=days_ahead)
                        else:
                            # Go to next week, first target day
                            days_ahead = 7 - current_weekday + min(target_days)
                            current_date += timedelta(days=days_ahead)
                    else:
                        # No valid days, just advance one day
                        current_date += timedelta(days=1)
                else:
                    # No recurrence days specified, just advance one day
                    current_date += timedelta(days=1)
                
            elif self.recurrence_pattern == 'monthly':
                # Add months
                month = current_date.month
                year = current_date.year
                month += self.recurrence_interval
                
                while month > 12:
                    month -= 12
                    year += 1
                
                try:
                    current_date = current_date.replace(year=year, month=month)
                except ValueError:
                    # Handle day overflow
                    import calendar
                    max_day = calendar.monthrange(year, month)[1]
                    day = min(current_date.day, max_day)
                    current_date = current_date.replace(year=year, month=month, day=day)
            
            count += 1
        
        return instances
    
    def update_recurring_series(self, **kwargs):
        """Update all instances in a recurring series"""
        if not self.is_recurring_parent:
            return 0
        
        # Update all instances
        instances = self.recurring_instances.all()
        updated_count = 0
        for instance in instances:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            instance.save()
            updated_count += 1
        return updated_count
    
    def delete_recurring_series(self):
        """Delete all instances in a recurring series"""
        deleted_count = 0
        if self.is_recurring_parent:
            deleted_count = self.recurring_instances.count()
            self.recurring_instances.all().delete()
        elif self.parent_event:
            # If deleting an instance, just delete this one
            deleted_count = 1
        self.delete()
        return deleted_count
    
    def get_series_info(self):
        """Get information about the recurring series"""
        if not self.is_recurring and not self.parent_event:
            return None
        
        parent = self.parent_event if self.parent_event else self
        total_instances = parent.recurring_instances.count() + 1  # +1 for parent
        
        pattern_text = {
            'daily': f"Daily (every {parent.recurrence_interval} day{'s' if parent.recurrence_interval > 1 else ''})",
            'weekly': f"Weekly (every {parent.recurrence_interval} week{'s' if parent.recurrence_interval > 1 else ''})",
            'biweekly': f"Bi-weekly (every {parent.recurrence_interval * 2} weeks)",
            'monthly': f"Monthly (every {parent.recurrence_interval} month{'s' if parent.recurrence_interval > 1 else ''})"
        }.get(parent.recurrence_pattern, 'Custom')
        
        if parent.recurrence_days:
            days = parent.get_recurrence_days_list()
            pattern_text += f" on {', '.join(days)}"
        
        return {
            'parent': parent,
            'total_instances': total_instances,
            'pattern': pattern_text,
            'end_date': parent.recurrence_end_date,
            'max_occurrences': parent.max_occurrences,
            'is_parent': self.is_recurring_parent
        }


# =============================================================================
# SECURITY MONITORING MODELS - Import from separate file
# =============================================================================

# Import all security models from models_security.py
from .models_security import (
    SecurityEvent, SystemMetrics, ThreatIntelligence, 
    AuditLog, AlertRule
)

# Add to __all__ for proper model discovery
__all__ = [
    'UserProfile', 'SiteTheme', 'UserThemePreference', 'Course', 'Enrollment',
    'Lesson', 'CourseMaterial', 'Assignment', 'Submission', 'Progress', 'Post',
    'Quiz', 'Question', 'Answer', 'QuizAttempt', 'QuizResponse', 'Announcement',
    'AnnouncementRead', 'Forum', 'Topic', 'ForumPost', 'BlogPost', 'BlogComment',
    'EventType', 'Event', 
    # Security models
    'SecurityEvent', 'SystemMetrics', 'ThreatIntelligence', 'AuditLog', 'AlertRule'
]

