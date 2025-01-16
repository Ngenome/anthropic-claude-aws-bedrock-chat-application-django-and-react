from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from PIL import Image
import magic
import os

def validate_image_size(image):
    if image.size > 3.75 * 1024 * 1024:  # 3.75MB
        raise ValidationError('Image size cannot exceed 3.75MB')
    
    img = Image.open(image)
    if img.height > 8000 or img.width > 8000:
        raise ValidationError('Image dimensions cannot exceed 8000x8000 pixels')

def validate_document_size(document):
    if document.size > 4.5 * 1024 * 1024:  # 4.5MB
        raise ValidationError('Document size cannot exceed 4.5MB')

def validate_mime_type(upload):
    valid_mime_types = {
        'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
        'document': ['application/pdf', 'text/plain', 'text/markdown',
                    'application/msword', 
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    }
    
    mime_type = magic.from_buffer(upload.read(1024), mime=True)
    upload.seek(0)  # Reset file pointer
    
    if not any(mime_type in types for types in valid_mime_types.values()):
        raise ValidationError(f'Unsupported file type: {mime_type}')
    
    return mime_type