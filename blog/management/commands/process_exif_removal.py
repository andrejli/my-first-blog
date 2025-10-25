"""
Django management command to process existing images and remove EXIF metadata.

This command scans all uploaded images in the media directory and processes them
to remove EXIF metadata for privacy and security compliance.

Usage:
    python manage.py process_exif_removal
    python manage.py process_exif_removal --dry-run
    python manage.py process_exif_removal --model=BlogPost
    python manage.py process_exif_removal --force
"""

import os
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import models
from blog.models import BlogPost, Event
from blog.utils.image_processing import process_uploaded_image, get_image_info
from blog.utils.storage import MediaStorage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process existing uploaded images to remove EXIF metadata'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Show what would be processed without making changes',
        )
        parser.add_argument(
            '--model',
            type=str,
            dest='model_name',
            choices=['BlogPost', 'Event', 'all'],
            default='all',
            help='Process images from specific model only (default: all)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            help='Force processing even if images appear to be already processed',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            dest='verbose',
            help='Show detailed processing information',
        )
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.force = options['force']
        self.verbose = options['verbose']
        self.model_name = options['model_name']
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE: No changes will be made')
            )
        
        self.stdout.write(f'Processing EXIF metadata removal for model: {self.model_name}')
        
        total_processed = 0
        total_errors = 0
        
        if self.model_name in ['BlogPost', 'all']:
            processed, errors = self.process_blog_posts()
            total_processed += processed
            total_errors += errors
        
        if self.model_name in ['Event', 'all']:
            processed, errors = self.process_events()
            total_processed += processed
            total_errors += errors
        
        # Summary
        if self.dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN COMPLETE: Would process {total_processed} images '
                    f'({total_errors} errors detected)'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'PROCESSING COMPLETE: {total_processed} images processed '
                    f'({total_errors} errors)'
                )
            )
    
    def process_blog_posts(self):
        """Process BlogPost featured images."""
        self.stdout.write('Processing BlogPost featured images...')
        
        blog_posts = BlogPost.objects.exclude(featured_image='')
        total_count = blog_posts.count()
        processed_count = 0
        error_count = 0
        
        self.stdout.write(f'Found {total_count} blog posts with featured images')
        
        for i, blog_post in enumerate(blog_posts, 1):
            if self.verbose:
                self.stdout.write(f'[{i}/{total_count}] Processing: {blog_post.title}')
            
            try:
                result = self.process_image_field(
                    blog_post, 
                    'featured_image', 
                    f'BlogPost "{blog_post.title}" (ID: {blog_post.id})'
                )
                if result:
                    processed_count += 1
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing {blog_post.title}: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'BlogPost processing: {processed_count} processed, {error_count} errors'
            )
        )
        
        return processed_count, error_count
    
    def process_events(self):
        """Process Event poster images."""
        self.stdout.write('Processing Event poster images...')
        
        events = Event.objects.exclude(poster='')
        total_count = events.count()
        processed_count = 0
        error_count = 0
        
        self.stdout.write(f'Found {total_count} events with poster images')
        
        for i, event in enumerate(events, 1):
            if self.verbose:
                self.stdout.write(f'[{i}/{total_count}] Processing: {event.title}')
            
            try:
                result = self.process_image_field(
                    event, 
                    'poster', 
                    f'Event "{event.title}" (ID: {event.id})'
                )
                if result:
                    processed_count += 1
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing {event.title}: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Event processing: {processed_count} processed, {error_count} errors'
            )
        )
        
        return processed_count, error_count
    
    def process_image_field(self, instance, field_name, description):
        """
        Process a single image field on a model instance.
        
        Args:
            instance: Model instance
            field_name: Name of the ImageField
            description: Human-readable description for logging
            
        Returns:
            bool: True if image was processed, False if skipped
        """
        image_field = getattr(instance, field_name)
        
        if not image_field:
            if self.verbose:
                self.stdout.write(f'  No image found for {description}')
            return False
        
        try:
            # Check if image exists on disk
            if not image_field.storage.exists(image_field.name):
                self.stdout.write(
                    self.style.WARNING(f'  Image file not found: {image_field.name}')
                )
                return False
            
            # Get image info to check for EXIF
            image_field.seek(0)
            image_info = get_image_info(image_field)
            
            if not self.force and not image_info.get('has_exif', False):
                if self.verbose:
                    self.stdout.write(f'  No EXIF data found in {description}')
                return False
            
            if self.dry_run:
                exif_status = "HAS EXIF" if image_info.get('has_exif', False) else "NO EXIF"
                size_mb = image_info.get('file_size', 0) / 1024 / 1024
                self.stdout.write(
                    f'  WOULD PROCESS: {description} '
                    f'({image_info.get("width", 0)}x{image_info.get("height", 0)}, '
                    f'{size_mb:.1f}MB, {exif_status})'
                )
                return True
            
            # Process the image
            image_field.seek(0)
            processed_image, processing_info = process_uploaded_image(
                image_field, 
                strip_exif=True
            )
            
            if processing_info.get('exif_removed', False):
                # Save the processed image
                original_name = image_field.name
                image_field.save(
                    os.path.basename(original_name),
                    processed_image,
                    save=True
                )
                
                # Log the processing
                original_size = processing_info.get('summary', {}).get('original_size', 0)
                processed_size = processing_info.get('summary', {}).get('processed_size', 0)
                exif_count = processing_info.get('summary', {}).get('exif_summary', {}).get('total_tags', 0)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  PROCESSED: {description} '
                        f'(Removed {exif_count} EXIF tags, '
                        f'{original_size}→{processed_size} bytes)'
                    )
                )
                
                # Log to file for audit trail
                logger.info(f"Management command EXIF removal: {description} processed")
                
                return True
            else:
                if self.verbose:
                    self.stdout.write(f'  No EXIF processing needed for {description}')
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'  ERROR processing {description}: {str(e)}'
                )
            )
            raise
    
    def get_media_statistics(self):
        """Get statistics about media files (for future enhancement)."""
        if not hasattr(settings, 'MEDIA_ROOT'):
            return {}
        
        media_root = settings.MEDIA_ROOT
        if not os.path.exists(media_root):
            return {}
        
        stats = {
            'total_files': 0,
            'image_files': 0,
            'total_size': 0
        }
        
        for root, dirs, files in os.walk(media_root):
            for file in files:
                file_path = os.path.join(root, file)
                stats['total_files'] += 1
                
                try:
                    stats['total_size'] += os.path.getsize(file_path)
                    
                    # Check if it's an image
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.tiff')):
                        stats['image_files'] += 1
                except OSError:
                    pass
        
        return stats