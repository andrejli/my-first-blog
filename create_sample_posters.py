#!/usr/bin/env python3
"""
Script to create sample poster images for testing the event poster display feature.
Creates blank posters in portrait format (400x720) with event information.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
import textwrap

def create_poster(title, event_type, date, filename, width=400, height=720):
    """Create a sample poster with event information"""
    
    # Create image with dark background
    image = Image.new('RGB', (width, height), color='#0a0a0a')
    draw = ImageDraw.Draw(image)
    
    # Try to use a basic font
    try:
        # Try to load a system font
        title_font = ImageFont.truetype("arial.ttf", 36)
        type_font = ImageFont.truetype("arial.ttf", 24)
        date_font = ImageFont.truetype("arial.ttf", 20)
        label_font = ImageFont.truetype("arial.ttf", 16)
    except:
        # Fallback to default font if system font not available
        title_font = ImageFont.load_default()
        type_font = ImageFont.load_default()
        date_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
    
    # Colors
    primary_color = '#32cd32'  # Terminal green
    secondary_color = '#ffc107'  # Yellow
    text_color = '#ffffff'
    
    # Draw border
    border_width = 4
    draw.rectangle([border_width, border_width, width-border_width, height-border_width], 
                   outline=primary_color, width=border_width)
    
    # Draw header background
    header_height = 80
    draw.rectangle([0, 0, width, header_height], fill=primary_color)
    
    # Draw "FORTIS AURIS LMS" header
    header_text = "FORTIS AURIS LMS"
    header_bbox = draw.textbbox((0, 0), header_text, font=type_font)
    header_width = header_bbox[2] - header_bbox[0]
    header_x = (width - header_width) // 2
    draw.text((header_x, 25), header_text, fill='#000000', font=type_font)
    
    # Draw event type badge
    type_y = header_height + 30
    type_bbox = draw.textbbox((0, 0), event_type.upper(), font=label_font)
    type_width = type_bbox[2] - type_bbox[0] + 20
    type_height = type_bbox[3] - type_bbox[1] + 10
    type_x = (width - type_width) // 2
    
    draw.rectangle([type_x, type_y, type_x + type_width, type_y + type_height], 
                   fill=secondary_color, outline=secondary_color)
    draw.text((type_x + 10, type_y + 5), event_type.upper(), fill='#000000', font=label_font)
    
    # Draw title (wrapped if necessary)
    title_y = type_y + type_height + 40
    wrapped_title = textwrap.fill(title, width=20)
    title_lines = wrapped_title.split('\n')
    
    for i, line in enumerate(title_lines):
        line_bbox = draw.textbbox((0, 0), line, font=title_font)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = (width - line_width) // 2
        draw.text((line_x, title_y + i * 45), line, fill=text_color, font=title_font)
    
    # Draw date
    date_y = title_y + len(title_lines) * 45 + 60
    date_bbox = draw.textbbox((0, 0), date, font=date_font)
    date_width = date_bbox[2] - date_bbox[0]
    date_x = (width - date_width) // 2
    draw.text((date_x, date_y), date, fill=secondary_color, font=date_font)
    
    # Draw decorative elements
    # Terminal cursor
    cursor_y = date_y + 80
    draw.rectangle([width//2 - 50, cursor_y, width//2 + 50, cursor_y + 20], fill=primary_color)
    
    # Bottom text
    bottom_text = "Event Details Available"
    bottom_y = height - 100
    bottom_bbox = draw.textbbox((0, 0), bottom_text, font=label_font)
    bottom_width = bottom_bbox[2] - bottom_bbox[0]
    bottom_x = (width - bottom_width) // 2
    draw.text((bottom_x, bottom_y), bottom_text, fill=text_color, font=label_font)
    
    # Footer
    footer_text = "SECURE LEARNING ENVIRONMENT"
    footer_y = height - 40
    footer_bbox = draw.textbbox((0, 0), footer_text, font=label_font)
    footer_width = footer_bbox[2] - footer_bbox[0]
    footer_x = (width - footer_width) // 2
    draw.text((footer_x, footer_y), footer_text, fill=primary_color, font=label_font)
    
    return image

def main():
    """Create sample posters for different event types"""
    
    # Create media directory if it doesn't exist
    media_dir = os.path.join(os.path.dirname(__file__), 'media', 'event_posters')
    os.makedirs(media_dir, exist_ok=True)
    
    # Sample events to create posters for
    sample_events = [
        {
            'title': 'Python Programming Workshop',
            'event_type': 'Workshop',
            'date': 'October 25, 2025',
            'filename': 'python_workshop_poster.jpg'
        },
        {
            'title': 'Database Design Fundamentals',
            'event_type': 'Lecture',
            'date': 'October 28, 2025',
            'filename': 'database_lecture_poster.jpg'
        },
        {
            'title': 'Web Development Bootcamp',
            'event_type': 'Bootcamp',
            'date': 'November 2, 2025',
            'filename': 'web_bootcamp_poster.jpg'
        },
        {
            'title': 'AI & Machine Learning Seminar',
            'event_type': 'Seminar',
            'date': 'November 5, 2025',
            'filename': 'ai_seminar_poster.jpg'
        },
        {
            'title': 'Career Development Session',
            'event_type': 'Career',
            'date': 'November 8, 2025',
            'filename': 'career_session_poster.jpg'
        },
        {
            'title': 'Cybersecurity Awareness',
            'event_type': 'Security',
            'date': 'November 12, 2025',
            'filename': 'cybersecurity_poster.jpg'
        },
        {
            'title': 'Project Showcase Event',
            'event_type': 'Showcase',
            'date': 'November 15, 2025',
            'filename': 'project_showcase_poster.jpg'
        },
        {
            'title': 'Cloud Computing Deep Dive',
            'event_type': 'Technical',
            'date': 'November 18, 2025',
            'filename': 'cloud_computing_poster.jpg'
        }
    ]
    
    print("Creating sample event posters...")
    
    for event in sample_events:
        print(f"Creating poster for: {event['title']}")
        
        # Create poster
        poster = create_poster(
            title=event['title'],
            event_type=event['event_type'],
            date=event['date'],
            filename=event['filename']
        )
        
        # Save poster
        poster_path = os.path.join(media_dir, event['filename'])
        poster.save(poster_path, 'JPEG', quality=90)
        
        print(f"  Saved: {poster_path}")
    
    print(f"\nAll {len(sample_events)} posters created successfully!")
    print(f"Posters saved to: {media_dir}")
    print("\nNext steps:")
    print("1. Access Django admin at http://localhost:8000/admin/")
    print("2. Go to Events section")
    print("3. Create events and upload the corresponding poster files")
    print("4. Visit the calendar to see the poster display feature in action")

if __name__ == "__main__":
    main()