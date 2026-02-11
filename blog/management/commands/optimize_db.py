"""
Database Performance Management Utility
Provides utilities for database optimization, monitoring, and maintenance
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings
import time
import logging

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Database optimization and monitoring utilities"""
    
    @staticmethod
    def analyze_slow_queries(threshold_ms=100):
        """Analyze slow queries using Django's query logging"""
        from django.db import reset_queries, connection
        from django.conf import settings
        
        if not settings.DEBUG:
            logger.warning("Query logging requires DEBUG=True")
            return []
        
        reset_queries()
        # This would be called after operations to analyze
        queries = connection.queries
        slow_queries = [q for q in queries if float(q['time']) * 1000 > threshold_ms]
        
        for query in slow_queries:
            logger.warning(f"Slow query ({query['time']}s): {query['sql'][:100]}...")
        
        return slow_queries
    
    @staticmethod
    def optimize_sqlite():
        """Run SQLite optimization commands"""
        with connection.cursor() as cursor:
            # Analyze database statistics
            cursor.execute("ANALYZE")
            
            # Rebuild indexes if needed
            cursor.execute("REINDEX")
            
            # Vacuum to reclaim space
            cursor.execute("VACUUM")
            
            # Update SQLite stats
            cursor.execute("PRAGMA optimize")
            
        logger.info("SQLite database optimized")
    
    @staticmethod
    def get_database_stats():
        """Get database performance statistics"""
        with connection.cursor() as cursor:
            stats = {}
            
            # Database size
            cursor.execute("PRAGMA page_count")
            result = cursor.fetchone()
            page_count = result[0] if result else 0
            
            cursor.execute("PRAGMA page_size")
            result = cursor.fetchone()
            page_size = result[0] if result else 4096
            
            stats['db_size_mb'] = (page_count * page_size) / (1024 * 1024)
            
            # Cache hit ratio
            cursor.execute("PRAGMA cache_size")
            result = cursor.fetchone()
            cache_size = result[0] if result else 0
            stats['cache_size'] = cache_size
            
            # Journal mode
            cursor.execute("PRAGMA journal_mode")
            result = cursor.fetchone()
            journal_mode = result[0] if result else 'unknown'
            stats['journal_mode'] = journal_mode
            
            # Foreign keys
            cursor.execute("PRAGMA foreign_keys")
            result = cursor.fetchone()
            foreign_keys = result[0] if result else 0
            stats['foreign_keys_enabled'] = bool(foreign_keys)
            
            # Index usage stats
            cursor.execute("""
                SELECT name, sql FROM sqlite_master 
                WHERE type='index' AND sql IS NOT NULL
            """)
            indexes = cursor.fetchall()
            stats['index_count'] = len(indexes)
            
        return stats
    
    @staticmethod
    def check_table_stats():
        """Check table statistics for optimization"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'blog_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            table_stats = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                result = cursor.fetchone()
                count = result[0] if result else 0
                table_stats[table] = {'row_count': count}
                
        return table_stats


class QueryOptimizer:
    """Query optimization utilities with enhanced prefetching patterns"""
    
    @staticmethod
    def get_optimized_course_queryset():
        """Get optimized course queryset with proper select_related and prefetching"""
        from blog.models import Course, Lesson
        from django.db.models import Count, Q, Prefetch
        
        return Course.objects.select_related(
            'instructor',
            'instructor__userprofile'
        ).prefetch_related(
            Prefetch(
                'lesson_set',
                queryset=Lesson.objects.select_related('course').order_by('order')
            ),
            'assignment_set',
            'quizzes'  # Course.quizzes is the correct related_name
        ).annotate(
            published_lessons_count=Count(
                'lesson',
                filter=Q(lesson__is_published=True)
            ),
            total_students=Count('enrollment', distinct=True),
            active_enrollments=Count(
                'enrollment',
                filter=Q(enrollment__status='enrolled'),
                distinct=True
            )
        )
    
    @staticmethod
    def get_optimized_enrollment_queryset():
        """Get optimized enrollment queryset with progress tracking"""
        from blog.models import Enrollment
        from django.db.models import Count, Q, F
        
        return Enrollment.objects.select_related(
            'student',
            'course',
            'student__userprofile',
            'course__instructor'
        ).annotate(
            completed_lessons_count=Count(
                'student__progress',
                filter=Q(
                    student__progress__lesson__course_id=F('course_id'),
                    student__progress__completed=True
                )
            )
        )
    
    @staticmethod
    def get_optimized_assignment_queryset():
        """Get optimized assignment queryset with submission prefetching"""
        from blog.models import Assignment
        
        return Assignment.objects.select_related(
            'course',
            'course__instructor'
        ).prefetch_related(
            'submission_set__student'
        )
    
    @staticmethod
    def get_optimized_quiz_queryset():
        """Get optimized quiz queryset with attempt statistics"""
        from blog.models import Quiz
        from django.db.models import Count, Avg
        
        return Quiz.objects.select_related(
            'course',
            'course__instructor'
        ).prefetch_related(
            'questions__answers'
        ).annotate(
            total_attempts=Count('attempts', distinct=True),  # Quiz.attempts is correct
            question_count=Count('questions', distinct=True),  # Rename to avoid @property conflict
            avg_score=Avg('attempts__score')  # Use attempts, not quizattempt
        )
    
    @staticmethod
    def get_optimized_lesson_queryset():
        """Get optimized lesson queryset with completion statistics"""
        from blog.models import Lesson
        from django.db.models import Count, Q
        
        return Lesson.objects.select_related(
            'course',
            'course__instructor'
        ).annotate(
            total_progress=Count('progress', distinct=True),
            completed_count=Count(
                'progress',
                filter=Q(progress__completed=True),
                distinct=True
            )
        ).order_by('course', 'order')
    
    @staticmethod
    def get_optimized_forum_queryset():
        """Get optimized forum queryset with topic and post counts"""
        from blog.models import Forum
        from django.db.models import Count, Max
        
        return Forum.objects.select_related(
            'course'
        ).annotate(
            topic_count=Count('topics', distinct=True),
            post_count=Count('topics__posts', distinct=True),
            last_post_date=Max('topics__posts__created_date')
        ).order_by('name')
    
    @staticmethod
    def get_optimized_event_queryset():
        """Get optimized event queryset for calendar views"""
        from blog.models import Event
        from django.utils import timezone
        
        return Event.objects.filter(
            is_published=True,
            start_date__gte=timezone.now()
        ).select_related(
            'course',
            'event_type'
        ).order_by('start_date', 'priority')


# Management command for database optimization
class Command(BaseCommand):
    help = 'Optimize database performance'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show database statistics',
        )
        parser.add_argument(
            '--optimize',
            action='store_true',
            help='Run database optimization',
        )
        parser.add_argument(
            '--check-queries',
            action='store_true',
            help='Check for slow queries',
        )
    
    def handle(self, *args, **options):
        optimizer = DatabaseOptimizer()
        
        if options['stats']:
            self.stdout.write("Database Statistics:")
            stats = optimizer.get_database_stats()
            for key, value in stats.items():
                self.stdout.write(f"  {key}: {value}")
            
            self.stdout.write("\nTable Statistics:")
            table_stats = optimizer.check_table_stats()
            for table, stats in table_stats.items():
                self.stdout.write(f"  {table}: {stats['row_count']} rows")
        
        if options['optimize']:
            self.stdout.write("Optimizing database...")
            optimizer.optimize_sqlite()
            self.stdout.write("Database optimization completed.")
        
        if options['check_queries']:
            self.stdout.write("Query optimization suggestions available in QueryOptimizer class.")