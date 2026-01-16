"""Build the script for marimo notebooks.

This script exports marimo notebooks to HTML/WebAssembly format and generates
an index.html file that lists all the notebooks. It handles both regular notebooks
(from the notebooks/ directory) and apps (from the apps/ directory).

The script can be run from the command line with optional arguments:
    uvx marimushka [--output-dir OUTPUT_DIR]

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
from loguru import logger
from rich import print as rich_print
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from . import __version__
from .exceptions import (
    BatchExportResult,
    IndexWriteError,
    NotebookExportResult,
    TemplateInvalidError,
    TemplateNotFoundError,
    TemplateRenderError,
)
from .notebook import Kind, Notebook, folder2notebooks

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
    if not template_path.exists():
        raise TemplateNotFoundError(template_path)
    if not template_path.is_file():
        raise TemplateInvalidError(template_path, reason="path is not a file")
    if template_path.suffix not in (".j2", ".jinja2"):
        logger.warning(f"Template file '{template_path}' does not have .j2 or .jinja2 extension")


def _export_notebook(
    notebook: Notebook,
    output_dir: Path,
    sandbox: bool,
    bin_path: Path | None,
) -> NotebookExportResult:
    """Export a single notebook and return the result.

    Args:
        notebook: The notebook to export.
        output_dir: Output directory for the exported HTML.
        sandbox: Whether to use sandbox mode.
        bin_path: Custom path to uvx executable.

    Returns:
        NotebookExportResult with success status and details.

    """
    return notebook.export(output_dir=output_dir, sandbox=sandbox, bin_path=bin_path)


def _export_notebooks_parallel(
    notebooks: list[Notebook],
    output_dir: Path,
    sandbox: bool,
    bin_path: Path | None,
    max_workers: int = 4,
    progress: Progress | None = None,
    task_id: int | None = None,
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

    Returns:
        BatchExportResult containing individual results and summary statistics.

    """
    batch_result = BatchExportResult()

    if not notebooks:
        return batch_result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_export_notebook, nb, output_dir, sandbox, bin_path): nb for nb in notebooks}

        for future in as_completed(futures):
            result = future.result()
            batch_result.add(result)

            if not result.success:
                error_msg = str(result.error) if result.error else "Unknown error"
                logger.error(f"Failed to export {result.notebook_path.name}: {error_msg}")

            if progress and task_id is not None:
                progress.advance(task_id)

    return batch_result


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """Run before any command and display help if no command is provided."""
    # If no command is provided, show help
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
        # Exit with code 0 to indicate success
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

    Returns:
        The rendered HTML content as a string.

    Raises:
        TemplateRenderError: If the template fails to render.
        IndexWriteError: If the index file cannot be written.

    """
    # Initialize empty lists if None is provided
    notebooks = notebooks or []
    apps = apps or []
    notebooks_wasm = notebooks_wasm or []

    total_notebooks = len(notebooks) + len(apps) + len(notebooks_wasm)
    combined_batch_result = BatchExportResult()

    if total_notebooks > 0:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[cyan]{task.completed}/{task.total}"),
        ) as progress:
            # Create progress tasks for each category
            if parallel:
                # Parallel export with combined progress
                task = progress.add_task("[green]Exporting notebooks...", total=total_notebooks)

                all_notebooks = [
                    (notebooks, output / "notebooks"),
                    (apps, output / "apps"),
                    (notebooks_wasm, output / "notebooks_wasm"),
                ]

                for nb_list, out_dir in all_notebooks:
                    if nb_list:
                        batch_result = _export_notebooks_parallel(
                            nb_list, out_dir, sandbox, bin_path, max_workers, progress, task
                        )
                        for result in batch_result.results:
                            combined_batch_result.add(result)

                if combined_batch_result.failed > 0:
                    logger.warning(
                        f"Export completed: {combined_batch_result.succeeded} succeeded, "
                        f"{combined_batch_result.failed} failed"
                    )
                    for failure in combined_batch_result.failures:
                        error_detail = str(failure.error) if failure.error else "Unknown error"
                        logger.debug(f"  - {failure.notebook_path.name}: {error_detail}")
            else:
                # Sequential export with progress bar
                task = progress.add_task("[green]Exporting notebooks...", total=total_notebooks)

                for nb in notebooks:
                    result = nb.export(output_dir=output / "notebooks", sandbox=sandbox, bin_path=bin_path)
                    combined_batch_result.add(result)
                    progress.advance(task)

                for nb in apps:
                    result = nb.export(output_dir=output / "apps", sandbox=sandbox, bin_path=bin_path)
                    combined_batch_result.add(result)
                    progress.advance(task)

                for nb in notebooks_wasm:
                    result = nb.export(output_dir=output / "notebooks_wasm", sandbox=sandbox, bin_path=bin_path)
                    combined_batch_result.add(result)
                    progress.advance(task)

                if combined_batch_result.failed > 0:
                    logger.warning(
                        f"Export completed: {combined_batch_result.succeeded} succeeded, "
                        f"{combined_batch_result.failed} failed"
                    )

    # Create the full path for the index.html file
    index_path: Path = Path(output) / "index.html"

    # Ensure the output directory exists
    Path(output).mkdir(parents=True, exist_ok=True)

    # Set up Jinja2 environment and load template
    template_dir = template_file.parent
    template_name = template_file.name

    try:
        # Create Jinja2 environment and load template
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir), autoescape=jinja2.select_autoescape(["html", "xml"])
        )
        template = env.get_template(template_name)

        # Render the template with notebook and app data
        rendered_html = template.render(
            notebooks=notebooks,
            apps=apps,
            notebooks_wasm=notebooks_wasm,
        )
    except jinja2.exceptions.TemplateError as e:
        raise TemplateRenderError(template_file, e) from e

    # Write the rendered HTML to the index.html file
    try:
        with Path.open(index_path, "w") as f:
            f.write(rendered_html)
        logger.info(f"Successfully generated index file at {index_path}")
    except OSError as e:
        raise IndexWriteError(index_path, e) from e

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
) -> str:
    """Implement the main function.

    This function contains the actual implementation of the main functionality.
    It is called by the main() function, which handles the Typer options.

    Raises:
        TemplateNotFoundError: If the template file does not exist.
        TemplateInvalidError: If the template path is not a file.
        TemplateRenderError: If the template fails to render.
        IndexWriteError: If the index file cannot be written.

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
    max_workers: int = typer.Option(4, "--max-workers", "-w", help="Maximum number of parallel workers"),
) -> None:
    """Export marimo notebooks and build an HTML index page linking to them."""
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
    max_workers: int = typer.Option(4, "--max-workers", "-w", help="Maximum number of parallel workers"),
) -> None:
    """Watch for changes and automatically re-export notebooks.

    This command watches the notebook directories and template file for changes,
    automatically re-exporting when files are modified.

    Requires the 'watchfiles' package: uv add watchfiles
    """
    try:
        from watchfiles import watch as watchfiles_watch
    except ImportError:
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
    )
    rich_print("[bold green]Initial export complete![/bold green]\n")

    # Watch for changes
    try:
        for changes in watchfiles_watch(*watch_paths):
            changed_files = [str(change[1]) for change in changes]
            rich_print("\n[bold yellow]Detected changes:[/bold yellow]")
            for f in changed_files[:5]:  # Show first 5 changed files
                rich_print(f"  [dim]{f}[/dim]")
            if len(changed_files) > 5:
                rich_print(f"  [dim]... and {len(changed_files) - 5} more[/dim]")

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
            )
            rich_print("[bold green]Export complete![/bold green]")
    except KeyboardInterrupt:
        rich_print("\n[bold green]Watch mode stopped.[/bold green]")


@app.command(name="version")
def version():
    """Show the version of Marimushka."""
    rich_print(f"[bold green]Marimushka[/bold green] version: [bold blue]{__version__}[/bold blue]")


def cli():
    """Run the CLI."""
    app()
