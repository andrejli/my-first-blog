"""
Image processing utilities for EXIF metadata removal and security.

This module provides functions to safely process uploaded images by:
- Removing all EXIF metadata (GPS, device info, timestamps)
- Preserving image quality and format
- Ensuring privacy and security compliance
"""

import io
import logging
from typing import Optional, Tuple, Union
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

logger = logging.getLogger(__name__)

# Supported image formats for EXIF processing
SUPPORTED_FORMATS = {'JPEG', 'JPG', 'TIFF', 'TIF'}
# Formats that support EXIF data
EXIF_FORMATS = {'JPEG', 'TIFF'}

def has_exif_data(image: Image.Image) -> bool:
    """
    Check if an image contains EXIF metadata.
    
    Args:
        image: PIL Image object
        
    Returns:
        bool: True if image has EXIF data, False otherwise
    """
    try:
        exif = image._getexif()
        return exif is not None and len(exif) > 0
    except (AttributeError, OSError):
        return False

def get_exif_summary(image: Image.Image) -> dict:
    """
    Extract a summary of EXIF data for logging/debugging purposes.
    
    Args:
        image: PIL Image object
        
    Returns:
        dict: Summary of EXIF tags found
    """
    summary = {
        'has_exif': False,
        'gps_data': False,
        'device_info': False,
        'timestamp': False,
        'total_tags': 0
    }
    
    try:
        exif = image._getexif()
        if exif:
            summary['has_exif'] = True
            summary['total_tags'] = len(exif)
            
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                
                # Check for GPS data
                if tag in ('GPS', 'GPSInfo') or 'GPS' in str(tag):
                    summary['gps_data'] = True
                    
                # Check for device information
                if tag in ('Make', 'Model', 'Software', 'Camera'):
                    summary['device_info'] = True
                    
                # Check for timestamp data
                if tag in ('DateTime', 'DateTimeOriginal', 'DateTimeDigitized'):
                    summary['timestamp'] = True
                    
    except (AttributeError, OSError):
        pass
        
    return summary

def strip_exif_metadata(image_file: Union[InMemoryUploadedFile, TemporaryUploadedFile, ContentFile]) -> Tuple[ContentFile, dict]:
    """
    Remove EXIF metadata from an uploaded image file.
    
    Args:
        image_file: Django uploaded file object
        
    Returns:
        Tuple[ContentFile, dict]: Cleaned image file and processing summary
        
    Raises:
        ValueError: If file is not a valid image
        OSError: If image processing fails
    """
    processing_summary = {
        'original_size': 0,
        'processed_size': 0,
        'exif_removed': False,
        'format': None,
        'exif_summary': {}
    }
    
    try:
        # Get original file size
        image_file.seek(0)
        original_content = image_file.read()
        processing_summary['original_size'] = len(original_content)
        
        # Open image with PIL
        image_file.seek(0)
        with Image.open(image_file) as img:
            # Store original format
            original_format = img.format
            processing_summary['format'] = original_format
            
            # Get EXIF summary before removal
            processing_summary['exif_summary'] = get_exif_summary(img)
            
            # Convert image to RGB if necessary (removes alpha channel issues)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Convert to RGB with white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = rgb_img
            elif img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Apply orientation from EXIF if present, then remove EXIF
            img = ImageOps.exif_transpose(img)
            
            # Create new image without EXIF data
            output = io.BytesIO()
            
            # Determine save format and quality
            save_format = 'JPEG' if original_format in ('JPEG', 'JPG') else original_format
            save_kwargs = {}
            
            if save_format == 'JPEG':
                save_kwargs = {
                    'format': 'JPEG',
                    'quality': 95,  # High quality to preserve image
                    'optimize': True,
                    'progressive': True
                }
            elif save_format == 'PNG':
                save_kwargs = {
                    'format': 'PNG',
                    'optimize': True
                }
            elif save_format in ('TIFF', 'TIF'):
                save_kwargs = {
                    'format': 'TIFF',
                    'compression': 'lzw'
                }
            else:
                # For other formats, save as JPEG
                save_format = 'JPEG'
                save_kwargs = {
                    'format': 'JPEG',
                    'quality': 95,
                    'optimize': True
                }
            
            # Save image without EXIF data
            img.save(output, **save_kwargs)
            
            # Get processed size
            processed_content = output.getvalue()
            processing_summary['processed_size'] = len(processed_content)
            processing_summary['exif_removed'] = True
            
            # Create ContentFile with cleaned image
            cleaned_file = ContentFile(
                processed_content,
                name=image_file.name
            )
            
            logger.info(f"EXIF removal completed: {image_file.name}, "
                       f"Original: {processing_summary['original_size']} bytes, "
                       f"Processed: {processing_summary['processed_size']} bytes, "
                       f"EXIF tags removed: {processing_summary['exif_summary']['total_tags']}")
            
            return cleaned_file, processing_summary
            
    except Exception as e:
        logger.error(f"Failed to process image {image_file.name}: {str(e)}")
        raise ValueError(f"Invalid image file or processing failed: {str(e)}")

def is_image_file(file) -> bool:
    """
    Check if uploaded file is a valid image.
    
    Args:
        file: Django uploaded file object
        
    Returns:
        bool: True if file is a valid image
    """
    try:
        file.seek(0)
        with Image.open(file) as img:
            img.verify()
        file.seek(0)
        return True
    except Exception:
        return False

def get_image_info(image_file) -> dict:
    """
    Get basic information about an image file.
    
    Args:
        image_file: Django uploaded file object
        
    Returns:
        dict: Image information including dimensions, format, etc.
    """
    info = {
        'width': 0,
        'height': 0,
        'format': None,
        'mode': None,
        'has_exif': False,
        'file_size': 0
    }
    
    try:
        image_file.seek(0)
        info['file_size'] = len(image_file.read())
        
        image_file.seek(0)
        with Image.open(image_file) as img:
            info['width'] = img.width
            info['height'] = img.height
            info['format'] = img.format
            info['mode'] = img.mode
            info['has_exif'] = has_exif_data(img)
            
    except Exception as e:
        logger.warning(f"Could not get image info for {image_file.name}: {str(e)}")
    
    return info

def process_uploaded_image(image_file, strip_exif: bool = True) -> Tuple[ContentFile, dict]:
    """
    Main function to process uploaded images with optional EXIF removal.
    
    Args:
        image_file: Django uploaded file object
        strip_exif: Whether to remove EXIF data (default: True)
        
    Returns:
        Tuple[ContentFile, dict]: Processed image file and processing info
        
    Raises:
        ValueError: If file is not a valid image
    """
    # Validate image file
    if not is_image_file(image_file):
        raise ValueError("File is not a valid image")
    
    # Get basic image info
    image_info = get_image_info(image_file)
    
    processing_info = {
        'original_info': image_info,
        'processing_applied': False,
        'exif_removed': False,
        'summary': {}
    }
    
    if strip_exif:
        try:
            processed_file, summary = strip_exif_metadata(image_file)
            processing_info['processing_applied'] = True
            processing_info['exif_removed'] = summary['exif_removed']
            processing_info['summary'] = summary
            return processed_file, processing_info
        except Exception as e:
            logger.error(f"EXIF removal failed for {image_file.name}: {str(e)}")
            # Fall back to original file if processing fails
            image_file.seek(0)
            return ContentFile(image_file.read(), name=image_file.name), processing_info
    else:
        # Return original file without processing
        image_file.seek(0)
        return ContentFile(image_file.read(), name=image_file.name), processing_info