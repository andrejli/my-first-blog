#!/usr/bin/env python
"""
Clean up duplicate ITSEC40 recurring event instances
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from blog.models import Event
from django.db.models import Count
from collections import defaultdict

def clean_itsec40_duplicates():
    print("🔍 Checking for ITSEC40 duplicate events...")
    
    # Get all ITSEC40 instances (excluding parent)
    instances = Event.objects.filter(
        title='ITSEC40', 
        parent_event__isnull=False
    ).order_by('start_date', 'id')
    
    print(f"📊 Found {instances.count()} ITSEC40 instances")
    
    # Group by start_date to find duplicates
    date_groups = defaultdict(list)
    for instance in instances:
        date_key = instance.start_date
        date_groups[date_key].append(instance)
    
    # Find and remove duplicates
    total_deleted = 0
    total_kept = 0
    
    for date, events in date_groups.items():
        if len(events) > 1:
            print(f"🔁 Found {len(events)} duplicates for {date}")
            
            # Keep the first one (oldest by ID), delete the rest
            keep_event = events[0]
            delete_events = events[1:]
            
            print(f"   ✅ Keeping: ID {keep_event.id}")
            total_kept += 1
            
            for event in delete_events:
                print(f"   ❌ Deleting: ID {event.id}")
                event.delete()
                total_deleted += 1
        else:
            total_kept += 1
    
    print("\n📋 Summary:")
    print(f"   Events kept: {total_kept}")
    print(f"   Events deleted: {total_deleted}")
    
    # Final verification
    final_count = Event.objects.filter(
        title='ITSEC40', 
        parent_event__isnull=False
    ).count()
    
    print(f"   Final instance count: {final_count}")
    
    # Show the remaining events
    print("\n📅 Remaining ITSEC40 events:")
    remaining = Event.objects.filter(
        title='ITSEC40', 
        parent_event__isnull=False
    ).order_by('start_date')
    
    for i, event in enumerate(remaining, 1):
        weekday = event.start_date.strftime('%A')
        date_str = event.start_date.strftime('%Y-%m-%d %H:%M')
        print(f"   {i:2d}. {date_str} ({weekday})")
    
    print("\n✅ Cleanup completed!")

if __name__ == '__main__':
    clean_itsec40_duplicates()