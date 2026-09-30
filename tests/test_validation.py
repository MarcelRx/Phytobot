"""
Tests for input validation module.
"""
import pytest
from io import BytesIO
from PIL import Image
from src.validation import validate_text_input, validate_image_file
from src.config import VisionConfig, TextConfig


class TestTextInputValidation:
    """Test text input validation."""
    
    def test_empty_text(self):
        """Test that empty text is rejected."""
        is_valid, error = validate_text_input("")
        assert not is_valid
        assert error is not None
    
    def test_whitespace_only_text(self):
        """Test that whitespace-only text is rejected."""
        is_valid, error = validate_text_input("   ")
        assert not is_valid
        assert error is not None
    
    def test_valid_text(self):
        """Test that valid text is accepted."""
        is_valid, error = validate_text_input("What herbs help with sleep?")
        assert is_valid
        assert error is None
    
    def test_text_too_long(self):
        """Test that text exceeding max length is rejected."""
        long_text = "a" * (TextConfig.MAX_QUERY_LENGTH + 1)
        is_valid, error = validate_text_input(long_text)
        assert not is_valid
        assert error is not None
    
    def test_text_at_max_length(self):
        """Test that text at max length is accepted."""
        max_text = "a" * TextConfig.MAX_QUERY_LENGTH
        is_valid, error = validate_text_input(max_text)
        assert is_valid
        assert error is None
    
    def test_text_normalization(self):
        """Test that text with extra whitespace is normalized."""
        # This test checks that the function doesn't crash on weird whitespace
        is_valid, error = validate_text_input("  Hello   world  ")
        assert is_valid
        assert error is None


class TestImageValidation:
    """Test image file validation."""
    
    def create_mock_upload(self, format='JPEG', size=(100, 100), file_size_mb=1):
        """Create a mock uploaded file object."""
        img = Image.new('RGB', size, color='red')
        buffer = BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)
        
        class MockUpload:
            def __init__(self, buffer, filename, size):
                self.buffer = buffer
                self.name = filename
                self.size = size
            
            def getbuffer(self):
                return self.buffer.getvalue()
            
            def getvalue(self):
                return self.buffer.getvalue()
        
        return MockUpload(buffer, f"test.{format.lower()}", file_size_mb * 1024 * 1024)
    
    def test_none_file(self):
        """Test that None file is rejected."""
        is_valid, error = validate_image_file(None)
        assert not is_valid
        assert error is not None
    
    def test_valid_jpeg(self):
        """Test that valid JPEG is accepted."""
        mock_file = self.create_mock_upload(format='JPEG', file_size_mb=1)
        is_valid, error = validate_image_file(mock_file)
        assert is_valid
        assert error is None
    
    def test_valid_png(self):
        """Test that valid PNG is accepted."""
        mock_file = self.create_mock_upload(format='PNG', file_size_mb=1)
        is_valid, error = validate_image_file(mock_file)
        assert is_valid
        assert error is None
    
    def test_file_too_large(self):
        """Test that file exceeding max size is rejected."""
        mock_file = self.create_mock_upload(format='JPEG', file_size_mb=VisionConfig.MAX_IMAGE_SIZE_MB + 1)
        is_valid, error = validate_image_file(mock_file)
        assert not is_valid
        assert error is not None
    
    def test_unsupported_extension(self):
        """Test that unsupported file extension is rejected."""
        mock_file = self.create_mock_upload(format='JPEG', file_size_mb=1)
        mock_file.name = "test.gif"  # Change extension to unsupported
        is_valid, error = validate_image_file(mock_file)
        assert not is_valid
        assert error is not None
    
    def test_corrupted_image(self):
        """Test that corrupted image data is rejected."""
        class CorruptedUpload:
            def __init__(self):
                self.name = "test.jpg"
                self.size = 1000
            
            def getvalue(self):
                return b"not a valid image"
        
        corrupted = CorruptedUpload()
        is_valid, error = validate_image_file(corrupted)
        assert not is_valid
        assert error is not None
