"""Build the script for marimo notebooks.

This script exports marimo notebooks to HTML/WebAssembly format and generates
an index.html file that lists all the notebooks. It handles both regular notebooks
(from the notebooks/ directory) and apps (from the apps/ directory).

The script can be run from the command line with optional arguments:
    uvx marimushka [--output-dir OUTPUT_DIR]

The exported files will be placed in the specified output directory (default: _site).
"""

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "jinja2==3.1.3",
#     "typer==0.16.0",
#     "loguru==0.7.0"
# ]
# ///

from pathlib import Path

import jinja2
import typer
from loguru import logger
from rich import print as rich_print

from . import __version__
from .notebook import Kind, Notebook, folder2notebooks

app = typer.Typer(help=f"Marimushka - Export marimo notebooks in style. Version: {__version__}")


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
) -> str:
    """Generate an index.html file that lists all the notebooks.

    This function creates an HTML index page that displays links to all the exported
    notebooks. The index page includes the marimo logo and displays each notebook
    with a formatted title and a link to open it.

    Args:
        notebooks_wasm:
        notebooks (List[Notebook]): List of notebooks with data for notebooks
        apps (List[Notebook]): List of notebooks with data for apps
        notebooks_wasm (List[Notebook]): List of notebooks with data for notebooks_wasm
        output (Path): Directory where the index.html file will be saved
        template_file (Path, optional): Path to the template file. If None, uses the default template.

    Returns:
        str: The rendered HTML content as a string

    """
    # Initialize empty lists if None is provided
    notebooks = notebooks or []
    apps = apps or []
    notebooks_wasm = notebooks_wasm or []

    # Export notebooks to WebAssembly
    for nb in notebooks:
        nb.export(output_dir=output / "notebooks")

    # Export apps to WebAssembly
    for nb in apps:
        nb.export(output_dir=output / "apps")

    for nb in notebooks_wasm:
        nb.export(output_dir=output / "notebooks_wasm")

    # Create the full path for the index.html file
    index_path: Path = Path(output) / "index.html"

    # Ensure the output directory exists
    Path(output).mkdir(parents=True, exist_ok=True)

    # Set up Jinja2 environment and load template
    template_dir = template_file.parent
    template_name = template_file.name

    rendered_html = ""
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

        # Write the rendered HTML to the index.html file
        try:
            with Path.open(index_path, "w") as f:
                f.write(rendered_html)
            logger.info(f"Successfully generated index file at {index_path}")
        except OSError as e:
            logger.error(f"Error writing index file to {index_path}: {e}")
    except jinja2.exceptions.TemplateError as e:
        logger.error(f"Error rendering template {template_file}: {e}")

    return rendered_html


def _main_impl(
    output: str | Path, template: str | Path, notebooks: str | Path, apps: str | Path, notebooks_wasm: str | Path
) -> str:
    """Implement the main function.

    This function contains the actual implementation of the main functionality.
    It is called by the main() function, which handles the Typer options.
    """
    logger.info("Starting marimushka build process")
    logger.info(f"Version of Marimushka: {__version__}")
    output = output or "_site"

    # Convert output_dir explicitly to Path
    output_dir: Path = Path(output)
    logger.info(f"Output directory: {output_dir}")

    # Make sure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert template to Path if provided
    template_file: Path = Path(template)
    logger.info(f"Using template file: {template_file}")
    logger.info(f"Notebooks: {notebooks}")
    logger.info(f"Apps: {apps}")
    logger.info(f"Notebooks-wasm: {notebooks_wasm}")

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
    )


def main(
    output: str | Path = "_site",
    template: str | Path = Path(__file__).parent / "templates" / "tailwind.html.j2",
    notebooks: str | Path = "notebooks",
    apps: str | Path = "apps",
    notebooks_wasm: str | Path = "notebooks",
) -> str:
    """Call the implementation function with the provided parameters and return its result.

    Parameters
    ----------
    output: str | Path
        The output directory where generated files will be stored.
        Defaults to "_site".
    template: str | Path
        Path to the template file used during the generation process.
        Defaults to a predefined "tailwind.html.j2" file.
    notebooks: str | Path
        Directory containing the notebooks to be processed.
        Defaults to "notebooks".
    apps: str | Path
        Directory containing application files. Defaults to "apps".
    notebooks_wasm: str | Path
        Directory containing WebAssembly-related files for notebooks.
        Defaults to "notebooks".

    Returns:
    -------
    str
        The result returned by the implementation function, representing the
        completion of the generation process or final outcome.

    """
    # Call the implementation function with the provided parameters and return its result
    return _main_impl(output=output, template=template, notebooks=notebooks, apps=apps, notebooks_wasm=notebooks_wasm)


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
) -> None:
    """Export marimo notebooks and build an HTML index page linking to them."""
    # When called through Typer, the parameters might be typer.Option objects
    # Extract the default values from the Option objects if necessary
    output_val = getattr(output, "default", output)
    template_val = getattr(template, "default", template)
    notebooks_val = getattr(notebooks, "default", notebooks)
    apps_val = getattr(apps, "default", apps)
    notebooks_wasm_val = getattr(notebooks_wasm, "default", notebooks_wasm)

    # Call the main function with the resolved parameter values
    main(
        output=output_val,
        template=template_val,
        notebooks=notebooks_val,
        apps=apps_val,
        notebooks_wasm=notebooks_wasm_val,
    )


@app.command(name="version")
def version():
    """Show the version of Marimushka."""
    rich_print(f"[bold green]Marimushka[/bold green] version: [bold blue]{__version__}[/bold blue]")


def cli():
    """Run the CLI."""
    app()
