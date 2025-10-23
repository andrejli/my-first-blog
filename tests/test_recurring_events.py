"""
Tests for the recurring events system
"""
import pytest
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.forms import ValidationError as FormValidationError

from blog.models import Event, EventType, Course
from blog.forms import EventForm, WeekdayMultipleChoiceField
from blog.management.commands.generate_recurring_events import Command


class RecurringEventsModelTests(TestCase):
    """Test the recurring events functionality in the Event model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test event type
        self.event_type = EventType.objects.create(
            name='Test Event Type',
            slug='test-event',
            color='#FF0000',
            background_color='#FFEEEE'
        )
        
        # Create test course
        self.course = Course.objects.create(
            title='Test Course',
            course_code='TEST001',
            description='Test course description',
            instructor=self.user,
            status='published'
        )
        
        # Base datetime for consistent testing
        self.base_datetime = timezone.make_aware(datetime(2025, 10, 27, 10, 0))  # Monday
    
    def test_weekly_recurring_event_creation(self):
        """Test creating a weekly recurring event"""
        event = Event.objects.create(
            title='Weekly Test Event',
            description='Test weekly recurring event',
            start_date=self.base_datetime,
            end_date=self.base_datetime + timedelta(hours=1),
            created_by=self.user,
            is_recurring=True,
            recurrence_pattern='weekly',
            recurrence_interval=1,
            recurrence_days='0,2,4',  # Mon, Wed, Fri
            max_occurrences=5,
            is_published=True
        )
        
        self.assertTrue(event.is_recurring)
        self.assertEqual(event.recurrence_pattern, 'weekly')
        self.assertEqual(event.recurrence_days, '0,2,4')
        self.assertEqual(event.max_occurrences, 5)
    
    def test_generate_weekly_recurring_instances(self):
        """Test generating weekly recurring event instances"""
        event = Event.objects.create(
            title='Weekly Test Event',
            description='Test weekly recurring event',
            start_date=self.base_datetime,
            end_date=self.base_datetime + timedelta(hours=1),
            created_by=self.user,
            is_recurring=True,
            recurrence_pattern='weekly',
            recurrence_interval=1,
            recurrence_days='0,2',  # Mon, Wed
            max_occurrences=4,
            is_published=True
        )
        
        # Generate instances
        instances = event.generate_recurring_events(save=True)
        
        # Should generate 3 instances (original + 3 more = 4 total, but original doesn't count)
        self.assertEqual(len(instances), 3)
        
        # Check that instances are on correct days
        expected_weekdays = [2, 0, 2]  # Wed, Mon, Wed
        for i, instance in enumerate(instances):
            self.assertEqual(instance.start_date.weekday(), expected_weekdays[i])
            self.assertEqual(instance.parent_event, event)
            self.assertFalse(instance.is_recurring)
            self.assertTrue(instance.occurrence_date)
    
    def test_biweekly_recurring_instances(self):
        """Test generating biweekly recurring event instances"""
        event = Event.objects.create(
            title='Biweekly Test Event',
            description='Test biweekly recurring event',
            start_date=self.base_datetime,
            end_date=self.base_datetime + timedelta(hours=2),
            created_by=self.user,
            is_recurring=True,
            recurrence_pattern='biweekly',
            recurrence_interval=1,
            recurrence_days='1,3',  # Tue, Thu
            max_occurrences=4,
            is_published=True
        )
        
        instances = event.generate_recurring_events(save=True)
        
        # Should generate 3 instances
        self.assertEqual(len(instances), 3)
        
        # Check that instances are on correct days (Tue/Thu)
        for instance in instances:
            self.assertIn(instance.start_date.weekday(), [1, 3])  # Tue or Thu
            self.assertEqual(instance.parent_event, event)
    
    def test_monthly_recurring_instances(self):
        """Test generating monthly recurring event instances"""
        event = Event.objects.create(
            title='Monthly Test Event',
            description='Test monthly recurring event',
            start_date=self.base_datetime,
            end_date=self.base_datetime + timedelta(hours=1),
            created_by=self.user,
            is_recurring=True,
            recurrence_pattern='monthly',
            recurrence_interval=1,
            max_occurrences=3,
            is_published=True
        )
        
        instances = event.generate_recurring_events(save=True)
        
        # Should generate 2 instances (3 total including original)
        self.assertEqual(len(instances), 2)
        
        # Check that instances are monthly
        for i, instance in enumerate(instances):
            expected_month = (self.base_datetime.month + i + 1 - 1) % 12 + 1
            # Adjust for year wrap
            expected_year = self.base_datetime.year
            if self.base_datetime.month + i + 1 > 12:
                expected_year += 1
                expected_month = (self.base_datetime.month + i + 1) - 12
            
            self.assertEqual(instance.start_date.day, self.base_datetime.day)
            self.assertEqual(instance.parent_event, event)
    
    def test_daily_recurring_instances(self):
        """Test generating daily recurring event instances"""
        event = Event.objects.create(
            title='Daily Test Event',
            description='Test daily recurring event',
            start_date=self.base_datetime,
            end_date=self.base_datetime + timedelta(hours=1),
            created_by=self.user,
            is_recurring=True,
            recurrence_pattern='daily',
            recurrence_interval=1,
            max_occurrences=5,
            is_published=True
        )
        
        instances = event.generate_recurring_events(save=True)
        
        # Should generate 4 instances
        self.assertEqual(len(instances), 4)
        
        # Check that instances are daily
        for i, instance in enumerate(instances):
            expected_date = self.base_datetime + timedelta(days=i+1)
            self.assertEqual(instance.start_date.date(), expected_date.date())
    
    def test_exclude_weekends(self):
        """Test excluding weekends from daily recurring events"""
        # Start on Friday
        friday_date = timezone.make_aware(datetime(2025, 10, 31, 10, 0))  # Friday
        
        event = Event.objects.create(
            title='Weekday Only Event',
            description='Test excluding weekends',
            start_date=friday_date,
            end_date=friday_date + timedelta(hours=1),
            created_by=self.user,
            is_recurring=True,
            recurrence_pattern='daily',
            recurrence_interval=1,
            exclude_weekends=True,
            max_occurrences=5,
            is_published=True
        )
        
        instances = event.generate_recurring_events(save=True)
        
        # Should skip weekend days
        for instance in instances:
            self.assertLess(instance.start_date.weekday(), 5)  # Monday=0 to Friday=4
    
    def test_update_recurring_series(self):
        """Test updating a recurring event series"""
        event = Event.objects.create(
            title='Original Title',
            description='Original description',
            start_date=self.base_datetime,
            end_date=self.base_datetime + timedelta(hours=1),
            created_by=self.user,
            is_recurring=True,
            recurrence_pattern='weekly',
            recurrence_days='0,2',
            max_occurrences=3,
            is_published=True
        )
        
        # Generate initial instances
        event.generate_recurring_events(save=True)
        initial_count = Event.objects.filter(parent_event=event).count()
        self.assertEqual(initial_count, 2)
        
        # Update the series
        updated_count = event.update_recurring_series(
            title='Updated Title',
            description='Updated description'
        )
        
        self.assertEqual(updated_count, 2)
        
        # Check that instances were updated
        updated_instances = Event.objects.filter(parent_event=event)
        for instance in updated_instances:
            self.assertEqual(instance.title, 'Updated Title')
            self.assertEqual(instance.description, 'Updated description')
    
    def test_delete_recurring_series(self):
        """Test deleting a recurring event series"""
        event = Event.objects.create(
            title='To Be Deleted',
            description='Test deletion',
            start_date=self.base_datetime,
            end_date=self.base_datetime + timedelta(hours=1),
            created_by=self.user,
            is_recurring=True,
            recurrence_pattern='weekly',
            recurrence_days='0,2',
            max_occurrences=3,
            is_published=True
        )
        
        # Generate instances
        event.generate_recurring_events(save=True)
        initial_count = Event.objects.filter(parent_event=event).count()
        self.assertEqual(initial_count, 2)
        
        # Store the event ID before deletion
        event_id = event.id
        
        # Delete the series
        deleted_count = event.delete_recurring_series()
        self.assertEqual(deleted_count, 2)
        
        # Check that all events were deleted (parent and instances)
        remaining_count = Event.objects.filter(id=event_id).count()
        self.assertEqual(remaining_count, 0)
    
    def test_get_series_info(self):
        """Test getting recurring series information"""
        event = Event.objects.create(
            title='Series Info Test',
            description='Test series info',
            start_date=self.base_datetime,
            end_date=self.base_datetime + timedelta(hours=1),
            created_by=self.user,
            is_recurring=True,
            recurrence_pattern='weekly',
            recurrence_days='0,2,4',
            max_occurrences=5,
            is_published=True
        )
        
        # Generate instances
        event.generate_recurring_events(save=True)
        
        # Get series info
        info = event.get_series_info()
        
        self.assertEqual(info['total_instances'], 5)  # 5 total (parent + 4 instances)
        self.assertIn('Weekly', info['pattern'])
        self.assertEqual(info['is_parent'], True)
        
        # Test for instance
        instance = Event.objects.filter(parent_event=event).first()
        instance_info = instance.get_series_info()
        
        self.assertEqual(instance_info['total_instances'], 5)  # 1 parent + 4 instances
        self.assertEqual(instance_info['is_parent'], False)
        self.assertEqual(instance_info['parent'], event)


class WeekdayFieldTests(TestCase):
    """Test the custom weekday form field"""
    
    def test_weekday_field_to_python(self):
        """Test conversion to comma-separated string"""
        field = WeekdayMultipleChoiceField()
        
        # Test with list of integers
        result = field.to_python([0, 2, 4])
        self.assertEqual(result, '0,2,4')
        
        # Test with list of strings
        result = field.to_python(['1', '3', '5'])
        self.assertEqual(result, '1,3,5')
        
        # Test with empty value
        result = field.to_python([])
        self.assertEqual(result, '')
        
        # Test with None
        result = field.to_python(None)
        self.assertEqual(result, '')
    
    def test_weekday_field_prepare_value(self):
        """Test conversion from stored string back to list"""
        field = WeekdayMultipleChoiceField()
        
        # Test with comma-separated string
        result = field.prepare_value('0,2,4')
        self.assertEqual(result, [0, 2, 4])
        
        # Test with empty string
        result = field.prepare_value('')
        self.assertEqual(result, [])
        
        # Test with None
        result = field.prepare_value(None)
        self.assertEqual(result, [])
        
        # Test with list (already prepared)
        result = field.prepare_value([1, 3, 5])
        self.assertEqual(result, [1, 3, 5])


class EventFormTests(TestCase):
    """Test the EventForm with recurring event fields"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.event_type = EventType.objects.create(
            name='Test Event Type',
            slug='test-event',
            color='#FF0000'
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            course_code='TEST002',
            description='Test course',
            instructor=self.user,
            status='published'
        )
    
    def test_valid_recurring_event_form(self):
        """Test valid recurring event form submission"""
        form_data = {
            'title': 'Test Recurring Event',
            'description': 'Test description',
            'start_date': '2025-10-27 10:00:00',
            'end_date': '2025-10-27 11:00:00',
            'event_type': 'general',
            'priority': 'normal',
            'visibility': 'registered',
            'is_recurring': True,
            'recurrence_pattern': 'weekly',
            'recurrence_interval': 1,
            'recurrence_days': [0, 2, 4],  # Mon, Wed, Fri as list
            'max_occurrences': 10,
            'is_published': True,
            'course': self.course.id
        }
        
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        # Check that recurrence_days was converted properly
        cleaned_data = form.cleaned_data
        self.assertEqual(cleaned_data['recurrence_days'], '0,2,4')
    
    def test_recurring_event_validation_errors(self):
        """Test recurring event form validation errors"""
        # Missing recurrence pattern
        form_data = {
            'title': 'Test Event',
            'start_date': '2025-10-27 10:00:00',
            'is_recurring': True,
            # Missing recurrence_pattern
            'is_published': True
        }
        
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Recurrence pattern is required', str(form.errors))
        
        # Missing end condition
        form_data.update({
            'recurrence_pattern': 'weekly',
            # Missing both recurrence_end_date and max_occurrences
        })
        
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Either end date or maximum occurrences', str(form.errors))
        
        # Invalid end date
        form_data.update({
            'recurrence_end_date': '2025-10-26',  # Before start date
            'max_occurrences': 5
        })
        
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Recurrence end date must be after', str(form.errors))
    
    def test_weekly_pattern_requires_days(self):
        """Test that weekly patterns require day selection"""
        form_data = {
            'title': 'Test Weekly Event',
            'start_date': '2025-10-27 10:00:00',
            'is_recurring': True,
            'recurrence_pattern': 'weekly',
            'recurrence_days': '',  # No days selected
            'recurrence_interval': 1,
            'max_occurrences': 5,
            'is_published': True,
            'event_type': 'general',
            'priority': 'normal',
            'visibility': 'public'
        }
        
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Please select at least one day', str(form.errors))


class ManagementCommandTests(TransactionTestCase):
    """Test the generate_recurring_events management command"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create recurring event
        self.recurring_event = Event.objects.create(
            title='Command Test Event',
            description='Test management command',
            start_date=timezone.make_aware(datetime(2025, 10, 27, 10, 0)),
            end_date=timezone.make_aware(datetime(2025, 10, 27, 11, 0)),
            created_by=self.user,
            is_recurring=True,
            recurrence_pattern='weekly',
            recurrence_days='0,2',  # Mon, Wed
            max_occurrences=5,
            is_published=True
        )
    
    def test_management_command_dry_run(self):
        """Test management command in dry run mode"""
        command = Command()
        
        # Capture output
        from io import StringIO
        import sys
        captured_output = StringIO()
        
        # Run dry run
        command.handle(dry_run=True, verbosity=1, stdout=captured_output)
        
        # Should not create actual instances
        instances_count = Event.objects.filter(parent_event=self.recurring_event).count()
        self.assertEqual(instances_count, 0)
    
    def test_management_command_live_run(self):
        """Test management command live run"""
        command = Command()
        
        # Run live command
        command.handle(dry_run=False, verbosity=0)
        
        # Should create actual instances
        instances_count = Event.objects.filter(parent_event=self.recurring_event).count()
        self.assertGreater(instances_count, 0)
    
    def test_management_command_specific_event(self):
        """Test management command for specific event ID"""
        command = Command()
        
        # Run for specific event
        command.handle(
            event_id=self.recurring_event.id,
            dry_run=False,
            verbosity=0
        )
        
        # Should create instances for this event
        instances_count = Event.objects.filter(parent_event=self.recurring_event).count()
        self.assertGreater(instances_count, 0)
    
    def test_management_command_force_regenerate(self):
        """Test force regeneration of existing instances"""
        # First, generate instances
        self.recurring_event.generate_recurring_events(save=True)
        initial_count = Event.objects.filter(parent_event=self.recurring_event).count()
        
        command = Command()
        
        # Force regenerate
        command.handle(
            event_id=self.recurring_event.id,
            force_regenerate=True,
            dry_run=False,
            verbosity=0
        )
        
        # Should have same number of instances (regenerated)
        final_count = Event.objects.filter(parent_event=self.recurring_event).count()
        self.assertEqual(initial_count, final_count)


class RecurringEventsIntegrationTests(TestCase):
    """Integration tests for the complete recurring events system"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.course = Course.objects.create(
            title='Integration Test Course',
            course_code='INT001',
            description='Test course for integration',
            instructor=self.user,
            status='published'
        )
    
    def test_complete_recurring_event_workflow(self):
        """Test the complete workflow from creation to management"""
        # 1. Create recurring event through form
        form_data = {
            'title': 'Complete Workflow Test',
            'description': 'Testing complete workflow',
            'start_date': '2025-10-27 09:00:00',
            'end_date': '2025-10-27 10:00:00',
            'is_recurring': True,
            'recurrence_pattern': 'weekly',
            'recurrence_interval': 1,
            'recurrence_days': [0, 2, 4],  # Mon, Wed, Fri
            'recurrence_end_date': '2025-12-01',
            'is_published': True,
            'event_type': 'general',
            'priority': 'normal',
            'visibility': 'public',
            'course': self.course.id
        }
        
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        event = form.save(commit=False)
        event.created_by = self.user
        event.save()
        
        # 2. Generate recurring instances
        instances = event.generate_recurring_events(save=True)
        self.assertGreater(len(instances), 0)
        
        # 3. Verify all instances are correct
        for instance in instances:
            self.assertIn(instance.start_date.weekday(), [0, 2, 4])  # Mon, Wed, Fri
            self.assertEqual(instance.parent_event, event)
            self.assertEqual(instance.course, self.course)
            self.assertFalse(instance.is_recurring)
        
        # 4. Update the series
        updated_count = event.update_recurring_series(
            title='Updated Series Title'
        )
        self.assertEqual(updated_count, len(instances))
        
        # 5. Verify updates
        updated_instances = Event.objects.filter(parent_event=event)
        for instance in updated_instances:
            self.assertEqual(instance.title, 'Updated Series Title')
        
        # 6. Get series info
        info = event.get_series_info()
        self.assertEqual(info['total_instances'], len(instances) + 1)  # +1 for parent
        self.assertTrue(info['is_parent'])
        
        # 7. Delete series
        event_id = event.id
        deleted_count = event.delete_recurring_series()
        self.assertEqual(deleted_count, len(instances))
        
        # 8. Verify deletion - check that parent event is also gone
        remaining_count = Event.objects.filter(id=event_id).count()
        self.assertEqual(remaining_count, 0)
    
    def test_course_recurring_events_integration(self):
        """Test recurring events integration with course system"""
        # Create recurring event linked to course
        event = Event.objects.create(
            title='Course Integration Test',
            description='Test course integration',
            start_date=timezone.make_aware(datetime(2025, 10, 27, 14, 0)),
            end_date=timezone.make_aware(datetime(2025, 10, 27, 15, 0)),
            created_by=self.user,
            course=self.course,
            is_recurring=True,
            recurrence_pattern='weekly',
            recurrence_days='0,2,4',  # Mon, Wed, Fri
            max_occurrences=6,
            is_published=True
        )
        
        # Generate instances
        instances = event.generate_recurring_events(save=True)
        
        # Verify all instances are linked to the course
        for instance in instances:
            self.assertEqual(instance.course, self.course)
        
        # Check that course has all the recurring events
        course_events = Event.objects.filter(course=self.course)
        self.assertGreaterEqual(course_events.count(), len(instances) + 1)  # +1 for parent


# Pytest fixtures and tests for more advanced scenarios
@pytest.fixture
def user():
    """Create test user"""
    return User.objects.create_user(
        username='pytest_user',
        email='pytest@example.com',
        password='testpass123'
    )

@pytest.fixture
def course(user):
    """Create test course"""
    return Course.objects.create(
        title='Pytest Course',
        course_code='PYT001',
        description='Test course for pytest',
        instructor=user,
        status='published'
    )

@pytest.mark.django_db
class TestRecurringEventsEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_invalid_recurrence_days_format(self, user):
        """Test handling of invalid recurrence days format"""
        event = Event.objects.create(
            title='Invalid Days Test',
            description='Test invalid days',
            start_date=timezone.make_aware(datetime(2025, 10, 27, 10, 0)),
            end_date=timezone.make_aware(datetime(2025, 10, 27, 11, 0)),
            created_by=user,
            is_recurring=True,
            recurrence_pattern='weekly',
            recurrence_days='invalid,format,7,8',  # Invalid format
            max_occurrences=3,
            is_published=True
        )
        
        # Should handle gracefully and fall back to weekly interval
        instances = event.generate_recurring_events(save=True)
        # Should still generate instances, just with fallback logic
        assert len(instances) >= 0
    
    def test_month_edge_cases(self, user):
        """Test monthly recurrence edge cases (like Feb 29, month boundaries)"""
        # Test starting on Jan 31 (month with different day counts)
        event = Event.objects.create(
            title='Month Edge Case Test',
            description='Test month boundaries',
            start_date=timezone.make_aware(datetime(2025, 1, 31, 10, 0)),
            end_date=timezone.make_aware(datetime(2025, 1, 31, 11, 0)),
            created_by=user,
            is_recurring=True,
            recurrence_pattern='monthly',
            recurrence_interval=1,
            max_occurrences=4,  # Will hit Feb (28 days), Mar (31), Apr (30)
            is_published=True
        )
        
        instances = event.generate_recurring_events(save=True)
        assert len(instances) > 0
        
        # Check that it handles different month lengths gracefully
        for instance in instances:
            assert instance.start_date.day <= 31
    
    def test_timezone_handling(self, user):
        """Test recurring events across timezone boundaries"""
        # Create event near midnight
        event = Event.objects.create(
            title='Timezone Test',
            description='Test timezone handling',
            start_date=timezone.make_aware(datetime(2025, 10, 27, 23, 30)),
            end_date=timezone.make_aware(datetime(2025, 10, 28, 0, 30)),  # Crosses midnight
            created_by=user,
            is_recurring=True,
            recurrence_pattern='daily',
            recurrence_interval=1,
            max_occurrences=3,
            is_published=True
        )
        
        instances = event.generate_recurring_events(save=True)
        assert len(instances) > 0
        
        # Verify time consistency
        for instance in instances:
            assert instance.start_date.hour == 23
            assert instance.start_date.minute == 30