from django.urls import path
from . import views

urlpatterns = [
    # Authentication views
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    
    # Public landing page
    path('', views.landing_page, name='landing'),
    
    # Legacy blog view
    path('posts/', views.post_list, name='post_list'),
    
    # Course views (main LMS functionality)
    path('courses/', views.course_list, name='course_list'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    
    # Enrollment system
    path('course/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('course/<int:course_id>/drop/', views.drop_course, name='drop_course'),
    path('course/<int:course_id>/students/', views.course_students, name='course_students'),
    
    # Lesson views
    path('course/<int:course_id>/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('course/<int:course_id>/lesson/<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
    
    # Dashboard and user views
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('instructor/', views.instructor_dashboard, name='instructor_dashboard'),
    path('my-courses/', views.my_courses, name='my_courses'),
    
    # Phase 2: Enhanced lesson management for instructors
    path('instructor/course/<int:course_id>/', views.instructor_course_detail, name='instructor_course_detail'),
    path('instructor/course/<int:course_id>/lesson/create/', views.create_lesson, name='create_lesson'),
    path('instructor/lesson/<int:lesson_id>/edit/', views.edit_lesson, name='edit_lesson'),
    path('instructor/lesson/<int:lesson_id>/delete/', views.delete_lesson, name='delete_lesson'),
    path('instructor/course/<int:course_id>/lessons/reorder/', views.reorder_lessons, name='reorder_lessons'),
    
    # Course creation for instructors
    path('instructor/course/create/', views.create_course, name='create_course'),
    path('instructor/course/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    
    # Phase 2.2: Content Upload System
    # Course Materials
    path('instructor/course/<int:course_id>/materials/', views.course_materials, name='course_materials'),
    path('instructor/course/<int:course_id>/material/upload/', views.upload_material, name='upload_material'),
    path('instructor/material/<int:material_id>/delete/', views.delete_material, name='delete_material'),
    
    # Assignments
    path('instructor/course/<int:course_id>/assignments/', views.course_assignments, name='course_assignments'),
    path('instructor/course/<int:course_id>/assignment/create/', views.create_assignment, name='create_assignment'),
    path('instructor/assignment/<int:assignment_id>/edit/', views.edit_assignment, name='edit_assignment'),
    path('instructor/assignment/<int:assignment_id>/delete/', views.delete_assignment, name='delete_assignment'),
    path('instructor/assignment/<int:assignment_id>/submissions/', views.assignment_submissions, name='assignment_submissions'),
    path('instructor/submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    
    # Student Assignment Views
    path('course/<int:course_id>/assignments/', views.student_assignments, name='student_assignments'),
    path('assignment/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('submission/<int:submission_id>/edit/', views.edit_submission, name='edit_submission'),
    
    # Quiz Management Views
    path('instructor/course/<int:course_id>/quizzes/', views.course_quizzes, name='course_quizzes'),
    path('instructor/course/<int:course_id>/quiz/create/', views.create_quiz, name='create_quiz'),
    path('course/<int:course_id>/quiz/create/', views.create_quiz, name='create_quiz_alt'),  # Alternative URL for tests
    path('instructor/quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('instructor/quiz/<int:quiz_id>/edit/', views.edit_quiz, name='edit_quiz'),
    path('instructor/quiz/<int:quiz_id>/toggle-publish/', views.toggle_quiz_publish, name='toggle_quiz_publish'),
    
    # Question Management Views
    path('instructor/quiz/<int:quiz_id>/question/add/', views.add_question, name='add_question'),
    path('quiz/<int:quiz_id>/question/create/', views.add_question, name='create_question'),  # Alternative URL for tests
    path('instructor/question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('instructor/question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('instructor/quiz/<int:quiz_id>/questions/reorder/', views.reorder_questions, name='reorder_questions'),
    
    # Student Quiz Taking Views
    path('course/<int:course_id>/quizzes/', views.quiz_list_for_students, name='student_quiz_list'),
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail_legacy'),  # Legacy URL for tests
    path('quiz/<int:quiz_id>/start/', views.start_quiz, name='start_quiz'),
    path('quiz/attempt/<int:attempt_id>/', views.take_quiz, name='take_quiz'),
    path('quiz/results/<int:attempt_id>/', views.quiz_results, name='quiz_results'),
    
    # Instructor Quiz Grading Views
    path('instructor/quiz/<int:quiz_id>/attempts/', views.quiz_attempts, name='quiz_attempts'),
    path('instructor/quiz/attempt/<int:attempt_id>/grade/', views.grade_quiz_attempt, name='grade_quiz_attempt'),
    
    # Phase 4: Course Announcements - ACTIVATED
    path('course/<int:course_id>/announcements/', views.course_announcements, name='course_announcements'),
    path('course/<int:course_id>/announcement/create/', views.create_announcement, name='create_announcement'),
    path('announcement/<int:announcement_id>/', views.announcement_detail, name='announcement_detail'),
    path('announcement/<int:announcement_id>/edit/', views.edit_announcement, name='edit_announcement'),
    path('announcement/<int:announcement_id>/delete/', views.delete_announcement, name='delete_announcement'),
    
    # Phase 4: Discussion Forums - NEW
    path('forums/', views.forum_list, name='forum_list'),
    path('forum/', views.forum_list, name='forum_list_legacy'),  # Legacy URL for tests
    path('forum/<int:forum_id>/', views.forum_detail, name='forum_detail'),
    path('forum/<int:forum_id>/create-topic/', views.create_topic, name='create_topic'),
    path('topic/<int:topic_id>/', views.topic_detail, name='topic_detail'),
    path('topic/<int:topic_id>/reply/', views.create_post, name='create_post'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    
    # Theme Management
    path('api/themes/', views.list_themes, name='list_themes'),
    path('api/theme/get/', views.get_user_theme, name='get_user_theme'),
    path('api/theme/set/', views.set_user_theme, name='set_user_theme'),
    path('set-theme/', views.set_user_theme, name='set_theme_legacy'),  # Legacy URL for tests
    
    # Phase 5B: Course Import/Export System
    path('instructor/course/<int:course_id>/export/', views.export_course, name='export_course'),
    path('instructor/course/import/', views.import_course, name='import_course'),
    path('instructor/course/import/confirm/', views.confirm_import_course, name='confirm_import_course'),
    
    # Phase 6: Individual User Blogs
    path('blogs/', views.all_blogs, name='all_blogs'),
    path('my-blog/', views.my_blog_dashboard, name='my_blog_dashboard'),
    path('blog/dashboard/', views.my_blog_dashboard, name='blog_dashboard_alias'),  # Alias for dashboard
    path('my-blog/create/', views.create_blog_post, name='create_blog_post'),
    path('blog/create/', views.create_blog_post, name='create_blog_post_alias'),  # Alias for common URL pattern
    path('my-blog/edit/<int:post_id>/', views.edit_blog_post, name='edit_blog_post'),
    path('my-blog/delete/<int:post_id>/', views.delete_blog_post, name='delete_blog_post'),
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('user/<str:username>/blog/', views.user_blog_list, name='user_blog_list'),
    path('user/<str:username>/blog/<slug:slug>/', views.blog_post_detail, name='blog_post_detail'),
    path('comment/<int:comment_id>/delete/', views.delete_blog_comment, name='delete_blog_comment'),
    path('api/blog/upload-image/', views.upload_blog_image, name='upload_blog_image'),
    
    # Event Management (Admin Only)
    path('event-management/', views.event_management, name='event_management'),
    path('event-management/add/', views.add_event, name='add_event'),
    path('event-management/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('event-management/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    
    # iCal Import/Export (Admin Only)
    path('ical-import-export/', views.ical_import_export_page, name='ical_import_export_page'),
    path('event-management/export-ical/', views.export_events_ical, name='export_events_ical'),
    path('event-management/import-ical/', views.import_events_ical, name='import_events_ical'),
    
    # Admin iCal Import/Export Interface
    path('admin/events/import-export/', views.admin_event_import_export, name='admin_event_import_export'),
    path('admin/events/export/', views.admin_export_ical, name='admin_export_ical'),
    path('admin/events/import/', views.admin_import_ical, name='admin_import_ical'),
    
    # Event Type Management
    path('event-types/', views.manage_event_types, name='manage_event_types'),
    path('event-types/add/', views.add_event_type, name='add_event_type'),
    path('event-types/<int:type_id>/edit/', views.edit_event_type, name='edit_event_type'),
    path('event-types/<int:type_id>/delete/', views.delete_event_type, name='delete_event_type'),
    
    # Calendar View
    path('calendar/', views.event_calendar, name='event_calendar'),
    
    # Content Quarantine Management (Admin/Staff Only)
    path('quarantine/forum-post/<int:post_id>/', views.quarantine_forum_post, name='quarantine_forum_post'),
    path('quarantine/blog-post/<int:post_id>/', views.quarantine_blog_post, name='quarantine_blog_post'),
    path('quarantine/<int:quarantine_id>/resolve/', views.resolve_quarantine, name='resolve_quarantine'),
    path('quarantine/dashboard/', views.quarantine_dashboard, name='quarantine_dashboard'),
    
    # Debug/Test Views
    path('debug/theme-test/', views.theme_debug_view, name='theme_debug'),
]