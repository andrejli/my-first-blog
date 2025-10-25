"""
Custom Django storage backend with automatic EXIF metadata removal.

This storage class extends Django's default file storage to automatically
process uploaded images and remove EXIF metadata for privacy and security.
"""

import logging
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.conf import settings
from .image_processing import process_uploaded_image, is_image_file

logger = logging.getLogger(__name__)

class SecureImageStorage(FileSystemStorage):
    """
    Custom storage class that automatically removes EXIF metadata from uploaded images.
    
    This storage backend:
    - Automatically detects image files
    - Strips EXIF metadata (GPS, device info, timestamps)
    - Preserves image quality and format
    - Logs processing activities
    - Falls back gracefully if processing fails
    """
    
    def __init__(self, location=None, base_url=None, strip_exif=True, log_processing=True):
        """
        Initialize secure image storage.
        
        Args:
            location: Storage location (defaults to MEDIA_ROOT)
            base_url: Base URL for files (defaults to MEDIA_URL)
            strip_exif: Whether to remove EXIF data (default: True)
            log_processing: Whether to log processing activities (default: True)
        """
        super().__init__(location, base_url)
        self.strip_exif = strip_exif
        self.log_processing = log_processing
        
    def _save(self, name, content):
        """
        Save file with automatic EXIF removal for images.
        
        Args:
            name: File name
            content: File content
            
        Returns:
            str: Saved file name
        """
        # Check if this is an image file that needs processing
        if self.strip_exif and is_image_file(content):
            try:
                # Process image to remove EXIF data
                processed_content, processing_info = process_uploaded_image(
                    content, 
                    strip_exif=True
                )
                
                if self.log_processing:
                    exif_summary = processing_info.get('summary', {}).get('exif_summary', {})
                    if exif_summary.get('has_exif', False):
                        logger.info(
                            f"EXIF data removed from {name}: "
                            f"GPS={exif_summary.get('gps_data', False)}, "
                            f"Device={exif_summary.get('device_info', False)}, "
                            f"Timestamp={exif_summary.get('timestamp', False)}, "
                            f"Total tags={exif_summary.get('total_tags', 0)}"
                        )
                    else:
                        logger.debug(f"No EXIF data found in {name}")
                
                # Save the processed image
                return super()._save(name, processed_content)
                
            except Exception as e:
                logger.warning(f"Failed to process image {name}: {str(e)}. Saving original file.")
                # Fall back to saving original file if processing fails
                return super()._save(name, content)
        else:
            # Save non-image files or when EXIF stripping is disabled
            return super()._save(name, content)
    
    def get_processing_stats(self):
        """
        Get statistics about image processing (placeholder for future implementation).
        
        Returns:
            dict: Processing statistics
        """
        # This could be extended to track processing statistics
        return {
            'strip_exif_enabled': self.strip_exif,
            'log_processing_enabled': self.log_processing
        }

class MediaStorage(SecureImageStorage):
    """
    Default media storage with EXIF removal enabled.
    
    This is a convenience class that can be used directly in Django settings
    or model field storage parameters.
    """
    
    def __init__(self):
        super().__init__(
            location=getattr(settings, 'MEDIA_ROOT', None),
            base_url=getattr(settings, 'MEDIA_URL', None),
            strip_exif=True,
            log_processing=True
        )

class LegacyImageStorage(FileSystemStorage):
    """
    Storage class that preserves original image files without EXIF removal.
    
    This can be used for cases where original image metadata needs to be preserved,
    such as for administrative or archival purposes.
    """
    
    def __init__(self):
        super().__init__(
            location=getattr(settings, 'MEDIA_ROOT', None),
            base_url=getattr(settings, 'MEDIA_URL', None)
        )

# Factory function to create storage instances
def get_secure_storage(strip_exif=True, log_processing=True):
    """
    Factory function to create secure storage instances.
    
    Args:
        strip_exif: Whether to remove EXIF data
        log_processing: Whether to log processing activities
        
    Returns:
        SecureImageStorage: Configured storage instance
    """
    return SecureImageStorage(
        strip_exif=strip_exif,
        log_processing=log_processing
    )