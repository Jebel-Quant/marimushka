# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Marimushka is a Python CLI tool for exporting [marimo](https://marimo.io) notebooks to HTML/WebAssembly format with custom Jinja2 templates. It generates an index page listing all notebooks and enables deployment to static hosting (GitHub Pages, S3, etc.) without requiring Python on the viewer's side.

## Development Commands

```bash
make install    # Create venv and install dependencies using uv
make test       # Run pytest with coverage (reports stored in _tests/)
make fmt        # Run ruff format and ruff check --fix
make deptry     # Check for missing/unused dependencies
make marimo     # Start marimo development server
make clean      # Clean artifacts and stale branches
```

## Architecture

### Core Modules (`src/marimushka/`)

**Call chain:** `cli.py` → `export.py` → `orchestrator.py` → `notebook.py`

- **`cli.py`** - CLI entry point (Typer app)
  - `cli()` → `app()` dispatches `export`, `watch`, `version` subcommands
  - `configure_logging()`: sets up loguru based on `--debug` flag
  - `watch_command()`: wraps `watchfiles` for auto re-export on file changes

- **`export.py`** - Public Python API
  - `main()`: validates template, scans notebook folders, calls `generate_index()`
  - Entry point for programmatic use: `from marimushka.export import main`

- **`orchestrator.py`** - Core export engine and template rendering
  - `generate_index()`: top-level orchestrator; exports all notebooks then renders index
  - `export_all_notebooks()`: dispatches to parallel or sequential path with Rich progress bar
  - `export_notebooks_parallel()`: ThreadPoolExecutor-based parallel export
  - `export_notebooks_sequential()`: single-threaded fallback
  - `render_template()`: Jinja2 `SandboxedEnvironment` rendering
  - `write_index_file()`: writes `index.html` with secure file permissions

- **`notebook.py`** - Notebook abstraction
  - `Kind` enum: `NB` (static HTML), `NB_WASM` (interactive edit mode), `APP` (run mode, code hidden)
  - `Notebook` dataclass: handles export via `uvx marimo export` subprocess
  - `folder2notebooks()`: scans directories for `.py` files

- **`validators.py`** - Input validation
  - `validate_template()`: checks path traversal, file existence, type, and size (10 MB limit)

- **`security.py`** - Security utilities
  - `validate_path_traversal()`, `validate_file_size()`, `validate_max_workers()`
  - `sanitize_error_message()`: redacts paths from error output
  - `safe_open_file()`, `set_secure_file_permissions()`

- **`audit.py`** - Structured audit logging
  - `AuditLogger`: logs file access, template renders, export operations as JSON
  - `get_audit_logger()`: factory returning a default logger instance

- **`config.py`** - TOML configuration
  - `MarimushkaConfig`: dataclass with all export options and sensible defaults
  - Loads from `pyproject.toml` or a custom TOML file via `from_toml()`

- **`dependencies.py`** - Dependency injection container
  - `Dependencies` dataclass: bundles `AuditLogger` + `MarimushkaConfig`
  - `create_dependencies()` / `create_test_dependencies()`: factory functions

- **`exceptions.py`** - Exception hierarchy and result types
  - `MarimushkaError` base class with specific subclasses (`TemplateNotFoundError`, `IndexWriteError`, etc.)
  - `NotebookExportResult`, `BatchExportResult`: typed result containers
  - `ProgressCallback`: type alias for progress hook `(completed, total, name) -> None`

### CLI Commands

- `marimushka export` - Export notebooks (default: parallel with 4 workers)
- `marimushka watch` - Watch mode for auto re-export on changes (requires `watchfiles`)
- `marimushka version` - Show version

### Export Types

| Kind | Export Command | Use Case |
|------|---------------|----------|
| `NB` | `marimo export html --sandbox` | Static HTML notebooks |
| `NB_WASM` | `marimo export html-wasm --mode edit --sandbox` | Interactive, editable |
| `APP` | `marimo export html-wasm --mode run --no-show-code --sandbox` | Clean app interface |

### Template System

Templates receive three lists: `notebooks`, `apps`, `notebooks_wasm`. Each notebook object has:
- `display_name` - Human-friendly name (underscores → spaces)
- `html_path` - Relative path to exported HTML
- `path` - Original `.py` file path
- `kind` - The notebook type

Default template: `src/marimushka/templates/tailwind.html.j2`

## Code Style

- **Ruff** for formatting and linting (line-length: 120, target: Python 3.11)
- **Google-style docstrings** (enforced via ruff pydocstyle)
- Full type annotations expected
- Tests in `tests/` using pytest (100% coverage target)
- Test fixtures in `tests/resources/` (apps/, notebooks/, notebooks_wasm/, templates/)

## Rhiza Framework

This project uses the Rhiza framework for standardized Python development. Key conventions:
- Dependencies managed via `pyproject.toml` using `uv add`
- Makefile includes sub-Makefiles from `tests/`, `book/`, `presentation/`, `.rhiza/`, `.github/`
- Workflow: `make install` → develop → `make test` → `make fmt`

## Documentation

| File | Purpose |
|------|---------|
| `README.md` | User guide, installation, CLI usage |
| `API.md` | Python API reference for programmatic use |
| `CHANGELOG.md` | Version history and release notes |
| `CONTRIBUTING.md` | Contribution guidelines |
| `src/marimushka/templates/README.md` | Template customization guide with examples |
