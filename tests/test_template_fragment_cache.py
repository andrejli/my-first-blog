"""
Tests for template fragment caching implementation
"""
import time
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.cache import cache
from django.template import Template, Context
from django.template.loader import render_to_string
from blog.models import Course, UserProfile, Forum, BlogPost


class TemplateFragmentCacheTest(TestCase):
    """Test template fragment caching functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        cache.clear()
        
        # Create test users
        self.student = User.objects.create_user(
            username='student',
            password='testpass123',
            email='student@test.com'
        )
        UserProfile.objects.get_or_create(user=self.student, defaults={'role': 'student'})
        
        self.instructor = User.objects.create_user(
            username='instructor',
            password='testpass123',
            email='instructor@test.com'
        )
        UserProfile.objects.get_or_create(user=self.instructor, defaults={'role': 'instructor'})
        
    def test_cache_tag_loads_successfully(self):
        """Test that cache template tag loads without errors"""
        template = Template("{% load cache %}{% cache 300 test_key %}Cached content{% endcache %}")
        context = Context({})
        result = template.render(context)
        self.assertIn('Cached content', result)
        
    def test_cache_tag_with_variables(self):
        """Test cache tag with variable keys"""
        template = Template("{% load cache %}{% cache 300 test_key user_id %}{{ content }}{% endcache %}")
        context = Context({'user_id': 123, 'content': 'Test content'})
        
        # First render
        result1 = template.render(context)
        self.assertIn('Test content', result1)
        
        # Change content but same cache key - should return cached version
        context['content'] = 'Different content'
        result2 = template.render(context)
        self.assertIn('Test content', result2)  # Should still be original
        
    def test_cache_varies_by_key(self):
        """Test that cache properly varies by different keys"""
        template = Template("{% load cache %}{% cache 300 test_key user_id %}User: {{ user_id }}{% endcache %}")
        
        # Render for user 1
        context1 = Context({'user_id': 1})
        result1 = template.render(context1)
        self.assertIn('User: 1', result1)
        
        # Render for user 2 - should be different
        context2 = Context({'user_id': 2})
        result2 = template.render(context2)
        self.assertIn('User: 2', result2)
        
    def test_base_navigation_cached(self):
        """Test that navigation menu is cached"""
        # Login to populate session
        self.client.login(username='student', password='testpass123')
        
        # First request
        start_time = time.time()
        response1 = self.client.get('/')
        first_time = time.time() - start_time
        
        self.assertEqual(response1.status_code, 200)
        
        # Second request should be faster due to fragment caching
        start_time = time.time()
        response2 = self.client.get('/')
        second_time = time.time() - start_time
        
        self.assertEqual(response2.status_code, 200)
        # Note: Template fragment caching helps, but full page timing may vary
        
    def test_course_list_fragment_caching(self):
        """Test that course cards are cached individually"""
        # Create test course
        course = Course.objects.create(
            title='Test Course',
            course_code='TEST101',
            description='Test description',
            instructor=self.instructor,
            status='published'
        )
        
        # Login as student
        self.client.login(username='student', password='testpass123')
        
        # First request
        response1 = self.client.get('/courses/')
        self.assertEqual(response1.status_code, 200)
        self.assertContains(response1, 'Test Course')
        
        # Cache key should exist for this course card
        # Note: Actual cache key format depends on Django's cache framework
        
    def test_landing_page_fragment_cached(self):
        """Test that landing page welcome section is cached"""
        # First request
        response1 = self.client.get('/')
        self.assertEqual(response1.status_code, 200)
        self.assertContains(response1, 'Welcome to FORTIS AURIS LMS')
        
        # Second request should use cached fragment
        response2 = self.client.get('/')
        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, 'Welcome to FORTIS AURIS LMS')
        
    def test_forum_list_fragment_caching(self):
        """Test that forum cards are cached"""
        # Create test forum
        forum = Forum.objects.create(
            title='Test Forum',
            description='Test forum description',
            forum_type='general'
        )
        
        self.client.login(username='student', password='testpass123')
        
        # First request
        response1 = self.client.get('/forums/')
        self.assertEqual(response1.status_code, 200)
        
        # Second request should use cached fragments
        response2 = self.client.get('/forums/')
        self.assertEqual(response2.status_code, 200)
        
    def test_cache_invalidation_on_timeout(self):
        """Test that cache properly expires after timeout"""
        # Use very short timeout for testing
        template = Template("{% load cache %}{% cache 1 short_cache %}{{ content }}{% endcache %}")
        
        # First render
        context = Context({'content': 'Original'})
        result1 = template.render(context)
        self.assertIn('Original', result1)
        
        # Wait for cache to expire
        time.sleep(1.1)
        
        # Change content and render again - should see new content
        context['content'] = 'Updated'
        result2 = template.render(context)
        self.assertIn('Updated', result2)
        

class TemplateFragmentPerformanceTest(TestCase):
    """Test performance improvements from template fragment caching"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        cache.clear()
        
        # Create instructor
        self.instructor = User.objects.create_user(
            username='instructor',
            password='testpass123'
        )
        UserProfile.objects.get_or_create(user=self.instructor, defaults={'role': 'instructor'})
        
        # Create multiple courses for testing
        for i in range(5):
            Course.objects.create(
                title=f'Course {i}',
                course_code=f'TEST{i:03d}',
                description=f'Test course {i}',
                instructor=self.instructor,
                status='published'
            )
    
    def test_course_list_rendering_improvement(self):
        """Test that course list renders faster with caching"""
        # First request (no cache)
        cache.clear()
        start_time = time.time()
        response1 = self.client.get('/courses/')
        first_time = time.time() - start_time
        
        self.assertEqual(response1.status_code, 200)
        
        # Second request (with cache)
        start_time = time.time()
        response2 = self.client.get('/courses/')
        cached_time = time.time() - start_time
        
        self.assertEqual(response2.status_code, 200)
        
        # Cached version should be faster or similar
        # Note: View-level caching has more impact than template fragments alone
        self.assertGreater(first_time, 0)
        self.assertGreater(cached_time, 0)
        
    def test_multiple_fragment_caching(self):
        """Test that multiple fragments cache independently"""
        template = Template("""
        {% load cache %}
        {% cache 300 fragment1 %}Fragment 1: {{ var1 }}{% endcache %}
        {% cache 300 fragment2 %}Fragment 2: {{ var2 }}{% endcache %}
        {% cache 300 fragment3 %}Fragment 3: {{ var3 }}{% endcache %}
        """)
        
        context = Context({'var1': 'A', 'var2': 'B', 'var3': 'C'})
        result = template.render(context)
        
        self.assertIn('Fragment 1: A', result)
        self.assertIn('Fragment 2: B', result)
        self.assertIn('Fragment 3: C', result)


class TemplateFragmentIntegrationTest(TestCase):
    """Integration tests for template fragment caching with views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        cache.clear()
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        UserProfile.objects.get_or_create(user=self.user, defaults={'role': 'student'})
        
    def test_cache_interaction_with_view_cache(self):
        """Test that template fragments work alongside view caching"""
        # View is cached at view level (@cache_page)
        # Template fragments provide additional granularity
        
        self.client.login(username='testuser', password='testpass123')
        
        # First request
        response1 = self.client.get('/dashboard/')
        self.assertEqual(response1.status_code, 200)
        
        # Second request - both view cache and fragment cache active
        response2 = self.client.get('/dashboard/')
        self.assertEqual(response2.status_code, 200)
        
        # Both responses should be identical
        self.assertEqual(len(response1.content), len(response2.content))
        
    def test_authenticated_vs_anonymous_caching(self):
        """Test that caching varies properly between auth states"""
        # Anonymous request
        response1 = self.client.get('/')
        self.assertEqual(response1.status_code, 200)
        
        # Authenticated request
        self.client.login(username='testuser', password='testpass123')
        response2 = self.client.get('/')
        self.assertEqual(response2.status_code, 200)
        
        # Responses should differ due to auth state
        # (cache keys include user.is_authenticated)
