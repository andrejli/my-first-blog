"""
Enhanced Markdown Template Tags with Obsidian Compatibility
Provides comprehensive markdown processing for the Terminal LMS
"""
import re
import markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from django import template
from django.utils.safestring import mark_safe
from django.urls import reverse, NoReverseMatch
from django.template.defaultfilters import slugify
from blog.models import Course, Lesson

register = template.Library()


class ObsidianExtension(Extension):
    """Custom Markdown extension for Obsidian-style syntax"""
    
    def extendMarkdown(self, md):
        # Add processors for Obsidian-style features
        # Note: Higher priority numbers run first!
        md.preprocessors.register(
            ImageEmbedPreprocessor(md),
            'obsidian_image_embeds',
            200  # Run BEFORE WikiLinks to catch ![[image]] patterns
        )
        md.preprocessors.register(
            WikiLinkPreprocessor(md, self.getConfig('base_url', '')),
            'obsidian_wikilinks',
            175
        )
        md.preprocessors.register(
            CalloutPreprocessor(md),
            'obsidian_callouts',
            150
        )


class WikiLinkPreprocessor(Preprocessor):
    """Process [[Wiki Links]] for internal course/lesson linking"""
    
    def __init__(self, md, base_url=''):
        super().__init__(md)
        self.base_url = base_url
        self.wikilink_re = re.compile(r'\[\[([^\]]+)\]\]')
    
    def run(self, lines):
        new_lines = []
        for line in lines:
            new_line = self.wikilink_re.sub(self._replace_wikilink, line)
            new_lines.append(new_line)
        return new_lines
    
    def _replace_wikilink(self, match):
        """Convert [[Link]] to proper HTML link"""
        link_text = match.group(1).strip()
        
        # Handle different link formats
        if '|' in link_text:
            # [[Course Title|Display Text]]
            target, display = link_text.split('|', 1)
            target = target.strip()
            display = display.strip()
        else:
            # [[Course Title]]
            target = display = link_text
        
        # Try to find matching course or lesson
        url = self._resolve_internal_link(target)
        
        if url:
            return f'<a href="{url}" class="wiki-link internal-link" title="{target}">{display}</a>'
        else:
            # Create a placeholder for broken links
            return f'<span class="wiki-link broken-link" title="Link not found: {target}">{display}</span>'
    
    def _resolve_internal_link(self, target):
        """Resolve internal links to courses or lessons"""
        try:
            # Try to find course by title
            course = Course.objects.filter(title__iexact=target).first()
            if course:
                return reverse('course_detail', args=[course.pk])
            
            # Try to find lesson by title
            lesson = Lesson.objects.filter(title__iexact=target, is_published=True).first()
            if lesson:
                return reverse('lesson_detail', args=[lesson.course.pk, lesson.pk])
            
            # Try course code match
            course = Course.objects.filter(course_code__iexact=target).first()
            if course:
                return reverse('course_detail', args=[course.pk])
                
        except (Course.DoesNotExist, Lesson.DoesNotExist, NoReverseMatch):
            pass
        
        return None


class CalloutPreprocessor(Preprocessor):
    """Process Obsidian-style callouts like > [!note]"""
    
    def __init__(self, md):
        super().__init__(md)
        self.callout_re = re.compile(r'^> \[!(\w+)\](.*?)$', re.MULTILINE)
    
    def run(self, lines):
        text = '\n'.join(lines)
        
        # Replace callout syntax with HTML
        def replace_callout(match):
            callout_type = match.group(1).lower()
            title = match.group(2).strip() or callout_type.title()
            
            # Map callout types to CSS classes and icons
            callout_map = {
                'note': ('info', '📝'),
                'tip': ('success', '💡'),
                'warning': ('warning', '⚠️'),
                'danger': ('danger', '❌'),
                'info': ('info', 'ℹ️'),
                'success': ('success', '✅'),
                'question': ('primary', '❓'),
                'quote': ('secondary', '💬'),
            }
            
            css_class, icon = callout_map.get(callout_type, ('info', '📋'))
            
            return f'''<div class="callout callout-{callout_type} alert alert-{css_class}">
                <div class="callout-title">
                    <span class="callout-icon">{icon}</span>
                    <strong>{title}</strong>
                </div>
                <div class="callout-content">'''
        
        # Process callouts
        processed = self.callout_re.sub(replace_callout, text)
        
        # Close callout divs (simple approach - assumes single line callouts for now)
        processed = re.sub(r'<div class="callout-content">\s*$', '<div class="callout-content"></div></div>', processed, flags=re.MULTILINE)
        
        return processed.split('\n')


class ImageEmbedPreprocessor(Preprocessor):
    """Process Obsidian-style image embeds like ![[image.png]]"""
    
    def __init__(self, md):
        super().__init__(md)
        self.image_embed_re = re.compile(r'!\[\[([^\]]+)\]\]')
    
    def run(self, lines):
        new_lines = []
        for line in lines:
            new_line = self.image_embed_re.sub(self._replace_image_embed, line)
            new_lines.append(new_line)
        return new_lines
    
    def _replace_image_embed(self, match):
        """Convert ![[image.png]] to proper image tag"""
        image_path = match.group(1).strip()
        
        # Handle image with alt text: ![[image.png|Alt Text]]
        if '|' in image_path:
            path, alt_text = image_path.split('|', 1)
            path = path.strip()
            alt_text = alt_text.strip()
        else:
            path = image_path
            alt_text = path
        
        # Determine the correct media path based on file pattern
        # Blog images uploaded via our system have user_id prefix
        if path.startswith('user_') and '_' in path:
            # Blog image format: user_123_abc12345.jpg
            media_path = f"/media/blog_images/{path}"
        else:
            # Course material or external image
            media_path = f"/media/course_materials/{path}"
        
        # Create responsive image HTML with proper CSS classes
        return f'<img src="{media_path}" alt="{alt_text}" class="img-responsive obsidian-image blog-image" title="{alt_text}">'


@register.filter
def obsidian_markdown(value):
    """
    Enhanced markdown filter with Obsidian compatibility
    
    Features:
    - [[Wiki Links]] for internal course/lesson linking
    - ![[Image embeds]] for course materials
    - > [!callout] blocks for notes, warnings, tips
    - Syntax highlighting for code blocks
    - Math equations with MathJax
    - Tables, task lists, and more
    """
    if not value:
        return ''
    
    # Configure markdown with extensions
    md = markdown.Markdown(
        extensions=[
            'markdown.extensions.extra',      # Tables, footnotes, etc.
            'markdown.extensions.codehilite', # Syntax highlighting
            'markdown.extensions.toc',        # Table of contents
            'markdown.extensions.admonition', # !!! note blocks
            ObsidianExtension(),              # Our custom Obsidian features
        ],
        extension_configs={
            'markdown.extensions.codehilite': {
                'css_class': 'highlight',
                'use_pygments': True,
            },
        }
    )
    
    # Convert markdown to HTML
    html = md.convert(value)
    
    return mark_safe(html)


@register.filter
def markdown_preview(value, max_words=50):
    """Generate a plain text preview of markdown content"""
    if not value:
        return ''
    
    # Simple markdown to text conversion
    # Remove markdown syntax for preview
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', value)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)       # Italic
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text) # Links
    text = re.sub(r'`(.*?)`', r'\1', text)          # Inline code
    text = re.sub(r'#{1,6}\s*(.*)', r'\1', text)    # Headers
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text) # Wiki links
    text = re.sub(r'!\[\[([^\]]+)\]\]', r'[Image: \1]', text) # Image embeds
    text = re.sub(r'> \[!\w+\].*', r'[Callout]', text) # Callouts
    
    words = text.split()
    if len(words) > max_words:
        return ' '.join(words[:max_words]) + '...'
    return ' '.join(words)


@register.simple_tag
def markdown_help():
    """Generate markdown help content"""
    return mark_safe("""
        <div class="markdown-help">
            <h5>Enhanced Markdown Help</h5>
            <div class="row">
                <div class="col-md-6">
                    <h6>Basic Formatting:</h6>
                    <code>**bold** *italic* `code`</code><br>
                    <code># Header 1</code><br>
                    <code>## Header 2</code><br>
                    <code>- List item</code><br>
                    <code>1. Numbered list</code>
                </div>
                <div class="col-md-6">
                    <h6>Obsidian Features:</h6>
                    <code>[[Course Title]]</code> - Link to course<br>
                    <code>![[image.png]]</code> - Embed image<br>
                    <code>> [!note] Title</code> - Callout box<br>
                    <code>- [ ] Task item</code> - Checkbox
                </div>
            </div>
        </div>
    """)