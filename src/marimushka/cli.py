"""Command-line interface for marimushka.

This module provides the CLI commands for exporting marimo notebooks,
watching for changes, and displaying version information.
"""

import sys
from pathlib import Path

import typer
from loguru import logger
from rich import print as rich_print

from . import __version__

# Global state for debug mode
_debug_mode = False

# Configure logger
logger.configure(extra={"subprocess": ""})
logger.remove()


def configure_logging(debug: bool = False) -> None:
    """Configure logging based on debug mode.

    Args:
        debug: Whether to enable debug mode.

    """
    global _debug_mode
    _debug_mode = debug

    # Remove existing handlers
    logger.remove()

    if debug:
        # Debug mode: show all logs including DEBUG level
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<magenta>{extra[subprocess]}</magenta><level>{message}</level>",
            level="DEBUG",
        )
        logger.debug("Debug mode enabled - showing all log messages")
    else:
        # Normal mode: show INFO and above
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<magenta>{extra[subprocess]}</magenta><level>{message}</level>",
            level="INFO",
        )


# Initial configuration with default settings
configure_logging(debug=False)

# Maximum number of changed files to display in watch mode
_MAX_CHANGED_FILES_TO_DISPLAY = 5

app = typer.Typer(help=f"Marimushka - Export marimo notebooks in style. Version: {__version__}")


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


@app.command(name="export")
def export_command(
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
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode with verbose logging"),
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

        # Enable debug mode for troubleshooting
        $ marimushka export --debug

    """
    # Configure logging based on debug flag
    configure_logging(debug=debug)

    from .export import main

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
def watch_command(
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
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode with verbose logging"),
) -> None:
    """Watch for changes and automatically re-export notebooks.

    This command watches the notebook directories and template file for changes,
    automatically re-exporting when files are modified.

    Requires the 'watchfiles' package: uv add watchfiles

    Example usage:
        # Basic watch mode
        $ marimushka watch

        # Watch with custom directories
        $ marimushka watch -n my_notebooks -a my_apps

        # Watch with debug logging
        $ marimushka watch --debug
    """
    # Configure logging based on debug flag
    configure_logging(debug=debug)

    try:
        from watchfiles import watch as watchfiles_watch
    except ImportError:  # pragma: no cover
        rich_print("[bold red]Error:[/bold red] watchfiles package is required for watch mode.")
        rich_print("Install it with: [cyan]uv add watchfiles[/cyan]")
        raise typer.Exit(1) from None

    from .export import main

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
def version_command() -> None:
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
