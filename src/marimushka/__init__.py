"""Marimushka - Export marimo notebooks to HTML/WebAssembly with custom templates.

This package provides tools for exporting marimo notebooks to static HTML and
interactive WebAssembly formats. It generates an index page listing all exported
notebooks, enabling deployment to static hosting platforms like GitHub Pages,
S3, or any web server without requiring Python on the viewer's side.

Key Features:
    - Export marimo notebooks to static HTML or interactive WebAssembly
    - Support for three export modes: static notebooks, interactive notebooks, and apps
    - Customizable index page generation using Jinja2 templates
    - Parallel export for improved performance
    - Watch mode for automatic re-export on file changes

Typical usage example:
    from marimushka.export import main

    # Export all notebooks in the default directories
    main()

    # Export with custom settings
    main(
        output="_site",
        notebooks="my_notebooks",
        apps="my_apps",
        parallel=True,
        max_workers=8,
    )

CLI usage:
    # Export notebooks
    marimushka export --output _site --notebooks notebooks --apps apps

    # Watch mode for development
    marimushka watch --notebooks notebooks --apps apps

Exports:
    This module re-exports the exception hierarchy and result types for
    convenient access by library users. See the exceptions module for
    detailed documentation of each exception class.
"""

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
    ProgressCallback,
    TemplateError,
    TemplateInvalidError,
    TemplateNotFoundError,
    TemplateRenderError,
)

__version__ = importlib.metadata.version("marimushka")

__all__ = [
    "BatchExportResult",
    # Export exceptions
    "ExportError",
    "ExportExecutableNotFoundError",
    "ExportSubprocessError",
    "IndexWriteError",
    # Base exceptions
    "MarimushkaError",
    # Notebook exceptions
    "NotebookError",
    # Result types
    "NotebookExportResult",
    "NotebookInvalidError",
    "NotebookNotFoundError",
    # Output exceptions
    "OutputError",
    # Progress callback
    "ProgressCallback",
    # Template exceptions
    "TemplateError",
    "TemplateInvalidError",
    "TemplateNotFoundError",
    "TemplateRenderError",
    "__version__",
]
