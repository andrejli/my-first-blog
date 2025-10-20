"""
File upload validators for secure handling of educational materials
including source code files (Python, Go, Rust, etc.)
"""

import os
import zipfile
import re
from django.core.exceptions import ValidationError
from django.conf import settings

# SAFE: Educational and source code files
ALLOWED_ASSIGNMENT_EXTENSIONS = {
    # Documents & Text
    '.pdf', '.txt', '.md', '.rtf', '.doc', '.docx',
    
    # Source Code - High Educational Value
    '.py',      # Python
    '.go',      # Go
    '.rs',      # Rust  
    '.js',      # JavaScript
    '.ts',      # TypeScript
    '.java',    # Java
    '.cpp', '.c', '.h', '.hpp',  # C/C++
    '.cs',      # C#
    '.rb',      # Ruby
    '.php',     # PHP (source code only, not executable)
    '.swift',   # Swift
    '.kt',      # Kotlin
    '.scala',   # Scala
    '.clj',     # Clojure
    '.hs',      # Haskell
    '.ml',      # OCaml
    '.r',       # R
    '.m',       # MATLAB/Objective-C
    
    # Web Development
    '.html', '.css', '.scss', '.sass', '.less',
    '.vue', '.jsx', '.tsx',
    
    # Configuration & Data
    '.json', '.xml', '.yaml', '.yml', '.toml', '.ini',
    '.sql', '.csv', '.tsv',
    '.env', '.gitignore', '.dockerignore',
    
    # Build & Config Files
    '.makefile', '.cmake', '.gradle', '.sbt',
    '.package.json', '.composer.json', '.requirements.txt',
    '.cargo.toml', '.go.mod', '.pom.xml',
    
    # Documentation
    '.readme', '.license', '.changelog',
    
    # Data Files
    '.xlsx', '.ods',
    
    # Images (for documentation/UI)
    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp',
    
    # Archives (with content validation)
    '.zip', '.tar', '.gz', '.tar.gz', '.tgz',
    
    # Notebooks
    '.ipynb',   # Jupyter notebooks
}

# DANGEROUS: Block executable and server-side files
BLOCKED_EXTENSIONS = {
    # Windows Executables
    '.exe', '.bat', '.cmd', '.com', '.scr', '.msi', '.dll',
    '.pif', '.application', '.gadget', '.msp', '.mst',
    
    # Unix/Linux Executables & Scripts
    '.sh', '.bash', '.zsh', '.fish', '.csh', '.tcsh',
    '.bin', '.run', '.app', '.deb', '.rpm', '.pkg',
    
    # PowerShell
    '.ps1', '.ps1xml', '.psm1', '.psd1', '.pssc', '.psrc',
    
    # Server-side scripts (when executed)
    '.asp', '.aspx', '.jsp', '.cfm', '.cgi', '.pl',
    
    # Macro-enabled documents
    '.docm', '.xlsm', '.pptm',
    
    # Script files
    '.vbs', '.vbe', '.jse', '.wsf', '.wsh',
    
    # Java executables
    '.jar', '.war', '.ear',
}

# MIME type mapping for validation
EXPECTED_MIME_TYPES = {
    '.pdf': ['application/pdf'],
    '.txt': ['text/plain'],
    '.md': ['text/plain', 'text/markdown'],
    '.py': ['text/plain', 'text/x-python', 'application/x-python-code'],
    '.go': ['text/plain'],
    '.rs': ['text/plain'],
    '.js': ['text/plain', 'application/javascript', 'text/javascript'],
    '.ts': ['text/plain'],
    '.java': ['text/plain', 'text/x-java-source'],
    '.cpp': ['text/plain', 'text/x-c++src'],
    '.c': ['text/plain', 'text/x-csrc'],
    '.h': ['text/plain', 'text/x-chdr'],
    '.html': ['text/html'],
    '.css': ['text/css'],
    '.json': ['application/json', 'text/json'],
    '.xml': ['application/xml', 'text/xml'],
    '.yaml': ['text/plain', 'application/x-yaml'],
    '.yml': ['text/plain', 'application/x-yaml'],
    '.sql': ['text/plain', 'application/sql'],
    '.zip': ['application/zip'],
    '.tar': ['application/x-tar'],
    '.gz': ['application/gzip'],
    '.jpg': ['image/jpeg'],
    '.jpeg': ['image/jpeg'],
    '.png': ['image/png'],
    '.gif': ['image/gif'],
    '.svg': ['image/svg+xml'],
    '.csv': ['text/csv'],
    '.xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    '.doc': ['application/msword'],
    '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    '.ipynb': ['application/json', 'text/plain'],
}

def validate_assignment_file(file):
    """
    Comprehensive file validation for assignment submissions.
    Allows educational source code while blocking dangerous executables.
    """
    
    # 1. Basic file checks
    if not file:
        raise ValidationError('No file provided')
    
    if not file.name:
        raise ValidationError('File must have a name')
    
    # 2. Extension validation
    ext = os.path.splitext(file.name)[1].lower()
    
    if not ext:
        raise ValidationError('File must have an extension')
    
    if ext in BLOCKED_EXTENSIONS:
        raise ValidationError(
            f'File type {ext} is blocked for security reasons. '
            f'This file type can contain executable code that could harm the system.'
        )
    
    if ext not in ALLOWED_ASSIGNMENT_EXTENSIONS:
        allowed_list = ', '.join(sorted(list(ALLOWED_ASSIGNMENT_EXTENSIONS)[:20])) + '...'
        raise ValidationError(
            f'File type {ext} is not allowed for assignments. '
            f'Allowed types include: {allowed_list}'
        )
    
    # 3. Filename security checks
    filename = os.path.basename(file.name)
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        raise ValidationError('Invalid filename: path traversal attempts detected')
    
    # Check for suspicious filenames
    if filename.startswith('.') and ext not in ['.gitignore', '.env', '.dockerignore']:
        raise ValidationError('Hidden files not allowed unless they are standard config files')
    
    # Length check
    if len(filename) > 255:
        raise ValidationError('Filename too long (max 255 characters)')
    
    # Character validation
    if not re.match(r'^[a-zA-Z0-9._\-\s()\[\]]+$', filename):
        raise ValidationError('Filename contains invalid characters. Use only letters, numbers, spaces, and: . _ - ( ) [ ]')
    
    # 4. File size validation
    max_size = getattr(settings, 'MAX_ASSIGNMENT_FILE_SIZE', 50 * 1024 * 1024)  # 50MB default
    if file.size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise ValidationError(f'File too large. Maximum size: {max_mb:.0f}MB')
    
    # Minimum size check (empty files)
    if file.size == 0:
        raise ValidationError('Empty files are not allowed')
    
    # 5. MIME type validation (if python-magic is available)
    try:
        import magic
        file.seek(0)
        file_content = file.read(2048)  # Read first 2KB for detection
        file.seek(0)  # Reset file pointer
        
        detected_mime = magic.from_buffer(file_content, mime=True)
        
        if ext in EXPECTED_MIME_TYPES:
            expected_mimes = EXPECTED_MIME_TYPES[ext]
            if detected_mime not in expected_mimes:
                # Some tolerance for text files
                if 'text/' in detected_mime and any('text/' in mime for mime in expected_mimes):
                    pass  # Allow text variations
                else:
                    raise ValidationError(
                        f'File content does not match extension {ext}. '
                        f'Expected: {", ".join(expected_mimes)}, '
                        f'Detected: {detected_mime}'
                    )
    except ImportError:
        # python-magic not installed, skip MIME validation
        # Install with: pip install python-magic
        # On Windows: pip install python-magic-bin
        pass
    except Exception:
        # MIME detection failed, continue without it
        pass
    
    # 6. Archive-specific validation
    if ext in ['.zip', '.tar', '.gz', '.tar.gz', '.tgz']:
        validate_archive_content(file, ext)
    
    # 7. Source code specific validation
    if ext in ['.py', '.js', '.php', '.sh', '.bat', '.ps1']:
        validate_source_code_content(file, ext)

def validate_archive_content(file, ext):
    """
    Validate archive contents for security threats.
    Prevents zip bombs, path traversal, and nested executables.
    """
    
    MAX_FILES_IN_ARCHIVE = 1000
    MAX_UNCOMPRESSED_SIZE = 500 * 1024 * 1024  # 500MB
    MAX_INDIVIDUAL_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    try:
        file.seek(0)
        
        if ext == '.zip':
            with zipfile.ZipFile(file, 'r') as zf:
                # Check number of files
                if len(zf.namelist()) > MAX_FILES_IN_ARCHIVE:
                    raise ValidationError(f'Archive contains too many files (max {MAX_FILES_IN_ARCHIVE})')
                
                total_uncompressed = 0
                
                for info in zf.infolist():
                    # Check individual file size
                    if info.file_size > MAX_INDIVIDUAL_FILE_SIZE:
                        max_mb = MAX_INDIVIDUAL_FILE_SIZE / (1024 * 1024)
                        raise ValidationError(f'Archive contains file too large: {info.filename} ({max_mb:.0f}MB max)')
                    
                    # Check total uncompressed size
                    total_uncompressed += info.file_size
                    if total_uncompressed > MAX_UNCOMPRESSED_SIZE:
                        max_mb = MAX_UNCOMPRESSED_SIZE / (1024 * 1024)
                        raise ValidationError(f'Archive uncompressed size too large (max {max_mb:.0f}MB)')
                    
                    # Check for path traversal
                    if '..' in info.filename or info.filename.startswith('/') or ':' in info.filename:
                        raise ValidationError(f'Archive contains unsafe file path: {info.filename}')
                    
                    # Check for dangerous file types inside archive
                    inner_ext = os.path.splitext(info.filename)[1].lower()
                    if inner_ext in BLOCKED_EXTENSIONS:
                        raise ValidationError(f'Archive contains blocked file type: {info.filename} ({inner_ext})')
                    
                    # Compression ratio check (zip bomb detection)
                    if info.file_size > 0 and info.compress_size > 0:
                        ratio = info.file_size / info.compress_size
                        if ratio > 100:  # Highly compressed
                            raise ValidationError(f'Suspicious compression ratio in file: {info.filename}')
        
        # Reset file pointer
        file.seek(0)
        
    except zipfile.BadZipFile:
        raise ValidationError('Invalid or corrupted archive file')
    except Exception as e:
        raise ValidationError(f'Error reading archive: {str(e)}')

def validate_source_code_content(file, ext):
    """
    Basic validation of source code files for obviously malicious content.
    This is not a complete security scan but catches obvious threats.
    """
    
    # Only scan text-based source files
    if ext not in ['.py', '.js', '.php', '.sh', '.bat', '.ps1']:
        return
    
    try:
        file.seek(0)
        # Read first 10KB for analysis
        content = file.read(10 * 1024).decode('utf-8', errors='ignore')
        file.seek(0)
        
        # Convert to lowercase for case-insensitive matching
        content_lower = content.lower()
        
        # Suspicious patterns that might indicate malicious code
        suspicious_patterns = [
            # Network operations that might be suspicious in student assignments
            'urllib.request.urlopen',
            'requests.get',
            'socket.connect',
            'subprocess.popen',
            'os.system',
            'exec(',
            'eval(',
            
            # File system operations that might be suspicious
            'os.remove',
            'os.rmdir',
            'shutil.rmtree',
            'os.chmod',
            
            # Windows specific
            'rundll32',
            'regsvr32',
            'powershell',
            
            # Unix/Linux specific
            'rm -rf',
            'chmod +x',
            '/bin/bash',
            
            # Common malware indicators
            'base64.b64decode',
            'zlib.decompress',
            '__import__',
        ]
        
        found_suspicious = []
        for pattern in suspicious_patterns:
            if pattern in content_lower:
                found_suspicious.append(pattern)
        
        # If multiple suspicious patterns found, flag for review
        if len(found_suspicious) >= 3:
            raise ValidationError(
                f'Source code contains multiple suspicious patterns that require instructor review: '
                f'{", ".join(found_suspicious[:5])}'
            )
        
        # Check for very long lines (might indicate obfuscated code)
        lines = content.split('\n')
        for i, line in enumerate(lines[:100]):  # Check first 100 lines
            if len(line) > 1000:  # Very long line
                raise ValidationError(f'Source code contains suspiciously long line at line {i+1} (possible obfuscation)')
        
    except UnicodeDecodeError:
        # File is not text, which is suspicious for source code
        raise ValidationError(f'Source code file {ext} is not readable as text')
    except Exception:
        # If we can't read the file for analysis, allow it through
        # Don't block legitimate files due to analysis errors
        pass

def get_file_info(file):
    """
    Get safe information about an uploaded file for logging.
    """
    if not file:
        return None
        
    return {
        'filename': os.path.basename(file.name),
        'size': file.size,
        'extension': os.path.splitext(file.name)[1].lower(),
        'content_type': getattr(file, 'content_type', 'unknown'),
    }