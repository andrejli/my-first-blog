"""
Modular views package for Django LMS.

✅ REFACTORING COMPLETE - Phase 2
This package addresses critical architectural issues:
✅ Wildcard imports removed
✅ Caching implemented  
✅ Views split into modules (14 modules extracted, ~5,000 lines / 98%)
🔄 Final cleanup in progress

Extracted Modules:
- helpers.py: Shared utility functions and decorators ✅
- auth.py: Authentication (login, logout, registration) ✅
- courses.py: Course management and enrollment ✅
- lessons.py: Lesson detail and completion tracking ✅
- dashboards.py: Student/instructor dashboards ✅
- assignments.py: Assignment submission and grading ✅
- quizzes.py: Quiz creation, taking, and grading ✅
- instructor_management.py: Course/lesson creation & materials ✅
- announcements.py: Course announcements ✅
- forums.py: Discussion forums and topics ✅
- blogs.py: Personal blog posts and comments ✅
- events.py: Event calendar and iCal import/export ✅
- utilities.py: Theme management and utilities ✅
- quarantine.py: Content moderation and quarantine ✅
- views_original.py: ~100 lines remaining (will be removed)

For full backward compatibility, all views are imported here.
"""

# Import helper functions and decorators
from .helpers import (
    is_content_quarantined,
    can_view_quarantined_content,
    instructor_required,
    admin_required
)

# Import course import/export functionality
from blog.course_import_export import (
    export_course,
    import_course,
    confirm_import_course
)

# Import authentication views
from .auth import (
    user_login,
    user_logout,
    user_register
)

# Import course and public views
from .courses import (
    post_list,
    landing_page,
    course_list,
    course_detail,
    enroll_course,
    drop_course
)

# Import lesson views
from .lessons import (
    lesson_detail,
    mark_lesson_complete
)

# Import dashboard views
from .dashboards import (
    student_dashboard,
    instructor_dashboard,
    my_courses,
    course_students
)

# Import assignment views
from .assignments import (
    course_assignments,
    create_assignment,
    edit_assignment,
    delete_assignment,
    assignment_submissions,
    grade_submission,
    student_assignments,
    assignment_detail,
    submit_assignment,
    edit_submission
)

# Import quiz views
from .quizzes import (
    course_quizzes,
    create_quiz,
    quiz_detail,
    edit_quiz,
    toggle_quiz_publish,
    add_question,
    edit_question,
    delete_question,
    reorder_questions,
    quiz_list_for_students,
    start_quiz,
    take_quiz,
    quiz_results,
    quiz_attempts,
    grade_quiz_attempt
)

# Import instructor management views
from .instructor_management import (
    instructor_course_detail,
    create_lesson,
    edit_lesson,
    delete_lesson,
    reorder_lessons,
    create_course,
    edit_course,
    course_materials,
    upload_material,
    delete_material
)

# Import announcement views
from .announcements import (
    course_announcements,
    create_announcement,
    edit_announcement,
    delete_announcement,
    announcement_detail
)

# Import forum views
from .forums import (
    forum_list,
    forum_detail,
    topic_detail,
    create_topic,
    create_post,
    edit_post,
    delete_post
)

# Import blog views
from .blogs import (
    user_profile,
    user_blog_list,
    blog_post_detail,
    my_blog_dashboard,
    create_blog_post,
    edit_blog_post,
    delete_blog_post,
    delete_blog_comment,
    all_blogs,
    upload_blog_image
)

# Import event and calendar views
from .events import (
    event_management,
    ical_import_export_page,
    admin_event_import_export,
    admin_export_ical,
    admin_import_ical,
    add_event,
    edit_event,
    delete_event,
    manage_event_types,
    add_event_type,
    edit_event_type,
    delete_event_type,
    delete_event_form,
    event_calendar,
    export_events_ical,
    import_events_ical,
    custom_404
)

# Import utility views
from .utilities import (
    get_user_theme,
    set_user_theme,
    list_themes,
    theme_debug_view
)

# Import quarantine management views
from .quarantine import (
    quarantine_forum_post,
    quarantine_blog_post,
    resolve_quarantine,
    quarantine_dashboard
)

# ============================================================================
# ALL VIEWS EXTRACTED - views_original.py can now be safely deleted
# ============================================================================
# The wildcard import has been removed. All views are now explicitly imported
# from their respective modules above.

# Explicitly re-export the refactored views to override the originals
__all__ = [
    # Helpers
    'is_content_quarantined',
    'can_view_quarantined_content',
    'instructor_required',
    'admin_required',
    # Course Import/Export
    'export_course',
    'import_course',
    'confirm_import_course',
    # Auth
    'user_login',
    'user_logout',
    'user_register',
    # Courses
    'post_list',
    'landing_page',
    'course_list',
    'course_detail',
    'enroll_course',
    'drop_course',
    # Lessons
    'lesson_detail',
    'mark_lesson_complete',
    # Dashboards
    'student_dashboard',
    'instructor_dashboard',
    'my_courses',
    'course_students',
    # Assignments
    'course_assignments',
    'create_assignment',
    'edit_assignment',
    'delete_assignment',
    'assignment_submissions',
    'grade_submission',
    'student_assignments',
    'assignment_detail',
    'submit_assignment',
    'edit_submission',
    # Quizzes
    'course_quizzes',
    'create_quiz',
    'quiz_detail',
    'edit_quiz',
    'toggle_quiz_publish',
    'add_question',
    'edit_question',
    'delete_question',
    'reorder_questions',
    'quiz_list_for_students',
    'start_quiz',
    'take_quiz',
    'quiz_results',
    'quiz_attempts',
    'grade_quiz_attempt',
    # Instructor Management
    'instructor_course_detail',
    'create_lesson',
    'edit_lesson',
    'delete_lesson',
    'reorder_lessons',
    'create_course',
    'edit_course',
    'course_materials',
    'upload_material',
    'delete_material',
    # Announcements
    'course_announcements',
    'create_announcement',
    'edit_announcement',
    'delete_announcement',
    'announcement_detail',
    # Forums
    'forum_list',
    'forum_detail',
    'topic_detail',
    'create_topic',
    'create_post',
    'edit_post',
    'delete_post',
    # Blogs
    'user_profile',
    'user_blog_list',
    'blog_post_detail',
    'my_blog_dashboard',
    'create_blog_post',
    'edit_blog_post',
    'delete_blog_post',
    'delete_blog_comment',
    'all_blogs',
    'upload_blog_image',
    # Events & Calendar
    'event_management',
    'ical_import_export_page',
    'admin_event_import_export',
    'admin_export_ical',
    'admin_import_ical',
    'add_event',
    'edit_event',
    'delete_event',
    'manage_event_types',
    'add_event_type',
    'edit_event_type',
    'delete_event_type',
    'delete_event_form',
    'event_calendar',
    'export_events_ical',
    'import_events_ical',
    'custom_404',
    # Utilities
    'get_user_theme',
    'set_user_theme',
    'list_themes',
    'theme_debug_view',
    # Quarantine Management
    'quarantine_forum_post',
    'quarantine_blog_post',
    'resolve_quarantine',
    'quarantine_dashboard',
]
