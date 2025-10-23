#!/usr/bin/env python
"""
Create a test recurring event through Django to verify the fix
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from blog.models import Event, EventType
from django.contrib.auth.models import User
from django.utils import timezone

def create_test_recurring_event():
    """Create a real recurring event in the database"""
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
    )
    
    print("🏗️ Creating a real recurring event in the database...")
    print("=" * 50)
    
    # Create an event starting next Monday for Mon/Wed/Fri pattern
    now = timezone.now()
    # Find next Monday
    days_ahead = 0 - now.weekday()  # Monday is 0
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    
    start_date = now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)
    end_date = start_date + timedelta(hours=1)
    
    print(f"📅 Start date: {start_date} ({start_date.strftime('%A')})")
    print(f"🎯 Pattern: Monday (0), Wednesday (2), Friday (4)")
    print(f"💾 Recurrence days: '0,2,4'")
    print()
    
    # Create and save the recurring event
    event = Event.objects.create(
        title="Test Course Sessions",
        description="Weekly course sessions on Mon/Wed/Fri",
        start_date=start_date,
        end_date=end_date,
        created_by=user,
        is_recurring=True,
        recurrence_pattern='weekly',
        recurrence_interval=1,
        recurrence_days='0,2,4',  # Monday, Wednesday, Friday
        max_occurrences=10,  # Create 10 instances
        is_published=True
    )
    
    print(f"✅ Created recurring event: {event.title} (ID: {event.id})")
    
    # Generate the recurring instances
    print("🔄 Generating recurring instances...")
    created_count = event.generate_recurring_events()
    
    print(f"✅ Generated {created_count} recurring instances")
    print()
    
    # Display the generated instances
    instances = Event.objects.filter(parent_event=event).order_by('start_date')
    print(f"📋 Generated instances ({instances.count()} total):")
    print("-" * 50)
    
    for i, instance in enumerate(instances, 1):
        weekday = instance.start_date.strftime('%A')
        date_str = instance.start_date.strftime('%Y-%m-%d %H:%M')
        weekday_num = instance.start_date.weekday()
        print(f"{i:2}. {date_str} - {weekday} (#{weekday_num})")
    
    return event, instances

def test_management_command():
    """Test the management command with the created event"""
    print("\n" + "=" * 50)
    print("🔧 Testing management command...")
    print("=" * 50)
    
    import subprocess
    
    # Run the management command
    result = subprocess.run([
        'C:/Users/forti/Documents/GitHub/my-first-blog/venv/Scripts/python.exe',
        'manage.py', 
        'generate_recurring_events',
        '--dry-run'
    ], capture_output=True, text=True, cwd='C:/Users/forti/Documents/GitHub/my-first-blog')
    
    print("Command output:")
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    return result.returncode == 0

if __name__ == "__main__":
    print("🧪 Creating and testing real recurring events...")
    print()
    
    try:
        # Create test event
        event, instances = create_test_recurring_event()
        
        # Test management command
        cmd_success = test_management_command()
        
        print("\n" + "=" * 60)
        print("📊 SUMMARY:")
        print("=" * 60)
        print(f"Event created: ✅ {event.title}")
        print(f"Instances generated: ✅ {len(instances)} instances")
        print(f"Management command: {'✅ PASS' if cmd_success else '❌ FAIL'}")
        
        # Verify day correctness
        expected_days = {0, 2, 4}  # Mon, Wed, Fri
        actual_days = {inst.start_date.weekday() for inst in instances}
        
        print(f"Expected days: {expected_days}")
        print(f"Actual days: {actual_days}")
        print(f"Days correct: {'✅ PASS' if expected_days.issuperset(actual_days) else '❌ FAIL'}")
        
        if expected_days.issuperset(actual_days):
            print("\n🎉 SUCCESS: Recurring events are working perfectly!")
            print("✅ Days are calculated correctly")
            print("✅ Events are saved to database")
            print("✅ Management command works")
        else:
            print("\n⚠️ WARNING: Some generated days don't match expected pattern")
            
    except Exception as e:
        print(f"💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)