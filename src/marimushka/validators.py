"""Input validation for paths, templates, and configuration.

This module provides validation functions for template files and other inputs
used in the export process. It ensures security by checking for path traversal,
file existence, and size limits.
"""

import stat as stat_module
from pathlib import Path

from loguru import logger

from .audit import AuditLogger
from .exceptions import TemplateInvalidError, TemplateNotFoundError
from .security import sanitize_error_message, validate_file_size, validate_path_traversal


def validate_template(template_path: Path, audit_logger: AuditLogger) -> None:
    """Validate the template file exists and has correct extension.

    Args:
        template_path: Path to the template file.
        audit_logger: Logger for audit events.

    Raises:
        TemplateNotFoundError: If the template file does not exist.
        TemplateInvalidError: If the template path is not a file.

    """
    # Validate path traversal
    try:
        validate_path_traversal(template_path)
        audit_logger.log_path_validation(template_path, "traversal", True)
    except ValueError as e:
        audit_logger.log_path_validation(template_path, "traversal", False, str(e))
        sanitized_msg = sanitize_error_message(str(e))
        raise TemplateInvalidError(template_path, reason=f"path traversal detected: {sanitized_msg}") from e

    # Check existence (avoid TOCTOU by using stat)
    try:
        stat_result = template_path.stat()
    except FileNotFoundError:
        audit_logger.log_path_validation(template_path, "existence", False, "file not found")
        raise TemplateNotFoundError(template_path) from None
    except OSError as e:
        audit_logger.log_path_validation(template_path, "existence", False, str(e))
        raise TemplateInvalidError(template_path, reason=f"cannot access file: {e}") from e

    # Check if it's a regular file
    if not stat_module.S_ISREG(stat_result.st_mode):
        audit_logger.log_path_validation(template_path, "file_type", False, "not a regular file")
        raise TemplateInvalidError(template_path, reason="path is not a file")

    # Check file size to prevent DoS
    try:
        validate_file_size(template_path, max_size_bytes=10 * 1024 * 1024)  # 10MB limit
    except ValueError as e:
        audit_logger.log_path_validation(template_path, "size", False, str(e))
        sanitized_msg = sanitize_error_message(str(e))
        raise TemplateInvalidError(template_path, reason=f"file size limit exceeded: {sanitized_msg}") from e

    if template_path.suffix not in (".j2", ".jinja2"):
        logger.warning(f"Template file '{template_path}' does not have .j2 or .jinja2 extension")

    audit_logger.log_path_validation(template_path, "complete", True)
