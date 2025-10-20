from django.core.management.base import BaseCommand
from blog.models import EventType


class Command(BaseCommand):
    help = 'Create default event types with colors and icons'

    def handle(self, *args, **options):
        default_types = [
            {
                'name': 'Workshop',
                'slug': 'workshop',
                'color': '#6f42c1',
                'background_color': '#0f1419',
                'icon': 'fas fa-laptop-code',
                'description': 'Hands-on learning sessions and coding workshops',
                'sort_order': 1
            },
            {
                'name': 'Seminar',
                'slug': 'seminar',
                'color': '#17a2b8',
                'background_color': '#0f1419',
                'icon': 'fas fa-chalkboard-teacher',
                'description': 'Educational seminars and presentations',
                'sort_order': 2
            },
            {
                'name': 'Conference',
                'slug': 'conference',
                'color': '#007bff',
                'background_color': '#0f1419',
                'icon': 'fas fa-users',
                'description': 'Large-scale conferences and symposiums',
                'sort_order': 3
            },
            {
                'name': 'Exam',
                'slug': 'exam',
                'color': '#fd7e14',
                'background_color': '#0f1419',
                'icon': 'fas fa-graduation-cap',
                'description': 'Tests, quizzes, and examinations',
                'sort_order': 4
            },
            {
                'name': 'Deadline',
                'slug': 'deadline',
                'color': '#dc3545',
                'background_color': '#0f1419',
                'icon': 'fas fa-exclamation-triangle',
                'description': 'Assignment and project deadlines',
                'sort_order': 5
            },
            {
                'name': 'Meeting',
                'slug': 'meeting',
                'color': '#28a745',
                'background_color': '#0f1419',
                'icon': 'fas fa-handshake',
                'description': 'Team meetings and discussions',
                'sort_order': 6
            },
            {
                'name': 'Holiday',
                'slug': 'holiday',
                'color': '#ffc107',
                'background_color': '#0f1419',
                'icon': 'fas fa-gift',
                'description': 'Holidays and special occasions',
                'sort_order': 7
            },
            {
                'name': 'Maintenance',
                'slug': 'maintenance',
                'color': '#6c757d',
                'background_color': '#0f1419',
                'icon': 'fas fa-tools',
                'description': 'System maintenance and downtime',
                'sort_order': 8
            },
            {
                'name': 'Career Event',
                'slug': 'career-event',
                'color': '#e83e8c',
                'background_color': '#0f1419',
                'icon': 'fas fa-briefcase',
                'description': 'Career development and job fairs',
                'sort_order': 9
            },
            {
                'name': 'Social Event',
                'slug': 'social-event',
                'color': '#20c997',
                'background_color': '#0f1419',
                'icon': 'fas fa-heart',
                'description': 'Social gatherings and community events',
                'sort_order': 10
            }
        ]

        created_count = 0
        updated_count = 0

        for event_type_data in default_types:
            event_type, created = EventType.objects.get_or_create(
                slug=event_type_data['slug'],
                defaults=event_type_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created event type: {event_type.name}')
                )
            else:
                # Update existing event type with new data
                for key, value in event_type_data.items():
                    setattr(event_type, key, value)
                event_type.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated event type: {event_type.name}')
                )

        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(default_types)} event types:\n'
                f'  • Created: {created_count}\n'
                f'  • Updated: {updated_count}\n\n'
                f'Event types are now ready for use in the admin interface!'
            )
        )