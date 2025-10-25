"""
Blog utilities package.

This package contains utility modules for:
- Image processing and EXIF metadata removal
- Custom storage backends for enhanced security
- File validation and security functions
"""

from .image_processing import (
    strip_exif_metadata,
    process_uploaded_image,
    is_image_file,
    get_image_info,
    has_exif_data
)

from .storage import (
    SecureImageStorage,
    MediaStorage,
    LegacyImageStorage,
    get_secure_storage
)

__all__ = [
    'strip_exif_metadata',
    'process_uploaded_image', 
    'is_image_file',
    'get_image_info',
    'has_exif_data',
    'SecureImageStorage',
    'MediaStorage',
    'LegacyImageStorage',
    'get_secure_storage'
]