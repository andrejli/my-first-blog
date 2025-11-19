"""
Test Quarantine System for Django LMS

This module contains comprehensive pytest tests for the content quarantine system:
- ContentQuarantine model functionality
- QuarantineDecision model and resolution workflow
- Access control for quarantined content
- View-level filtering for forum posts and blog posts
- Admin actions and management interface
"""

import pytest
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.urls import reverse

from blog.models import (
    ContentQuarantine, QuarantineDecision, 
    ForumPost, BlogPost, Course, Forum, UserProfile
)
from blog.views import is_content_quarantined, can_view_quarantined_content


# ================================
# PYTEST FIXTURES
# ================================

@pytest.fixture
def admin_user(db):
    """Create an admin user"""
    user = User.objects.create_user(
        username='admin_quarantine',
        email='admin@test.com',
        password='adminpass123',
        is_staff=True,
        is_superuser=True
    )
    # UserProfile is automatically created via signal
    profile = UserProfile.objects.get(user=user)
    profile.role = 'admin'
    profile.save()
    return user


@pytest.fixture
def instructor_user(db):
    """Create an instructor user"""
    user = User.objects.create_user(
        username='instructor_quarantine',
        email='instructor@test.com',
        password='instructorpass123'
    )
    # UserProfile is automatically created via signal
    profile = UserProfile.objects.get(user=user)
    profile.role = 'instructor'
    profile.save()
    return user


@pytest.fixture
def student_user(db):
    """Create a student user"""
    user = User.objects.create_user(
        username='student_quarantine',
        email='student@test.com',
        password='studentpass123'
    )
    # UserProfile is automatically created via signal
    profile = UserProfile.objects.get(user=user)
    profile.role = 'student'
    profile.save()
    return user


@pytest.fixture
def test_course(db, instructor_user):
    """Create a test course"""
    return Course.objects.create(
        title='Quarantine Test Course',
        course_code='QTEST101',
        description='Test course for quarantine system',
        instructor=instructor_user,
        status='published'
    )


@pytest.fixture
def test_forum(db, test_course):
    """Create a test forum"""
    return Forum.objects.create(
        title='Test Forum',
        description='Test forum for quarantine',
        course=test_course,
        forum_type='course'
    )


@pytest.fixture
def test_forum_post(db, test_forum, student_user):
    """Create a test forum post"""
    topic = test_forum.topics.create(
        title='Test Topic',
        created_by=student_user
    )
    return ForumPost.objects.create(
        topic=topic,
        author=student_user,
        content='This is a test forum post content.'
    )


@pytest.fixture
def test_blog_post(db, student_user):
    """Create a test blog post"""
    return BlogPost.objects.create(
        title='Test Blog Post',
        content='This is a test blog post content.',
        author=student_user,
        status='published'
    )


# ================================
# CONTENT QUARANTINE MODEL TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.quarantine
class TestContentQuarantineModel:
    """Test cases for ContentQuarantine model"""
    
    def test_create_forum_post_quarantine(self, test_forum_post, admin_user):
        """Test creating a quarantine for a forum post"""
        content_type = ContentType.objects.get_for_model(ForumPost)
        
        quarantine = ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Test inappropriate content',
            status='ACTIVE'
        )
        
        assert quarantine.content_object == test_forum_post
        assert quarantine.quarantined_by == admin_user
        assert quarantine.is_active() is True
        assert quarantine.status == 'ACTIVE'
        assert 'forumpost' in str(quarantine).lower()
    
    def test_create_blog_post_quarantine(self, test_blog_post, admin_user):
        """Test creating a quarantine for a blog post"""
        content_type = ContentType.objects.get_for_model(BlogPost)
        
        quarantine = ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_blog_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Test policy violation',
            status='ACTIVE'
        )
        
        assert quarantine.content_object == test_blog_post
        assert quarantine.is_active() is True
        assert 'blogpost' in str(quarantine).lower()
    
    def test_quarantine_status_choices(self, test_forum_post, admin_user):
        """Test all quarantine status choices"""
        content_type = ContentType.objects.get_for_model(ForumPost)
        
        statuses = ['ACTIVE', 'RESOLVED_RESTORE', 'RESOLVED_DELETE', 'RESOLVED_EXTENDED']
        
        for status in statuses:
            quarantine = ContentQuarantine.objects.create(
                content_type=content_type,
                object_id=test_forum_post.id,
                quarantined_by=admin_user,
                quarantine_reason=f'Test {status}',
                status=status
            )
            
            assert quarantine.status == status
            if status == 'ACTIVE':
                assert quarantine.is_active() is True
            else:
                assert quarantine.is_active() is False
    
    def test_quarantine_with_deadline(self, test_forum_post, admin_user):
        """Test quarantine with resolution deadline"""
        content_type = ContentType.objects.get_for_model(ForumPost)
        deadline = timezone.now() + timedelta(days=7)
        
        quarantine = ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Test with deadline',
            resolution_deadline=deadline
        )
        
        assert quarantine.resolution_deadline is not None
        assert quarantine.resolution_deadline > timezone.now()
    
    def test_quarantine_ordering(self, test_forum_post, admin_user):
        """Test quarantines are ordered by date descending"""
        content_type = ContentType.objects.get_for_model(ForumPost)
        
        # Create two quarantines
        q1 = ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='First quarantine'
        )
        
        q2 = ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Second quarantine'
        )
        
        quarantines = list(ContentQuarantine.objects.all())
        assert quarantines[0] == q2  # Most recent first
        assert quarantines[1] == q1


# ================================
# QUARANTINE ACCESS CONTROL TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.quarantine
class TestQuarantineAccessControl:
    """Test access control for quarantined content"""
    
    def test_admin_can_view_quarantined_content(self, test_forum_post, admin_user):
        """Test that admins can view quarantined content"""
        content_type = ContentType.objects.get_for_model(ForumPost)
        
        quarantine = ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Test admin access'
        )
        
        assert quarantine.can_view_content(admin_user) is True
    
    def test_author_can_view_quarantined_content(self, test_forum_post, student_user):
        """Test that content author can view their quarantined content"""
        content_type = ContentType.objects.get_for_model(ForumPost)
        admin = User.objects.create_superuser('admin2', 'admin2@test.com', 'pass')
        
        quarantine = ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_forum_post.id,
            quarantined_by=admin,
            quarantine_reason='Test author access'
        )
        
        # Student is the author of test_forum_post
        assert quarantine.can_view_content(student_user) is True
    
    def test_other_users_cannot_view_quarantined_content(self, test_forum_post, admin_user, instructor_user):
        """Test that other users cannot view quarantined content"""
        content_type = ContentType.objects.get_for_model(ForumPost)
        
        quarantine = ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Test other user access'
        )
        
        # Instructor is not the author and not admin
        assert quarantine.can_view_content(instructor_user) is False
    
    def test_anonymous_users_cannot_view_quarantined_content(self, test_forum_post, admin_user):
        """Test that anonymous users cannot view quarantined content"""
        from django.contrib.auth.models import AnonymousUser
        
        content_type = ContentType.objects.get_for_model(ForumPost)
        
        quarantine = ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Test anonymous access'
        )
        
        anon_user = AnonymousUser()
        assert quarantine.can_view_content(anon_user) is False


# ================================
# QUARANTINE HELPER FUNCTION TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.quarantine
class TestQuarantineHelperFunctions:
    """Test quarantine helper functions from views"""
    
    def test_is_content_quarantined_returns_quarantine(self, test_forum_post, admin_user):
        """Test is_content_quarantined returns quarantine for active quarantine"""
        content_type = ContentType.objects.get_for_model(ForumPost)
        
        quarantine = ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Test helper function',
            status='ACTIVE'
        )
        
        result = is_content_quarantined(test_forum_post)
        assert result is not None
        assert result == quarantine
    
    def test_is_content_quarantined_returns_none_for_no_quarantine(self, test_forum_post):
        """Test is_content_quarantined returns None when not quarantined"""
        result = is_content_quarantined(test_forum_post)
        assert result is None
    
    def test_is_content_quarantined_returns_none_for_resolved(self, test_forum_post, admin_user):
        """Test is_content_quarantined returns None for resolved quarantine"""
        content_type = ContentType.objects.get_for_model(ForumPost)
        
        ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Test resolved',
            status='RESOLVED_RESTORE'
        )
        
        result = is_content_quarantined(test_forum_post)
        assert result is None
    
    def test_can_view_quarantined_content_helper(self, test_forum_post, admin_user, student_user):
        """Test can_view_quarantined_content helper function"""
        content_type = ContentType.objects.get_for_model(ForumPost)
        
        ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Test helper'
        )
        
        # Admin can view
        assert can_view_quarantined_content(test_forum_post, admin_user) is True
        
        # Author can view
        assert can_view_quarantined_content(test_forum_post, student_user) is True


# ================================
# QUARANTINE DECISION TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.quarantine
class TestQuarantineDecision:
    """Test cases for QuarantineDecision model"""
    
    def test_create_quarantine_decision(self, test_forum_post, admin_user):
        """Test creating a quarantine decision"""
        content_type = ContentType.objects.get_for_model(ForumPost)
        
        quarantine = ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Test decision'
        )
        
        decision = QuarantineDecision.objects.create(
            quarantine=quarantine,
            poll_result='RESTORE',
            action_taken='RESOLVED_RESTORE',
            decision_notes='Community voted to restore content',
            decided_by=admin_user
        )
        
        assert decision.quarantine == quarantine
        assert decision.poll_result == 'RESTORE'
        assert decision.action_taken == 'RESOLVED_RESTORE'
        assert decision.decided_by == admin_user
    
    def test_quarantine_decision_with_delete_action(self, test_forum_post, admin_user):
        """Test decision to delete content"""
        content_type = ContentType.objects.get_for_model(ForumPost)
        
        quarantine = ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Severe violation'
        )
        
        decision = QuarantineDecision.objects.create(
            quarantine=quarantine,
            poll_result='DELETE',
            action_taken='RESOLVED_DELETE',
            decision_notes='Content permanently removed',
            decided_by=admin_user
        )
        
        assert decision.action_taken == 'RESOLVED_DELETE'
    
    def test_resolution_workflow(self, test_forum_post, admin_user):
        """Test complete resolution workflow"""
        content_type = ContentType.objects.get_for_model(ForumPost)
        
        # Create quarantine
        quarantine = ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Test workflow',
            status='ACTIVE'
        )
        
        assert quarantine.is_active() is True
        
        # Create decision to restore
        decision = QuarantineDecision.objects.create(
            quarantine=quarantine,
            poll_result='RESTORE',
            action_taken='RESOLVED_RESTORE',
            decision_notes='Restored after review',
            decided_by=admin_user
        )
        
        # Update quarantine status
        quarantine.status = 'RESOLVED_RESTORE'
        quarantine.save()
        
        assert quarantine.is_active() is False
        assert quarantine.status == 'RESOLVED_RESTORE'


# ================================
# QUARANTINE STATISTICS TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.quarantine
class TestQuarantineStatistics:
    """Test quarantine statistics and reporting"""
    
    def test_count_active_quarantines(self, test_forum_post, test_blog_post, admin_user):
        """Test counting active quarantines"""
        forum_ct = ContentType.objects.get_for_model(ForumPost)
        blog_ct = ContentType.objects.get_for_model(BlogPost)
        
        # Create active quarantines
        ContentQuarantine.objects.create(
            content_type=forum_ct,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Active 1',
            status='ACTIVE'
        )
        
        ContentQuarantine.objects.create(
            content_type=blog_ct,
            object_id=test_blog_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Active 2',
            status='ACTIVE'
        )
        
        # Create resolved quarantine
        ContentQuarantine.objects.create(
            content_type=forum_ct,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Resolved',
            status='RESOLVED_RESTORE'
        )
        
        active_count = ContentQuarantine.objects.filter(status='ACTIVE').count()
        assert active_count == 2
    
    def test_count_by_content_type(self, test_forum_post, test_blog_post, admin_user):
        """Test counting quarantines by content type"""
        forum_ct = ContentType.objects.get_for_model(ForumPost)
        blog_ct = ContentType.objects.get_for_model(BlogPost)
        
        ContentQuarantine.objects.create(
            content_type=forum_ct,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Forum quarantine'
        )
        
        ContentQuarantine.objects.create(
            content_type=blog_ct,
            object_id=test_blog_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Blog quarantine'
        )
        
        forum_count = ContentQuarantine.objects.filter(content_type=forum_ct).count()
        blog_count = ContentQuarantine.objects.filter(content_type=blog_ct).count()
        
        assert forum_count >= 1
        assert blog_count >= 1
    
    def test_recent_quarantines(self, test_forum_post, admin_user):
        """Test retrieving recent quarantines"""
        content_type = ContentType.objects.get_for_model(ForumPost)
        
        # Create multiple quarantines
        for i in range(3):
            ContentQuarantine.objects.create(
                content_type=content_type,
                object_id=test_forum_post.id,
                quarantined_by=admin_user,
                quarantine_reason=f'Recent {i}'
            )
        
        recent = ContentQuarantine.objects.all()[:5]
        assert len(recent) >= 3


# ================================
# INTEGRATION TESTS
# ================================

@pytest.mark.django_db
@pytest.mark.quarantine
@pytest.mark.integration
class TestQuarantineIntegration:
    """Integration tests for quarantine system"""
    
    def test_multiple_content_types_quarantine(self, test_forum_post, test_blog_post, admin_user):
        """Test quarantining multiple content types simultaneously"""
        forum_ct = ContentType.objects.get_for_model(ForumPost)
        blog_ct = ContentType.objects.get_for_model(BlogPost)
        
        forum_q = ContentQuarantine.objects.create(
            content_type=forum_ct,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Forum violation'
        )
        
        blog_q = ContentQuarantine.objects.create(
            content_type=blog_ct,
            object_id=test_blog_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Blog violation'
        )
        
        assert forum_q.content_object == test_forum_post
        assert blog_q.content_object == test_blog_post
        assert ContentQuarantine.objects.count() == 2
    
    def test_quarantine_lifecycle(self, test_forum_post, admin_user):
        """Test complete quarantine lifecycle"""
        content_type = ContentType.objects.get_for_model(ForumPost)
        
        # 1. Create quarantine
        quarantine = ContentQuarantine.objects.create(
            content_type=content_type,
            object_id=test_forum_post.id,
            quarantined_by=admin_user,
            quarantine_reason='Lifecycle test',
            status='ACTIVE'
        )
        
        assert quarantine.is_active() is True
        
        # 2. Check access control
        assert quarantine.can_view_content(admin_user) is True
        
        # 3. Create decision
        decision = QuarantineDecision.objects.create(
            quarantine=quarantine,
            poll_result='RESTORE',
            action_taken='RESOLVED_RESTORE',
            decided_by=admin_user
        )
        
        # 4. Resolve quarantine
        quarantine.status = 'RESOLVED_RESTORE'
        quarantine.save()
        
        assert quarantine.is_active() is False
        assert decision.quarantine == quarantine
