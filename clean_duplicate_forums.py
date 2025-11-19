"""
Clean up duplicate Forum entries in the database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from blog.models import Forum

def clean_duplicate_forums():
    """Remove duplicate general and instructor forums"""
    
    # Check and clean general forums
    general_forums = Forum.objects.filter(forum_type='general', course=None)
    general_count = general_forums.count()
    print(f"Found {general_count} general forum(s) with course=None")
    
    if general_count > 1:
        print("  Removing duplicates...")
        keep = general_forums.first()
        print(f"  Keeping forum ID {keep.id}: '{keep.title}'")
        duplicates = general_forums.exclude(id=keep.id)
        for dup in duplicates:
            print(f"  Deleting forum ID {dup.id}: '{dup.title}'")
        duplicates.delete()
        print(f"  Deleted {general_count - 1} duplicate general forum(s)")
    elif general_count == 1:
        print("  No duplicates found")
    else:
        print("  No general forum exists (will be created on next access)")
    
    print()
    
    # Check and clean instructor forums
    instructor_forums = Forum.objects.filter(forum_type='instructor', course=None)
    instructor_count = instructor_forums.count()
    print(f"Found {instructor_count} instructor forum(s) with course=None")
    
    if instructor_count > 1:
        print("  Removing duplicates...")
        keep = instructor_forums.first()
        print(f"  Keeping forum ID {keep.id}: '{keep.title}'")
        duplicates = instructor_forums.exclude(id=keep.id)
        for dup in duplicates:
            print(f"  Deleting forum ID {dup.id}: '{dup.title}'")
        duplicates.delete()
        print(f"  Deleted {instructor_count - 1} duplicate instructor forum(s)")
    elif instructor_count == 1:
        print("  No duplicates found")
    else:
        print("  No instructor forum exists (will be created on next access)")
    
    print("\n✅ Forum cleanup complete!")
    print("\nCurrent forum status:")
    print(f"  General forums (course=None): {Forum.objects.filter(forum_type='general', course=None).count()}")
    print(f"  Instructor forums (course=None): {Forum.objects.filter(forum_type='instructor', course=None).count()}")
    print(f"  Course forums: {Forum.objects.filter(forum_type='course').exclude(course=None).count()}")

if __name__ == '__main__':
    clean_duplicate_forums()
