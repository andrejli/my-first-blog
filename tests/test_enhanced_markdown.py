"""
Tests for Enhanced Markdown System with Obsidian Compatibility
"""

import pytest
from django.test import TestCase
from blog.templatetags.markdown_extras import obsidian_markdown, markdown_preview
from blog.models import Course, Lesson, User, UserProfile


class EnhancedMarkdownTest(TestCase):
    
    def setUp(self):
        # Create test user and course for link testing
        self.user = User.objects.create_user(
            username='testinstructor',
            email='test@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.user, role='instructor')
        
        self.course = Course.objects.create(
            title='Python Programming Basics',
            course_code='PY101', 
            description='Test course',
            instructor=self.user,
            status='published'
        )
        
        self.lesson = Lesson.objects.create(
            course=self.course,
            title='Introduction to Variables',
            content='Test lesson content',
            order=1,
            is_published=True
        )
    
    def test_basic_markdown_formatting(self):
        """Test basic markdown features work correctly"""
        content = """
        # Header 1
        ## Header 2
        **Bold text** and *italic text*
        `inline code`
        """
        result = obsidian_markdown(content)
        
        self.assertIn('<h1>Header 1</h1>', result)
        self.assertIn('<h2>Header 2</h2>', result)
        self.assertIn('<strong>Bold text</strong>', result)
        self.assertIn('<em>italic text</em>', result)
        self.assertIn('<code>inline code</code>', result)
    
    def test_wiki_links(self):
        """Test Obsidian-style wiki links"""
        content = "Check out [[Python Programming Basics]] course"
        result = obsidian_markdown(content)
        
        self.assertIn('wiki-link', result)
        self.assertIn('internal-link', result)
        self.assertIn('Python Programming Basics', result)
    
    def test_wiki_links_with_display_text(self):
        """Test wiki links with custom display text"""
        content = "See [[Python Programming Basics|Python Course]] for details"
        result = obsidian_markdown(content)
        
        self.assertIn('wiki-link', result)
        self.assertIn('Python Course', result)
    
    def test_broken_wiki_links(self):
        """Test handling of non-existent wiki links"""
        content = "Link to [[Non-Existent Course]]"
        result = obsidian_markdown(content)
        
        self.assertIn('broken-link', result)
        self.assertIn('Non-Existent Course', result)
    
    def test_callouts(self):
        """Test Obsidian-style callouts"""
        test_cases = [
            ('> [!note] Important Note', 'callout-note'),
            ('> [!tip] Pro Tip', 'callout-tip'),
            ('> [!warning] Be Careful', 'callout-warning'),
            ('> [!danger] Danger Zone', 'callout-danger'),
        ]
        
        for content, expected_class in test_cases:
            with self.subTest(content=content):
                result = obsidian_markdown(content)
                self.assertIn('callout', result)
                self.assertIn(expected_class, result)
    
    def test_image_embeds(self):
        """Test Obsidian-style image embeds"""
        content = "Here's a diagram: ![[diagram.png]]"
        result = obsidian_markdown(content)
        
        self.assertIn('obsidian-image', result)
        self.assertIn('/media/course_materials/diagram.png', result)
        self.assertIn('img-responsive', result)
    
    def test_image_embeds_with_alt_text(self):
        """Test image embeds with alt text"""
        content = "![[diagram.png|System Architecture]]"
        result = obsidian_markdown(content)
        
        self.assertIn('alt="System Architecture"', result)
        self.assertIn('title="System Architecture"', result)
    
    def test_code_blocks(self):
        """Test code block rendering"""
        content = """
        ```python
        def hello():
            print("Hello World!")
        ```
        """
        result = obsidian_markdown(content)
        
        self.assertIn('<pre>', result)
        self.assertIn('<code>', result)
        self.assertIn('def hello():', result)
    
    def test_tables(self):
        """Test markdown table rendering"""
        content = """
        | Feature | Status |
        |---------|--------|
        | Tables  | ✅     |
        | Lists   | ✅     |
        """
        result = obsidian_markdown(content)
        
        self.assertIn('<table>', result)
        self.assertIn('<th>Feature</th>', result)
        self.assertIn('<td>Tables</td>', result)
    
    def test_task_lists(self):
        """Test task list rendering"""
        content = """
        - [x] Completed task
        - [ ] Incomplete task
        """
        result = obsidian_markdown(content)
        
        self.assertIn('<ul>', result)
        self.assertIn('<li>', result)
    
    def test_mixed_content(self):
        """Test complex content with multiple features"""
        content = """
        # Course Overview
        
        Welcome to [[Python Programming Basics]]!
        
        > [!note] Getting Started
        > This course covers the fundamentals.
        
        ## Topics Covered
        - **Variables** and `data types`
        - *Control structures*
        - Functions and classes
        
        See the diagram: ![[course-overview.png]]
        
        ```python
        # Sample code
        name = "Student"
        print(f"Hello, {name}!")
        ```
        """
        result = obsidian_markdown(content)
        
        # Verify multiple features work together
        self.assertIn('<h1>Course Overview</h1>', result)
        self.assertIn('wiki-link', result)
        self.assertIn('callout', result)
        self.assertIn('<strong>Variables</strong>', result)
        self.assertIn('<code>data types</code>', result)
        self.assertIn('obsidian-image', result)
        self.assertIn('print(f"Hello, {name}!")', result)
    
    def test_markdown_preview_filter(self):
        """Test markdown preview functionality"""
        content = """
        # Long Header
        
        This is a **very long** piece of content that should be truncated
        when creating a preview. It has multiple sentences and lots of
        markdown formatting that should be stripped out for the preview.
        """
        preview = markdown_preview(content, max_words=10)
        
        # Should be truncated
        self.assertTrue(len(preview.split()) <= 11)  # 10 words + "..."
        # Should not contain markdown
        self.assertNotIn('**', preview)
        self.assertNotIn('#', preview)
    
    def test_empty_content(self):
        """Test handling of empty/None content"""
        self.assertEqual(obsidian_markdown(None), '')
        self.assertEqual(obsidian_markdown(''), '')
        self.assertEqual(obsidian_markdown('   '), '<p></p>')
    
    def test_security_escaping(self):
        """Test that HTML is properly escaped"""
        content = '<script>alert("xss")</script>'
        result = obsidian_markdown(content)
        
        # Should be escaped, not executed
        self.assertNotIn('<script>', result)
        self.assertIn('&lt;script&gt;', result)


# Integration test with actual lesson content
class MarkdownIntegrationTest(TestCase):
    
    def test_lesson_content_rendering(self):
        """Test that lesson content is properly processed"""
        # This would normally be tested through the view
        # but we can test the template tag directly
        user = User.objects.create_user(
            username='testinstructor2',
            email='test2@example.com', 
            password='testpass123'
        )
        UserProfile.objects.create(user=user, role='instructor')
        
        course = Course.objects.create(
            title='Test Course',
            course_code='TEST101',
            description='Test course',
            instructor=user,
            status='published'
        )
        
        lesson_content = """
        # Welcome to the Course
        
        This lesson covers [[Advanced Topics]] and includes:
        
        > [!tip] Study Tips
        > Review the materials regularly
        
        Code example:
        ```python
        print("Hello, LMS!")
        ```
        """
        
        lesson = Lesson.objects.create(
            course=course,
            title='Test Lesson',
            content=lesson_content,
            order=1,
            is_published=True
        )
        
        # Process the content
        rendered = obsidian_markdown(lesson.content)
        
        # Verify the content was properly processed
        self.assertIn('<h1>Welcome to the Course</h1>', rendered)
        self.assertIn('wiki-link', rendered)
        self.assertIn('callout', rendered)
        self.assertIn('print("Hello, LMS!")', rendered)