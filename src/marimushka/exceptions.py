"""Custom exceptions and result types for marimushka.

This module defines a hierarchy of exceptions for specific error scenarios,
enabling callers to handle different failure modes appropriately. It also
defines result types for operations that can partially succeed.
"""

from dataclasses import dataclass, field
from pathlib import Path


class MarimushkaError(Exception):
    """Base exception for all marimushka errors.

    All marimushka-specific exceptions inherit from this class,
    allowing callers to catch all marimushka errors with a single handler.

    Attributes:
        message: Human-readable error description.

    """

    def __init__(self, message: str) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error description.

        """
        self.message = message
        super().__init__(message)


class TemplateError(MarimushkaError):
    """Base exception for template-related errors."""

    pass


class TemplateNotFoundError(TemplateError):
    """Raised when the specified template file does not exist.

    Attributes:
        template_path: Path to the missing template file.

    """

    def __init__(self, template_path: Path) -> None:
        """Initialize the exception.

        Args:
            template_path: Path to the missing template file.

        """
        self.template_path = template_path
        super().__init__(f"Template file not found: {template_path}")


class TemplateInvalidError(TemplateError):
    """Raised when the template path is not a valid file.

    Attributes:
        template_path: Path that is not a valid file.

    """

    def __init__(self, template_path: Path, reason: str = "not a file") -> None:
        """Initialize the exception.

        Args:
            template_path: Path that is not a valid file.
            reason: Explanation of why the path is invalid.

        """
        self.template_path = template_path
        self.reason = reason
        super().__init__(f"Invalid template path ({reason}): {template_path}")


class TemplateRenderError(TemplateError):
    """Raised when template rendering fails.

    Attributes:
        template_path: Path to the template that failed to render.
        original_error: The underlying Jinja2 error.

    """

    def __init__(self, template_path: Path, original_error: Exception) -> None:
        """Initialize the exception.

        Args:
            template_path: Path to the template that failed to render.
            original_error: The underlying Jinja2 error.

        """
        self.template_path = template_path
        self.original_error = original_error
        super().__init__(f"Failed to render template {template_path}: {original_error}")


class NotebookError(MarimushkaError):
    """Base exception for notebook-related errors."""

    pass


class NotebookNotFoundError(NotebookError):
    """Raised when the specified notebook file does not exist.

    Attributes:
        notebook_path: Path to the missing notebook file.

    """

    def __init__(self, notebook_path: Path) -> None:
        """Initialize the exception.

        Args:
            notebook_path: Path to the missing notebook file.

        """
        self.notebook_path = notebook_path
        super().__init__(f"Notebook file not found: {notebook_path}")


class NotebookInvalidError(NotebookError):
    """Raised when the notebook path is not a valid Python file.

    Attributes:
        notebook_path: Path to the invalid notebook.
        reason: Explanation of why the notebook is invalid.

    """

    def __init__(self, notebook_path: Path, reason: str) -> None:
        """Initialize the exception.

        Args:
            notebook_path: Path to the invalid notebook.
            reason: Explanation of why the notebook is invalid.

        """
        self.notebook_path = notebook_path
        self.reason = reason
        super().__init__(f"Invalid notebook ({reason}): {notebook_path}")


class ExportError(MarimushkaError):
    """Base exception for export-related errors."""

    pass


class ExportExecutableNotFoundError(ExportError):
    """Raised when the export executable (uvx/marimo) cannot be found.

    Attributes:
        executable: Name of the missing executable.
        search_path: Path where the executable was searched for.

    """

    def __init__(self, executable: str, search_path: Path | None = None) -> None:
        """Initialize the exception.

        Args:
            executable: Name of the missing executable.
            search_path: Path where the executable was searched for.

        """
        self.executable = executable
        self.search_path = search_path
        if search_path:
            message = f"Executable '{executable}' not found in {search_path}"
        else:
            message = f"Executable '{executable}' not found in PATH"
        super().__init__(message)


class ExportSubprocessError(ExportError):
    """Raised when the export subprocess fails.

    Attributes:
        notebook_path: Path to the notebook being exported.
        command: The command that was executed.
        return_code: Exit code from the subprocess.
        stdout: Standard output from the subprocess.
        stderr: Standard error from the subprocess.

    """

    def __init__(
        self,
        notebook_path: Path,
        command: list[str],
        return_code: int,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        """Initialize the exception.

        Args:
            notebook_path: Path to the notebook being exported.
            command: The command that was executed.
            return_code: Exit code from the subprocess.
            stdout: Standard output from the subprocess.
            stderr: Standard error from the subprocess.

        """
        self.notebook_path = notebook_path
        self.command = command
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr
        message = f"Export failed for {notebook_path.name} (exit code {return_code})"
        if stderr:
            message += f": {stderr[:200]}"
        super().__init__(message)


class OutputError(MarimushkaError):
    """Base exception for output-related errors."""

    pass


class OutputDirectoryError(OutputError):
    """Raised when the output directory cannot be created or accessed.

    Attributes:
        output_path: Path to the output directory.
        original_error: The underlying OS error.

    """

    def __init__(self, output_path: Path, original_error: Exception) -> None:
        """Initialize the exception.

        Args:
            output_path: Path to the output directory.
            original_error: The underlying OS error.

        """
        self.output_path = output_path
        self.original_error = original_error
        super().__init__(f"Cannot create/access output directory {output_path}: {original_error}")


class IndexWriteError(OutputError):
    """Raised when the index.html file cannot be written.

    Attributes:
        index_path: Path where the index file was to be written.
        original_error: The underlying OS error.

    """

    def __init__(self, index_path: Path, original_error: Exception) -> None:
        """Initialize the exception.

        Args:
            index_path: Path where the index file was to be written.
            original_error: The underlying OS error.

        """
        self.index_path = index_path
        self.original_error = original_error
        super().__init__(f"Failed to write index file to {index_path}: {original_error}")


# Result types for operations that can partially succeed


@dataclass(frozen=True)
class NotebookExportResult:
    """Result of exporting a single notebook.

    Attributes:
        notebook_path: Path to the notebook that was exported.
        success: Whether the export succeeded.
        output_path: Path to the exported HTML file (if successful).
        error: The error that occurred (if failed).

    """

    notebook_path: Path
    success: bool
    output_path: Path | None = None
    error: ExportError | None = None

    @classmethod
    def succeeded(cls, notebook_path: Path, output_path: Path) -> "NotebookExportResult":
        """Create a successful result.

        Args:
            notebook_path: Path to the notebook that was exported.
            output_path: Path to the exported HTML file.

        Returns:
            A NotebookExportResult indicating success.

        """
        return cls(notebook_path=notebook_path, success=True, output_path=output_path)

    @classmethod
    def failed(cls, notebook_path: Path, error: ExportError) -> "NotebookExportResult":
        """Create a failed result.

        Args:
            notebook_path: Path to the notebook that failed to export.
            error: The error that occurred.

        Returns:
            A NotebookExportResult indicating failure.

        """
        return cls(notebook_path=notebook_path, success=False, error=error)


@dataclass
class BatchExportResult:
    """Result of exporting multiple notebooks.

    Attributes:
        results: List of individual notebook export results.
        total: Total number of notebooks attempted.
        succeeded: Number of successful exports.
        failed: Number of failed exports.

    """

    results: list[NotebookExportResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Return total number of notebooks attempted."""
        return len(self.results)

    @property
    def succeeded(self) -> int:
        """Return number of successful exports."""
        return sum(1 for r in self.results if r.success)

    @property
    def failed(self) -> int:
        """Return number of failed exports."""
        return sum(1 for r in self.results if not r.success)

    @property
    def all_succeeded(self) -> bool:
        """Return True if all exports succeeded."""
        return self.failed == 0

    @property
    def failures(self) -> list[NotebookExportResult]:
        """Return list of failed results."""
        return [r for r in self.results if not r.success]

    @property
    def successes(self) -> list[NotebookExportResult]:
        """Return list of successful results."""
        return [r for r in self.results if r.success]

    def add(self, result: NotebookExportResult) -> None:
        """Add a result to the batch.

        Args:
            result: The export result to add.

        """
        self.results.append(result)
