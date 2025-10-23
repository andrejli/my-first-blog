"""
Management command to generate recurring events
Usage: python manage.py generate_recurring_events
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from blog.models import Event


class Command(BaseCommand):
    help = 'Generate recurring event instances for all recurring events'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-ahead',
            type=int,
            default=90,
            help='Generate events up to N days ahead (default: 90)',
        )
        parser.add_argument(
            '--event-id',
            type=int,
            help='Generate instances for specific event ID only',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating events',
        )
        parser.add_argument(
            '--force-regenerate',
            action='store_true',
            help='Delete existing instances and regenerate all',
        )

    def handle(self, *args, **options):
        days_ahead = options.get('days_ahead', 90)
        event_id = options.get('event_id', None)
        dry_run = options.get('dry_run', False)
        force_regenerate = options.get('force_regenerate', False)
        
        self.stdout.write(
            self.style.SUCCESS(f'Generating recurring events ({"DRY RUN" if dry_run else "LIVE RUN"})')
        )
        
        # Get recurring events
        if event_id:
            try:
                recurring_events = Event.objects.filter(id=event_id, is_recurring=True, parent_event=None)
                if not recurring_events.exists():
                    raise CommandError(f'Event with ID {event_id} not found or not a recurring event')
            except Event.DoesNotExist:
                raise CommandError(f'Event with ID {event_id} does not exist')
        else:
            recurring_events = Event.objects.filter(is_recurring=True, parent_event=None)
        
        if not recurring_events.exists():
            self.stdout.write(self.style.WARNING('[WARNING] No recurring events found'))
            return
        
        total_created = 0
        total_deleted = 0
        
        for event in recurring_events:
            self.stdout.write(f'\n[EVENT] Processing: {event.title}')
            self.stdout.write(f'   Pattern: {event.recurrence_pattern}')
            self.stdout.write(f'   Course: {event.course.title if event.course else "No course"}')
            
            if force_regenerate:
                # Delete existing instances
                existing_count = event.recurring_instances.count()
                if not dry_run:
                    event.recurring_instances.all().delete()
                total_deleted += existing_count
                self.stdout.write(f'   [DELETED] Removed {existing_count} existing instances')
            
            # Set end date based on days_ahead
            if not event.recurrence_end_date:
                temp_end_date = timezone.now() + timedelta(days=days_ahead)
                event.recurrence_end_date = temp_end_date
            
            # Generate instances
            if not dry_run:
                instances = event.generate_recurring_events(save=True)
            else:
                instances = event.generate_recurring_events(save=False)
            
            created_count = len(instances)
            total_created += created_count
            
            self.stdout.write(f'   [SUCCESS] Created {created_count} new instances')
            
            # Show first few instances as preview
            if instances:
                self.stdout.write('   [PREVIEW] Instances:')
                for i, instance in enumerate(instances[:5]):
                    self.stdout.write(f'      {i+1}. {instance.start_date.strftime("%Y-%m-%d %H:%M")} - {instance.title}')
                if len(instances) > 5:
                    self.stdout.write(f'      ... and {len(instances) - 5} more')
        
        # Summary
        self.stdout.write(f'\n[SUMMARY]:')
        self.stdout.write(f'   Events processed: {recurring_events.count()}')
        if force_regenerate:
            self.stdout.write(f'   Instances deleted: {total_deleted}')
        self.stdout.write(f'   Instances created: {total_created}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('[DRY RUN] This was a DRY RUN - no events were actually created')
            )
            self.stdout.write('Run without --dry-run to actually create the events')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'[SUCCESS] Successfully generated {total_created} recurring event instances!')
            )
            
        # Show next steps
        self.stdout.write(f'\n[INFO] Next steps:')
        self.stdout.write(f'   1. Visit calendar to see generated events: /calendar/')
        self.stdout.write(f'   2. Set up cron job to run this command regularly')
        self.stdout.write(f'   3. Use --days-ahead to control how far ahead to generate')
        self.stdout.write(f'   4. Use --force-regenerate to refresh all instances')