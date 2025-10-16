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


# Site Configuration Models
class SiteTheme(models.Model):
    THEME_CHOICES = [
        ('terminal-green', 'Terminal Green'),
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
    featured_image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    
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

