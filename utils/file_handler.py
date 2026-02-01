import os
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid

class FileHandler:
    """Handle file uploads and validation"""
    
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in FileHandler.ALLOWED_EXTENSIONS
    
    @staticmethod
    def get_file_extension(filename):
        """Get file extension"""
        if '.' in filename:
            return filename.rsplit('.', 1)[1].lower()
        return None
    
    @staticmethod
    def generate_unique_filename(original_filename):
        """Generate unique filename to prevent conflicts"""
        ext = FileHandler.get_file_extension(original_filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return f"{timestamp}_{unique_id}.{ext}"
    
    @staticmethod
    def validate_file_size(file):
        """Check if file size is within limits"""
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        return file_size <= FileHandler.MAX_FILE_SIZE
    
    @staticmethod
    def get_file_size_mb(file):
        """Get file size in MB"""
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        return round(file_size / (1024 * 1024), 2)
    
    @staticmethod
    def save_file(file, upload_folder):
        """Save file and return file info"""
        if not file:
            return None, "No file provided"
        
        if file.filename == '':
            return None, "No file selected"
        
        if not FileHandler.allowed_file(file.filename):
            return None, f"File type not allowed. Allowed types: {', '.join(FileHandler.ALLOWED_EXTENSIONS)}"
        
        if not FileHandler.validate_file_size(file):
            return None, f"File too large. Maximum size: {FileHandler.MAX_FILE_SIZE / (1024*1024)}MB"
        
        try:
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            unique_filename = FileHandler.generate_unique_filename(original_filename)
            
            # Create upload folder if not exists
            os.makedirs(upload_folder, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            
            # Get file info
            file_size = FileHandler.get_file_size_mb(file)
            
            return {
                'original_filename': original_filename,
                'saved_filename': unique_filename,
                'file_path': file_path,
                'file_size': file_size,
                'file_extension': FileHandler.get_file_extension(original_filename)
            }, None
            
        except Exception as e:
            return None, f"Error saving file: {str(e)}"
    
    @staticmethod
    def delete_file(file_path):
        """Delete a file from disk"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True, "File deleted successfully"
            return False, "File not found"
        except Exception as e:
            return False, f"Error deleting file: {str(e)}"
    
    @staticmethod
    def get_file_type(filename):
        """Determine document type based on filename"""
        filename_lower = filename.lower()
        
        if 'invoice' in filename_lower:
            return 'invoice'
        elif 'receipt' in filename_lower:
            return 'receipt'
        elif 'statement' in filename_lower or 'bank' in filename_lower:
            return 'statement'
        elif 'bill' in filename_lower:
            return 'invoice'
        else:
            return 'other'