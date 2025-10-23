"""
Database Performance Testing Script
Tests database performance with and without optimizations
"""

import time
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from blog.models import Course, Enrollment, Assignment, Quiz, QuizAttempt, Submission
from django.db import connection, reset_queries
from django.conf import settings

class PerformanceTester:
    """Database performance testing utilities"""
    
    def __init__(self):
        self.results = {}
    
    def time_query(self, name, func):
        """Time a database operation"""
        reset_queries()
        start_time = time.time()
        
        result = func()
        
        end_time = time.time()
        query_count = len(connection.queries)
        execution_time = end_time - start_time
        
        self.results[name] = {
            'time': execution_time,
            'queries': query_count,
            'result_count': len(result) if hasattr(result, '__len__') else 1
        }
        
        print(f"✅ {name}:")
        print(f"   Time: {execution_time:.4f}s")
        print(f"   Queries: {query_count}")
        if hasattr(result, '__len__'):
            print(f"   Results: {len(result)} items")
        print()
        
        return result
    
    def test_course_queries(self):
        """Test course-related queries"""
        print("🔍 Testing Course Queries")
        print("=" * 50)
        
        # Test 1: Get all published courses with instructor info
        def get_published_courses():
            return list(Course.objects.select_related(
                'instructor', 'instructor__userprofile'
            ).filter(status='published'))
        
        self.time_query("Published courses with instructor", get_published_courses)
        
        # Test 2: Get courses with enrollment counts
        def get_courses_with_enrollment_counts():
            from django.db.models import Count
            return list(Course.objects.annotate(
                enrollment_count=Count('enrollment')
            ).select_related('instructor'))
        
        self.time_query("Courses with enrollment counts", get_courses_with_enrollment_counts)
        
        # Test 3: Get course with all related data
        def get_course_with_all_data():
            courses = Course.objects.select_related(
                'instructor', 'instructor__userprofile'
            ).prefetch_related(
                'lesson_set', 'assignment_set', 'quizzes', 'enrollment_set__student'
            ).filter(status='published')
            return list(courses)
        
        self.time_query("Courses with all related data", get_course_with_all_data)
    
    def test_enrollment_queries(self):
        """Test enrollment-related queries"""
        print("🔍 Testing Enrollment Queries")
        print("=" * 50)
        
        # Test 1: Get active enrollments
        def get_active_enrollments():
            return list(Enrollment.objects.select_related(
                'student', 'course', 'student__userprofile'
            ).filter(status='enrolled'))
        
        self.time_query("Active enrollments", get_active_enrollments)
        
        # Test 2: Get enrollments by course
        def get_enrollments_by_course():
            from django.db.models import Count
            return list(Enrollment.objects.values(
                'course__title', 'course__course_code'
            ).annotate(count=Count('id')))
        
        self.time_query("Enrollments by course", get_enrollments_by_course)
    
    def test_assignment_queries(self):
        """Test assignment-related queries"""
        print("🔍 Testing Assignment Queries")
        print("=" * 50)
        
        # Test 1: Get assignments with submission counts
        def get_assignments_with_submissions():
            from django.db.models import Count
            return list(Assignment.objects.select_related(
                'course'
            ).annotate(
                submission_count=Count('submission')
            ).filter(is_published=True))
        
        self.time_query("Assignments with submission counts", get_assignments_with_submissions)
        
        # Test 2: Get overdue assignments
        def get_overdue_assignments():
            from django.utils import timezone
            return list(Assignment.objects.filter(
                due_date__lt=timezone.now(),
                is_published=True
            ).select_related('course'))
        
        self.time_query("Overdue assignments", get_overdue_assignments)
    
    def test_complex_queries(self):
        """Test complex cross-table queries"""
        print("🔍 Testing Complex Queries")
        print("=" * 50)
        
        # Test 1: Get student performance summary
        def get_student_performance():
            from django.db.models import Avg, Count
            return list(User.objects.filter(
                userprofile__role='student'
            ).annotate(
                avg_quiz_score=Avg('quizattempt__percentage'),
                quiz_count=Count('quizattempt'),
                enrollment_count=Count('enrollment')
            ).select_related('userprofile'))
        
        self.time_query("Student performance summary", get_student_performance)
        
        # Test 2: Get instructor dashboard data
        def get_instructor_dashboard():
            from django.db.models import Count, Avg
            return list(User.objects.filter(
                userprofile__role='instructor'
            ).annotate(
                course_count=Count('course'),
                total_students=Count('course__enrollment'),
                avg_course_rating=Avg('course__enrollment__grade')
            ).select_related('userprofile'))
        
        self.time_query("Instructor dashboard data", get_instructor_dashboard)
    
    def run_all_tests(self):
        """Run all performance tests"""
        print("🚀 Database Performance Testing")
        print(f"📊 Database: {settings.DATABASES['default']['NAME']}")
        print(f"🔧 Cache size: {settings.DATABASES['default']['OPTIONS']['init_command']}")
        print()
        
        # Enable query logging for testing
        original_debug = settings.DEBUG
        settings.DEBUG = True
        
        try:
            self.test_course_queries()
            self.test_enrollment_queries()
            self.test_assignment_queries()
            self.test_complex_queries()
            
            # Summary
            print("📋 Performance Summary")
            print("=" * 50)
            total_time = sum(r['time'] for r in self.results.values())
            total_queries = sum(r['queries'] for r in self.results.values())
            
            print(f"Total execution time: {total_time:.4f}s")
            print(f"Total queries: {total_queries}")
            print(f"Average time per test: {total_time/len(self.results):.4f}s")
            print()
            
            # Identify slowest operations
            slowest = sorted(self.results.items(), key=lambda x: x[1]['time'], reverse=True)
            print("🐌 Slowest operations:")
            for name, data in slowest[:3]:
                print(f"  {name}: {data['time']:.4f}s ({data['queries']} queries)")
            
        finally:
            settings.DEBUG = original_debug


if __name__ == '__main__':
    tester = PerformanceTester()
    tester.run_all_tests()