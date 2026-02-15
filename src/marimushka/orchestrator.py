"""Export orchestration and template rendering.

This module handles the core export workflow including parallel/sequential export,
template rendering, and index file generation.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import jinja2
from jinja2.sandbox import SandboxedEnvironment
from loguru import logger
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TaskProgressColumn, TextColumn

from .audit import AuditLogger, get_audit_logger
from .exceptions import (
    BatchExportResult,
    IndexWriteError,
    NotebookExportResult,
    ProgressCallback,
    TemplateRenderError,
)
from .notebook import Notebook
from .security import (
    sanitize_error_message,
    set_secure_file_permissions,
    validate_max_workers,
)


def export_notebook(
    notebook: Notebook,
    output_dir: Path,
    sandbox: bool,
    bin_path: Path | None,
    timeout: int = 300,
) -> NotebookExportResult:
    """Export a single notebook and return the result.

    Args:
        notebook: The notebook to export.
        output_dir: Output directory for the exported HTML.
        sandbox: Whether to use sandbox mode.
        bin_path: Custom path to uvx executable.
        timeout: Maximum time in seconds for the export process. Defaults to 300.

    Returns:
        NotebookExportResult with success status and details.

    """
    return notebook.export(output_dir=output_dir, sandbox=sandbox, bin_path=bin_path, timeout=timeout)


def export_notebooks_parallel(
    notebooks: list[Notebook],
    output_dir: Path,
    sandbox: bool,
    bin_path: Path | None,
    max_workers: int = 4,
    progress: Progress | None = None,
    task_id: TaskID | None = None,
    timeout: int = 300,
    on_progress: ProgressCallback | None = None,
) -> BatchExportResult:
    """Export notebooks in parallel using a thread pool.

    Args:
        notebooks: List of notebooks to export.
        output_dir: Output directory for exported HTML files.
        sandbox: Whether to use sandbox mode.
        bin_path: Custom path to uvx executable.
        max_workers: Maximum number of parallel workers. Defaults to 4.
        progress: Optional Rich Progress instance for progress tracking.
        task_id: Optional task ID for progress updates.
        timeout: Maximum time in seconds for each export. Defaults to 300.
        on_progress: Optional callback called after each notebook export.
                    Signature: on_progress(completed, total, notebook_name)

    Returns:
        BatchExportResult containing individual results and summary statistics.

    """
    # Validate and bound max_workers for security
    max_workers = validate_max_workers(max_workers)

    batch_result = BatchExportResult()

    if not notebooks:
        return batch_result

    total_notebooks = len(notebooks)
    completed_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(export_notebook, nb, output_dir, sandbox, bin_path, timeout): nb for nb in notebooks}

        for future in as_completed(futures):
            result = future.result()
            batch_result.add(result)
            completed_count += 1

            if not result.success:
                error_msg = sanitize_error_message(str(result.error)) if result.error else "Unknown error"
                logger.error(f"Failed to export {result.notebook_path.name}: {error_msg}")

            # Call user callback if provided
            if on_progress:
                on_progress(completed_count, total_notebooks, result.notebook_path.name)

            if progress and task_id is not None:
                progress.advance(task_id)

    return batch_result


def export_notebooks_sequential(
    notebooks: list[Notebook],
    output_dir: Path,
    sandbox: bool,
    bin_path: Path | None,
    progress: Progress | None = None,
    task_id: TaskID | None = None,
    timeout: int = 300,
    on_progress: ProgressCallback | None = None,
) -> BatchExportResult:
    """Export notebooks sequentially.

    Args:
        notebooks: List of notebooks to export.
        output_dir: Output directory for exported HTML files.
        sandbox: Whether to use sandbox mode.
        bin_path: Custom path to uvx executable.
        progress: Optional Rich Progress instance for progress tracking.
        task_id: Optional task ID for progress updates.
        timeout: Maximum time in seconds for each export. Defaults to 300.
        on_progress: Optional callback called after each notebook export.
                    Signature: on_progress(completed, total, notebook_name)

    Returns:
        BatchExportResult containing individual results and summary statistics.

    """
    batch_result = BatchExportResult()
    total_notebooks = len(notebooks)

    for idx, nb in enumerate(notebooks, 1):
        result = nb.export(output_dir=output_dir, sandbox=sandbox, bin_path=bin_path, timeout=timeout)
        batch_result.add(result)

        # Call user callback if provided
        if on_progress:
            on_progress(idx, total_notebooks, nb.path.name)

        if progress and task_id is not None:
            progress.advance(task_id)

    return batch_result


def export_all_notebooks(
    output: Path,
    notebooks: list[Notebook],
    apps: list[Notebook],
    notebooks_wasm: list[Notebook],
    sandbox: bool,
    bin_path: Path | None,
    parallel: bool,
    max_workers: int,
    timeout: int = 300,
    on_progress: ProgressCallback | None = None,
) -> BatchExportResult:
    """Export all notebooks with progress tracking.

    Args:
        output: Base output directory.
        notebooks: List of notebooks for static HTML export.
        apps: List of notebooks for app export.
        notebooks_wasm: List of notebooks for interactive WebAssembly export.
        sandbox: Whether to use sandbox mode.
        bin_path: Custom path to uvx executable.
        parallel: Whether to export notebooks in parallel.
        max_workers: Maximum number of parallel workers.
        timeout: Maximum time in seconds for each export. Defaults to 300.
        on_progress: Optional callback called after each notebook export.
                    Signature: on_progress(completed, total, notebook_name)

    Returns:
        BatchExportResult containing all export results.

    """
    total_notebooks = len(notebooks) + len(apps) + len(notebooks_wasm)
    combined_batch_result = BatchExportResult()

    if total_notebooks == 0:
        return combined_batch_result

    # Define notebook categories and their output directories
    notebook_categories = [
        (notebooks, output / "notebooks"),
        (apps, output / "apps"),
        (notebooks_wasm, output / "notebooks_wasm"),
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[cyan]{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task("[green]Exporting notebooks...", total=total_notebooks)

        for nb_list, out_dir in notebook_categories:
            if not nb_list:
                continue

            if parallel:
                batch_result = export_notebooks_parallel(
                    nb_list, out_dir, sandbox, bin_path, max_workers, progress, task, timeout, on_progress
                )
            else:
                batch_result = export_notebooks_sequential(
                    nb_list, out_dir, sandbox, bin_path, progress, task, timeout, on_progress
                )

            for result in batch_result.results:
                combined_batch_result.add(result)

    if combined_batch_result.failed > 0:  # pragma: no cover
        logger.warning(
            f"Export completed: {combined_batch_result.succeeded} succeeded, {combined_batch_result.failed} failed"
        )
        for failure in combined_batch_result.failures:
            error_detail = sanitize_error_message(str(failure.error)) if failure.error else "Unknown error"
            logger.debug(f"  - {failure.notebook_path.name}: {error_detail}")

    return combined_batch_result


def render_template(
    template_file: Path,
    notebooks: list[Notebook],
    apps: list[Notebook],
    notebooks_wasm: list[Notebook],
    audit_logger: AuditLogger,
) -> str:
    """Render the index template with notebook data.

    Args:
        template_file: Path to the Jinja2 template file.
        notebooks: List of notebooks for static HTML export.
        apps: List of notebooks for app export.
        notebooks_wasm: List of notebooks for interactive WebAssembly export.
        audit_logger: Logger for audit events.

    Returns:
        The rendered HTML content as a string.

    Raises:
        TemplateRenderError: If the template fails to render.

    """
    template_dir = template_file.parent
    template_name = template_file.name

    try:
        # Use SandboxedEnvironment for security
        env = SandboxedEnvironment(
            loader=jinja2.FileSystemLoader(template_dir), autoescape=jinja2.select_autoescape(["html", "xml"])
        )
        template = env.get_template(template_name)

        rendered = template.render(
            notebooks=notebooks,
            apps=apps,
            notebooks_wasm=notebooks_wasm,
        )
        audit_logger.log_template_render(template_file, True)
    except jinja2.exceptions.TemplateError as e:
        sanitized_error = sanitize_error_message(str(e))
        audit_logger.log_template_render(template_file, False, sanitized_error)
        raise TemplateRenderError(template_file, e) from e
    else:
        return rendered


def write_index_file(index_path: Path, content: str, audit_logger: AuditLogger) -> None:
    """Write the rendered HTML content to the index file.

    Args:
        index_path: Path where the index.html file will be written.
        content: The rendered HTML content to write.
        audit_logger: Logger for audit events.

    Raises:
        IndexWriteError: If the file cannot be written.

    """
    try:
        # Write file with secure content
        with Path.open(index_path, "w") as f:
            f.write(content)

        # Set secure file permissions
        set_secure_file_permissions(index_path, mode=0o644)

        logger.info(f"Successfully generated index file at {index_path}")
        audit_logger.log_file_access(index_path, "write", True)
    except OSError as e:
        sanitized_error = sanitize_error_message(str(e))
        audit_logger.log_file_access(index_path, "write", False, sanitized_error)
        raise IndexWriteError(index_path, e) from e


def generate_index(
    output: Path,
    template_file: Path,
    notebooks: list[Notebook] | None = None,
    apps: list[Notebook] | None = None,
    notebooks_wasm: list[Notebook] | None = None,
    sandbox: bool = True,
    bin_path: Path | None = None,
    parallel: bool = True,
    max_workers: int = 4,
    timeout: int = 300,
    on_progress: ProgressCallback | None = None,
    audit_logger: AuditLogger | None = None,
) -> str:
    """Generate an index.html file that lists all the notebooks.

    This function creates an HTML index page that displays links to all the exported
    notebooks. The index page includes the marimo logo and displays each notebook
    with a formatted title and a link to open it.

    Args:
        output: Directory where the index.html file will be saved.
        template_file: Path to the Jinja2 template file.
        notebooks: List of notebooks for static HTML export.
        apps: List of notebooks for app export.
        notebooks_wasm: List of notebooks for interactive WebAssembly export.
        sandbox: Whether to run the notebook in a sandbox. Defaults to True.
        bin_path: The directory where the executable is located. Defaults to None.
        parallel: Whether to export notebooks in parallel. Defaults to True.
        max_workers: Maximum number of parallel workers. Defaults to 4.
        timeout: Maximum time in seconds for each export. Defaults to 300.
        audit_logger: Logger for audit events. If None, creates a default logger.

    Returns:
        The rendered HTML content as a string.

    Raises:
        TemplateRenderError: If the template fails to render.
        IndexWriteError: If the index file cannot be written.

    """
    if audit_logger is None:
        audit_logger = get_audit_logger()

    notebooks = notebooks or []
    apps = apps or []
    notebooks_wasm = notebooks_wasm or []

    # Export all notebooks with progress tracking
    export_all_notebooks(
        output=output,
        notebooks=notebooks,
        apps=apps,
        notebooks_wasm=notebooks_wasm,
        sandbox=sandbox,
        bin_path=bin_path,
        parallel=parallel,
        max_workers=max_workers,
        timeout=timeout,
        on_progress=on_progress,
    )

    # Ensure the output directory exists
    output.mkdir(parents=True, exist_ok=True)

    # Render template and write index file
    rendered_html = render_template(template_file, notebooks, apps, notebooks_wasm, audit_logger)
    write_index_file(output / "index.html", rendered_html, audit_logger)

    return rendered_html
