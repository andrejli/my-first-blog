"""
Management command to import events from iCal (.ics) files.

Usage:
    python manage.py import_ical path/to/events.ics
    python manage.py import_ical path/to/events.ics --dry-run
    python manage.py import_ical path/to/events.ics --creator=admin
"""

import os
import re
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from blog.models import Event, Course


class Command(BaseCommand):
    help = 'Import events from iCal (.ics) file'

    def add_arguments(self, parser):
        parser.add_argument('ical_file', type=str, help='Path to the iCal (.ics) file')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview import without creating events'
        )
        parser.add_argument(
            '--creator',
            type=str,
            default='admin',
            help='Username of the user to set as event creator (default: admin)'
        )
        parser.add_argument(
            '--default-course',
            type=str,
            help='Course code to assign to events (optional)'
        )

    def handle(self, *args, **options):
        ical_file = options['ical_file']
        dry_run = options['dry_run']
        creator_username = options['creator']
        default_course_code = options.get('default_course')

        # Validate file
        if not os.path.exists(ical_file):
            raise CommandError(f'iCal file not found: {ical_file}')

        if not ical_file.lower().endswith('.ics'):
            raise CommandError('File must have .ics extension')

        # Get creator user
        try:
            creator = User.objects.get(username=creator_username)
        except User.DoesNotExist:
            raise CommandError(f'User "{creator_username}" not found')

        # Get default course if specified
        default_course = None
        if default_course_code:
            try:
                default_course = Course.objects.get(course_code=default_course_code)
            except Course.DoesNotExist:
                raise CommandError(f'Course "{default_course_code}" not found')

        # Parse iCal file
        events = self.parse_ical_file(ical_file)
        
        if not events:
            self.stdout.write(self.style.WARNING('No events found in iCal file'))
            return

        self.stdout.write(f'Found {len(events)} events in iCal file')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No events will be created'))

        # Import events
        imported_count = 0
        skipped_count = 0
        error_count = 0

        for event_data in events:
            try:
                if dry_run:
                    self.stdout.write(f'PREVIEW: {event_data["title"]} - {event_data["start_date"]}')
                    imported_count += 1
                else:
                    # Check if event already exists (by title and start date)
                    existing = Event.objects.filter(
                        title=event_data['title'],
                        start_date=event_data['start_date']
                    ).first()

                    if existing:
                        self.stdout.write(f'SKIPPED: Event already exists - {event_data["title"]}')
                        skipped_count += 1
                        continue

                    # Create event
                    event = Event.objects.create(
                        title=event_data['title'],
                        description=event_data.get('description', ''),
                        start_date=event_data['start_date'],
                        end_date=event_data.get('end_date'),
                        event_type=self.map_category_to_event_type(event_data.get('categories', '')),
                        priority=self.map_priority(event_data.get('priority', '5')),
                        created_by=creator,
                        course=default_course,
                        is_published=True
                    )

                    self.stdout.write(f'IMPORTED: {event.title} - {event.start_date}')
                    imported_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'ERROR importing {event_data.get("title", "Unknown")}: {str(e)}'))
                error_count += 1

        # Summary
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'DRY RUN COMPLETE: {imported_count} events would be imported'))
        else:
            self.stdout.write(self.style.SUCCESS(f'IMPORT COMPLETE: {imported_count} events imported'))
            if skipped_count > 0:
                self.stdout.write(self.style.WARNING(f'Skipped {skipped_count} duplicate events'))
            if error_count > 0:
                self.stdout.write(self.style.ERROR(f'Failed to import {error_count} events'))

    def parse_ical_file(self, ical_file):
        """Parse iCal file and extract event data."""
        events = []
        
        with open(ical_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split into events
        event_blocks = re.findall(r'BEGIN:VEVENT.*?END:VEVENT', content, re.DOTALL)

        for block in event_blocks:
            event_data = self.parse_event_block(block)
            if event_data:
                events.append(event_data)

        return events

    def parse_event_block(self, block):
        """Parse individual event block from iCal."""
        event_data = {}
        
        lines = block.split('\n')
        current_field = None
        current_value = ''

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Handle line continuation (starts with space or tab)
            if line.startswith(' ') or line.startswith('\t'):
                current_value += line[1:]
                continue

            # Process previous field
            if current_field:
                event_data[current_field] = current_value

            # Parse new field
            if ':' in line:
                field, value = line.split(':', 1)
                current_field = field.upper()
                current_value = value
            else:
                current_field = None
                current_value = ''

        # Process last field
        if current_field:
            event_data[current_field] = current_value

        # Convert to our format
        return self.convert_event_data(event_data)

    def convert_event_data(self, raw_data):
        """Convert raw iCal data to our event format."""
        if 'SUMMARY' not in raw_data:
            return None

        event_data = {
            'title': raw_data.get('SUMMARY', 'Untitled Event'),
            'description': raw_data.get('DESCRIPTION', ''),
            'categories': raw_data.get('CATEGORIES', ''),
            'priority': raw_data.get('PRIORITY', '5'),
        }

        # Parse dates
        try:
            dtstart = raw_data.get('DTSTART', '')
            if dtstart:
                event_data['start_date'] = self.parse_datetime(dtstart)

            dtend = raw_data.get('DTEND', '')
            if dtend:
                event_data['end_date'] = self.parse_datetime(dtend)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error parsing dates for {event_data["title"]}: {str(e)}'))
            return None

        return event_data

    def parse_datetime(self, dt_string):
        """Parse iCal datetime string."""
        # Remove timezone info for simplicity
        dt_string = dt_string.split(';')[0]
        
        # Basic format: YYYYMMDDTHHMMSS
        if 'T' in dt_string:
            dt = datetime.strptime(dt_string, '%Y%m%dT%H%M%S')
        else:
            # Date only: YYYYMMDD
            dt = datetime.strptime(dt_string, '%Y%m%d')
        
        # Convert to timezone-aware datetime
        return timezone.make_aware(dt, timezone.get_current_timezone())

    def map_category_to_event_type(self, categories):
        """Map iCal categories to our event types."""
        categories_lower = categories.lower()
        
        mapping = {
            'deadline': 'deadline',
            'assignment': 'deadline',
            'exam': 'exam',
            'test': 'exam',
            'holiday': 'holiday',
            'vacation': 'holiday',
            'maintenance': 'maintenance',
            'meeting': 'meeting',
            'workshop': 'workshop',
            'training': 'workshop',
            'announcement': 'announcement',
        }
        
        for keyword, event_type in mapping.items():
            if keyword in categories_lower:
                return event_type
        
        return 'general'

    def map_priority(self, priority_str):
        """Map iCal priority to our priority levels."""
        try:
            priority_num = int(priority_str)
            if priority_num <= 2:
                return 'urgent'
            elif priority_num <= 4:
                return 'high'
            elif priority_num <= 6:
                return 'normal'
            else:
                return 'low'
        except (ValueError, TypeError):
            return 'normal'