# Code Tour for Contributors

Welcome to the Marimushka codebase! This guide will help you understand the project structure and where to find things.

## Table of Contents

- [Project Overview](#project-overview)
- [Directory Structure](#directory-structure)
- [Core Modules](#core-modules)
- [Configuration System](#configuration-system)
- [Testing Infrastructure](#testing-infrastructure)
- [Development Workflow](#development-workflow)
- [Common Tasks](#common-tasks)

---

## Project Overview

**What is Marimushka?**
A CLI tool that batch-exports marimo notebooks to HTML/WebAssembly with custom templates and automated CI/CD integration.

**Key Components**:
1. **CLI** (`export.py`) - Command-line interface
2. **Notebook** (`notebook.py`) - Notebook abstraction and export logic
3. **Config** (`config.py`) - Configuration loading and validation
4. **Security** (`security.py`) - Path validation and security utilities
5. **Audit** (`audit.py`) - Security event logging

---

## Directory Structure

```
marimushka/
├── src/marimushka/        # Source code
│   ├── __init__.py        # Package initialization, version
│   ├── export.py          # CLI and main export logic (⭐ START HERE)
│   ├── notebook.py        # Notebook class and export (⭐ CORE LOGIC)
│   ├── config.py          # Configuration system
│   ├── security.py        # Security utilities
│   ├── audit.py           # Audit logging
│   ├── exceptions.py      # Custom exceptions
│   └── templates/         # Default Jinja2 templates
│       └── tailwind.html.j2
│
├── tests/                 # Test suite
│   ├── test_export.py     # Export tests
│   ├── test_notebook.py   # Notebook tests
│   ├── test_config.py     # Configuration tests
│   ├── test_security.py   # Security tests
│   └── resources/         # Test fixtures
│       ├── marimo/        # Sample notebooks
│       └── templates/     # Sample templates
│
├── .github/               # GitHub configuration
│   ├── workflows/         # CI/CD workflows
│   │   ├── rhiza_ci.yml   # Main CI
│   │   └── ...
│   └── hooks/             # Copilot hooks
│
├── docs/                  # Additional documentation
├── book/                  # Jupyter book source
├── templates/             # User-facing templates
│   ├── README.md          # Template guide
│   └── tailwind.html.j2   # Default template
│
├── API.md                 # API reference
├── README.md              # Main documentation
├── CONTRIBUTING.md        # Contribution guide
├── DESIGN.md              # Design decisions
├── CODE_TOUR.md           # This file
└── pyproject.toml         # Project configuration
```

---

## Core Modules

### 1. `src/marimushka/export.py` ⭐ **START HERE**

**Purpose**: CLI entry point and main export orchestration.

**Key Functions**:

```python
# High-level export (⭐ Most important)
def main(
    output: str | Path = "_site",
    template: str | Path = ...,
    notebooks: str | Path = "notebooks",
    apps: str | Path = "apps",
    notebooks_wasm: str | Path = "notebooks",
    sandbox: bool = True,
    parallel: bool = True,
    max_workers: int = 4,
) -> str:
    """
    Main export function.
    
    Flow:
    1. Load configuration
    2. Scan directories for notebooks
    3. Export notebooks (parallel or sequential)
    4. Generate index.html from template
    """
```

**Code Flow**:
```
cli() [Typer entry point]
  └─> app() [Typer app with commands]
      └─> main() [High-level function]
          └─> _main_impl() [Implementation]
              ├─> _validate_template() [Early validation]
              ├─> folder2notebooks() [Scan directories]
              ├─> _export_notebooks_parallel() or _export_notebooks_sequential()
              └─> _generate_index() [Render template]
```

**Lines of Interest**:
- Lines 100-150: `main()` function (main API)
- Lines 200-250: `_export_notebooks_parallel()` (parallelization logic)
- Lines 300-350: `_generate_index()` (template rendering)
- Lines 400+: CLI commands and Typer app

**When to Modify**:
- Adding CLI flags → Edit `app` Typer functions
- Changing export flow → Edit `_main_impl()`
- Adding parallelization → Edit `_export_notebooks_parallel()`

---

### 2. `src/marimushka/notebook.py` ⭐ **CORE LOGIC**

**Purpose**: Notebook abstraction and export logic.

**Key Classes**:

```python
class Kind(Enum):
    """Notebook types."""
    NB = "notebook"           # Static HTML
    NB_WASM = "notebook_wasm" # Interactive WASM
    APP = "app"               # App (code hidden)
    
    @property
    def command(self) -> list[str]:
        """Return marimo export command for this kind."""
        # Lines 50-70: Command mapping

@dataclass(frozen=True)
class Notebook:
    """Immutable notebook representation."""
    path: Path
    kind: Kind = Kind.NB
    
    def export(self, output_dir: Path, sandbox: bool = True) -> bool:
        """
        Export this notebook.
        
        Flow:
        1. Construct uvx marimo export command
        2. Run subprocess with timeout
        3. Handle errors
        4. Return success/failure
        
        Lines 150-250: Export implementation
        """

def folder2notebooks(folder: Path | str | None, kind: Kind) -> list[Notebook]:
    """
    Scan directory for .py files, return Notebook objects.
    
    Lines 300-350: Implementation
    """
```

**Code Flow**:
```
Notebook.export()
  ├─> Build command (kind.command + paths + flags)
  ├─> Run subprocess (subprocess.run with timeout)
  ├─> Check return code
  └─> Return success/failure
```

**When to Modify**:
- Adding notebook types → Add to `Kind` enum
- Changing export command → Edit `Kind.command` property
- Changing export logic → Edit `Notebook.export()`
- Changing scan logic → Edit `folder2notebooks()`

---

### 3. `src/marimushka/config.py`

**Purpose**: Configuration loading from `.marimushka.toml` and CLI.

**Key Classes**:

```python
@dataclass
class SecurityConfig:
    """Security settings."""
    audit_enabled: bool = True
    audit_log: str = ".marimushka-audit.log"
    max_file_size_mb: int = 10
    file_permissions: str = "0o644"

@dataclass
class Config:
    """Main configuration."""
    output: str = "_site"
    notebooks: str = "notebooks"
    apps: str = "apps"
    notebooks_wasm: str = "notebooks_wasm"
    template: str | None = None
    sandbox: bool = True
    parallel: bool = True
    max_workers: int = 4
    timeout: int = 300
    security: SecurityConfig = field(default_factory=SecurityConfig)

def load_config(config_file: str = ".marimushka.toml") -> Config:
    """
    Load configuration from TOML file.
    
    Flow:
    1. Check if file exists
    2. Parse TOML
    3. Validate values
    4. Return Config object
    
    Lines 100-150: Implementation
    """
```

**When to Modify**:
- Adding config options → Add to `Config` dataclass
- Changing defaults → Edit dataclass defaults
- Adding validation → Edit `load_config()`

---

### 4. `src/marimushka/security.py`

**Purpose**: Security utilities (path validation, sandboxing).

**Key Functions**:

```python
def validate_path(path: Path, base_dir: Path | None = None) -> Path:
    """
    Validate path to prevent traversal attacks.
    
    Flow:
    1. Resolve to absolute path
    2. Check if within base_dir (if provided)
    3. Return validated path
    
    Lines 50-80: Implementation
    """

def validate_template_path(template_path: Path) -> None:
    """
    Validate template file exists and is readable.
    
    Lines 100-120: Implementation
    """
```

**When to Modify**:
- Adding security checks → Add functions here
- Changing path validation → Edit `validate_path()`

---

### 5. `src/marimushka/audit.py`

**Purpose**: Audit logging for security events.

**Key Classes**:

```python
class AuditLogger:
    """Structured audit logger."""
    
    def log_event(self, event_type: str, details: dict) -> None:
        """
        Log security event to audit log.
        
        Format: JSON lines (one event per line)
        
        Lines 50-100: Implementation
        """

# Usage example:
audit = AuditLogger("audit.log")
audit.log_event("export", {"notebook": "test.py", "success": True})
```

**When to Modify**:
- Adding audit events → Call `log_event()` in relevant code
- Changing log format → Edit `AuditLogger.log_event()`

---

## Configuration System

### Configuration Precedence

```
CLI flags > .marimushka.toml > defaults
```

**Example**:
```python
# 1. Defaults in config.py
@dataclass
class Config:
    max_workers: int = 4

# 2. Override from .marimushka.toml
[marimushka]
max_workers = 8

# 3. Override from CLI
uvx marimushka export --max-workers 16
# Final value: 16
```

### Adding a New Configuration Option

1. **Add to `Config` dataclass** (`config.py`):
   ```python
   @dataclass
   class Config:
       new_option: str = "default_value"
   ```

2. **Add CLI flag** (`export.py`):
   ```python
   @app.command()
   def export(
       new_option: str = typer.Option("default_value", help="...")
   ):
       pass
   ```

3. **Pass to `main()`** (`export.py`):
   ```python
   main(new_option=new_option, ...)
   ```

4. **Update `.marimushka.toml.example`**:
   ```toml
   [marimushka]
   new_option = "example_value"
   ```

5. **Document** in `README.md`, `API.md`, `CONFIGURATION.md`

---

## Testing Infrastructure

### Test Organization

```
tests/
├── test_export.py       # Export function tests
├── test_notebook.py     # Notebook class tests
├── test_config.py       # Configuration tests
├── test_security.py     # Security tests
└── resources/
    ├── marimo/          # Sample notebooks
    │   ├── notebooks/
    │   ├── apps/
    │   └── notebooks_wasm/
    └── templates/       # Sample templates
```

### Running Tests

```bash
# All tests
make test

# Specific test file
pytest tests/test_export.py

# Specific test
pytest tests/test_export.py::test_main_basic

# With coverage
pytest --cov=marimushka --cov-report=html

# Verbose
pytest -v
```

### Writing Tests

**Example test**:
```python
def test_notebook_export_success(tmp_path):
    """Test successful notebook export."""
    # Setup
    notebook_path = tmp_path / "test.py"
    notebook_path.write_text("# Test notebook")
    
    # Execute
    nb = Notebook(path=notebook_path, kind=Kind.NB)
    success = nb.export(output_dir=tmp_path, sandbox=False)
    
    # Assert
    assert success
    assert (tmp_path / "test.html").exists()
```

**Test Fixtures**:
```python
# In conftest.py
@pytest.fixture
def sample_notebook(tmp_path):
    """Create a sample notebook for testing."""
    path = tmp_path / "sample.py"
    path.write_text("import marimo\nmo = marimo.App()")
    return path
```

---

## Development Workflow

### 1. Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/jebel-quant/marimushka.git
cd marimushka

# Install dependencies (creates .venv)
make install

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows
```

### 2. Making Changes

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes to code

# Run tests
make test

# Run linter
make fmt

# Check coverage
make test
# Open: _tests/html-coverage/index.html
```

### 3. Testing Changes

```bash
# Test CLI locally
uv run marimushka export --help

# Test with sample notebooks
cd tests/resources/marimo
uv run marimushka export

# Test specific function
python -c "from marimushka.notebook import Notebook; print(Notebook.__doc__)"
```

### 4. Submitting Changes

```bash
# Ensure tests pass
make test

# Ensure code is formatted
make fmt

# Commit changes
git add .
git commit -m "feat: add new feature"

# Push to GitHub
git push origin feature/my-feature

# Open Pull Request on GitHub
```

---

## Common Tasks

### Adding a New CLI Command

1. **Define command** in `export.py`:
   ```python
   @app.command()
   def my_command(
       arg: str = typer.Argument(..., help="Description"),
       flag: bool = typer.Option(False, help="Description")
   ):
       """Command description."""
       # Implementation
       pass
   ```

2. **Add tests** in `tests/test_export.py`:
   ```python
   def test_my_command():
       result = runner.invoke(app, ["my-command", "value", "--flag"])
       assert result.exit_code == 0
   ```

3. **Document** in `README.md` and `API.md`

### Adding a New Notebook Type

1. **Add to `Kind` enum** in `notebook.py`:
   ```python
   class Kind(Enum):
       NEW_TYPE = "new_type"
       
       @property
       def command(self) -> list[str]:
           if self == Kind.NEW_TYPE:
               return ["marimo", "export", "new-format"]
           # ...
   ```

2. **Add directory parameter** in `export.py`:
   ```python
   def main(
       new_type: str | Path = "new_type_dir",
       ...
   ):
       new_type_nbs = folder2notebooks(new_type, Kind.NEW_TYPE)
       # ...
   ```

3. **Update template**:
   ```html
   {% if new_type_notebooks %}
   <h2>New Type</h2>
   <ul>
     {% for nb in new_type_notebooks %}
     <li><a href="{{ nb.html_path }}">{{ nb.display_name }}</a></li>
     {% endfor %}
   </ul>
   {% endif %}
   ```

4. **Add tests**, **update docs**

### Adding a Security Feature

1. **Implement** in `security.py`:
   ```python
   def new_security_check(data: Any) -> bool:
       """Check if data is safe."""
       # Implementation
       return True
   ```

2. **Add audit logging** in relevant code:
   ```python
   from .audit import get_audit_logger
   
   audit = get_audit_logger()
   audit.log_event("security_check", {"data": data, "safe": safe})
   ```

3. **Add tests** in `tests/test_security.py`

4. **Document** in `SECURITY.md`

### Debugging

```python
# Add debug logging
from loguru import logger

logger.debug("Variable value: {}", variable)
logger.info("Processing notebook: {}", notebook.path)
logger.warning("Potential issue: {}", issue)
logger.error("Error occurred: {}", error)

# Set log level
export MARIMUSHKA_LOG_LEVEL=DEBUG
uv run marimushka export
```

```python
# Use pdb
import pdb; pdb.set_trace()

# Or use IPython
from IPython import embed; embed()
```

---

## Code Style

- **Formatting**: Use `ruff format` (automated via `make fmt`)
- **Linting**: Use `ruff check` (automated via `make fmt`)
- **Type hints**: Use throughout (enforced by mypy)
- **Docstrings**: Google style for public APIs
- **Line length**: 120 characters

**Example**:
```python
def example_function(param: str, flag: bool = False) -> dict[str, Any]:
    """
    Short description.
    
    Longer description with details about what the function does.
    
    Args:
        param: Description of param
        flag: Description of flag
        
    Returns:
        Dictionary with results
        
    Raises:
        ValueError: If param is invalid
        
    Example:
        >>> example_function("test", True)
        {'result': 'success'}
    """
    if not param:
        raise ValueError("param cannot be empty")
    return {"result": "success"}
```

---

## Getting Help

- **Ask questions**: [GitHub Discussions](https://github.com/jebel-quant/marimushka/discussions)
- **Report bugs**: [GitHub Issues](https://github.com/jebel-quant/marimushka/issues)
- **Read docs**: [README.md](README.md), [API.md](API.md), [DESIGN.md](DESIGN.md)

---

## Next Steps

1. **Explore the code**: Start with `export.py` and `notebook.py`
2. **Run the tests**: `make test` to see how things work
3. **Try making a change**: Fix a typo, improve a docstring
4. **Check existing issues**: Look for `good first issue` labels

**Welcome to the team! 🎉**

---

**Last updated**: 2025-01-15  
**Need help?** Ask in [Discussions](https://github.com/jebel-quant/marimushka/discussions)!
