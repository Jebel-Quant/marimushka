"""Export module for building and deploying marimo notebooks.

This module provides the CLI interface and core export functionality for
converting marimo notebooks into deployable HTML/WebAssembly format. It
orchestrates the export process, handles template rendering, and generates
an index page that serves as a navigation hub for all exported notebooks.

Architecture:
    The export flow follows this path:
    cli() → app() (Typer) → main() → _main_impl() → _generate_index()

    - cli(): Entry point that invokes the Typer application
    - app: Typer application with subcommands (export, watch, version)
    - main(): Public Python API with sensible defaults
    - _main_impl(): Implementation with logging and orchestration
    - _generate_index(): Core export logic with template rendering

CLI Commands:
    - export: Export notebooks to HTML/WASM and generate index page
    - watch: Monitor directories and auto-export on file changes
    - version: Display the current marimushka version

Parallel Export:
    The module supports parallel notebook export using ThreadPoolExecutor.
    By default, it uses 4 worker threads, configurable via --max-workers.
    Progress is displayed using Rich progress bars.

Template System:
    Index pages are generated using Jinja2 templates. Templates receive
    three lists (notebooks, apps, notebooks_wasm) where each item has:
    - display_name: Human-readable name (underscores converted to spaces)
    - html_path: Relative path to the exported HTML file
    - path: Original .py file path
    - kind: The notebook type (Kind enum)

Example::

    # CLI usage
    $ marimushka export --notebooks notebooks --apps apps --output _site

    # Python API
    from marimushka.export import main
    main(notebooks="notebooks", apps="apps", output="_site")

The exported files will be placed in the specified output directory (default: _site).
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "jinja2>=3.1.6",
#     "typer>=0.16.0",
#     "loguru>=0.7.3",
#     "rich>=14.0.0",
# ]
# ///

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import jinja2
import typer
from jinja2.sandbox import SandboxedEnvironment
from loguru import logger
from rich import print as rich_print
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TaskProgressColumn, TextColumn

from . import __version__
from .audit import get_audit_logger
from .exceptions import (
    BatchExportResult,
    IndexWriteError,
    NotebookExportResult,
    TemplateInvalidError,
    TemplateNotFoundError,
    TemplateRenderError,
)
from .notebook import Kind, Notebook, folder2notebooks
from .security import (
    sanitize_error_message,
    set_secure_file_permissions,
    validate_file_size,
    validate_max_workers,
    validate_path_traversal,
)

# Maximum number of changed files to display in watch mode
_MAX_CHANGED_FILES_TO_DISPLAY = 5

# Configure logger
logger.configure(extra={"subprocess": ""})
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:"
    "<cyan>{function}</cyan>:<cyan>{line}</cyan> | <magenta>{extra[subprocess]}</magenta><level>{message}</level>",
)

app = typer.Typer(help=f"Marimushka - Export marimo notebooks in style. Version: {__version__}")


def _validate_template(template_path: Path) -> None:
    """Validate the template file exists and has correct extension.

    Args:
        template_path: Path to the template file.

    Raises:
        TemplateNotFoundError: If the template file does not exist.
        TemplateInvalidError: If the template path is not a file.

    """
    audit_logger = get_audit_logger()

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
    import stat

    if not stat.S_ISREG(stat_result.st_mode):
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


def _export_notebook(
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


def _export_notebooks_parallel(
    notebooks: list[Notebook],
    output_dir: Path,
    sandbox: bool,
    bin_path: Path | None,
    max_workers: int = 4,
    progress: Progress | None = None,
    task_id: TaskID | None = None,
    timeout: int = 300,
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

    Returns:
        BatchExportResult containing individual results and summary statistics.

    """
    # Validate and bound max_workers for security
    max_workers = validate_max_workers(max_workers)

    batch_result = BatchExportResult()

    if not notebooks:
        return batch_result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_export_notebook, nb, output_dir, sandbox, bin_path, timeout): nb for nb in notebooks
        }

        for future in as_completed(futures):
            result = future.result()
            batch_result.add(result)

            if not result.success:
                error_msg = sanitize_error_message(str(result.error)) if result.error else "Unknown error"
                logger.error(f"Failed to export {result.notebook_path.name}: {error_msg}")

            if progress and task_id is not None:
                progress.advance(task_id)

    return batch_result


def _export_notebooks_sequential(
    notebooks: list[Notebook],
    output_dir: Path,
    sandbox: bool,
    bin_path: Path | None,
    progress: Progress | None = None,
    task_id: TaskID | None = None,
    timeout: int = 300,
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

    Returns:
        BatchExportResult containing individual results and summary statistics.

    """
    batch_result = BatchExportResult()

    for nb in notebooks:
        result = nb.export(output_dir=output_dir, sandbox=sandbox, bin_path=bin_path, timeout=timeout)
        batch_result.add(result)
        if progress and task_id is not None:
            progress.advance(task_id)

    return batch_result


def _export_all_notebooks(
    output: Path,
    notebooks: list[Notebook],
    apps: list[Notebook],
    notebooks_wasm: list[Notebook],
    sandbox: bool,
    bin_path: Path | None,
    parallel: bool,
    max_workers: int,
    timeout: int = 300,
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
                batch_result = _export_notebooks_parallel(
                    nb_list, out_dir, sandbox, bin_path, max_workers, progress, task, timeout
                )
            else:
                batch_result = _export_notebooks_sequential(
                    nb_list, out_dir, sandbox, bin_path, progress, task, timeout
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


def _render_template(
    template_file: Path,
    notebooks: list[Notebook],
    apps: list[Notebook],
    notebooks_wasm: list[Notebook],
) -> str:
    """Render the index template with notebook data.

    Args:
        template_file: Path to the Jinja2 template file.
        notebooks: List of notebooks for static HTML export.
        apps: List of notebooks for app export.
        notebooks_wasm: List of notebooks for interactive WebAssembly export.

    Returns:
        The rendered HTML content as a string.

    Raises:
        TemplateRenderError: If the template fails to render.

    """
    audit_logger = get_audit_logger()
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


def _write_index_file(index_path: Path, content: str) -> None:
    """Write the rendered HTML content to the index file.

    Args:
        index_path: Path where the index.html file will be written.
        content: The rendered HTML content to write.

    Raises:
        IndexWriteError: If the file cannot be written.

    """
    audit_logger = get_audit_logger()
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


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    """Handle the CLI invocation without a subcommand.

    This callback runs before any subcommand and displays help text if the
    user invokes marimushka without specifying a subcommand (e.g., just
    `marimushka` instead of `marimushka export`).

    Args:
        ctx: Typer context containing invocation information, including
            which subcommand (if any) was specified.

    Raises:
        typer.Exit: Always raised when no subcommand is provided, with
            exit code 0 to indicate this is expected behavior.

    """
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
        raise typer.Exit()


def _generate_index(
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

    Returns:
        The rendered HTML content as a string.

    Raises:
        TemplateRenderError: If the template fails to render.
        IndexWriteError: If the index file cannot be written.

    """
    notebooks = notebooks or []
    apps = apps or []
    notebooks_wasm = notebooks_wasm or []

    # Export all notebooks with progress tracking
    _export_all_notebooks(
        output=output,
        notebooks=notebooks,
        apps=apps,
        notebooks_wasm=notebooks_wasm,
        sandbox=sandbox,
        bin_path=bin_path,
        parallel=parallel,
        max_workers=max_workers,
        timeout=timeout,
    )

    # Ensure the output directory exists
    output.mkdir(parents=True, exist_ok=True)

    # Render template and write index file
    rendered_html = _render_template(template_file, notebooks, apps, notebooks_wasm)
    _write_index_file(output / "index.html", rendered_html)

    return rendered_html


def _main_impl(
    output: str | Path,
    template: str | Path,
    notebooks: str | Path,
    apps: str | Path,
    notebooks_wasm: str | Path,
    sandbox: bool = True,
    bin_path: str | Path | None = None,
    parallel: bool = True,
    max_workers: int = 4,
    timeout: int = 300,
) -> str:
    """Execute the main export workflow with logging and validation.

    This is the internal implementation function that contains the actual
    export logic. It validates inputs, discovers notebooks in each directory,
    exports them according to their type, and generates the index page.
    All operations are logged for debugging and monitoring.

    This function is called by main() (Python API) and _main_typer() (CLI).
    It separates the implementation from the interface, allowing both the
    Python API and CLI to share the same core logic.

    Args:
        output: Directory where exported files will be saved. Created if
            it doesn't exist. Subdirectories (notebooks/, apps/, notebooks_wasm/)
            are created automatically based on content.
        template: Path to the Jinja2 template file for the index page.
            Must have .j2 or .jinja2 extension (warning logged otherwise).
        notebooks: Directory containing marimo notebooks for static HTML export.
            All .py files in this directory are treated as notebooks.
        apps: Directory containing marimo notebooks for app-mode export.
            All .py files are exported with code hidden in run mode.
        notebooks_wasm: Directory containing marimo notebooks for interactive
            WebAssembly export with edit mode enabled.
        sandbox: Whether to run notebooks in sandbox mode during export.
            Defaults to True for security. Set False only for trusted code.
        bin_path: Custom directory containing the uvx executable. If None,
            uvx is located via the system PATH.
        parallel: Whether to export notebooks in parallel using threads.
            Defaults to True for performance.
        max_workers: Maximum number of parallel worker threads. Only used
            when parallel=True. Defaults to 4.
        timeout: Maximum time in seconds for each export. Defaults to 300.

    Returns:
        The rendered HTML content of the index page as a string. Returns
        an empty string if no notebooks or apps were found.

    Raises:
        TemplateNotFoundError: If the template file does not exist.
        TemplateInvalidError: If the template path is not a valid file.
        TemplateRenderError: If the template fails to render due to Jinja2 errors.
        IndexWriteError: If the index.html file cannot be written to disk.

    """
    logger.info("Starting marimushka build process")
    logger.info(f"Version of Marimushka: {__version__}")
    output = output or "_site"

    # Convert output_dir explicitly to Path
    output_dir: Path = Path(output)
    logger.info(f"Output directory: {output_dir}")

    # Make sure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert template to Path and validate early
    template_file: Path = Path(template)
    _validate_template(template_file)

    logger.info(f"Using template file: {template_file}")
    logger.info(f"Notebooks: {notebooks}")
    logger.info(f"Apps: {apps}")
    logger.info(f"Notebooks-wasm: {notebooks_wasm}")
    logger.info(f"Sandbox: {sandbox}")
    logger.info(f"Parallel: {parallel} (max_workers={max_workers})")
    logger.info(f"Bin path: {bin_path}")
    logger.info(f"Timeout: {timeout}s")

    # Convert bin_path to Path if provided
    bin_path_obj: Path | None = Path(bin_path) if bin_path else None

    notebooks_data = folder2notebooks(folder=notebooks, kind=Kind.NB)
    apps_data = folder2notebooks(folder=apps, kind=Kind.APP)
    notebooks_wasm_data = folder2notebooks(folder=notebooks_wasm, kind=Kind.NB_WASM)

    logger.info(f"# notebooks_data: {len(notebooks_data)}")
    logger.info(f"# apps_data: {len(apps_data)}")
    logger.info(f"# notebooks_wasm_data: {len(notebooks_wasm_data)}")

    # Exit if no notebooks or apps were found
    if not notebooks_data and not apps_data and not notebooks_wasm_data:
        logger.warning("No notebooks or apps found!")
        return ""

    return _generate_index(
        output=output_dir,
        template_file=template_file,
        notebooks=notebooks_data,
        apps=apps_data,
        notebooks_wasm=notebooks_wasm_data,
        sandbox=sandbox,
        bin_path=bin_path_obj,
        parallel=parallel,
        max_workers=max_workers,
        timeout=timeout,
    )


def main(
    output: str | Path = "_site",
    template: str | Path = Path(__file__).parent / "templates" / "tailwind.html.j2",
    notebooks: str | Path = "notebooks",
    apps: str | Path = "apps",
    notebooks_wasm: str | Path = "notebooks",
    sandbox: bool = True,
    bin_path: str | Path | None = None,
    parallel: bool = True,
    max_workers: int = 4,
    timeout: int = 300,
) -> str:
    """Export marimo notebooks and generate an index page.

    Args:
        output: Output directory for generated files. Defaults to "_site".
        template: Path to Jinja2 template file. Defaults to built-in Tailwind template.
        notebooks: Directory containing static notebooks. Defaults to "notebooks".
        apps: Directory containing app notebooks. Defaults to "apps".
        notebooks_wasm: Directory containing interactive notebooks. Defaults to "notebooks".
        sandbox: Whether to run exports in isolated sandbox. Defaults to True.
        bin_path: Custom path to uvx executable. Defaults to None.
        parallel: Whether to export notebooks in parallel. Defaults to True.
        max_workers: Maximum number of parallel workers. Defaults to 4.
        timeout: Maximum time in seconds for each export. Defaults to 300.

    Returns:
        Rendered HTML content as string, empty if no notebooks found.

    Raises:
        TemplateNotFoundError: If the template file does not exist.
        TemplateInvalidError: If the template path is not a file.
        TemplateRenderError: If the template fails to render.
        IndexWriteError: If the index file cannot be written.

    """
    # Call the implementation function with the provided parameters and return its result
    return _main_impl(
        output=output,
        template=template,
        notebooks=notebooks,
        apps=apps,
        notebooks_wasm=notebooks_wasm,
        sandbox=sandbox,
        bin_path=bin_path,
        parallel=parallel,
        max_workers=max_workers,
        timeout=timeout,
    )


@app.command(name="export")
def _main_typer(
    output: str = typer.Option("_site", "--output", "-o", help="Directory where the exported files will be saved"),
    template: str = typer.Option(
        str(Path(__file__).parent / "templates" / "tailwind.html.j2"),
        "--template",
        "-t",
        help="Path to the template file",
    ),
    notebooks: str = typer.Option("notebooks", "--notebooks", "-n", help="Directory containing marimo notebooks"),
    apps: str = typer.Option("apps", "--apps", "-a", help="Directory containing marimo apps"),
    notebooks_wasm: str = typer.Option(
        "notebooks_wasm", "--notebooks-wasm", "-nw", help="Directory containing marimo notebooks"
    ),
    sandbox: bool = typer.Option(True, "--sandbox/--no-sandbox", help="Whether to run the notebook in a sandbox"),
    bin_path: str | None = typer.Option(None, "--bin-path", "-b", help="The directory where the executable is located"),
    parallel: bool = typer.Option(True, "--parallel/--no-parallel", help="Whether to export notebooks in parallel"),
    max_workers: int = typer.Option(4, "--max-workers", "-w", help="Maximum number of parallel workers (1-16)"),
    timeout: int = typer.Option(300, "--timeout", help="Timeout in seconds for each notebook export"),
) -> None:
    """Export marimo notebooks and build an HTML index page linking to them.

    This is the main CLI command for exporting notebooks. It scans the specified
    directories for marimo notebook files (.py), exports each one to HTML or
    WebAssembly format based on its category, and generates an index.html page
    that provides navigation links to all exported notebooks.

    The export process uses marimo's built-in export functionality via uvx,
    running each notebook in sandbox mode by default for security.

    Example usage:
        # Basic export with defaults
        $ marimushka export

        # Custom directories
        $ marimushka export -n my_notebooks -a my_apps -o dist

        # Disable parallel processing
        $ marimushka export --no-parallel

        # Use custom template
        $ marimushka export -t my_template.html.j2

    """
    main(
        output=output,
        template=template,
        notebooks=notebooks,
        apps=apps,
        notebooks_wasm=notebooks_wasm,
        sandbox=sandbox,
        bin_path=bin_path,
        parallel=parallel,
        max_workers=max_workers,
        timeout=timeout,
    )


@app.command(name="watch")
def watch(
    output: str = typer.Option("_site", "--output", "-o", help="Directory where the exported files will be saved"),
    template: str = typer.Option(
        str(Path(__file__).parent / "templates" / "tailwind.html.j2"),
        "--template",
        "-t",
        help="Path to the template file",
    ),
    notebooks: str = typer.Option("notebooks", "--notebooks", "-n", help="Directory containing marimo notebooks"),
    apps: str = typer.Option("apps", "--apps", "-a", help="Directory containing marimo apps"),
    notebooks_wasm: str = typer.Option(
        "notebooks_wasm", "--notebooks-wasm", "-nw", help="Directory containing marimo notebooks"
    ),
    sandbox: bool = typer.Option(True, "--sandbox/--no-sandbox", help="Whether to run the notebook in a sandbox"),
    bin_path: str | None = typer.Option(None, "--bin-path", "-b", help="The directory where the executable is located"),
    parallel: bool = typer.Option(True, "--parallel/--no-parallel", help="Whether to export notebooks in parallel"),
    max_workers: int = typer.Option(4, "--max-workers", "-w", help="Maximum number of parallel workers (1-16)"),
    timeout: int = typer.Option(300, "--timeout", help="Timeout in seconds for each notebook export"),
) -> None:
    """Watch for changes and automatically re-export notebooks.

    This command watches the notebook directories and template file for changes,
    automatically re-exporting when files are modified.

    Requires the 'watchfiles' package: uv add watchfiles
    """
    try:
        from watchfiles import watch as watchfiles_watch
    except ImportError:  # pragma: no cover
        rich_print("[bold red]Error:[/bold red] watchfiles package is required for watch mode.")
        rich_print("Install it with: [cyan]uv add watchfiles[/cyan]")
        raise typer.Exit(1) from None

    # Build list of paths to watch
    watch_paths: list[Path] = []

    template_path = Path(template)
    if template_path.exists():
        watch_paths.append(template_path.parent)

    for folder in [notebooks, apps, notebooks_wasm]:
        folder_path = Path(folder)
        if folder_path.exists() and folder_path.is_dir():
            watch_paths.append(folder_path)

    if not watch_paths:
        rich_print("[bold yellow]Warning:[/bold yellow] No directories to watch!")
        raise typer.Exit(1)

    rich_print("[bold green]Watching for changes in:[/bold green]")
    for p in watch_paths:
        rich_print(f"  [cyan]{p}[/cyan]")
    rich_print("\n[dim]Press Ctrl+C to stop[/dim]\n")

    # Initial export
    rich_print("[bold blue]Running initial export...[/bold blue]")
    main(
        output=output,
        template=template,
        notebooks=notebooks,
        apps=apps,
        notebooks_wasm=notebooks_wasm,
        sandbox=sandbox,
        bin_path=bin_path,
        parallel=parallel,
        max_workers=max_workers,
        timeout=timeout,
    )
    rich_print("[bold green]Initial export complete![/bold green]\n")

    # Watch for changes (interactive loop - excluded from coverage)
    try:
        for changes in watchfiles_watch(*watch_paths):  # pragma: no cover
            changed_files = [str(change[1]) for change in changes]
            rich_print("\n[bold yellow]Detected changes:[/bold yellow]")
            for f in changed_files[:_MAX_CHANGED_FILES_TO_DISPLAY]:
                rich_print(f"  [dim]{f}[/dim]")
            if len(changed_files) > _MAX_CHANGED_FILES_TO_DISPLAY:
                rich_print(f"  [dim]... and {len(changed_files) - _MAX_CHANGED_FILES_TO_DISPLAY} more[/dim]")

            rich_print("[bold blue]Re-exporting...[/bold blue]")
            main(
                output=output,
                template=template,
                notebooks=notebooks,
                apps=apps,
                notebooks_wasm=notebooks_wasm,
                sandbox=sandbox,
                bin_path=bin_path,
                parallel=parallel,
                max_workers=max_workers,
                timeout=timeout,
            )
            rich_print("[bold green]Export complete![/bold green]")
    except KeyboardInterrupt:
        rich_print("\n[bold green]Watch mode stopped.[/bold green]")


@app.command(name="version")
def version() -> None:
    """Display the current version of Marimushka.

    Prints the package version with colored formatting using Rich. The version
    is read from the package metadata at runtime, ensuring it always reflects
    the installed version.

    Example:
        $ marimushka version
        Marimushka version: 0.1.0

    """
    rich_print(f"[bold green]Marimushka[/bold green] version: [bold blue]{__version__}[/bold blue]")


def cli() -> None:
    """Entry point for the marimushka command-line interface.

    This function is registered as the console script entry point in
    pyproject.toml. It invokes the Typer application which handles
    argument parsing and command dispatch.

    The CLI supports the following subcommands:
        - export: Export notebooks and generate index page
        - watch: Monitor for changes and auto-export
        - version: Display the installed version

    Running without a subcommand displays help text.

    Example:
        $ marimushka          # Shows help
        $ marimushka export   # Run export command
        $ marimushka --help   # Shows help

    """
    app()
