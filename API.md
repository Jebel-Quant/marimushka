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

## Dependency Injection

Marimushka uses dependency injection to make testing easier and allow customization of core components. This section explains how to use the dependency injection system.

### Overview

The dependency injection container (`Dependencies`) encapsulates injectable components:

- `audit_logger`: Logs security-relevant events (path validation, exports, template rendering)
- `config`: Configuration settings (output paths, worker counts, timeouts, security settings)

### Basic Usage

```python
from pathlib import Path
from marimushka.dependencies import create_dependencies
from marimushka.orchestrator import generate_index
from marimushka.notebook import folder2notebooks, Kind

# Create dependencies with defaults
deps = create_dependencies()

# Use with lower-level functions
notebooks = folder2notebooks("notebooks", Kind.NB)
html = generate_index(
    output=Path("_site"),
    template_file=Path("template.html.j2"),
    notebooks=notebooks,
    audit_logger=deps.audit_logger  # Inject audit logger
)
```

### Custom Audit Logging

```python
from pathlib import Path
from marimushka.dependencies import create_dependencies
from marimushka.audit import AuditLogger
from marimushka.orchestrator import generate_index

# Create dependencies with custom audit log file
deps = create_dependencies(audit_log=Path("custom_audit.log"))

# Or create custom audit logger
custom_logger = AuditLogger(
    enabled=True,
    log_file=Path("security_audit.log")
)
deps = deps.with_audit_logger(custom_logger)

# Use in export
html = generate_index(
    ...,
    audit_logger=deps.audit_logger
)

# Audit log contains JSON entries for all security events
# Example log entry:
# {"timestamp": "2025-01-20T10:30:45Z", "event_type": "export", "success": true, ...}
```

### Configuration-Based Dependencies

```python
from pathlib import Path
from marimushka.dependencies import create_dependencies_from_config_file
from marimushka.config import MarimushkaConfig
from marimushka.export import main

# Load from TOML config file
deps = create_dependencies_from_config_file(Path(".marimushka.toml"))

# Use configuration
html = main(
    output=deps.config.output,
    notebooks=deps.config.notebooks,
    apps=deps.config.apps,
    max_workers=deps.config.max_workers,
    timeout=deps.config.timeout
)

# Or create custom config
config = MarimushkaConfig(
    output="_site",
    notebooks="notebooks",
    apps="apps",
    max_workers=8,
    timeout=600,
    parallel=True,
    sandbox=True
)
deps = create_dependencies(config=config)
```

### Testing with Dependencies

```python
from pathlib import Path
from marimushka.dependencies import create_test_dependencies

def test_export(tmp_path):
    """Test export with isolated dependencies."""
    # Create test dependencies with audit logging to temp dir
    deps = create_test_dependencies(tmp_path)

    # Use in test
    from marimushka.orchestrator import generate_index
    html = generate_index(
        output=tmp_path / "output",
        template_file=Path("template.html.j2"),
        notebooks=[],
        audit_logger=deps.audit_logger
    )

    # Verify audit log was created
    audit_log = tmp_path / "test_audit.log"
    assert audit_log.exists()
```

### Immutable Updates

The `Dependencies` class supports immutable updates:

```python
from marimushka.dependencies import Dependencies
from marimushka.audit import AuditLogger
from marimushka.config import MarimushkaConfig

# Create base dependencies
deps = Dependencies()

# Create new instance with different audit logger
new_logger = AuditLogger(log_file=Path("new_audit.log"))
new_deps = deps.with_audit_logger(new_logger)

# Original unchanged
assert deps.audit_logger != new_logger
assert new_deps.audit_logger == new_logger

# Create new instance with different config
new_config = MarimushkaConfig(max_workers=16)
final_deps = new_deps.with_config(new_config)
```

### Factory Functions

Marimushka provides several factory functions for creating dependencies:

#### `create_dependencies()`

Creates dependencies with optional customization:

```python
from pathlib import Path
from marimushka.dependencies import create_dependencies
from marimushka.config import MarimushkaConfig

# Simplest: all defaults
deps = create_dependencies()

# With audit log file
deps = create_dependencies(audit_log=Path("audit.log"))

# With custom config
config = MarimushkaConfig(max_workers=8, timeout=900)
deps = create_dependencies(config=config)

# With both
deps = create_dependencies(
    audit_log=Path("audit.log"),
    config=MarimushkaConfig(parallel=True, max_workers=16)
)
```

#### `create_dependencies_from_config_file()`

Loads configuration from TOML file:

```python
from pathlib import Path
from marimushka.dependencies import create_dependencies_from_config_file

# Load from config file
deps = create_dependencies_from_config_file(Path(".marimushka.toml"))

# Override audit log path
deps = create_dependencies_from_config_file(
    config_path=Path(".marimushka.toml"),
    audit_log=Path("custom_audit.log")
)
```

Example `.marimushka.toml`:

```toml
[marimushka]
output = "_site"
notebooks = "notebooks"
apps = "apps"
notebooks_wasm = "notebooks_wasm"
max_workers = 8
timeout = 600
parallel = true
sandbox = true

[marimushka.security]
audit_enabled = true
audit_log = "audit.log"
max_file_size_mb = 10
file_permissions = "0o644"
```

#### `create_test_dependencies()`

Creates dependencies suitable for testing:

```python
from pathlib import Path
from marimushka.dependencies import create_test_dependencies

def test_something(tmp_path):
    # Creates audit logger in tmp_path/test_audit.log
    deps = create_test_dependencies(tmp_path)

    # Use deps in test...
    assert deps.audit_logger.log_file == tmp_path / "test_audit.log"
    assert deps.config.max_workers == 4  # Default config
```

### Integration with Lower-Level Functions

Most lower-level functions accept optional `audit_logger` parameter:

```python
from marimushka.dependencies import create_dependencies
from marimushka.orchestrator import (
    generate_index,
    render_template,
    write_index_file
)
from marimushka.validators import validate_template
from marimushka.notebook import Notebook

# Create dependencies
deps = create_dependencies()

# Validate template with audit logging
validate_template(template_path, deps.audit_logger)

# Render template with audit logging
html = render_template(
    template_file,
    notebooks,
    apps,
    notebooks_wasm,
    deps.audit_logger
)

# Write index with audit logging
write_index_file(index_path, html, deps.audit_logger)

# Export notebook with audit logging
notebook = Notebook(notebook_path)
result = notebook.export(
    output_dir=output_dir,
    audit_logger=deps.audit_logger
)
```

### Best Practices

1. **Use factory functions**: Prefer `create_dependencies()` over direct construction
2. **Inject explicitly**: Pass dependencies to functions rather than using globals
3. **Test with isolation**: Use `create_test_dependencies()` for test isolation
4. **Immutable updates**: Use `with_*()` methods instead of modifying in place
5. **Configuration files**: Use `.marimushka.toml` for project-level settings
6. **Audit logging**: Enable audit logging in production for security monitoring

### Example: Custom Export Pipeline

```python
from pathlib import Path
from marimushka.dependencies import create_dependencies
from marimushka.config import MarimushkaConfig
from marimushka.audit import AuditLogger
from marimushka.notebook import folder2notebooks, Kind
from marimushka.orchestrator import generate_index

# Step 1: Create custom configuration
config = MarimushkaConfig(
    output="_site",
    notebooks="notebooks",
    apps="apps",
    max_workers=8,
    timeout=900,
    parallel=True,
    sandbox=True,
    audit_enabled=True
)

# Step 2: Create custom audit logger
audit_logger = AuditLogger(
    enabled=True,
    log_file=Path("production_audit.log")
)

# Step 3: Create dependencies
deps = create_dependencies(config=config)
deps = deps.with_audit_logger(audit_logger)

# Step 4: Discover notebooks
notebooks = folder2notebooks(config.notebooks, Kind.NB)
apps = folder2notebooks(config.apps, Kind.APP)
notebooks_wasm = folder2notebooks(config.notebooks_wasm, Kind.NB_WASM)

# Step 5: Generate index with dependency injection
html = generate_index(
    output=Path(config.output),
    template_file=Path("templates/custom.html.j2"),
    notebooks=notebooks,
    apps=apps,
    notebooks_wasm=notebooks_wasm,
    sandbox=config.sandbox,
    parallel=config.parallel,
    max_workers=config.max_workers,
    timeout=config.timeout,
    audit_logger=deps.audit_logger
)

print(f"Exported {len(notebooks)} notebooks")
print(f"Audit log: {audit_logger.log_file}")
```

### See Also

- [ADR-001: Module Structure Refactoring](docs/adr/ADR-001-module-structure-refactoring.md) - Architecture decisions
- [`Dependencies` class documentation](src/marimushka/dependencies.py) - Full API reference
- [`AuditLogger` class documentation](src/marimushka/audit.py) - Audit logging details
- [`MarimushkaConfig` class documentation](src/marimushka/config.py) - Configuration options

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

**Examples:**

```python
from pathlib import Path
from marimushka.export import main

# Example 1: Basic export with defaults
html = main(notebooks="docs/notebooks", output="public")

# Example 2: Custom template with no sandbox
html = main(
    template=Path("templates/custom.html.j2"),
    notebooks="src/notebooks",
    apps="src/apps",
    notebooks_wasm="src/interactive",
    sandbox=False,
    output="dist"
)

# Example 3: Sequential export (slower but less memory intensive)
html = main(
    notebooks="large_notebooks",
    output="_site",
    parallel=False  # Disables parallel processing
)

# Example 4: High-performance parallel export
html = main(
    notebooks="notebooks",
    apps="apps",
    notebooks_wasm="interactive",
    output="_site",
    parallel=True,
    max_workers=8  # More workers for faster export on multi-core systems
)

# Example 5: Check if export produced content
if html:
    print("Export successful!")
else:
    print("No notebooks found")
```

**Edge Cases:**

- **Empty directories**: Returns empty string (`""`) without error if all directories are empty.
- **Missing directories**: Silently skips non-existent directories (no error raised).
- **Invalid template**: Raises `FileNotFoundError` if template doesn't exist, `ValueError` if not a file.
- **Permission errors**: Fails during export if output directory is not writable (returns empty string).
- **Corrupted notebooks**: Notebooks with syntax errors fail silently; check logs for details.
- **Large notebooks**: Memory usage scales with `max_workers` × notebook size. Reduce `max_workers` if OOM errors occur.
- **Conflicting filenames**: If notebooks have identical names across directories, later exports overwrite earlier ones.

**Performance:**

- **Parallel export**: With `parallel=True` (default), exports are ~4x faster on multi-core systems.
- **Worker tuning**: Optimal `max_workers` ≈ CPU cores. Beyond 8 workers shows diminishing returns.
- **Sequential mode**: Use `parallel=False` for memory-constrained environments or debugging.
- **Benchmark**: Typical export times (4 workers, 8-core system):
  - 10 notebooks: ~5 seconds
  - 50 notebooks: ~20 seconds
  - 100 notebooks: ~40 seconds
- **Bottleneck**: Export time is dominated by `marimo export` subprocess calls, not file I/O.

**See Also:**

- [`Notebook.export()`](#notebook) - Low-level export method for individual notebooks
- [`folder2notebooks()`](#folder2notebooks) - Scan directories for notebooks
- [`_generate_index()`](#complete-examples) - Template rendering (used in custom pipelines)

#### `cli()`

Entry point for the command-line interface. Typically not called directly.

```python
def cli() -> None
```

**Examples:**

```python
# Example 1: Call programmatically (unusual, but possible)
from marimushka.export import cli

cli()  # Runs the Typer CLI interface

# Example 2: Use in custom CLI wrapper
import sys
from marimushka.export import cli

if __name__ == "__main__":
    # Add custom pre-processing
    print("Starting Marimushka export...")
    cli()
    print("Export complete!")

# Example 3: Typically invoked via command line (recommended)
# $ uvx marimushka export --help
```

**Edge Cases:**

- **Programmatic use**: Prefer `main()` over `cli()` for programmatic access (avoids argument parsing).
- **Exit behavior**: Calls `sys.exit()` on errors, which terminates the process (not ideal for embedded use).
- **Argument conflicts**: CLI argument parsing may conflict with your application's arguments if called programmatically.

**Performance:**

- Identical to `main()` performance; adds minimal overhead for argument parsing (~1ms).

**See Also:**

- [`main()`](#main) - High-level export function (preferred for programmatic use)
- [CLI Commands](#cli-commands) - Full CLI documentation

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
# Example 1: Parse string to Kind
kind = Kind.from_str("notebook")  # Returns Kind.NB
kind = Kind.from_str("app")       # Returns Kind.APP

# Example 2: Case-sensitive parsing
kind = Kind.from_str("notebook_wasm")  # Returns Kind.NB_WASM

# Example 3: Error handling
try:
    kind = Kind.from_str("invalid")
except ValueError as e:
    print(f"Invalid kind: {e}")  # ValueError: Invalid Kind: 'invalid'

# Example 4: Use in dynamic configuration
config = {"type": "app"}
kind = Kind.from_str(config["type"])
```

**Edge Cases:**

- **Case sensitivity**: `from_str()` is case-sensitive. `"App"` or `"APP"` will raise `ValueError`.
- **Whitespace**: Leading/trailing whitespace is not stripped. `" notebook "` raises `ValueError`.
- **Empty string**: Raises `ValueError` for empty string.
- **Type confusion**: Only accepts strings; passing `Kind.NB` to `from_str()` raises `AttributeError`.

**Properties:**

```python
# Example 1: Get marimo export command
kind = Kind.NB
kind.command  # ["marimo", "export", "html"]

# Example 2: Get output subdirectory
kind = Kind.NB
kind.html_path  # Path("notebooks")

# Example 3: Build custom export command
kind = Kind.APP
base_cmd = kind.command
custom_cmd = base_cmd + ["--sandbox"]  # ["marimo", "export", "html-wasm", "--mode", "run", "--no-show-code", "--sandbox"]

# Example 4: Determine output location
kind = Kind.NB_WASM
output_dir = Path("_site") / kind.html_path  # Path("_site/notebooks")
```

**Command Mapping:**

| Kind | Command |
|------|---------|
| `Kind.NB` | `marimo export html` |
| `Kind.NB_WASM` | `marimo export html-wasm --mode edit` |
| `Kind.APP` | `marimo export html-wasm --mode run --no-show-code` |

**Edge Cases:**

- **Command immutability**: `command` returns a new list each time; modifying it doesn't affect the Kind.
- **Path behavior**: `html_path` returns a `Path` object; string operations require conversion to string.

**Performance:**

- Property access is O(1) and negligible overhead.

**See Also:**

- [`Notebook.export()`](#notebook) - Uses `Kind.command` internally
- [Command Mapping Table](#command-mapping) - Full command reference

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

# Example 1: Basic notebook creation
nb = Notebook(path=Path("notebooks/analysis.py"))

# Example 2: Create app notebook
app = Notebook(path=Path("apps/dashboard.py"), kind=Kind.APP)

# Example 3: Interactive WebAssembly notebook
interactive = Notebook(path=Path("notebooks/demo.py"), kind=Kind.NB_WASM)

# Example 4: Using string paths (automatically converted to Path)
nb = Notebook(path="notebooks/report.py")

# Example 5: Complex type annotation usage
from typing import List

notebooks: List[Notebook] = [
    Notebook(path=Path("notebooks/intro.py")),
    Notebook(path=Path("notebooks/analysis.py"), kind=Kind.NB),
]
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

**Edge Cases:**

- **Relative vs absolute paths**: Both work; relative paths are resolved from current working directory.
- **Symlinks**: Followed transparently; the target file must exist and be a `.py` file.
- **Case sensitivity**: Path validation is OS-dependent (case-insensitive on macOS/Windows, sensitive on Linux).
- **Unicode filenames**: Fully supported; e.g., `Notebook(path=Path("notebooks/分析.py"))` is valid.
- **Spaces in paths**: Handled correctly; e.g., `Path("my notebooks/analysis.py")` works.
- **Hidden files**: Files starting with `.` (e.g., `.hidden.py`) are valid notebooks.
- **Frozen dataclass**: Cannot modify attributes after creation; use `dataclasses.replace()` for copies:
  ```python
  from dataclasses import replace
  nb2 = replace(nb, kind=Kind.APP)
  ```

**Properties:**

```python
# Example 1: Basic property access
nb = Notebook(path=Path("notebooks/my_analysis.py"))
nb.display_name  # "my analysis" (underscores → spaces)
nb.html_path     # Path("notebooks/my_analysis.html")
nb.path          # Path("notebooks/my_analysis.py")
nb.kind          # Kind.NB

# Example 2: Display name transformations
nb = Notebook(path=Path("notebooks/multi_word_notebook.py"))
nb.display_name  # "multi word notebook"

# Example 3: HTML path changes with Kind
nb_static = Notebook(path=Path("demo.py"), kind=Kind.NB)
nb_static.html_path  # Path("notebooks/demo.html")

nb_app = Notebook(path=Path("demo.py"), kind=Kind.APP)
nb_app.html_path  # Path("apps/demo.html")

# Example 4: Use in templates
notebooks = [Notebook(path=Path(f"notebooks/nb{i}.py")) for i in range(3)]
for nb in notebooks:
    print(f"<a href='{nb.html_path}'>{nb.display_name}</a>")
```

**Edge Cases:**

- **Display name**: Only stem (filename without extension) is transformed. Directory names are not included.
- **Multiple underscores**: Consecutive underscores become single spaces: `"a__b.py"` → `"a b"`.
- **Leading/trailing underscores**: Preserved in display name: `"_private.py"` → `"_private"`.
- **HTML path**: Always relative; includes kind-specific subdirectory (e.g., `notebooks/`, `apps/`).
- **Non-ASCII characters**: Preserved in `display_name` and `html_path`.

**Performance:**

- All properties are computed on-demand (not cached), but overhead is negligible (< 1μs per access).

**See Also:**

- [`Kind.html_path`](#kind) - Determines subdirectory in `html_path`
- [`export()`](#methods) - Uses `html_path` for output location

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

**Examples:**

```python
# Example 1: Basic export
nb = Notebook(path=Path("notebooks/demo.py"))
success = nb.export(output_dir=Path("_site"))

if success:
    print(f"Exported to _site/{nb.html_path}")

# Example 2: Export without sandbox (faster, less isolated)
nb = Notebook(path=Path("notebooks/analysis.py"))
success = nb.export(output_dir=Path("dist"), sandbox=False)

# Example 3: Custom uvx path
nb = Notebook(path=Path("notebooks/report.py"))
success = nb.export(
    output_dir=Path("_site"),
    bin_path=Path("/custom/bin/uvx")
)

# Example 4: Batch export with error handling
from pathlib import Path
from marimushka.notebook import folder2notebooks

notebooks = folder2notebooks("notebooks")
failed = []

for nb in notebooks:
    if not nb.export(output_dir=Path("_site")):
        failed.append(nb.path)

if failed:
    print(f"Failed to export: {failed}")
```

**Edge Cases:**

- **Output directory creation**: Automatically creates `output_dir` and subdirectories if they don't exist.
- **Existing files**: Overwrites existing HTML files without warning.
- **Permission errors**: Returns `False` if cannot write to `output_dir`.
- **Invalid notebooks**: Returns `False` for notebooks with syntax errors; check logs for details.
- **Missing marimo**: Returns `False` if `marimo` is not available via `uvx`.
- **Network errors**: WASM exports may fail if CDN resources are unavailable (rare).
- **Subprocess timeout**: Very large notebooks may timeout; no timeout is enforced by default.

**Performance:**

- **Export time**: Varies by notebook size and Kind:
  - `Kind.NB`: ~500ms - 2s per notebook
  - `Kind.NB_WASM` / `Kind.APP`: ~1s - 3s per notebook (WASM compilation overhead)
- **Sandbox overhead**: `sandbox=True` adds ~100-200ms per export for isolation setup.
- **Parallel exports**: Use `ThreadPoolExecutor` or `main(parallel=True)` for batching (see examples).
- **Memory**: Peak memory usage ~50-100 MB per export (subprocess overhead).

**See Also:**

- [`main()`](#main) - High-level export with automatic parallelization
- [`folder2notebooks()`](#folder2notebooks) - Get all notebooks in a directory
- [`Kind.command`](#kind) - Export command used internally

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

**Examples:**

```python
from marimushka.notebook import folder2notebooks, Kind
from pathlib import Path

# Example 1: Get all notebooks in a directory
notebooks = folder2notebooks("notebooks")
apps = folder2notebooks("apps", kind=Kind.APP)
interactive = folder2notebooks("interactive", kind=Kind.NB_WASM)

# Example 2: Empty/None returns empty list
folder2notebooks(None)  # []
folder2notebooks("")    # []

# Example 3: Use Path objects
notebooks = folder2notebooks(Path("my_notebooks"))

# Example 4: Filter results
all_notebooks = folder2notebooks("notebooks")
public_notebooks = [nb for nb in all_notebooks if not nb.path.stem.startswith("_")]

# Example 5: Recursive scanning (manual)
from pathlib import Path

all_nbs = []
for subdir in Path("notebooks").rglob("*"):
    if subdir.is_dir():
        all_nbs.extend(folder2notebooks(subdir))

# Example 6: Count notebooks by type
notebooks = folder2notebooks("notebooks", kind=Kind.NB)
apps = folder2notebooks("apps", kind=Kind.APP)
wasm_nbs = folder2notebooks("interactive", kind=Kind.NB_WASM)

print(f"Found {len(notebooks)} notebooks, {len(apps)} apps, {len(wasm_nbs)} interactive notebooks")
```

**Edge Cases:**

- **Non-existent directory**: Returns empty list `[]` without raising an error.
- **Empty directory**: Returns empty list `[]`.
- **Non-directory path**: Raises `NotADirectoryError` if path is a file.
- **Permission errors**: Silently skips directories without read permission (returns `[]`).
- **Non-Python files**: Ignores files without `.py` extension (e.g., `.pyc`, `.txt`).
- **Subdirectories**: Only scans the top level; does not recurse into subdirectories.
- **Hidden files**: Includes files starting with `.` (e.g., `.hidden.py`).
- **Symbolic links**: Follows symlinks to directories; scans target directory.
- **Invalid notebooks**: Includes all `.py` files; validation happens during `Notebook()` construction or `export()`.

**Performance:**

- **Scan speed**: ~1000 files/sec on typical filesystems (SSD).
- **Memory**: Minimal; only stores `Path` objects, not file contents.
- **Complexity**: O(n) where n = number of files in directory.
- **Optimization**: For large directories (>1000 files), consider filtering at filesystem level:
  ```python
  # Faster than scanning all files
  notebooks = [Notebook(path=p, kind=Kind.NB) for p in Path("notebooks").glob("*.py")]
  ```

**See Also:**

- [`Notebook`](#notebook) - Individual notebook representation
- [`main()`](#main) - Uses `folder2notebooks()` internally to discover notebooks
- [Custom Export Pipeline](#custom-export-pipeline) - Advanced filtering examples

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

**Performance:** ~5-40 seconds for 10-100 notebooks with default settings (4 workers).

**See Also:**

- [`main()`](#main) - Full parameter documentation
- [Watch Command](#watch-command) - Auto-export on file changes

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

**Edge Cases:**

- **Empty result after filtering**: `_generate_index()` creates an empty index.html if all notebooks are filtered out.
- **Missing template**: Raises `FileNotFoundError` if custom template doesn't exist.

**Performance:** Filtering is O(n) where n = total notebooks; minimal overhead (<1ms per notebook).

**See Also:**

- [`folder2notebooks()`](#folder2notebooks) - Scan directories for notebooks
- [Batch Export with Progress](#batch-export-with-progress) - Progress reporting example

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

**Edge Cases:**

- **Empty directory**: Returns `{"total": 0, "success": 0, "failed": 0}` without error.
- **All exports fail**: `success` remains 0; consider logging failed notebooks for debugging.

**Performance:** Sequential export (1 notebook at a time). For faster export, use `main(parallel=True)`.

**See Also:**

- [`main()`](#main) - Built-in parallel export with progress bar
- [`Notebook.export()`](#methods) - Low-level export method

---

## Error Handling

### Common Exceptions

```python
from pathlib import Path
from marimushka.notebook import Notebook, Kind

# Example 1: FileNotFoundError - file doesn't exist
try:
    nb = Notebook(path=Path("nonexistent.py"))
except FileNotFoundError as e:
    print(f"File not found: {e}")

# Example 2: ValueError - invalid file type
try:
    nb = Notebook(path=Path("data.json"))
except ValueError as e:
    print(f"Invalid notebook: {e}")

# Example 3: ValueError - path is a directory
try:
    nb = Notebook(path=Path("notebooks/"))
except ValueError as e:
    print(f"Invalid path: {e}")

# Example 4: ValueError - invalid Kind string
try:
    kind = Kind.from_str("invalid")
except ValueError as e:
    print(f"Invalid kind: {e}")

# Example 5: Template validation errors
from marimushka.export import main

try:
    main(template=Path("missing_template.html.j2"))
except FileNotFoundError as e:
    print(f"Template not found: {e}")

try:
    main(template=Path("templates/"))  # Directory, not file
except ValueError as e:
    print(f"Invalid template: {e}")
```

**Edge Cases:**

- **Subprocess errors**: `Notebook.export()` returns `False` instead of raising exceptions for subprocess failures.
- **Permission errors**: May raise `PermissionError` during file operations (rare).
- **Encoding errors**: Rare; `UnicodeDecodeError` if notebook contains invalid UTF-8.

**See Also:**

- [`main()`](#main) - Raises for parameter validation
- [`Notebook.export()`](#methods) - Returns boolean, logs errors instead of raising

### Export Failures

The `export()` method returns `False` on failure rather than raising exceptions:

```python
# Example 1: Basic failure handling
nb = Notebook(path=Path("notebooks/broken.py"))

if not nb.export(output_dir=Path("_site")):
    # Check logs for details (uses loguru)
    print("Export failed - check logs for details")

# Example 2: Collect failed exports
from marimushka.notebook import folder2notebooks

notebooks = folder2notebooks("notebooks")
failed = [nb for nb in notebooks if not nb.export(output_dir=Path("_site"))]

if failed:
    print(f"Failed to export {len(failed)} notebooks:")
    for nb in failed:
        print(f"  - {nb.path}")

# Example 3: Retry with different settings
nb = Notebook(path=Path("notebooks/large.py"))

if not nb.export(output_dir=Path("_site"), sandbox=True):
    print("Sandbox export failed, retrying without sandbox...")
    success = nb.export(output_dir=Path("_site"), sandbox=False)
    print(f"Retry {'succeeded' if success else 'failed'}")
```

**Edge Cases:**

- **Silent failures**: Always check return value; `export()` doesn't raise exceptions for subprocess errors.
- **Logging**: Uses `loguru` for detailed error messages; check console/log files for subprocess output.

**Performance:** Failed exports typically complete quickly (~100-500ms) as they fail early in subprocess execution.

**See Also:**

- [Common Exceptions](#common-exceptions) - Parameter validation errors
- [`Notebook.export()`](#methods) - Full export documentation

---

## Integration Examples

### With pytest

```python
# test_export.py
import pytest
from pathlib import Path
from marimushka.notebook import Notebook, Kind


def test_notebook_display_name():
    """Test display name transformation."""
    nb = Notebook(path=Path("tests/resources/marimo/notebooks/my_notebook.py"))
    assert nb.display_name == "my notebook"


def test_notebook_html_path():
    """Test HTML path generation for different kinds."""
    nb = Notebook(path=Path("tests/resources/marimo/notebooks/demo.py"), kind=Kind.APP)
    assert nb.html_path == Path("apps/demo.html")


def test_notebook_validation():
    """Test notebook validation."""
    with pytest.raises(FileNotFoundError):
        Notebook(path=Path("nonexistent.py"))
    
    with pytest.raises(ValueError):
        Notebook(path=Path("data.json"))


def test_export_success(tmp_path):
    """Test successful export."""
    nb = Notebook(path=Path("tests/resources/marimo/notebooks/simple.py"))
    success = nb.export(output_dir=tmp_path)
    assert success
    assert (tmp_path / nb.html_path).exists()


@pytest.mark.parametrize("kind,expected_subdir", [
    (Kind.NB, "notebooks"),
    (Kind.APP, "apps"),
    (Kind.NB_WASM, "notebooks"),
])
def test_kind_html_paths(kind, expected_subdir):
    """Test HTML paths for different kinds."""
    nb = Notebook(path=Path("tests/resources/marimo/notebooks/demo.py"), kind=kind)
    assert nb.html_path.parts[0] == expected_subdir
```

**Performance:** Test suite with ~20 tests runs in <10 seconds (includes subprocess exports).

**See Also:**

- [Batch Export with Progress](#batch-export-with-progress) - Export with error tracking
- [`Notebook`](#notebook) - Full API documentation

### With GitHub Actions

```yaml
# Example 1: Basic export in CI
- name: Export notebooks
  run: |
    python -c "
    from marimushka.export import main
    main(notebooks='docs/notebooks', apps='docs/apps', output='_site')
    "

# Example 2: Full workflow with deployment
- name: Install dependencies
  run: |
    pip install marimushka

- name: Export notebooks
  run: |
    uvx marimushka export \
      --notebooks docs/notebooks \
      --apps docs/apps \
      --output _site \
      --parallel \
      --max-workers 8

- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./_site

# Example 3: Conditional export with error handling
- name: Export notebooks
  run: |
    python -c "
    from marimushka.export import main
    import sys
    
    html = main(notebooks='notebooks', output='_site')
    if not html:
        print('Warning: No notebooks found, but continuing...')
    else:
        print(f'Exported {len(html)} bytes of HTML')
    "

# Example 4: Cache uvx for faster builds
- name: Cache uvx
  uses: actions/cache@v3
  with:
    path: ~/.cache/uv
    key: ${{ runner.os }}-uv-${{ hashFiles('**/pyproject.toml') }}

- name: Export notebooks
  run: uvx marimushka export
```

**Performance:** 

- CI export time: ~30-60 seconds for 50 notebooks (including dependency install)
- Caching `~/.cache/uv` reduces setup time by ~10-20 seconds

**See Also:**

- [CLI Commands](#cli-commands) - Full CLI reference
- [`main()`](#main) - Programmatic export

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

**Examples:**

```bash
# Example 1: Basic watch mode
uvx marimushka watch

# Example 2: Watch with custom directories
uvx marimushka watch --notebooks docs/notebooks --output dist

# Example 3: Watch without parallel export (useful for debugging)
uvx marimushka watch --no-parallel

# Example 4: Watch with more workers for faster re-export
uvx marimushka watch --max-workers 8
```

**Edge Cases:**

- **Missing watchfiles**: Raises `ImportError` if `watchfiles` is not installed.
- **Rapid changes**: Debounces file changes; waits ~500ms after last change before re-exporting.
- **Large directories**: May be slow to detect changes in directories with >1000 files.
- **Symlinks**: Follows symlinks; changes to linked files trigger re-export.

**Performance:**

- **Initial export**: Same as `export` command.
- **Watch overhead**: ~1-5 MB memory for file watching.
- **Re-export latency**: ~500ms debounce + export time (~5-40s for 10-100 notebooks).
- **CPU usage**: Minimal when idle (<1%); spikes during re-export.

**See Also:**

- [Export Command](#export-command) - Options available in watch mode
- [`main()`](#main) - Underlying export function

---

## Version

```python
from marimushka import __version__

print(f"Marimushka version: {__version__}")
```

**Examples:**

```python
# Example 1: Check version
from marimushka import __version__

print(f"Marimushka version: {__version__}")

# Example 2: Version-dependent logic
from marimushka import __version__
from packaging.version import Version

if Version(__version__) >= Version("0.2.0"):
    print("Parallel export is available")

# Example 3: Display in logs
import logging
from marimushka import __version__

logging.info(f"Starting export with marimushka v{__version__}")
```

**See Also:**

- [CLI Commands](#cli-commands) - Use `uvx marimushka version` for CLI version check
