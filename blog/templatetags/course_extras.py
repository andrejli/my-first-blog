from django import template
from blog.models import Progress, Lesson

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary in a template"""
    if dictionary and key in dictionary:
        return dictionary[key]
    return None

@register.filter
def mul(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide value by arg"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_user_progress(course, user):
    """Get user progress for a course"""
    if not course or not user:
        return {'completed_lessons': 0, 'total_lessons': 0, 'progress_percentage': 0}
    
    total_lessons = Lesson.objects.filter(course=course, is_published=True).count()
    completed_lessons = Progress.objects.filter(
        student=user,
        lesson__course=course,
        lesson__is_published=True,
        completed=True
    ).count()
    
    progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
    
    return {
        'completed_lessons': completed_lessons,
        'total_lessons': total_lessons,
        'progress_percentage': progress_percentage
    }