from django.urls import path
from . import views

urlpatterns = [
    # Authentication views
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    
    # Legacy blog view
    path('posts/', views.post_list, name='post_list'),
    
    # Course views (main LMS functionality)
    path('', views.course_list, name='course_list'),
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
]