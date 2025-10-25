"""
Management command to export events to iCal (.ics) format.

Usage:
    python manage.py export_ical events.ics
    python manage.py export_ical events.ics --course=CS101
    python manage.py export_ical events.ics --start-date=2025-01-01 --end-date=2025-12-31
"""

import os
from datetime import datetime, date
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from blog.models import Event, Course


class Command(BaseCommand):
    help = 'Export events to iCal (.ics) format'

    def add_arguments(self, parser):
        parser.add_argument('output_file', type=str, help='Output iCal file path (.ics)')
        parser.add_argument(
            '--course',
            type=str,
            help='Export events for specific course code only'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Export events from this date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='Export events until this date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--published-only',
            action='store_true',
            help='Export only published events (default: all events)'
        )

    def handle(self, *args, **options):
        output_file = options['output_file']
        course_code = options.get('course')
        start_date_str = options.get('start_date')
        end_date_str = options.get('end_date')
        published_only = options.get('published_only', False)

        # Validate output file
        if not output_file.lower().endswith('.ics'):
            output_file += '.ics'

        # Build queryset
        queryset = Event.objects.all()

        if published_only:
            queryset = queryset.filter(is_published=True)

        if course_code:
            try:
                course = Course.objects.get(course_code=course_code)
                queryset = queryset.filter(course=course)
                self.stdout.write(f'Filtering events for course: {course.title}')
            except Course.DoesNotExist:
                raise CommandError(f'Course "{course_code}" not found')

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(start_date__date__gte=start_date)
                self.stdout.write(f'Filtering events from: {start_date}')
            except ValueError:
                raise CommandError('Invalid start date format. Use YYYY-MM-DD')

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(start_date__date__lte=end_date)
                self.stdout.write(f'Filtering events until: {end_date}')
            except ValueError:
                raise CommandError('Invalid end date format. Use YYYY-MM-DD')

        queryset = queryset.order_by('start_date')
        event_count = queryset.count()

        if event_count == 0:
            self.stdout.write(self.style.WARNING('No events found matching criteria'))
            return

        self.stdout.write(f'Exporting {event_count} events...')

        # Generate iCal content
        ical_content = self.create_ical_content(queryset)

        # Write to file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(ical_content)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully exported {event_count} events to {output_file}'))
            
            # Show file info
            file_size = os.path.getsize(output_file)
            self.stdout.write(f'File size: {file_size} bytes')
            
        except Exception as e:
            raise CommandError(f'Error writing file: {str(e)}')

    def create_ical_content(self, queryset):
        """Create iCal content from event queryset."""
        lines = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//FORTIS AURIS LMS//Event Calendar//EN',
            'CALSCALE:GREGORIAN',
            'METHOD:PUBLISH',
            f'X-WR-CALNAME:FORTIS AURIS LMS Events',
            f'X-WR-CALDESC:Events exported from FORTIS AURIS Learning Management System',
        ]

        for event in queryset:
            lines.extend(self.create_event_lines(event))

        lines.append('END:VCALENDAR')
        return '\r\n'.join(lines)

    def create_event_lines(self, event):
        """Create iCal lines for a single event."""
        # Format dates for iCal
        start_dt = event.start_date.strftime('%Y%m%dT%H%M%S')
        end_dt = event.end_date.strftime('%Y%m%dT%H%M%S') if event.end_date else start_dt
        created_dt = event.created_at.strftime('%Y%m%dT%H%M%SZ')
        updated_dt = event.updated_at.strftime('%Y%m%dT%H%M%SZ')

        lines = [
            'BEGIN:VEVENT',
            f'UID:{event.id}@fortisauris.lms',
            f'DTSTART:{start_dt}',
            f'DTEND:{end_dt}',
            f'DTSTAMP:{created_dt}',
            f'CREATED:{created_dt}',
            f'LAST-MODIFIED:{updated_dt}',
            f'SUMMARY:{self.escape_text(event.title)}',
        ]

        # Add description if present
        if event.description:
            lines.append(f'DESCRIPTION:{self.escape_text(event.description)}')

        # Add location (course title)
        if event.course:
            lines.append(f'LOCATION:{self.escape_text(event.course.title)}')

        # Add categories
        lines.append(f'CATEGORIES:{event.get_event_type_display()}')

        # Add priority
        lines.append(f'PRIORITY:{self.get_ical_priority(event.priority)}')

        # Add organizer (event creator)
        if event.created_by:
            organizer_email = event.created_by.email or f'{event.created_by.username}@fortisauris.lms'
            organizer_name = event.created_by.get_full_name() or event.created_by.username
            lines.append(f'ORGANIZER;CN={self.escape_text(organizer_name)}:MAILTO:{organizer_email}')

        # Add URL if there's a lesson link
        if event.get_lesson_url():
            lines.append(f'URL:http://localhost:8000{event.get_lesson_url()}')

        # Add custom properties
        lines.append(f'X-LMS-EVENT-TYPE:{event.event_type}')
        lines.append(f'X-LMS-PRIORITY:{event.priority}')
        lines.append(f'X-LMS-VISIBILITY:{event.visibility}')
        
        if event.course:
            lines.append(f'X-LMS-COURSE-CODE:{event.course.course_code}')

        lines.append('END:VEVENT')
        return lines

    def escape_text(self, text):
        """Escape text for iCal format."""
        if not text:
            return ''
        
        # Replace special characters
        text = str(text)
        text = text.replace('\\', '\\\\')
        text = text.replace(',', '\\,')
        text = text.replace(';', '\\;')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '')
        
        return text

    def get_ical_priority(self, priority):
        """Convert LMS priority to iCal priority (1=high, 5=medium, 9=low)."""
        priority_map = {
            'urgent': '1',
            'high': '3',
            'normal': '5',
            'low': '9'
        }
        return priority_map.get(priority, '5')