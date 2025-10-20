from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from blog.models import Event, Course, Lesson


class Command(BaseCommand):
    help = 'Create sample events with Obsidian-style lesson links for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing events before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            Event.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all existing events.'))

        # Get or create admin user
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')

        # Get available courses and lessons
        courses = Course.objects.all()
        lessons = Lesson.objects.all()

        if not courses.exists():
            self.stdout.write(
                self.style.ERROR('No courses found. Please create some courses and lessons first.')
            )
            return

        if not lessons.exists():
            self.stdout.write(
                self.style.ERROR('No lessons found. Please create some lessons first.')
            )
            return

        # Sample events with various linking methods
        sample_events = [
            {
                'title': 'Introduction to Programming Concepts',
                'description': 'Learn the basic concepts of programming before diving into Python.',
                'obsidian_link': '[[Python Fundamentals - Introduction to Programming]]',
                'days_from_now': 1,
                'event_type': 'workshop'
            },
            {
                'title': 'Variables and Data Types Study Session',
                'description': 'Review session covering variables, strings, numbers, and basic data types.',
                'obsidian_link': '[[Variables and Data Types]]',  # Just lesson title
                'days_from_now': 3,
                'event_type': 'general'
            },
            {
                'title': 'Web Development Workshop',
                'description': 'Hands-on workshop for HTML, CSS, and JavaScript basics.',
                'obsidian_link': '[[Web Development - HTML Basics]]',
                'days_from_now': 7,
                'event_type': 'workshop'
            },
            {
                'title': 'Database Fundamentals Review',
                'description': 'Review key database concepts before the upcoming exam.',
                'obsidian_link': 'Database Design',  # Search term without brackets
                'days_from_now': 10,
                'event_type': 'exam'
            },
            {
                'title': 'Direct Lesson Link Example',
                'description': 'This event uses a direct lesson link instead of Obsidian syntax.',
                'linked_lesson': lessons.first() if lessons.exists() else None,  # Direct lesson link
                'days_from_now': 14,
                'event_type': 'general'
            }
        ]

        created_count = 0
        base_time = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)

        for event_data in sample_events:
            start_date = base_time + timedelta(days=event_data['days_from_now'])
            end_date = start_date + timedelta(hours=2)  # 2-hour events

            event = Event.objects.create(
                title=event_data['title'],
                description=event_data['description'],
                event_type=event_data['event_type'],
                start_date=start_date,
                end_date=end_date,
                created_by=admin_user,
                is_published=True,
                visibility='public',
                obsidian_link=event_data.get('obsidian_link', ''),
                linked_lesson=event_data.get('linked_lesson')
            )

            created_count += 1
            
            # Test the linking functionality
            linked_lesson = event.get_linked_lesson()
            lesson_url = event.get_lesson_url()
            lesson_display = event.get_lesson_display()
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created: {event.title}')
            )
            
            if event.obsidian_link:
                self.stdout.write(f'  📎 Obsidian Link: {event.obsidian_link}')
            
            if event.linked_lesson:
                self.stdout.write(f'  🔗 Direct Link: {event.linked_lesson}')
            
            if linked_lesson:
                self.stdout.write(f'  ✅ Resolved to: {linked_lesson.course.title} - {linked_lesson.title}')
            else:
                self.stdout.write(f'  ❌ Could not resolve lesson link')
            
            if lesson_url:
                self.stdout.write(f'  🌐 URL: {lesson_url}')
            
            if lesson_display:
                self.stdout.write(f'  📝 Display: {lesson_display}')
            
            self.stdout.write('')  # Empty line

        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} sample events with lesson links!\n\n'
                f'Test the functionality by:\n'
                f'1. Visiting the calendar at /calendar/\n'
                f'2. Checking event management at /event-management/\n'
                f'3. Looking for lesson link buttons in event details\n\n'
                f'Obsidian Link Examples:\n'
                f'• [[Course Name - Lesson Title]] - Full format\n'
                f'• [[Lesson Title]] - Lesson only\n'
                f'• Lesson Title - Simple search\n'
            )
        )