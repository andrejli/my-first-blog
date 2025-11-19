"""
Test script for Content Quarantine System.

This script tests the quarantine functionality for forum posts and blog posts.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from blog.models import (
    ForumPost, BlogPost, ContentQuarantine, QuarantineDecision,
    Forum, Topic, UserProfile
)
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def test_forum_post_quarantine():
    """Test quarantining forum posts."""
    print_header("TEST 1: Forum Post Quarantine")
    
    # Get or create test users
    admin_user, _ = User.objects.get_or_create(
        username='admin_test',
        defaults={'is_staff': True, 'is_superuser': True}
    )
    student_user, _ = User.objects.get_or_create(
        username='student_test',
        defaults={'is_staff': False}
    )
    
    # Ensure user profiles exist
    UserProfile.objects.get_or_create(user=admin_user, defaults={'role': 'admin'})
    UserProfile.objects.get_or_create(user=student_user, defaults={'role': 'student'})
    
    # Get or create a forum and topic
    forum, _ = Forum.objects.get_or_create(
        title='Test Forum',
        defaults={
            'description': 'Test forum for quarantine testing',
            'forum_type': 'general'
        }
    )
    
    topic, _ = Topic.objects.get_or_create(
        forum=forum,
        title='Test Topic',
        defaults={'created_by': student_user}
    )
    
    # Create a test forum post
    forum_post = ForumPost.objects.create(
        topic=topic,
        author=student_user,
        content='This is a test forum post that will be quarantined.',
        is_first_post=False
    )
    
    print(f"✓ Created forum post #{forum_post.id}")
    print(f"  Author: {forum_post.author.username}")
    print(f"  Content: {forum_post.content[:50]}...")
    
    # Quarantine the post
    ct = ContentType.objects.get_for_model(forum_post)
    quarantine = ContentQuarantine.objects.create(
        content_type=ct,
        object_id=forum_post.id,
        quarantined_by=admin_user,
        quarantine_reason="Test quarantine: Inappropriate content",
        resolution_deadline=timezone.now() + timedelta(days=7)
    )
    
    print(f"\n✓ Quarantined forum post #{forum_post.id}")
    print(f"  Quarantined by: {quarantine.quarantined_by.username}")
    print(f"  Reason: {quarantine.quarantine_reason}")
    print(f"  Status: {quarantine.status}")
    print(f"  Deadline: {quarantine.resolution_deadline.strftime('%Y-%m-%d')}")
    
    # Test access control
    print(f"\n✓ Access Control Tests:")
    print(f"  Admin can view: {quarantine.can_view_content(admin_user)}")
    print(f"  Author can view: {quarantine.can_view_content(student_user)}")
    
    # Create another user to test
    other_user, _ = User.objects.get_or_create(
        username='other_test',
        defaults={'is_staff': False}
    )
    UserProfile.objects.get_or_create(user=other_user, defaults={'role': 'student'})
    print(f"  Other user can view: {quarantine.can_view_content(other_user)}")
    
    # Test quarantine check function
    from blog.views import is_content_quarantined
    quarantine_check = is_content_quarantined(forum_post)
    print(f"\n✓ Quarantine Check: {quarantine_check is not None}")
    
    return quarantine, forum_post


def test_blog_post_quarantine():
    """Test quarantining blog posts."""
    print_header("TEST 2: Blog Post Quarantine")
    
    # Get test users
    admin_user = User.objects.get(username='admin_test')
    student_user = User.objects.get(username='student_test')
    
    # Create a test blog post
    blog_post = BlogPost.objects.create(
        author=student_user,
        title='Test Blog Post',
        slug='test-blog-post-quarantine',
        content='This is a test blog post that will be quarantined.',
        status='published',
        published_date=timezone.now()
    )
    
    print(f"✓ Created blog post #{blog_post.id}")
    print(f"  Author: {blog_post.author.username}")
    print(f"  Title: {blog_post.title}")
    print(f"  Status: {blog_post.status}")
    
    # Quarantine the blog post
    ct = ContentType.objects.get_for_model(blog_post)
    quarantine = ContentQuarantine.objects.create(
        content_type=ct,
        object_id=blog_post.id,
        quarantined_by=admin_user,
        quarantine_reason="Test quarantine: Spam content",
        resolution_deadline=timezone.now() + timedelta(days=7)
    )
    
    print(f"\n✓ Quarantined blog post #{blog_post.id}")
    print(f"  Quarantined by: {quarantine.quarantined_by.username}")
    print(f"  Reason: {quarantine.quarantine_reason}")
    print(f"  Content Preview: {quarantine.get_content_preview()}")
    
    # Test access control
    print(f"\n✓ Access Control Tests:")
    print(f"  Admin can view: {quarantine.can_view_content(admin_user)}")
    print(f"  Author can view: {quarantine.can_view_content(student_user)}")
    
    other_user = User.objects.get(username='other_test')
    print(f"  Other user can view: {quarantine.can_view_content(other_user)}")
    
    return quarantine, blog_post


def test_quarantine_resolution():
    """Test resolving quarantines."""
    print_header("TEST 3: Quarantine Resolution")
    
    admin_user = User.objects.get(username='admin_test')
    
    # Get an active quarantine
    quarantine = ContentQuarantine.objects.filter(status='ACTIVE').first()
    
    if not quarantine:
        print("⚠ No active quarantines found to resolve")
        return
    
    print(f"✓ Resolving quarantine #{quarantine.id}")
    print(f"  Content: {quarantine.content_type.model} #{quarantine.object_id}")
    
    # Create a decision to restore content
    decision = QuarantineDecision.objects.create(
        quarantine=quarantine,
        poll_result='RESTORE',
        action_taken='RESTORED',
        decided_by=admin_user,
        decision_notes='Test resolution: Content approved by community vote'
    )
    
    # Update quarantine status
    quarantine.status = 'RESOLVED_RESTORE'
    quarantine.save()
    
    print(f"\n✓ Quarantine resolved:")
    print(f"  Poll Result: {decision.poll_result}")
    print(f"  Action Taken: {decision.action_taken}")
    print(f"  Decided By: {decision.decided_by.username}")
    print(f"  New Status: {quarantine.status}")
    print(f"  Decision Notes: {decision.decision_notes}")


def test_quarantine_statistics():
    """Display quarantine statistics."""
    print_header("TEST 4: Quarantine Statistics")
    
    total = ContentQuarantine.objects.count()
    active = ContentQuarantine.objects.filter(status='ACTIVE').count()
    restored = ContentQuarantine.objects.filter(status='RESOLVED_RESTORE').count()
    deleted = ContentQuarantine.objects.filter(status='RESOLVED_DELETE').count()
    
    print(f"Total Quarantines: {total}")
    print(f"  Active: {active}")
    print(f"  Restored: {restored}")
    print(f"  Deleted: {deleted}")
    
    # Group by content type
    print(f"\nBy Content Type:")
    for ct in ContentType.objects.filter(
        id__in=ContentQuarantine.objects.values_list('content_type_id', flat=True)
    ):
        count = ContentQuarantine.objects.filter(content_type=ct).count()
        print(f"  {ct.model}: {count}")
    
    # Recent quarantines
    print(f"\nRecent Quarantines (Last 5):")
    for q in ContentQuarantine.objects.order_by('-quarantine_date')[:5]:
        print(f"  #{q.id}: {q.content_type.model} - {q.status} - {q.quarantine_date.strftime('%Y-%m-%d %H:%M')}")


def cleanup_test_data():
    """Clean up test data."""
    print_header("CLEANUP: Removing Test Data")
    
    # Delete test quarantines
    count = ContentQuarantine.objects.filter(
        quarantined_by__username='admin_test'
    ).count()
    
    if count > 0:
        response = input(f"\nDelete {count} test quarantine(s)? (yes/no): ")
        if response.lower() == 'yes':
            ContentQuarantine.objects.filter(
                quarantined_by__username='admin_test'
            ).delete()
            print(f"✓ Deleted {count} test quarantine(s)")
        else:
            print("✗ Cleanup cancelled")
    else:
        print("No test quarantines to clean up")


def main():
    """Run all quarantine tests."""
    print("\n" + "=" * 70)
    print("  CONTENT QUARANTINE SYSTEM TEST SUITE")
    print("=" * 70)
    
    try:
        # Run tests
        test_forum_post_quarantine()
        test_blog_post_quarantine()
        test_quarantine_resolution()
        test_quarantine_statistics()
        
        print_header("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        
        # Offer cleanup
        print("\nTest data created. You can:")
        print("1. View quarantines in Django admin at /admin/blog/contentquarantine/")
        print("2. Test quarantine actions in admin interface")
        print("3. Run cleanup to remove test data")
        
        cleanup_response = input("\nRun cleanup now? (yes/no): ")
        if cleanup_response.lower() == 'yes':
            cleanup_test_data()
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
