"""Tests for the audit module."""

import json
from pathlib import Path

from marimushka.audit import AuditLogger, get_audit_logger, init_audit_logger


class TestAuditLogger:
    """Tests for AuditLogger class."""

    def test_audit_logger_initialization(self):
        """Test audit logger initialization."""
        # Execute
        logger = AuditLogger(enabled=True)

        # Assert
        assert logger.enabled is True
        assert logger.log_file is None

    def test_audit_logger_with_file(self, tmp_path):
        """Test audit logger with file output."""
        # Setup
        log_file = tmp_path / "audit.log"

        # Execute
        logger = AuditLogger(enabled=True, log_file=log_file)

        # Assert
        assert logger.enabled is True
        assert logger.log_file == log_file

    def test_log_path_validation(self, tmp_path):
        """Test logging path validation events."""
        # Setup
        log_file = tmp_path / "audit.log"
        logger = AuditLogger(enabled=True, log_file=log_file)
        test_path = Path("/test/path")

        # Execute
        logger.log_path_validation(test_path, "traversal", True)

        # Assert
        assert log_file.exists()
        log_content = log_file.read_text()
        log_entry = json.loads(log_content.strip())
        assert log_entry["event_type"] == "path_validation"
        assert log_entry["path"] == str(test_path)
        assert log_entry["validation_type"] == "traversal"
        assert log_entry["success"] is True

    def test_log_export(self, tmp_path):
        """Test logging export events."""
        # Setup
        log_file = tmp_path / "audit.log"
        logger = AuditLogger(enabled=True, log_file=log_file)
        notebook_path = Path("/test/notebook.py")
        output_path = Path("/test/output.html")

        # Execute
        logger.log_export(notebook_path, output_path, True)

        # Assert
        assert log_file.exists()
        log_content = log_file.read_text()
        log_entry = json.loads(log_content.strip())
        assert log_entry["event_type"] == "export"
        assert log_entry["notebook_path"] == str(notebook_path)
        assert log_entry["output_path"] == str(output_path)
        assert log_entry["success"] is True

    def test_log_template_render(self, tmp_path):
        """Test logging template render events."""
        # Setup
        log_file = tmp_path / "audit.log"
        logger = AuditLogger(enabled=True, log_file=log_file)
        template_path = Path("/test/template.html.j2")

        # Execute
        logger.log_template_render(template_path, True)

        # Assert
        assert log_file.exists()
        log_content = log_file.read_text()
        log_entry = json.loads(log_content.strip())
        assert log_entry["event_type"] == "template_render"
        assert log_entry["template_path"] == str(template_path)
        assert log_entry["success"] is True

    def test_log_config_load(self, tmp_path):
        """Test logging config load events."""
        # Setup
        log_file = tmp_path / "audit.log"
        logger = AuditLogger(enabled=True, log_file=log_file)
        config_path = Path("/test/config.toml")

        # Execute
        logger.log_config_load(config_path, True)

        # Assert
        assert log_file.exists()
        log_content = log_file.read_text()
        log_entry = json.loads(log_content.strip())
        assert log_entry["event_type"] == "config_load"
        assert log_entry["config_path"] == str(config_path)
        assert log_entry["success"] is True

    def test_log_file_access(self, tmp_path):
        """Test logging file access events."""
        # Setup
        log_file = tmp_path / "audit.log"
        logger = AuditLogger(enabled=True, log_file=log_file)
        file_path = Path("/test/file.txt")

        # Execute
        logger.log_file_access(file_path, "read", True)

        # Assert
        assert log_file.exists()
        log_content = log_file.read_text()
        log_entry = json.loads(log_content.strip())
        assert log_entry["event_type"] == "file_access"
        assert log_entry["file_path"] == str(file_path)
        assert log_entry["operation"] == "read"
        assert log_entry["success"] is True

    def test_disabled_logger(self, tmp_path):
        """Test that disabled logger doesn't write logs."""
        # Setup
        log_file = tmp_path / "audit.log"
        logger = AuditLogger(enabled=False, log_file=log_file)

        # Execute
        logger.log_path_validation(Path("/test"), "traversal", True)

        # Assert
        assert not log_file.exists()


class TestGlobalAuditLogger:
    """Tests for global audit logger functions."""

    def test_get_audit_logger(self):
        """Test getting global audit logger."""
        # Execute
        logger = get_audit_logger()

        # Assert
        assert logger is not None
        assert isinstance(logger, AuditLogger)

    def test_init_audit_logger(self, tmp_path):
        """Test initializing global audit logger."""
        # Setup
        log_file = tmp_path / "audit.log"

        # Execute
        logger = init_audit_logger(enabled=True, log_file=log_file)

        # Assert
        assert logger is not None
        assert logger.enabled is True
        assert logger.log_file == log_file

        # Verify it's the global instance
        assert get_audit_logger() is logger
