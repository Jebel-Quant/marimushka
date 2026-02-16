"""Export module providing the public Python API.

This module provides the main Python API for exporting marimo notebooks.
For CLI usage, see the cli module.

Example::

    # Python API
    from marimushka.export import main
    main(notebooks="notebooks", apps="apps", output="_site")

The exported files will be placed in the specified output directory (default: _site).
"""

from pathlib import Path

from loguru import logger

from . import __version__
from .audit import get_audit_logger
from .exceptions import ProgressCallback
from .notebook import Kind, folder2notebooks
from .orchestrator import generate_index
from .validators import validate_template


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
    on_progress: ProgressCallback | None = None,
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
        on_progress: Optional callback for progress tracking. Called after each notebook export
                    with signature: on_progress(completed, total, notebook_name).

    Returns:
        Rendered HTML content as string, empty if no notebooks found.

    Raises:
        TemplateNotFoundError: If the template file does not exist.
        TemplateInvalidError: If the template path is not a file.
        TemplateRenderError: If the template fails to render.
        IndexWriteError: If the index file cannot be written.

    Example:
        >>> from marimushka.export import main
        >>>
        >>> # Simple usage
        >>> main(notebooks="my-notebooks", apps="my-apps")
        >>>
        >>> # With progress callback
        >>> def progress_handler(completed, total, name):
        ...     print(f"[{completed}/{total}] Exported {name}")
        >>>
        >>> main(notebooks="my-notebooks", on_progress=progress_handler)

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
    audit_logger = get_audit_logger()
    validate_template(template_file, audit_logger)

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

    return generate_index(
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
        on_progress=on_progress,
        audit_logger=audit_logger,
    )
