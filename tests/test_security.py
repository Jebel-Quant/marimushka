"""Tests for the security module."""

import pytest

from marimushka.security import (
    safe_open_file,
    sanitize_error_message,
    set_secure_file_permissions,
    validate_bin_path,
    validate_file_path,
    validate_file_size,
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

    def test_validate_path_traversal_no_base_dir(self, tmp_path):
        """Test validation without base directory constraint."""
        # Setup
        test_path = tmp_path / "test.py"

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
        with pytest.raises(ValueError, match=r"File extension \.txt not allowed"):
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
        with pytest.raises(TypeError, match="max_workers must be an integer"):
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
        with pytest.raises(ValueError, match=r"max_allowed .* must be >= min_workers"):
            validate_max_workers(4, min_workers=10, max_allowed=5)

        with pytest.raises(ValueError, match="min_workers must be at least 1"):
            validate_max_workers(4, min_workers=0, max_allowed=10)


class TestValidateFileSize:
    """Tests for validate_file_size function."""

    def test_validate_file_size_within_limit(self, tmp_path):
        """Test validation of file within size limit."""
        # Setup
        test_file = tmp_path / "test.txt"
        test_file.write_text("small content")

        # Execute
        result = validate_file_size(test_file, max_size_bytes=1024)

        # Assert
        assert result is True

    def test_validate_file_size_exceeds_limit(self, tmp_path):
        """Test validation fails for file exceeding limit."""
        # Setup
        test_file = tmp_path / "large.txt"
        test_file.write_text("x" * 2000)

        # Execute & Assert
        with pytest.raises(ValueError, match=r"File size .* exceeds limit"):
            validate_file_size(test_file, max_size_bytes=1000)

    def test_validate_file_size_not_exists(self, tmp_path):
        """Test validation fails for non-existent file."""
        # Setup
        test_file = tmp_path / "nonexistent.txt"

        # Execute & Assert
        with pytest.raises(ValueError, match="File does not exist"):
            validate_file_size(test_file)


class TestSafeOpenFile:
    """Tests for safe_open_file function."""

    def test_safe_open_file_write(self, tmp_path):
        """Test safe file opening for writing."""
        # Setup
        test_file = tmp_path / "test.txt"

        # Execute
        import os

        fd = safe_open_file(test_file, "w")
        with os.fdopen(fd, "w") as f:
            f.write("test content")

        # Assert
        assert test_file.read_text() == "test content"

    def test_safe_open_file_read(self, tmp_path):
        """Test safe file opening for reading."""
        # Setup
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Execute
        import os

        fd = safe_open_file(test_file, "r")
        with os.fdopen(fd, "r") as f:
            content = f.read()

        # Assert
        assert content == "test content"

    def test_safe_open_file_symlink_rejected(self, tmp_path):
        """Test that symlinks are rejected."""
        # Setup
        real_file = tmp_path / "real.txt"
        real_file.write_text("content")
        symlink = tmp_path / "link.txt"
        symlink.symlink_to(real_file)

        # Execute & Assert
        with pytest.raises(ValueError, match="Cannot open symlink"):
            safe_open_file(symlink, "r")


class TestSetSecureFilePermissions:
    """Tests for set_secure_file_permissions function."""

    def test_set_secure_file_permissions(self, tmp_path):
        """Test setting file permissions."""
        # Setup
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        # Execute
        set_secure_file_permissions(test_file, mode=0o600)

        # Assert
        import os
        import stat

        st = os.stat(test_file)
        assert stat.S_IMODE(st.st_mode) == 0o600

    def test_set_secure_file_permissions_not_exists(self, tmp_path):
        """Test setting permissions on non-existent file fails."""
        # Setup
        test_file = tmp_path / "nonexistent.txt"

        # Execute & Assert
        with pytest.raises(ValueError, match="File does not exist"):
            set_secure_file_permissions(test_file)
