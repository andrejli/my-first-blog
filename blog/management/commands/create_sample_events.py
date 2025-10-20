"""
Django management command to create sample events with posters for testing
"""
import os
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files import File
from django.contrib.auth.models import User
from blog.models import Event


class Command(BaseCommand):
    help = 'Creates sample events with posters for testing the calendar poster display feature'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing events before creating new ones',
        )

    def handle(self, *args, **options):
        # Get or create an admin user to assign as event creator
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            admin_user = User.objects.first()
        
        if not admin_user:
            self.stdout.write(self.style.ERROR('No users found in database. Please create a user first.'))
            return

        if options['clear']:
            self.stdout.write('Clearing existing events...')
            Event.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing events cleared.'))

        # Sample events data - spread across different days for realistic testing
        sample_events = [
            {
                'title': 'Python Programming Workshop',
                'description': 'Learn Python fundamentals and advanced concepts in this hands-on workshop. Perfect for beginners and intermediate developers.',
                'event_type': 'workshop',
                'priority': 'high',
                'start_date': timezone.now() + timedelta(days=2),  # Oct 22
                'end_date': timezone.now() + timedelta(days=2, hours=3),
                'all_day': False,
                'visibility': 'public',
                'poster_filename': 'python_workshop_poster.jpg'
            },
            {
                'title': 'Database Design Fundamentals',
                'description': 'Comprehensive lecture on database design principles, normalization, and best practices for modern applications.',
                'event_type': 'general',
                'priority': 'normal',
                'start_date': timezone.now() + timedelta(days=5),  # Oct 25
                'end_date': timezone.now() + timedelta(days=5, hours=2),
                'all_day': False,
                'visibility': 'public',
                'poster_filename': 'database_lecture_poster.jpg'
            },
            {
                'title': 'Web Development Bootcamp',
                'description': 'Intensive 5-day bootcamp covering HTML, CSS, JavaScript, and modern web frameworks.',
                'event_type': 'workshop',
                'priority': 'high',
                'start_date': timezone.now() + timedelta(days=8),  # Oct 28
                'end_date': timezone.now() + timedelta(days=12),
                'all_day': True,
                'visibility': 'public',
                'poster_filename': 'web_bootcamp_poster.jpg'
            },
            {
                'title': 'AI & Machine Learning Seminar',
                'description': 'Explore the latest trends in artificial intelligence and machine learning technologies.',
                'event_type': 'general',
                'priority': 'high',
                'start_date': timezone.now() + timedelta(days=15),  # Nov 4
                'end_date': timezone.now() + timedelta(days=15, hours=4),
                'all_day': False,
                'visibility': 'public',
                'poster_filename': 'ai_seminar_poster.jpg'
            },
            {
                'title': 'Career Development Session',
                'description': 'Professional development workshop focusing on resume building, interview skills, and career planning.',
                'event_type': 'general',
                'priority': 'normal',
                'start_date': timezone.now() + timedelta(days=18),  # Nov 7
                'end_date': timezone.now() + timedelta(days=18, hours=2.5),
                'all_day': False,
                'visibility': 'registered',
                'poster_filename': 'career_session_poster.jpg'
            },
            {
                'title': 'Cybersecurity Awareness',
                'description': 'Essential cybersecurity training covering threat detection, prevention, and best security practices.',
                'event_type': 'general',
                'priority': 'high',
                'start_date': timezone.now() + timedelta(days=22),  # Nov 11
                'end_date': timezone.now() + timedelta(days=22, hours=3),
                'all_day': False,
                'visibility': 'public',
                'poster_filename': 'cybersecurity_poster.jpg'
            },
            {
                'title': 'Project Showcase Event',
                'description': 'Students present their final projects and demonstrate their technical achievements.',
                'event_type': 'general',
                'priority': 'normal',
                'start_date': timezone.now() + timedelta(days=26),  # Nov 15
                'end_date': timezone.now() + timedelta(days=26, hours=4),
                'all_day': False,
                'visibility': 'public',
                'poster_filename': 'project_showcase_poster.jpg'
            },
            {
                'title': 'Cloud Computing Deep Dive',
                'description': 'Advanced technical session on cloud architectures, containers, and modern deployment strategies.',
                'event_type': 'general',
                'priority': 'normal',
                'start_date': timezone.now() + timedelta(days=30),  # Nov 19
                'end_date': timezone.now() + timedelta(days=30, hours=3.5),
                'all_day': False,
                'visibility': 'registered',
                'poster_filename': 'cloud_computing_poster.jpg'
            }
        ]

        media_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'media', 'event_posters')
        
        self.stdout.write('Creating sample events with posters...')
        self.stdout.write(f'Using admin user: {admin_user.username}')
        
        for event_data in sample_events:
            # Create the event
            event = Event.objects.create(
                title=event_data['title'],
                description=event_data['description'],
                event_type=event_data['event_type'],
                priority=event_data['priority'],
                start_date=event_data['start_date'],
                end_date=event_data['end_date'],
                all_day=event_data['all_day'],
                visibility=event_data['visibility'],
                is_published=True,
                is_featured=True,
                created_by=admin_user
            )
            
            # Attach poster if file exists
            poster_path = os.path.join(media_path, event_data['poster_filename'])
            if os.path.exists(poster_path):
                try:
                    with open(poster_path, 'rb') as f:
                        event.poster.save(
                            event_data['poster_filename'],
                            File(f),
                            save=True
                        )
                    self.stdout.write(f'  ✓ Created event: {event.title} (with poster)')
                except Exception as e:
                    self.stdout.write(f'  ⚠ Created event: {event.title} (poster failed: {e})')
            else:
                self.stdout.write(f'  ⚠ Created event: {event.title} (poster not found: {poster_path})')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(sample_events)} sample events!'))
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('1. Visit http://localhost:8000/calendar/ to see the calendar')
        self.stdout.write('2. Test different views (Month/Week/Day) to see poster indicators')
        self.stdout.write('3. Check the sidebar for poster thumbnails')
        self.stdout.write('4. Click on poster thumbnails to view full-size images')