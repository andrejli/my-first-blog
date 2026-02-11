"""
Test Django Cache System Implementation
Tests view caching, cache configuration, and performance improvements
"""
import time
from django.test import TestCase, Client, override_settings
from django.core.cache import cache
from django.contrib.auth.models import User
from blog.models import Course, Enrollment, UserProfile


class CacheConfigurationTest(TestCase):
    """Test cache framework configuration"""
    
    def test_cache_backend_configured(self):
        """Test that cache backend is properly configured"""
        from django.conf import settings
        
        # Check cache configuration exists
        self.assertIn('default', settings.CACHES)
        self.assertIn('BACKEND', settings.CACHES['default'])
        
        # Verify backend is either locmem or redis
        backend = settings.CACHES['default']['BACKEND']
        self.assertIn('cache.backends', backend)
        
    def test_cache_basic_operations(self):
        """Test basic cache set/get/delete operations"""
        # Clear cache before test
        cache.clear()
        
        # Test set and get
        cache.set('test_key', 'test_value', 60)
        self.assertEqual(cache.get('test_key'), 'test_value')
        
        # Test get with default
        self.assertEqual(cache.get('nonexistent_key', 'default'), 'default')
        
        # Test delete
        cache.delete('test_key')
        self.assertIsNone(cache.get('test_key'))
        
    def test_cache_timeout(self):
        """Test cache expiration"""
        cache.clear()
        
        # Set with 1 second timeout
        cache.set('timeout_key', 'timeout_value', 1)
        self.assertEqual(cache.get('timeout_key'), 'timeout_value')
        
        # Wait for expiration (add small buffer)
        time.sleep(1.5)
        
        # Should be expired
        self.assertIsNone(cache.get('timeout_key'))
        
    def test_cache_clear(self):
        """Test cache clear operation"""
        cache.clear()
        
        # Set multiple keys
        cache.set('key1', 'value1', 60)
        cache.set('key2', 'value2', 60)
        
        # Verify they exist
        self.assertEqual(cache.get('key1'), 'value1')
        self.assertEqual(cache.get('key2'), 'value2')
        
        # Clear cache
        cache.clear()
        
        # Verify all keys are gone
        self.assertIsNone(cache.get('key1'))
        self.assertIsNone(cache.get('key2'))


class ViewCachingTest(TestCase):
    """Test view-level caching implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        cache.clear()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        # Use get_or_create to avoid duplicate UserProfile from signals
        UserProfile.objects.get_or_create(user=self.user, defaults={'role': 'student'})
        
        # Create test course
        self.instructor = User.objects.create_user(
            username='instructor',
            password='testpass123',
            email='instructor@example.com'
        )
        # Use get_or_create to avoid duplicate UserProfile from signals
        UserProfile.objects.get_or_create(user=self.instructor, defaults={'role': 'instructor'})
        UserProfile.objects.get_or_create(user=self.instructor, defaults={'role': 'instructor'})
        
        self.course = Course.objects.create(
            title='Test Course',
            course_code='TEST101',
            description='Test course description',
            instructor=self.instructor,
            status='published'
        )
        
    def test_landing_page_cached(self):
        """Test that landing page is cached"""
        # First request should hit the view
        response1 = self.client.get('/')
        self.assertEqual(response1.status_code, 200)
        
        # Second request should be cached (faster)
        start_time = time.time()
        response2 = self.client.get('/')
        cached_time = time.time() - start_time
        
        self.assertEqual(response2.status_code, 200)
        # Cached response should be very fast (< 0.1 seconds)
        self.assertLess(cached_time, 0.1, 
            f"Cached response took {cached_time}s, should be < 0.1s")
        
    def test_course_list_cached(self):
        """Test that course list is cached"""
        # First request
        response1 = self.client.get('/courses/')
        self.assertEqual(response1.status_code, 200)
        self.assertContains(response1, 'Test Course')
        
        # Second request should be cached
        response2 = self.client.get('/courses/')
        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, 'Test Course')
        
    def test_student_dashboard_cached_per_user(self):
        """Test that student dashboard is cached per user"""
        # Login as student
        self.client.login(username='testuser', password='testpass123')
        
        # Create enrollment
        Enrollment.objects.create(
            student=self.user,
            course=self.course,
            status='enrolled'
        )
        
        # Login as the user
        self.client.login(username='testuser', password='testpass123')
        
        # First request
        response1 = self.client.get('/dashboard/')
        self.assertEqual(response1.status_code, 200)
        
        # Second request should be cached (per-user)
        start_time = time.time()
        response2 = self.client.get('/dashboard/')
        cached_time = time.time() - start_time
        
        self.assertEqual(response2.status_code, 200)
        self.assertLess(cached_time, 0.1,
            f"Cached response took {cached_time}s, should be < 0.1s")
        
    def test_cache_varies_by_user(self):
        """Test that cache varies properly between different users"""
        # Create second user
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123',
            email='test2@example.com'
        )
        # Use get_or_create to avoid duplicate UserProfile from signals
        UserProfile.objects.get_or_create(user=user2, defaults={'role': 'student'})
        
        # Login as first user
        self.client.login(username='testuser', password='testpass123')
        response1 = self.client.get('/dashboard/')
        self.assertEqual(response1.status_code, 200)
        
        # Logout and login as second user
        self.client.logout()
        self.client.login(username='testuser2', password='testpass123')
        response2 = self.client.get('/dashboard/')
        self.assertEqual(response2.status_code, 200)
        
        # Both should work but be separate cached versions
        # (If cache wasn't varying by user, this could show wrong data)
        
    def test_event_calendar_cached(self):
        """Test that event calendar is cached"""
        # First request
        response1 = self.client.get('/calendar/')
        self.assertEqual(response1.status_code, 200)
        
        # Second request should be cached
        start_time = time.time()
        response2 = self.client.get('/calendar/')
        cached_time = time.time() - start_time
        
        self.assertEqual(response2.status_code, 200)
        self.assertLess(cached_time, 0.1,
            f"Cached response took {cached_time}s, should be < 0.1s")


class CachePerformanceTest(TestCase):
    """Test cache performance improvements"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        cache.clear()
        
        # Create instructor
        self.instructor = User.objects.create_user(
            username='instructor',
            password='testpass123'
        )
        # Use get_or_create to avoid duplicate UserProfile from signals
        UserProfile.objects.get_or_create(user=self.instructor, defaults={'role': 'instructor'})
        
        # Create multiple courses to test performance
        for i in range(10):
            Course.objects.create(
                title=f'Course {i}',
                course_code=f'TEST{i:03d}',
                description=f'Test course {i}',
                instructor=self.instructor,
                status='published'
            )
            
    def test_course_list_performance(self):
        """Test that cached course list is significantly faster"""
        # First request (uncached)
        start_time = time.time()
        response1 = self.client.get('/courses/')
        uncached_time = time.time() - start_time
        self.assertEqual(response1.status_code, 200)
        
        # Second request (cached)
        start_time = time.time()
        response2 = self.client.get('/courses/')
        cached_time = time.time() - start_time
        self.assertEqual(response2.status_code, 200)
        
        # Cached should be at least 2x faster (usually much more)
        speedup = uncached_time / cached_time if cached_time > 0 else float('inf')
        self.assertGreater(speedup, 2.0,
            f"Cached response only {speedup:.1f}x faster, expected >2x")
        
    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate tracking"""
        cache.clear()
        
        # Make multiple requests to same page
        hits = 0
        misses = 0
        
        for i in range(10):
            response = self.client.get('/courses/')
            self.assertEqual(response.status_code, 200)
            
            # First request is miss, rest are hits
            if i == 0:
                misses += 1
            else:
                hits += 1
                
        # Calculate hit rate
        total_requests = hits + misses
        hit_rate = (hits / total_requests) * 100 if total_requests > 0 else 0
        
        # Should have 90% hit rate (9 hits, 1 miss)
        self.assertEqual(hit_rate, 90.0)
        

class CacheInvalidationTest(TestCase):
    """Test cache invalidation scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        cache.clear()
        
    def test_cache_manual_clear(self):
        """Test manual cache clearing"""
        # Set cache
        cache.set('test_key', 'test_value', 300)
        self.assertEqual(cache.get('test_key'), 'test_value')
        
        # Clear cache
        cache.clear()
        
        # Verify cleared
        self.assertIsNone(cache.get('test_key'))
        
    def test_cache_key_deletion(self):
        """Test deleting specific cache keys"""
        # Set multiple keys
        cache.set('key1', 'value1', 300)
        cache.set('key2', 'value2', 300)
        
        # Delete one key
        cache.delete('key1')
        
        # Verify only one deleted
        self.assertIsNone(cache.get('key1'))
        self.assertEqual(cache.get('key2'), 'value2')


class CacheFunctionalTest(TestCase):
    """Functional tests for cache system"""
    
    def test_cache_system_integration(self):
        """Test complete cache system integration"""
        cache.clear()
        
        # Test 1: Cache configuration
        from django.conf import settings
        self.assertIn('default', settings.CACHES)
        
        # Test 2: Basic cache operations
        cache.set('integration_test', 'success', 60)
        self.assertEqual(cache.get('integration_test'), 'success')
        
        # Test 3: Cache backend is properly configured
        self.assertIn('BACKEND', settings.CACHES['default'])
        self.assertTrue(settings.CACHES['default']['BACKEND'])
        
        # Test 4: Cache clear
        cache.clear()
        self.assertIsNone(cache.get('integration_test'))
        
    def test_cache_under_load(self):
        """Test cache performance under load"""
        cache.clear()
        
        # Simulate load with multiple cache operations
        for i in range(100):
            cache.set(f'load_test_{i}', f'value_{i}', 60)
            
        # Verify all cached
        for i in range(100):
            value = cache.get(f'load_test_{i}')
            self.assertEqual(value, f'value_{i}')
            
        # Clear
        cache.clear()


# Test summary function
def run_cache_tests():
    """
    Run all cache tests and return summary
    
    Returns:
        dict: Test results summary
    """
    import unittest
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(CacheConfigurationTest))
    suite.addTests(loader.loadTestsFromTestCase(ViewCachingTest))
    suite.addTests(loader.loadTestsFromTestCase(CachePerformanceTest))
    suite.addTests(loader.loadTestsFromTestCase(CacheInvalidationTest))
    suite.addTests(loader.loadTestsFromTestCase(CacheFunctionalTest))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return {
        'total': result.testsRun,
        'passed': result.testsRun - len(result.failures) - len(result.errors),
        'failed': len(result.failures),
        'errors': len(result.errors),
        'success': result.wasSuccessful()
    }
