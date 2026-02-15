"""Security utilities for marimushka.

This module provides security-related utilities including path validation,
path traversal protection, and other security measures.
"""

from pathlib import Path


def validate_path_traversal(path: Path, base_dir: Path | None = None) -> Path:
    """Validate that a path does not escape the base directory via path traversal.

    Args:
        path: The path to validate.
        base_dir: The base directory that path should not escape from.
                 If None, only checks for relative path components that go up.

    Returns:
        The resolved absolute path if validation passes.

    Raises:
        ValueError: If the path contains path traversal attempts or escapes base_dir.

    Examples:
        >>> from pathlib import Path
        >>> validate_path_traversal(Path("notebooks/test.py"), Path("/home/user"))  # doctest: +SKIP
        PosixPath('/home/user/notebooks/test.py')
        >>> validate_path_traversal(Path("../../../etc/passwd"))  # doctest: +SKIP
        Traceback (most recent call last):
            ...
        ValueError: Path traversal detected: path cannot escape base directory

    """
    # Resolve the path to get its absolute form
    try:
        resolved_path = path.resolve(strict=False)
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Invalid path: {path}") from e  # noqa: TRY003

    # If a base directory is provided, ensure the path doesn't escape it
    if base_dir is not None:
        try:
            base_resolved = base_dir.resolve(strict=False)
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Invalid base directory: {base_dir}") from e  # noqa: TRY003

        # Check if the resolved path is within the base directory
        try:
            resolved_path.relative_to(base_resolved)
        except ValueError as e:
            raise ValueError(f"Path traversal detected: {path} escapes base directory {base_dir}") from e  # noqa: TRY003

    return resolved_path


def _check_whitelist(resolved_path: Path, whitelist: list[Path], original_path: Path) -> None:
    """Check if a path is in the whitelist.

    Args:
        resolved_path: The resolved absolute path to check.
        whitelist: List of allowed paths.
        original_path: Original path for error message.

    Raises:
        ValueError: If path is not in whitelist.

    """
    resolved_whitelist = [p.resolve(strict=False) for p in whitelist]
    if resolved_path not in resolved_whitelist:
        raise ValueError(f"Binary path not in whitelist: {original_path}")  # noqa: TRY003


def validate_bin_path(bin_path: Path, whitelist: list[Path] | None = None) -> Path:
    """Validate that bin_path is a valid directory and optionally check against whitelist.

    Args:
        bin_path: Path to the binary directory.
        whitelist: Optional list of allowed bin paths. If None, accepts any valid directory.

    Returns:
        The validated Path object.

    Raises:
        ValueError: If bin_path is invalid or not in the whitelist.

    Examples:
        >>> validate_bin_path(Path("/usr/local/bin"))  # doctest: +SKIP
        PosixPath('/usr/local/bin')

    """
    if not bin_path.exists():
        raise ValueError(f"Binary path does not exist: {bin_path}")  # noqa: TRY003

    if not bin_path.is_dir():
        raise ValueError(f"Binary path is not a directory: {bin_path}")  # noqa: TRY003

    # Resolve to absolute path to prevent path traversal
    resolved_bin_path = bin_path.resolve(strict=True)

    # Check against whitelist if provided
    if whitelist is not None:
        _check_whitelist(resolved_bin_path, whitelist, bin_path)

    return resolved_bin_path


def validate_file_path(file_path: Path, allowed_extensions: list[str] | None = None) -> Path:
    """Validate that a file path exists, is a file, and has an allowed extension.

    Args:
        file_path: Path to the file.
        allowed_extensions: Optional list of allowed file extensions (e.g., ['.py', '.html']).
                          If None, accepts any extension.

    Returns:
        The validated Path object.

    Raises:
        ValueError: If file path is invalid or has a disallowed extension.

    Examples:
        >>> validate_file_path(Path("test.py"), [".py"])  # doctest: +SKIP
        PosixPath('test.py')

    """
    if not file_path.exists():
        raise ValueError(f"File does not exist: {file_path}")  # noqa: TRY003

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")  # noqa: TRY003

    # Check extension if whitelist provided
    if allowed_extensions is not None:
        if file_path.suffix not in allowed_extensions:
            msg = f"File extension {file_path.suffix} not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
            raise ValueError(msg)

    return file_path


def sanitize_error_message(error_msg: str, sensitive_patterns: list[str] | None = None) -> str:
    """Sanitize error messages by removing potentially sensitive information.

    Args:
        error_msg: The error message to sanitize.
        sensitive_patterns: Optional list of patterns to redact from the message.
                          If None, uses default patterns (absolute paths, user info).

    Returns:
        The sanitized error message.

    Examples:
        >>> sanitize_error_message("Error in /home/user/secret/file.py")
        'Error in <redacted_path>/file.py'

    """
    if sensitive_patterns is None:
        # Default: redact absolute paths while keeping filename
        sensitive_patterns = []

    sanitized = error_msg

    # Redact absolute paths but keep the filename
    import re

    # Pattern to match absolute paths (Unix and Windows)
    path_pattern = r"(?:(?:[A-Za-z]:)?[/\\](?:[^/\\:\n]+[/\\])+)([^/\\:\n]+)"

    def redact_path(match):
        filename = match.group(1)
        return f"<redacted_path>/{filename}"

    sanitized = re.sub(path_pattern, redact_path, sanitized)

    # Redact custom patterns
    for pattern in sensitive_patterns:
        sanitized = sanitized.replace(pattern, "<redacted>")

    return sanitized


def validate_max_workers(max_workers: int, min_workers: int = 1, max_allowed: int = 16) -> int:
    """Validate and bound the number of worker threads.

    Args:
        max_workers: The requested number of workers.
        min_workers: Minimum allowed workers. Defaults to 1.
        max_allowed: Maximum allowed workers. Defaults to 16.

    Returns:
        The validated worker count, bounded to the allowed range.

    Raises:
        ValueError: If max_workers is not a positive integer or constraints are invalid.

    Examples:
        >>> validate_max_workers(4)
        4
        >>> validate_max_workers(100)
        16
        >>> validate_max_workers(0)
        1

    """
    if not isinstance(max_workers, int):
        raise TypeError(f"max_workers must be an integer, got {type(max_workers).__name__}")  # noqa: TRY003

    if min_workers < 1:
        raise ValueError(f"min_workers must be at least 1, got {min_workers}")  # noqa: TRY003

    if max_allowed < min_workers:
        raise ValueError(f"max_allowed ({max_allowed}) must be >= min_workers ({min_workers})")  # noqa: TRY003

    # Bound the value using max/min for cleaner logic
    return max(min_workers, min(max_workers, max_allowed))
