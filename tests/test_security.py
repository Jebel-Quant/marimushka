"""Tests for the security module."""

import tempfile
from pathlib import Path

import pytest

from marimushka.security import (
    sanitize_error_message,
    validate_bin_path,
    validate_file_path,
    validate_max_workers,
    validate_path_traversal,
)


class TestValidatePathTraversal:
    """Tests for validate_path_traversal function."""

    def test_validate_path_traversal_safe_path(self, tmp_path):
        """Test validation of a safe path."""
        # Setup
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        safe_path = base_dir / "notebooks" / "test.py"

        # Execute
        result = validate_path_traversal(safe_path, base_dir)

        # Assert - should resolve without error
        assert result.is_absolute()

    def test_validate_path_traversal_escapes_base(self, tmp_path):
        """Test that path traversal attempts are detected."""
        # Setup
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        escape_path = base_dir / ".." / ".." / "etc" / "passwd"

        # Execute & Assert
        with pytest.raises(ValueError, match="Path traversal detected"):
            validate_path_traversal(escape_path, base_dir)

    def test_validate_path_traversal_no_base_dir(self):
        """Test validation without base directory constraint."""
        # Setup
        test_path = Path("/tmp/test.py")

        # Execute
        result = validate_path_traversal(test_path)

        # Assert - should resolve to absolute path
        assert result.is_absolute()

    def test_validate_path_traversal_symlink_escape(self, tmp_path):
        """Test that symlink-based path traversal is detected."""
        # Setup
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()

        # Create a symlink inside base_dir that points outside
        symlink = base_dir / "escape_link"
        symlink.symlink_to(outside_dir)

        # Execute & Assert
        with pytest.raises(ValueError, match="Path traversal detected"):
            validate_path_traversal(symlink / "file.txt", base_dir)


class TestValidateBinPath:
    """Tests for validate_bin_path function."""

    def test_validate_bin_path_success(self, tmp_path):
        """Test validation of a valid bin path."""
        # Setup
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        # Execute
        result = validate_bin_path(bin_dir)

        # Assert
        assert result.is_absolute()
        assert result.is_dir()

    def test_validate_bin_path_not_exists(self, tmp_path):
        """Test validation fails for non-existent path."""
        # Setup
        bin_dir = tmp_path / "nonexistent"

        # Execute & Assert
        with pytest.raises(ValueError, match="Binary path does not exist"):
            validate_bin_path(bin_dir)

    def test_validate_bin_path_not_directory(self, tmp_path):
        """Test validation fails for file instead of directory."""
        # Setup
        bin_file = tmp_path / "not_a_dir.txt"
        bin_file.write_text("test")

        # Execute & Assert
        with pytest.raises(ValueError, match="Binary path is not a directory"):
            validate_bin_path(bin_file)

    def test_validate_bin_path_whitelist_success(self, tmp_path):
        """Test validation with whitelist acceptance."""
        # Setup
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        whitelist = [bin_dir, tmp_path / "other"]

        # Execute
        result = validate_bin_path(bin_dir, whitelist=whitelist)

        # Assert
        assert result == bin_dir.resolve()

    def test_validate_bin_path_whitelist_rejection(self, tmp_path):
        """Test validation with whitelist rejection."""
        # Setup
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        whitelist = [other_dir]

        # Execute & Assert
        with pytest.raises(ValueError, match="Binary path not in whitelist"):
            validate_bin_path(bin_dir, whitelist=whitelist)


class TestValidateFilePath:
    """Tests for validate_file_path function."""

    def test_validate_file_path_success(self, tmp_path):
        """Test validation of a valid file path."""
        # Setup
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        # Execute
        result = validate_file_path(test_file, allowed_extensions=[".py"])

        # Assert
        assert result == test_file

    def test_validate_file_path_not_exists(self, tmp_path):
        """Test validation fails for non-existent file."""
        # Setup
        test_file = tmp_path / "nonexistent.py"

        # Execute & Assert
        with pytest.raises(ValueError, match="File does not exist"):
            validate_file_path(test_file)

    def test_validate_file_path_not_file(self, tmp_path):
        """Test validation fails for directory instead of file."""
        # Setup
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        # Execute & Assert
        with pytest.raises(ValueError, match="Path is not a file"):
            validate_file_path(test_dir)

    def test_validate_file_path_wrong_extension(self, tmp_path):
        """Test validation fails for disallowed extension."""
        # Setup
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Execute & Assert
        with pytest.raises(ValueError, match="File extension .txt not allowed"):
            validate_file_path(test_file, allowed_extensions=[".py", ".html"])

    def test_validate_file_path_no_extension_check(self, tmp_path):
        """Test validation without extension checking."""
        # Setup
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Execute
        result = validate_file_path(test_file)

        # Assert
        assert result == test_file


class TestSanitizeErrorMessage:
    """Tests for sanitize_error_message function."""

    def test_sanitize_unix_path(self):
        """Test sanitization of Unix absolute paths."""
        # Setup
        error_msg = "Error in /home/user/secret/notebook.py"

        # Execute
        result = sanitize_error_message(error_msg)

        # Assert
        assert "/home/user/secret" not in result
        assert "notebook.py" in result
        assert "<redacted_path>" in result

    def test_sanitize_windows_path(self):
        """Test sanitization of Windows absolute paths."""
        # Setup
        error_msg = "Error in C:\\Users\\user\\secret\\notebook.py"

        # Execute
        result = sanitize_error_message(error_msg)

        # Assert
        assert "C:\\Users\\user\\secret" not in result
        assert "notebook.py" in result
        assert "<redacted_path>" in result

    def test_sanitize_custom_patterns(self):
        """Test sanitization with custom patterns."""
        # Setup
        error_msg = "API key: secret123, User: admin"
        sensitive_patterns = ["secret123", "admin"]

        # Execute
        result = sanitize_error_message(error_msg, sensitive_patterns=sensitive_patterns)

        # Assert
        assert "secret123" not in result
        assert "admin" not in result
        assert "<redacted>" in result

    def test_sanitize_no_sensitive_data(self):
        """Test sanitization of message without sensitive data."""
        # Setup
        error_msg = "Simple error message"

        # Execute
        result = sanitize_error_message(error_msg)

        # Assert
        assert result == error_msg


class TestValidateMaxWorkers:
    """Tests for validate_max_workers function."""

    def test_validate_max_workers_within_bounds(self):
        """Test validation of worker count within bounds."""
        # Execute
        result = validate_max_workers(4)

        # Assert
        assert result == 4

    def test_validate_max_workers_below_minimum(self):
        """Test validation clamps to minimum."""
        # Execute
        result = validate_max_workers(0)

        # Assert
        assert result == 1

    def test_validate_max_workers_above_maximum(self):
        """Test validation clamps to maximum."""
        # Execute
        result = validate_max_workers(100)

        # Assert
        assert result == 16

    def test_validate_max_workers_negative(self):
        """Test validation clamps negative values."""
        # Execute
        result = validate_max_workers(-5)

        # Assert
        assert result == 1

    def test_validate_max_workers_not_integer(self):
        """Test validation fails for non-integer."""
        # Execute & Assert
        with pytest.raises(ValueError, match="max_workers must be an integer"):
            validate_max_workers(4.5)

    def test_validate_max_workers_custom_bounds(self):
        """Test validation with custom bounds."""
        # Execute
        result = validate_max_workers(10, min_workers=2, max_allowed=8)

        # Assert
        assert result == 8

    def test_validate_max_workers_invalid_constraints(self):
        """Test validation fails for invalid constraints."""
        # Execute & Assert
        with pytest.raises(ValueError, match="max_allowed .* must be >= min_workers"):
            validate_max_workers(4, min_workers=10, max_allowed=5)

        with pytest.raises(ValueError, match="min_workers must be at least 1"):
            validate_max_workers(4, min_workers=0, max_allowed=10)
