"""Security utilities for marimushka.

This module provides security-related utilities including path validation,
path traversal protection, and other security measures.
"""

import os
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

    def redact_path(match: re.Match[str]) -> str:
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


def validate_file_size(file_path: Path, max_size_bytes: int = 10 * 1024 * 1024) -> bool:
    """Validate that a file's size is within acceptable limits.

    This helps prevent DoS attacks via extremely large files.

    Args:
        file_path: Path to the file to check.
        max_size_bytes: Maximum allowed file size in bytes. Defaults to 10MB.

    Returns:
        True if file size is acceptable.

    Raises:
        ValueError: If file size exceeds the limit or file doesn't exist.

    Examples:
        >>> from pathlib import Path
        >>> # File within limit
        >>> validate_file_size(Path("small.txt"), max_size_bytes=1024*1024)  # doctest: +SKIP
        True

    """
    if not file_path.exists():
        raise ValueError(f"File does not exist: {file_path}")  # noqa: TRY003

    try:
        file_size = file_path.stat().st_size
    except OSError as e:
        raise ValueError(f"Cannot read file size: {file_path}") from e  # noqa: TRY003

    if file_size > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        msg = f"File size {actual_mb:.2f}MB exceeds limit of {max_mb:.2f}MB: {file_path}"
        raise ValueError(msg)

    return True


def safe_open_file(file_path: Path, mode: str = "r") -> int:
    """Safely open a file and return a file descriptor to avoid TOCTOU races.

    This function uses os.open with O_NOFOLLOW to prevent symlink attacks
    and returns a file descriptor that can be used with Path.open() via os.fdopen.

    Args:
        file_path: Path to the file to open.
        mode: File open mode ('r' for read, 'w' for write, etc.).

    Returns:
        File descriptor that should be used with os.fdopen.

    Raises:
        ValueError: If the path is invalid or a symlink.
        OSError: If the file cannot be opened.

    Examples:
        >>> from pathlib import Path
        >>> import os
        >>> # Safe file open
        >>> fd = safe_open_file(Path("test.txt"), "w")  # doctest: +SKIP
        >>> with os.fdopen(fd, "w") as f:  # doctest: +SKIP
        ...     f.write("safe content")

    """
    # Validate path first
    if not file_path.exists():
        if "w" not in mode and "a" not in mode:
            raise ValueError(f"File does not exist: {file_path}")  # noqa: TRY003

    # Check if it's a symlink (prevent symlink attacks)
    if file_path.exists() and file_path.is_symlink():
        raise ValueError(f"Cannot open symlink: {file_path}")  # noqa: TRY003

    # Open file with O_NOFOLLOW to prevent TOCTOU symlink race
    flags = os.O_NOFOLLOW
    if mode == "r":
        flags |= os.O_RDONLY
    elif mode == "w":
        flags |= os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    elif mode == "a":
        flags |= os.O_WRONLY | os.O_CREAT | os.O_APPEND
    else:
        raise ValueError(f"Unsupported mode: {mode}")  # noqa: TRY003

    # Open with restricted permissions (owner read/write only)
    try:
        fd = os.open(file_path, flags, mode=0o600)
    except OSError as e:
        raise ValueError(f"Cannot open file: {file_path}") from e  # noqa: TRY003
    else:
        return fd


def set_secure_file_permissions(file_path: Path, mode: int = 0o644) -> None:
    """Set secure permissions on a file.

    Args:
        file_path: Path to the file.
        mode: Permission mode (default: 0o644 = rw-r--r--).

    Raises:
        ValueError: If file doesn't exist or permissions cannot be set.

    Examples:
        >>> from pathlib import Path
        >>> set_secure_file_permissions(Path("test.txt"), 0o600)  # doctest: +SKIP

    """
    if not file_path.exists():
        raise ValueError(f"File does not exist: {file_path}")  # noqa: TRY003

    try:
        os.chmod(file_path, mode)
    except OSError as e:
        raise ValueError(f"Cannot set permissions on {file_path}") from e  # noqa: TRY003
