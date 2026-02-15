"""Audit logging for security-relevant events.

This module provides structured audit logging for security-critical operations
such as file access, export operations, and configuration changes.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger


class AuditLogger:
    """Audit logger for security-relevant events.

    This class provides structured logging for security events with
    consistent formatting and optional file output.

    Attributes:
        enabled: Whether audit logging is enabled.
        log_file: Optional path to audit log file.

    """

    def __init__(self, enabled: bool = True, log_file: Path | None = None) -> None:
        """Initialize the audit logger.

        Args:
            enabled: Whether to enable audit logging. Defaults to True.
            log_file: Optional path to write audit logs to file.

        """
        self.enabled = enabled
        self.log_file = log_file

        if self.log_file:
            # Ensure audit log directory exists
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _log_event(self, event_type: str, details: dict[str, Any]) -> None:
        """Log an audit event.

        Args:
            event_type: Type of event (e.g., 'path_validation', 'export').
            details: Dictionary containing event details.

        """
        if not self.enabled:
            return

        audit_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            **details,
        }

        # Log to structured logger
        logger.info(f"[AUDIT] {event_type}", extra={"audit": audit_entry})

        # Optionally write to file
        if self.log_file:
            try:
                with self.log_file.open("a") as f:
                    f.write(json.dumps(audit_entry) + "\n")
            except OSError as e:  # pragma: no cover
                logger.error(f"Failed to write audit log: {e}")

    def log_path_validation(self, path: Path, validation_type: str, success: bool, reason: str | None = None) -> None:
        """Log a path validation event.

        Args:
            path: The path that was validated.
            validation_type: Type of validation (e.g., 'traversal', 'bin_path').
            success: Whether validation succeeded.
            reason: Optional reason for failure.

        """
        self._log_event(
            "path_validation",
            {
                "path": str(path),
                "validation_type": validation_type,
                "success": success,
                "reason": reason,
            },
        )

    def log_export(
        self, notebook_path: Path, output_path: Path | None, success: bool, error: str | None = None
    ) -> None:
        """Log a notebook export event.

        Args:
            notebook_path: Path to the notebook being exported.
            output_path: Path to the output file (if successful).
            success: Whether export succeeded.
            error: Optional error message.

        """
        self._log_event(
            "export",
            {
                "notebook_path": str(notebook_path),
                "output_path": str(output_path) if output_path else None,
                "success": success,
                "error": error,
            },
        )

    def log_template_render(self, template_path: Path, success: bool, error: str | None = None) -> None:
        """Log a template rendering event.

        Args:
            template_path: Path to the template being rendered.
            success: Whether rendering succeeded.
            error: Optional error message.

        """
        self._log_event(
            "template_render",
            {
                "template_path": str(template_path),
                "success": success,
                "error": error,
            },
        )

    def log_config_load(self, config_path: Path | None, success: bool, error: str | None = None) -> None:
        """Log a configuration load event.

        Args:
            config_path: Path to config file (or None if using defaults).
            success: Whether loading succeeded.
            error: Optional error message.

        """
        self._log_event(
            "config_load",
            {
                "config_path": str(config_path) if config_path else None,
                "success": success,
                "error": error,
            },
        )

    def log_file_access(self, file_path: Path, operation: str, success: bool, error: str | None = None) -> None:
        """Log a file access event.

        Args:
            file_path: Path to the file being accessed.
            operation: Type of operation (e.g., 'read', 'write').
            success: Whether operation succeeded.
            error: Optional error message.

        """
        self._log_event(
            "file_access",
            {
                "file_path": str(file_path),
                "operation": operation,
                "success": success,
                "error": error,
            },
        )


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance.

    Returns:
        The global AuditLogger instance.

    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def init_audit_logger(enabled: bool = True, log_file: Path | None = None) -> AuditLogger:
    """Initialize the global audit logger.

    Args:
        enabled: Whether to enable audit logging.
        log_file: Optional path to audit log file.

    Returns:
        The initialized AuditLogger instance.

    """
    global _audit_logger
    _audit_logger = AuditLogger(enabled=enabled, log_file=log_file)
    return _audit_logger
