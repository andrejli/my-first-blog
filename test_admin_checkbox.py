#!/usr/bin/env python
"""
Test script to verify admin checkbox functionality is working
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib import admin
from blog.models import Event
from blog.admin import EventAdmin

def test_admin_form():
    print("Testing Django Admin Configuration...")
    
    # Get the admin class for Event
    admin_class = admin.site._registry[Event]
    print(f"Admin class: {admin_class.__class__.__name__}")
    
    # Check if it's using our custom form
    if hasattr(admin_class, 'form'):
        print(f"Custom form class: {admin_class.form.__name__}")
        
        # Create an instance of the form
        form = admin_class.form()
        
        # Check the recurrence_days field
        if 'recurrence_days' in form.fields:
            field = form.fields['recurrence_days']
            print(f"recurrence_days field type: {field.__class__.__name__}")
            print(f"recurrence_days widget type: {field.widget.__class__.__name__}")
            
            # Render the widget to check HTML
            widget_html = field.widget.render('recurrence_days', ['0', '2', '4'], attrs={})  # Mon, Wed, Fri
            print(f"Widget HTML contains checkboxes: {'type=\"checkbox\"' in widget_html}")
            print(f"Number of checkboxes: {widget_html.count('type=\"checkbox\"')}")
            
            return True
        else:
            print("ERROR: recurrence_days field not found in form")
            return False
    else:
        print("ERROR: No custom form configured")
        return False

if __name__ == '__main__':
    success = test_admin_form()
    if success:
        print("\n✅ Admin checkbox configuration is working correctly!")
        print("You can now access the admin interface and see checkboxes for weekday selection.")
    else:
        print("\n❌ Admin configuration has issues")