#!/usr/bin/env python3
"""
Simple script to verify the created posters and events
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from blog.models import Event
from PIL import Image

def check_events_and_posters():
    """Check all events and their poster information"""
    events = Event.objects.all().order_by('start_date')
    
    print("📅 FORTIS AURIS LMS - Event & Poster Status")
    print("=" * 50)
    print()
    
    if not events:
        print("❌ No events found in database.")
        return
    
    print(f"✅ Found {events.count()} events:")
    print()
    
    for i, event in enumerate(events, 1):
        print(f"{i}. {event.title}")
        print(f"   📅 Date: {event.start_date.strftime('%B %d, %Y at %H:%M')}")
        print(f"   🏷️  Type: {event.get_event_type_display()}")
        print(f"   🎯 Priority: {event.get_priority_display()}")
        print(f"   👁️  Visibility: {event.get_visibility_display()}")
        
        if event.has_poster:
            poster_path = event.poster.path
            if os.path.exists(poster_path):
                try:
                    with Image.open(poster_path) as img:
                        width, height = img.size
                        aspect_ratio = width / height
                        print(f"   🖼️  Poster: ✅ {width}x{height}px (ratio: {aspect_ratio:.2f})")
                        if width == 400 and height == 720:
                            print(f"   📐 Perfect portrait format! ✅")
                        else:
                            print(f"   📐 Not standard format (expected 400x720)")
                except Exception as e:
                    print(f"   🖼️  Poster: ❌ Error reading image: {e}")
            else:
                print(f"   🖼️  Poster: ❌ File not found: {poster_path}")
        else:
            print(f"   🖼️  Poster: ❌ No poster attached")
        
        print()
    
    # Summary
    events_with_posters = sum(1 for event in events if event.has_poster)
    print("📊 SUMMARY")
    print("-" * 20)
    print(f"Total Events: {events.count()}")
    print(f"Events with Posters: {events_with_posters}")
    print(f"Events without Posters: {events.count() - events_with_posters}")
    print()
    print("🎯 Next Steps:")
    print("1. Visit http://localhost:8000/calendar/ to test the calendar")
    print("2. Check Month/Week/Day views for poster indicators (📷 icons)")
    print("3. Look for poster thumbnails in the sidebar")
    print("4. Click thumbnails to view full-size posters")

if __name__ == "__main__":
    check_events_and_posters()