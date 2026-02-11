"""
Event Management and Calendar Views
------------------------------------
Calendar display, event CRUD operations, event types, and iCal import/export.
"""

import calendar
from datetime import datetime, timedelta
from html import escape

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.management import call_command
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import cache_page

from blog.models import Course, Event, EventType, BlogPost
from blog.views.helpers import admin_required


# =============================================================================
# EVENT MANAGEMENT VIEWS (Admin Only)
# =============================================================================

@admin_required
def event_management(request):
    """Enhanced admin page for managing calendar events"""
    from blog.forms import EventFilterForm
    
    events = Event.objects.all().order_by('-created_at')
    
    # Enhanced filtering
    filter_form = EventFilterForm(request.GET)
    if filter_form.is_valid():
        # Status filtering
        status = filter_form.cleaned_data.get('status')
        if status == 'published':
            events = events.filter(is_published=True)
        elif status == 'draft':
            events = events.filter(is_published=False)
        elif status == 'featured':
            events = events.filter(is_featured=True)
        
        # Custom event type filtering
        event_type_new = filter_form.cleaned_data.get('event_type_new')
        if event_type_new:
            events = events.filter(event_type_new=event_type_new)
        
        # Legacy event type filtering
        event_type = filter_form.cleaned_data.get('event_type')
        if event_type:
            events = events.filter(event_type=event_type)
        
        # Priority filtering
        priority = filter_form.cleaned_data.get('priority')
        if priority:
            events = events.filter(priority=priority)
        
        # Course filtering
        course = filter_form.cleaned_data.get('course')
        if course:
            events = events.filter(course=course)
    
    # Get statistics
    total_events = Event.objects.count()
    published_events = Event.objects.filter(is_published=True).count()
    featured_events = Event.objects.filter(is_featured=True).count()
    custom_type_events = Event.objects.filter(event_type_new__isnull=False).count()
    
    context = {
        'events': events,
        'filter_form': filter_form,
        'event_types': Event.EVENT_TYPE_CHOICES,
        'custom_event_types': EventType.objects.filter(is_active=True).order_by('sort_order', 'name'),
        'stats': {
            'total': total_events,
            'published': published_events,
            'featured': featured_events,
            'custom_types': custom_type_events,
        }
    }
    
    return render(request, 'blog/admin/event_management.html', context)


@user_passes_test(lambda u: u.is_superuser)
def ical_import_export_page(request):
    """Dedicated standalone page for iCal import/export - SUPERUSER ONLY."""
    # Get statistics
    total_events = Event.objects.count()
    published_events = Event.objects.filter(is_published=True).count()
    upcoming_events = Event.objects.filter(
        start_date__gte=datetime.now().date(),
        is_published=True
    ).count()
    courses_with_events = Course.objects.filter(event__isnull=False).distinct().count()
    
    # Get all courses for dropdown
    courses = Course.objects.all().order_by('course_code')
    
    context = {
        'total_events': total_events,
        'published_events': published_events,
        'upcoming_events': upcoming_events,
        'courses_with_events': courses_with_events,
        'courses': courses,
    }
    
    return render(request, 'blog/ical_import_export.html', context)


@admin_required
def admin_event_import_export(request):
    """Admin interface for iCal import/export with web-based functionality."""
    # Get statistics
    total_events = Event.objects.count()
    published_events = Event.objects.filter(is_published=True).count()
    upcoming_events = Event.objects.filter(
        start_date__gte=datetime.now().date(),
        is_published=True
    ).count()
    courses_with_events = Course.objects.filter(event__isnull=False).distinct().count()
    
    # Get all courses for dropdown
    courses = Course.objects.all().order_by('course_code')
    
    context = {
        'total_events': total_events,
        'published_events': published_events,
        'upcoming_events': upcoming_events,
        'courses_with_events': courses_with_events,
        'courses': courses,
    }
    
    return render(request, 'blog/admin/event_import_export.html', context)


@user_passes_test(lambda u: u.is_superuser)
def admin_export_ical(request):
    """Handle iCal export from admin interface - SUPERUSER ONLY."""
    if request.method != 'POST':
        return redirect('admin_event_import_export')
    
    try:
        import io
        import os
        import sys
        import tempfile
        
        # Get form parameters
        export_type = request.POST.get('export_type', 'all')
        course_filter = request.POST.get('course_filter', '')
        start_date = request.POST.get('start_date', '')
        end_date = request.POST.get('end_date', '')
        
        # Create temporary file for export
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.ics', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        # Build command arguments
        cmd_args = [temp_filename]
        
        if course_filter:
            try:
                course = Course.objects.get(id=course_filter)
                cmd_args.extend(['--course', course.course_code])
            except Course.DoesNotExist:
                pass
        
        if start_date:
            cmd_args.extend(['--start-date', start_date])
        
        if end_date:
            cmd_args.extend(['--end-date', end_date])
        
        if export_type == 'published':
            cmd_args.append('--published-only')
        
        # Run export command
        call_command('export_ical', *cmd_args)
        
        # Read the exported file
        with open(temp_filename, 'r', encoding='utf-8') as f:
            ical_content = f.read()
        
        # Clean up temporary file
        os.unlink(temp_filename)
        
        # Create response
        response = HttpResponse(ical_content, content_type='text/calendar; charset=utf-8')
        
        # Generate filename
        filename_parts = ['events']
        if course_filter:
            try:
                course = Course.objects.get(id=course_filter)
                filename_parts.append(course.course_code)
            except Course.DoesNotExist:
                pass
        if export_type == 'published':
            filename_parts.append('published')
        filename_parts.append(datetime.now().strftime('%Y%m%d'))
        
        filename = '_'.join(filename_parts) + '.ics'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        safe_filename = escape(filename)
        messages.success(request, f'Successfully exported events to {safe_filename}')
        return response
        
    except Exception as e:
        safe_error = escape(str(e))[:200]  # Limit error message length and escape HTML
        messages.error(request, f'Export failed: {safe_error}')
        return redirect('admin_event_import_export')


@user_passes_test(lambda u: u.is_superuser)
def admin_import_ical(request):
    """Handle iCal import from admin interface - SUPERUSER ONLY."""
    if request.method != 'POST':
        return redirect('admin_event_import_export')
    
    try:
        import io
        import os
        import sys
        import tempfile
        
        # Get uploaded file
        ical_file = request.FILES.get('ical_file')
        if not ical_file:
            messages.error(request, 'Please select an iCal file to import.')
            return redirect('admin_event_import_export')
        
        # Get form parameters
        default_course = request.POST.get('default_course', '')
        dry_run = request.POST.get('dry_run') == '1'
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.ics', delete=False) as temp_file:
            for chunk in ical_file.chunks():
                temp_file.write(chunk)
            temp_filename = temp_file.name
        
        # Build command arguments
        cmd_args = [temp_filename]
        
        if dry_run:
            cmd_args.append('--dry-run')
        
        cmd_args.extend(['--creator', request.user.username])
        
        if default_course:
            try:
                course = Course.objects.get(id=default_course)
                cmd_args.extend(['--default-course', course.course_code])
            except Course.DoesNotExist:
                pass
        
        # Capture command output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # Run import command
            call_command('import_ical', *cmd_args)
            
            # Get output
            stdout_content = stdout_capture.getvalue()
            stderr_content = stderr_capture.getvalue()
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        # Clean up temporary file
        os.unlink(temp_filename)
        
        # Process results - sanitize command output to prevent XSS
        if stderr_content:
            safe_stderr = escape(stderr_content.strip())[:500]  # Limit length and escape HTML
            messages.error(request, f'Import error: {safe_stderr}')
        elif dry_run:
            safe_stdout = escape(stdout_content.strip())[:1000]  # Limit length and escape HTML
            messages.info(request, f'Preview completed successfully:\n{safe_stdout}')
        else:
            safe_stdout = escape(stdout_content.strip())[:1000]  # Limit length and escape HTML
            messages.success(request, f'Import completed successfully:\n{safe_stdout}')
        
        return redirect('admin_event_import_export')
        
    except Exception as e:
        messages.error(request, f'Import failed: {str(e)}')
        return redirect('admin_event_import_export')


@admin_required
def add_event(request):
    """Enhanced event creation with custom types and colors and recurring events"""
    from blog.forms import EventForm
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            
            # Handle recurring event generation
            if event.is_recurring:
                try:
                    created_count = event.generate_recurring_events()
                    if created_count > 0:
                        messages.success(request, 
                            f'Recurring event "{event.title}" created successfully! '
                            f'Generated {created_count} recurring instances.')
                    else:
                        messages.success(request, 
                            f'Recurring event "{event.title}" created successfully! '
                            f'No recurring instances were generated (check your settings).')
                except Exception as e:
                    messages.warning(request, 
                        f'Event "{event.title}" created but recurring instances failed: {str(e)}')
            else:
                messages.success(request, f'Event "{event.title}" created successfully!')
                
            return redirect('event_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EventForm()
    
    context = {
        'form': form,
        'title': 'Add New Event',
        'submit_text': 'Create Event'
    }
    return render(request, 'blog/admin/event_form.html', context)


@admin_required
def edit_event(request, event_id):
    """Edit an existing event with recurring event handling"""
    from blog.forms import EventForm
    
    event = get_object_or_404(Event, id=event_id)
    old_is_recurring = event.is_recurring  # Store original recurring status
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            updated_event = form.save()
            
            # Handle recurring event changes
            if updated_event.is_recurring and not old_is_recurring:
                # Event was made recurring - generate instances
                try:
                    created_count = updated_event.generate_recurring_events()
                    messages.success(request, 
                        f'Event "{updated_event.title}" updated and made recurring! '
                        f'Generated {created_count} recurring instances.')
                except Exception as e:
                    messages.warning(request, 
                        f'Event updated but recurring instances failed: {str(e)}')
                        
            elif updated_event.is_recurring and old_is_recurring:
                # Event was already recurring - offer to regenerate
                messages.success(request, 
                    f'Recurring event "{updated_event.title}" updated successfully! '
                    f'Use "Generate Recurring Events" action in admin to regenerate instances if needed.')
                    
            elif not updated_event.is_recurring and old_is_recurring:
                # Event was made non-recurring - clean up instances
                try:
                    deleted_count = updated_event.delete_recurring_series()
                    messages.success(request, 
                        f'Event "{updated_event.title}" updated and made non-recurring! '
                        f'Removed {deleted_count} recurring instances.')
                except Exception as e:
                    messages.warning(request, 
                        f'Event updated but cleanup failed: {str(e)}')
            else:
                # Regular non-recurring event update
                messages.success(request, f'Event "{updated_event.title}" updated successfully!')
                
            return redirect('event_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EventForm(instance=event)
    
    context = {
        'form': form,
        'event': event,
        'title': f'Edit Event: {event.title}',
        'submit_text': 'Update Event'
    }
    return render(request, 'blog/admin/event_form.html', context)


@admin_required  
def manage_event_types(request):
    """Manage custom event types"""
    event_types = EventType.objects.all().order_by('sort_order', 'name')
    
    context = {
        'event_types': event_types,
    }
    return render(request, 'blog/admin/event_types.html', context)


@admin_required
def add_event_type(request):
    """Add a new custom event type"""
    from blog.forms import EventTypeForm
    
    if request.method == 'POST':
        form = EventTypeForm(request.POST)
        if form.is_valid():
            event_type = form.save()
            messages.success(request, f'Event type "{event_type.name}" created successfully!')
            return redirect('manage_event_types')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EventTypeForm()
    
    context = {
        'form': form,
        'title': 'Add New Event Type',
        'submit_text': 'Create Event Type'
    }
    return render(request, 'blog/admin/event_type_form.html', context)


@admin_required
def edit_event_type(request, type_id):
    """Edit an existing event type"""
    from blog.forms import EventTypeForm
    
    event_type = get_object_or_404(EventType, id=type_id)
    
    if request.method == 'POST':
        form = EventTypeForm(request.POST, instance=event_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'Event type "{event_type.name}" updated successfully!')
            return redirect('manage_event_types')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EventTypeForm(instance=event_type)
    
    context = {
        'form': form,
        'event_type': event_type,
        'title': f'Edit Event Type: {event_type.name}',
        'submit_text': 'Update Event Type'
    }
    return render(request, 'blog/admin/event_type_form.html', context)


@admin_required
def delete_event_type(request, type_id):
    """Delete an event type"""
    event_type = get_object_or_404(EventType, id=type_id)
    
    # Check if any events are using this type
    events_using_type = Event.objects.filter(event_type_new=event_type).count()
    
    if events_using_type > 0:
        messages.error(request, f'Cannot delete "{event_type.name}" - it is used by {events_using_type} event(s).')
        return redirect('manage_event_types')
    
    event_type_name = event_type.name
    event_type.delete()
    messages.success(request, f'Event type "{event_type_name}" deleted successfully!')
    return redirect('manage_event_types')


def delete_event_form(request, event_id):
    """Delete a calendar event form"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f'Event "{event_title}" deleted successfully!')
        return redirect('event_management')
    
    context = {'event': event}
    return render(request, 'blog/admin/delete_event.html', context)


# =============================================================================
# PUBLIC EVENT CALENDAR
# =============================================================================

@cache_page(900)  # Cache for 15 minutes
def event_calendar(request):
    """Display calendar view of events with Month, Week, and Day views"""
    # Get view mode (month, week, day)
    view_mode = request.GET.get('view', 'month')
    if view_mode not in ['month', 'week', 'day']:
        view_mode = 'month'
    
    # Get year, month, and day with proper validation
    try:
        year_param = request.GET.get('year', '')
        year = int(year_param) if year_param else timezone.now().year
    except (ValueError, TypeError):
        year = timezone.now().year
    
    try:
        month_param = request.GET.get('month', '')
        month = int(month_param) if month_param else timezone.now().month
    except (ValueError, TypeError):
        month = timezone.now().month
    
    try:
        day_param = request.GET.get('day', '')
        day = int(day_param) if day_param else timezone.now().day
    except (ValueError, TypeError):
        day = timezone.now().day
    
    # Validate date ranges
    if month < 1 or month > 12:
        month = timezone.now().month
        year = timezone.now().year
    
    try:
        current_date = timezone.datetime(year, month, day).date()
    except ValueError:
        current_date = timezone.now().date()
        year = current_date.year
        month = current_date.month
        day = current_date.day
    
    # Determine date range based on view mode
    if view_mode == 'month':
        # Month view - show entire month
        start_date = timezone.datetime(year, month, 1)
        if month == 12:
            end_date = timezone.datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = timezone.datetime(year, month + 1, 1) - timedelta(days=1)
    elif view_mode == 'week':
        # Week view - show Monday to Sunday
        weekday = current_date.weekday()  # Monday = 0, Sunday = 6
        start_date = current_date - timedelta(days=weekday)
        end_date = start_date + timedelta(days=6)
    else:  # day view
        # Day view - show single day
        start_date = current_date
        end_date = current_date
    
    # Filter events based on visibility and user authentication
    events_query = Event.objects.filter(
        is_published=True,
        start_date__date__range=[start_date, end_date]
    )
    
    # Apply visibility filtering
    if request.user.is_authenticated:
        # Authenticated users can see both public and registered events
        events = events_query.filter(visibility__in=['public', 'registered'])
    else:
        # Anonymous users can only see public events
        events = events_query.filter(visibility='public')
    
    events = events.order_by('start_date')
    
    # Group events by date
    events_by_date = {}
    for event in events:
        date_key = event.start_date.date()
        if date_key not in events_by_date:
            events_by_date[date_key] = []
        events_by_date[date_key].append(event)
    
    # Generate calendar structure based on view mode
    calendar_weeks = []
    week_days = []
    day_hours = []
    all_day_events = []
    today = timezone.now().date()
    current_month_date = timezone.datetime(year, month, 1).date()
    
    if view_mode == 'month':
        # Month view - use Python calendar module
        cal = calendar.monthcalendar(year, month)
        
        for week in cal:
            week_days_list = []
            for day in week:
                if day == 0:
                    # Empty day (previous/next month)
                    week_days_list.append({
                        'day': '',
                        'is_today': False,
                        'is_current_month': False,
                        'events': []
                    })
                else:
                    day_date = timezone.datetime(year, month, day).date()
                    week_days_list.append({
                        'day': day,
                        'is_today': day_date == today,
                        'is_current_month': True,
                        'date': day_date,
                        'events': events_by_date.get(day_date, [])
                    })
            calendar_weeks.append(week_days_list)
    
    elif view_mode == 'week':
        # Week view - show 7 days starting from Monday
        week_days = []
        for i in range(7):
            day_date = start_date + timedelta(days=i)
            week_days.append({
                'day': day_date.day,
                'date': day_date,
                'weekday': calendar.day_name[day_date.weekday()],
                'weekday_short': calendar.day_abbr[day_date.weekday()],
                'is_today': day_date == today,
                'is_current_month': day_date.month == month,
                'events': events_by_date.get(day_date, [])
            })
        calendar_weeks = [week_days]  # Single week
    
    else:  # day view
        # Day view - show single day with hourly breakdown
        day_hours = []
        for hour in range(24):
            hour_events = []
            for event in events_by_date.get(current_date, []):
                if not event.all_day and event.start_date.hour == hour:
                    hour_events.append(event)
            
            day_hours.append({
                'hour': hour,
                'hour_24': timezone.datetime.combine(current_date, timezone.datetime.min.time().replace(hour=hour)).strftime('%H:00'),
                'events': hour_events
            })
        
        # Add all-day events
        all_day_events = [event for event in events_by_date.get(current_date, []) if event.all_day]
    
    # Navigation logic based on view mode
    if view_mode == 'month':
        # Month navigation
        if month == 1:
            prev_obj = timezone.datetime(year - 1, 12, 1)
        else:
            prev_obj = timezone.datetime(year, month - 1, 1)
        
        if month == 12:
            next_obj = timezone.datetime(year + 1, 1, 1)
        else:
            next_obj = timezone.datetime(year, month + 1, 1)
    
    elif view_mode == 'week':
        # Week navigation
        prev_obj = start_date - timedelta(days=7)
        next_obj = start_date + timedelta(days=7)
    
    else:  # day view
        # Day navigation
        prev_obj = current_date - timedelta(days=1)
        next_obj = current_date + timedelta(days=1)
    
    # Get today's events and upcoming events for sidebar with visibility filtering
    if request.user.is_authenticated:
        todays_events = Event.objects.filter(
            is_published=True,
            start_date__date=today,
            visibility__in=['public', 'registered']
        ).order_by('start_date')
        
        upcoming_events = Event.objects.filter(
            is_published=True,
            start_date__date__gt=today,
            visibility__in=['public', 'registered']
        ).order_by('start_date')[:10]
    else:
        todays_events = Event.objects.filter(
            is_published=True,
            start_date__date=today,
            visibility='public'
        ).order_by('start_date')
        
        upcoming_events = Event.objects.filter(
            is_published=True,
            start_date__date__gt=today,
            visibility='public'
        ).order_by('start_date')[:10]
    
    context = {
        'calendar_weeks': calendar_weeks,
        'week_days': week_days if view_mode == 'week' else None,
        'day_hours': day_hours if view_mode == 'day' else None,
        'all_day_events': all_day_events if view_mode == 'day' else None,
        'current_month': current_month_date,
        'current_date': current_date,
        'today': today,
        'year': year,
        'month': month,
        'day': day,
        'month_name': calendar.month_name[month],
        'view_mode': view_mode,
        'events_by_date': events_by_date,
        'prev_obj': prev_obj,
        'next_obj': next_obj,
        'todays_events': todays_events,
        'upcoming_events': upcoming_events,
    }
    
    return render(request, 'blog/event_calendar.html', context)


# =============================================================================
# iCAL IMPORT/EXPORT HELPER FUNCTIONS
# =============================================================================

@login_required
def export_events_ical(request):
    """Export events to iCal format with admin interface."""
    # Check if user is admin
    if not request.user.is_staff:
        messages.error(request, 'Only administrators can export events.')
        return redirect('event_management')
    
    # Get filter parameters
    course_id = request.GET.get('course')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    published_only = request.GET.get('published_only') == 'on'
    
    # Build queryset
    queryset = Event.objects.all()
    
    if published_only:
        queryset = queryset.filter(is_published=True)
    
    if course_id:
        try:
            course = Course.objects.get(id=course_id)
            queryset = queryset.filter(course=course)
        except Course.DoesNotExist:
            messages.error(request, f'Course not found.')
            return redirect('event_management')
    
    if start_date:
        queryset = queryset.filter(start_date__date__gte=start_date)
    
    if end_date:
        queryset = queryset.filter(start_date__date__lte=end_date)
    
    queryset = queryset.order_by('start_date')
    event_count = queryset.count()
    
    if event_count == 0:
        messages.warning(request, 'No events found matching the criteria.')
        return redirect('event_management')
    
    # Generate iCal content
    ical_content = _create_admin_ical_content(queryset)
    
    # Create HTTP response
    response = HttpResponse(ical_content, content_type='text/calendar')
    filename = f"events_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    messages.success(request, f'Successfully exported {event_count} events to {filename}')
    
    return response


@login_required
def import_events_ical(request):
    """Import events from iCal file with admin interface."""
    import os
    import sys
    import tempfile
    from io import StringIO
    
    # Check if user is admin
    if not request.user.is_staff:
        messages.error(request, 'Only administrators can import events.')
        return redirect('event_management')
    
    if request.method == 'POST':
        ical_file = request.FILES.get('ical_file')
        dry_run = request.POST.get('dry_run') == 'on'
        default_course_id = request.POST.get('default_course')
        
        if not ical_file:
            messages.error(request, 'Please select an iCal file to import.')
            return redirect('import_events_ical')
        
        if not ical_file.name.lower().endswith('.ics'):
            messages.error(request, 'Please upload a valid .ics file.')
            return redirect('import_events_ical')
        
        try:
            # Save file temporarily
            with tempfile.NamedTemporaryFile(mode='w+b', suffix='.ics', delete=False) as temp_file:
                for chunk in ical_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            # Prepare command arguments
            cmd_args = [temp_file_path]
            cmd_kwargs = {
                'creator': request.user.username,
                'verbosity': 1,
            }
            
            if dry_run:
                cmd_kwargs['dry_run'] = True
            
            if default_course_id:
                try:
                    course = Course.objects.get(id=default_course_id)
                    cmd_kwargs['default_course'] = course.course_code
                except Course.DoesNotExist:
                    pass
            
            # Capture command output
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_capture = StringIO()
            stderr_capture = StringIO()
            
            try:
                sys.stdout = stdout_capture
                sys.stderr = stderr_capture
                
                # Import management command from the same module
                from blog.management.commands.import_ical import Command
                import_command = Command()
                import_command.handle(*cmd_args, **cmd_kwargs)
                
                output = stdout_capture.getvalue()
                errors = stderr_capture.getvalue()
                
                if errors:
                    messages.error(request, f'Import errors: {errors}')
                else:
                    if dry_run:
                        messages.info(request, f'Dry run completed. Output: {output}')
                    else:
                        messages.success(request, f'Import completed successfully. {output}')
                
            except Exception as e:
                messages.error(request, f'Import failed: {str(e)}')
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
        
        return redirect('event_management')
    
    # GET request - show import form
    courses = Course.objects.all().order_by('course_code')
    context = {
        'courses': courses,
        'page_title': 'Import iCal Events',
    }
    
    return render(request, 'blog/admin/import_ical.html', context)


def _create_admin_ical_content(queryset):
    """Create iCal content from event queryset for admin export."""
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
        lines.extend(_create_admin_event_lines(event))
    
    lines.append('END:VCALENDAR')
    return '\r\n'.join(lines)


def _create_admin_event_lines(event):
    """Create iCal lines for a single event in admin export."""
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
        f'SUMMARY:{_escape_ical_text(event.title)}',
    ]
    
    # Add description if present
    if event.description:
        lines.append(f'DESCRIPTION:{_escape_ical_text(event.description)}')
    
    # Add location (course title)
    if event.course:
        lines.append(f'LOCATION:{_escape_ical_text(event.course.title)}')
    
    # Add categories
    lines.append(f'CATEGORIES:{event.get_event_type_display()}')
    
    # Add priority
    lines.append(f'PRIORITY:{_get_admin_ical_priority(event.priority)}')
    
    # Add organizer (event creator)
    if event.created_by:
        organizer_email = event.created_by.email or f'{event.created_by.username}@fortisauris.lms'
        organizer_name = event.created_by.get_full_name() or event.created_by.username
        lines.append(f'ORGANIZER;CN={_escape_ical_text(organizer_name)}:MAILTO:{organizer_email}')
    
    # Add custom properties
    lines.append(f'X-LMS-EVENT-TYPE:{event.event_type}')
    lines.append(f'X-LMS-PRIORITY:{event.priority}')
    lines.append(f'X-LMS-VISIBILITY:{event.visibility}')
    
    if event.course:
        lines.append(f'X-LMS-COURSE-CODE:{event.course.course_code}')
    
    lines.append('END:VEVENT')
    return lines


def _escape_ical_text(text):
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


def _get_admin_ical_priority(priority):
    """Convert LMS priority to iCal priority (1=high, 5=medium, 9=low)."""
    priority_map = {
        'urgent': '1',
        'high': '3',
        'normal': '5',
        'low': '9'
    }
    return priority_map.get(priority, '5')


# 404 Error Handler
def custom_404(request, exception):
    """Custom 404 handler with helpful construction page"""
    return render(request, 'blog/404.html', status=404)


# Alias for backward compatibility
delete_event = delete_event_form
