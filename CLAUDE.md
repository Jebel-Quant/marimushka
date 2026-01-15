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

- **`export.py`** - CLI entry point and export orchestration
  - `cli()` → `app()` (Typer) → `main()` → `_main_impl()` → `_generate_index()`
  - Handles template rendering with Jinja2
  - Default output: `_site/`

- **`notebook.py`** - Notebook abstraction
  - `Kind` enum: `NB` (static HTML), `NB_WASM` (interactive edit mode), `APP` (run mode, code hidden)
  - `Notebook` dataclass: handles export via `uvx marimo export` subprocess
  - `folder2notebooks()`: scans directories for `.py` files

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
| `templates/README.md` | Template customization guide with examples |
