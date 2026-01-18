# Marimushka API Reference

This document covers programmatic usage of Marimushka in Python applications.

## Installation

```bash
# Install as a dependency
uv add marimushka

# Or with pip
pip install marimushka
```

## Quick Start

```python
from marimushka.export import main

# Export with defaults
main()

# Export with custom directories
main(
    notebooks="my_notebooks",
    apps="my_apps",
    output="dist"
)
```

## Module Reference

### `marimushka.export`

The main export module containing the CLI and core export functions.

#### `main()`

High-level export function suitable for programmatic use.

```python
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
) -> str
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output` | `str \| Path` | `"_site"` | Output directory for exported files |
| `template` | `str \| Path` | Built-in Tailwind | Jinja2 template for index.html |
| `notebooks` | `str \| Path` | `"notebooks"` | Directory containing static notebooks |
| `apps` | `str \| Path` | `"apps"` | Directory containing app notebooks |
| `notebooks_wasm` | `str \| Path` | `"notebooks"` | Directory containing interactive notebooks |
| `sandbox` | `bool` | `True` | Run exports in isolated sandbox |
| `bin_path` | `str \| Path \| None` | `None` | Custom path to `uvx` executable |
| `parallel` | `bool` | `True` | Export notebooks in parallel for faster execution |
| `max_workers` | `int` | `4` | Maximum number of parallel workers |

**Returns:** Rendered HTML content as a string (empty string if no notebooks found).

**Raises:**
- `FileNotFoundError`: If the template file does not exist.
- `ValueError`: If the template path is not a file.

**Example:**

```python
from pathlib import Path
from marimushka.export import main

# Basic export
html = main(notebooks="docs/notebooks", output="public")

# Custom template with no sandbox
html = main(
    template=Path("templates/custom.html.j2"),
    notebooks="src/notebooks",
    apps="src/apps",
    notebooks_wasm="src/interactive",
    sandbox=False,
    output="dist"
)

# Check if export produced content
if html:
    print("Export successful!")
else:
    print("No notebooks found")
```

#### `cli()`

Entry point for the command-line interface. Typically not called directly.

```python
def cli() -> None
```

---

### `marimushka.notebook`

Module containing the `Notebook` class and `Kind` enum.

#### `Kind`

Enum defining notebook export types.

```python
class Kind(Enum):
    NB = "notebook"        # Static HTML export
    NB_WASM = "notebook_wasm"  # Interactive WebAssembly (edit mode)
    APP = "app"            # Application WebAssembly (run mode, code hidden)
```

**Class Methods:**

```python
# Parse string to Kind
kind = Kind.from_str("notebook")  # Returns Kind.NB
kind = Kind.from_str("app")       # Returns Kind.APP

# Raises ValueError for invalid strings
Kind.from_str("invalid")  # ValueError: Invalid Kind: 'invalid'
```

**Properties:**

```python
kind = Kind.NB

# Get marimo export command
kind.command  # ["marimo", "export", "html"]

# Get output subdirectory
kind.html_path  # Path("notebooks")
```

**Command Mapping:**

| Kind | Command |
|------|---------|
| `Kind.NB` | `marimo export html` |
| `Kind.NB_WASM` | `marimo export html-wasm --mode edit` |
| `Kind.APP` | `marimo export html-wasm --mode run --no-show-code` |

#### `Notebook`

Frozen dataclass representing a marimo notebook.

```python
@dataclass(frozen=True)
class Notebook:
    path: Path
    kind: Kind = Kind.NB
```

**Initialization:**

```python
from pathlib import Path
from marimushka.notebook import Notebook, Kind

# Create notebook instances
nb = Notebook(path=Path("notebooks/analysis.py"))
app = Notebook(path=Path("apps/dashboard.py"), kind=Kind.APP)
interactive = Notebook(path=Path("notebooks/demo.py"), kind=Kind.NB_WASM)
```

**Validation:** The constructor validates that:
- The file exists
- The path points to a file (not directory)
- The file has a `.py` extension

```python
# These raise exceptions:
Notebook(path=Path("nonexistent.py"))  # FileNotFoundError
Notebook(path=Path("somedir/"))        # ValueError: not a file
Notebook(path=Path("data.json"))       # ValueError: not a Python file
```

**Properties:**

```python
nb = Notebook(path=Path("notebooks/my_analysis.py"))

nb.display_name  # "my analysis" (underscores → spaces)
nb.html_path     # Path("notebooks/my_analysis.html")
nb.path          # Path("notebooks/my_analysis.py")
nb.kind          # Kind.NB
```

**Methods:**

```python
def export(
    self,
    output_dir: Path,
    sandbox: bool = True,
    bin_path: Path | None = None
) -> bool
```

Export the notebook to HTML/WebAssembly format.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_dir` | `Path` | required | Directory for exported HTML |
| `sandbox` | `bool` | `True` | Use sandbox mode |
| `bin_path` | `Path \| None` | `None` | Custom `uvx` location |

**Returns:** `True` if export succeeded, `False` otherwise.

```python
nb = Notebook(path=Path("notebooks/demo.py"))
success = nb.export(output_dir=Path("_site/notebooks"))

if success:
    print(f"Exported to _site/{nb.html_path}")
```

#### `folder2notebooks()`

Scan a directory for Python files and create Notebook objects.

```python
def folder2notebooks(
    folder: Path | str | None,
    kind: Kind = Kind.NB
) -> list[Notebook]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `folder` | `Path \| str \| None` | required | Directory to scan |
| `kind` | `Kind` | `Kind.NB` | Kind to assign to found notebooks |

**Returns:** List of `Notebook` objects for each `.py` file found.

```python
from marimushka.notebook import folder2notebooks, Kind

# Get all notebooks in a directory
notebooks = folder2notebooks("notebooks")
apps = folder2notebooks("apps", kind=Kind.APP)
interactive = folder2notebooks("interactive", kind=Kind.NB_WASM)

# Empty/None returns empty list
folder2notebooks(None)  # []
folder2notebooks("")    # []
```

---

## Complete Examples

### Basic Export Script

```python
#!/usr/bin/env python3
"""Export all notebooks to a static site."""

from marimushka.export import main

if __name__ == "__main__":
    html = main(
        notebooks="notebooks",
        apps="apps",
        output="_site"
    )

    if html:
        print("Export complete! Open _site/index.html")
    else:
        print("No notebooks found to export")
```

### Custom Export Pipeline

```python
#!/usr/bin/env python3
"""Custom export with preprocessing."""

from pathlib import Path
from marimushka.notebook import Notebook, Kind, folder2notebooks
from marimushka.export import _generate_index

def export_with_filter(
    notebooks_dir: str,
    apps_dir: str,
    output_dir: str,
    exclude_prefix: str = "_"
) -> None:
    """Export notebooks, excluding those starting with a prefix."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    # Get notebooks and filter
    all_notebooks = folder2notebooks(notebooks_dir, Kind.NB)
    all_apps = folder2notebooks(apps_dir, Kind.APP)

    notebooks = [nb for nb in all_notebooks if not nb.path.stem.startswith(exclude_prefix)]
    apps = [app for app in all_apps if not app.path.stem.startswith(exclude_prefix)]

    print(f"Exporting {len(notebooks)} notebooks and {len(apps)} apps")
    print(f"Excluded {len(all_notebooks) - len(notebooks) + len(all_apps) - len(apps)} items")

    # Use default template
    template = Path(__file__).parent / "templates" / "custom.html.j2"

    _generate_index(
        output=output,
        template_file=template,
        notebooks=notebooks,
        apps=apps,
        notebooks_wasm=[],
        sandbox=True
    )

if __name__ == "__main__":
    export_with_filter(
        notebooks_dir="notebooks",
        apps_dir="apps",
        output_dir="dist",
        exclude_prefix="_draft"
    )
```

### Batch Export with Progress

```python
#!/usr/bin/env python3
"""Export notebooks with progress reporting."""

from pathlib import Path
from marimushka.notebook import Notebook, Kind, folder2notebooks

def export_with_progress(source_dir: str, output_dir: str, kind: Kind) -> dict:
    """Export notebooks and return statistics."""

    notebooks = folder2notebooks(source_dir, kind)
    output = Path(output_dir)

    stats = {"total": len(notebooks), "success": 0, "failed": 0}

    for i, nb in enumerate(notebooks, 1):
        print(f"[{i}/{stats['total']}] Exporting {nb.path.name}...")

        if nb.export(output_dir=output, sandbox=True):
            stats["success"] += 1
            print(f"  ✓ Success")
        else:
            stats["failed"] += 1
            print(f"  ✗ Failed")

    return stats

if __name__ == "__main__":
    stats = export_with_progress("notebooks", "_site/notebooks", Kind.NB)
    print(f"\nCompleted: {stats['success']}/{stats['total']} successful")
```

---

## Error Handling

### Common Exceptions

```python
from pathlib import Path
from marimushka.notebook import Notebook, Kind

# FileNotFoundError - file doesn't exist
try:
    nb = Notebook(path=Path("nonexistent.py"))
except FileNotFoundError as e:
    print(f"File not found: {e}")

# ValueError - invalid file type or path
try:
    nb = Notebook(path=Path("data.json"))
except ValueError as e:
    print(f"Invalid notebook: {e}")

# ValueError - invalid Kind string
try:
    kind = Kind.from_str("invalid")
except ValueError as e:
    print(f"Invalid kind: {e}")
```

### Export Failures

The `export()` method returns `False` on failure rather than raising exceptions:

```python
nb = Notebook(path=Path("notebooks/broken.py"))

if not nb.export(output_dir=Path("_site")):
    # Check logs for details (uses loguru)
    print("Export failed - check logs for details")
```

---

## Integration Examples

### With pytest

```python
# test_export.py
import pytest
from pathlib import Path
from marimushka.notebook import Notebook, Kind


def test_notebook_display_name():
    nb = Notebook(path=Path("tests/resources/marimo/notebooks/my_notebook.py"))
    assert nb.display_name == "my notebook"


def test_notebook_html_path():
    nb = Notebook(path=Path("tests/resources/marimo/notebooks/demo.py"), kind=Kind.APP)
    assert nb.html_path == Path("apps/demo.html")
```

### With GitHub Actions

```yaml
- name: Export notebooks
  run: |
    python -c "
    from marimushka.export import main
    main(notebooks='docs/notebooks', apps='docs/apps', output='_site')
    "
```

---

## CLI Commands

### Export Command

```bash
uvx marimushka export [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--output, -o` | `_site` | Output directory |
| `--template, -t` | Built-in Tailwind | Template file path |
| `--notebooks, -n` | `notebooks` | Notebooks directory |
| `--apps, -a` | `apps` | Apps directory |
| `--notebooks-wasm, -nw` | `notebooks_wasm` | Interactive notebooks directory |
| `--sandbox/--no-sandbox` | `--sandbox` | Enable/disable sandbox mode |
| `--parallel/--no-parallel` | `--parallel` | Enable/disable parallel export |
| `--max-workers, -w` | `4` | Number of parallel workers |

### Watch Command

Watch for file changes and automatically re-export:

```bash
uvx marimushka watch [OPTIONS]
```

Requires the `watchfiles` package:

```bash
# Install with watch support
uv add marimushka[watch]

# Or install watchfiles separately
uv add watchfiles
```

The watch command accepts the same options as `export` and will:
1. Run an initial export
2. Watch notebook directories and template for changes
3. Automatically re-export when files change

---

## Version

```python
from marimushka import __version__

print(f"Marimushka version: {__version__}")
```
