"""Marimushka."""

import importlib.metadata

from .exceptions import (
    BatchExportResult,
    ExportError,
    ExportExecutableNotFoundError,
    ExportSubprocessError,
    IndexWriteError,
    MarimushkaError,
    NotebookError,
    NotebookExportResult,
    NotebookInvalidError,
    NotebookNotFoundError,
    OutputError,
    TemplateError,
    TemplateInvalidError,
    TemplateNotFoundError,
    TemplateRenderError,
)

__version__ = importlib.metadata.version("marimushka")

__all__ = [
    "__version__",
    # Base exceptions
    "MarimushkaError",
    # Template exceptions
    "TemplateError",
    "TemplateNotFoundError",
    "TemplateInvalidError",
    "TemplateRenderError",
    # Notebook exceptions
    "NotebookError",
    "NotebookNotFoundError",
    "NotebookInvalidError",
    # Export exceptions
    "ExportError",
    "ExportExecutableNotFoundError",
    "ExportSubprocessError",
    # Output exceptions
    "OutputError",
    "IndexWriteError",
    # Result types
    "NotebookExportResult",
    "BatchExportResult",
]
