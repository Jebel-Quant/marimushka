# Contributing

Thank you for your interest in contributing to Marimushka! This guide will help you make your first contribution.

We welcome all contributions - from typo fixes to major features. You don't need to be an expert to help out!

## Table of Contents

- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Contribution Workflow](#contribution-workflow)
- [Code Style](#code-style)
- [Writing Tests](#writing-tests)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Getting Help](#getting-help)

---

## Quick Start

**First time contributor?** Start here:

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/marimushka.git
   cd marimushka
   ```
3. **Set up development environment**:
   ```bash
   make install
   ```
4. **Create a branch**:
   ```bash
   git checkout -b fix/my-fix
   ```
5. **Make your changes** and test them
6. **Submit a pull request**

**Need more details?** Keep reading!

---

## Development Setup

### Prerequisites

- **Git**: For version control
- **Make**: For running development commands
- **Python 3.10+**: Will be installed automatically by `uv`

**Note**: You don't need to install Python manually. The `make install` command will install the correct Python version automatically.

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/jebel-quant/marimushka.git
cd marimushka

# Install all dependencies (including uv, Python, and packages)
make install

# Verify setup
make test
```

**What `make install` does**:
1. Installs `uv` package manager (if not already installed)
2. Downloads Python 3.13 (specified in `.python-version`)
3. Creates a virtual environment (`.venv`)
4. Installs all project dependencies

### Common Development Commands

```bash
# Install/update dependencies
make install

# Run all tests with coverage
make test

# Format code and run linter
make fmt

# Check dependencies
make deptry

# Clean build artifacts
make clean

# Start marimo development server
make marimo

# Build documentation
make book
```

---

## Contribution Workflow

### 1. Find Something to Work On

**Good starting points**:
- 🐛 [Bug reports](https://github.com/jebel-quant/marimushka/issues?q=is%3Aissue+is%3Aopen+label%3Abug)
- 🎯 [Good first issues](https://github.com/jebel-quant/marimushka/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
- 📚 Documentation improvements
- ✅ TODOs in the code
- 💡 Feature requests (discuss first!)

**Before starting**:
- Check if someone is already working on it
- For big changes, [open an issue](https://github.com/jebel-quant/marimushka/issues/new) to discuss first

### 2. Create a Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b type/description

# Branch naming conventions:
# - fix/     → Bug fixes
# - feat/    → New features
# - docs/    → Documentation
# - test/    → Test additions
# - refactor/→ Code refactoring
# - chore/   → Maintenance tasks

# Examples:
# fix/template-path-validation
# feat/parallel-export
# docs/add-examples
```

### 3. Make Your Changes

**Edit code**: Use your favorite editor

**Test as you go**:
```bash
# Run tests
make test

# Test specific file
pytest tests/test_export.py

# Run your changes
uv run marimushka export --help
```

**Code quality**:
```bash
# Format and lint (do this before committing!)
make fmt
```

### 4. Write Tests

**Every code change needs tests**. Even bug fixes!

```bash
# Create test file (if needed)
touch tests/test_my_feature.py

# Write test
def test_my_feature():
    # Arrange
    input_data = ...
    
    # Act
    result = my_function(input_data)
    
    # Assert
    assert result == expected
```

**Test guidelines**:
- Test both success and failure cases
- Use descriptive test names
- Keep tests focused and simple
- Use fixtures for common setup

**Example test**:
```python
import pytest
from pathlib import Path
from marimushka.notebook import Notebook, Kind


def test_notebook_display_name_conversion():
    """Test that underscores are converted to spaces."""
    nb = Notebook(path=Path("notebooks/my_analysis.py"))
    assert nb.display_name == "my analysis"


def test_notebook_export_invalid_path(tmp_path):
    """Test that export fails gracefully with invalid path."""
    nonexistent = tmp_path / "nonexistent.py"
    with pytest.raises(FileNotFoundError):
        Notebook(path=nonexistent)
```

### 5. Update Documentation

**If your change affects users**, update docs:

| Change Type | Update These |
|-------------|-------------|
| New CLI flag | README.md, API.md |
| New feature | README.md, CHANGELOG.md |
| Bug fix | CHANGELOG.md |
| API change | API.md |
| Configuration | README.md, .marimushka.toml.example |

**Documentation files**:
- `README.md` - Main user guide
- `API.md` - Python API reference
- `CHANGELOG.md` - Version history
- `TROUBLESHOOTING.md` - Common issues
- `RECIPES.md` - Usage examples
- `FAQ.md` - Frequently asked questions

### 6. Commit Your Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "type: brief description

Longer explanation if needed. Explain:
- What changed
- Why it changed
- Any breaking changes

Fixes #123"
```

**Commit message format**:
```
type: short description (50 chars max)

Longer description explaining the change in detail.
Wrap at 72 characters. Explain:
- What problem does this solve?
- How does it solve it?
- Any side effects or trade-offs?

Breaking Changes: (if applicable)
- List any breaking changes

Closes #123
Fixes #456
```

**Commit types**:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `test:` - Test additions/changes
- `refactor:` - Code restructuring
- `perf:` - Performance improvement
- `chore:` - Maintenance tasks

**Examples**:
```bash
# Good commits
git commit -m "feat: add parallel export support

Implements parallel notebook export using ThreadPoolExecutor.
Default worker count is 4, configurable via --max-workers flag.

Performance: 3.75x faster for 10+ notebooks.

Closes #42"

git commit -m "fix: prevent path traversal in template loading

Validates template paths to ensure they don't escape the project
directory. Uses Path.resolve() and .is_relative_to() checks.

Fixes #89"

# Bad commits (avoid these)
git commit -m "fix stuff"
git commit -m "WIP"
git commit -m "updates"
```

### 7. Push and Create Pull Request

```bash
# Push to your fork
git push origin your-branch-name

# If branch doesn't exist yet:
git push -u origin your-branch-name
```

**On GitHub**:
1. Go to your fork
2. Click "Compare & pull request"
3. Fill out the PR template:
   - **Title**: Clear, concise description
   - **Description**: What, why, how
   - **Related issues**: Link to issues
   - **Testing**: How you tested
   - **Screenshots**: If UI changes

**Pull Request Template**:
```markdown
## Description
Brief description of the change.

## Motivation
Why is this change needed?

## Changes
- List of changes made
- Another change

## Testing
How did you test this?
- [ ] Unit tests added/updated
- [ ] Manual testing performed
- [ ] Documentation updated

## Related Issues
Closes #123
```

---

## Code Style

We use **ruff** for formatting and linting.

### Running Code Quality Checks

```bash
# Format and lint (do this before every commit!)
make fmt

# This runs:
# - ruff format  (formats code)
# - ruff check --fix  (fixes linting issues)
```

### Style Guidelines

**General**:
- Line length: 120 characters
- Indentation: 4 spaces (no tabs)
- Imports: Sorted alphabetically
- Type hints: Always use for public APIs

**Naming**:
```python
# Classes: PascalCase
class NotebookExporter:
    pass

# Functions/methods: snake_case
def export_notebook():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_WORKERS = 16

# Private: Leading underscore
def _internal_helper():
    pass
```

**Docstrings** (Google style):
```python
def example_function(param1: str, param2: int = 0) -> bool:
    """
    Short description (one line).
    
    Longer description explaining what the function does in detail.
    Can span multiple lines.
    
    Args:
        param1: Description of param1
        param2: Description of param2. Defaults to 0.
        
    Returns:
        True if successful, False otherwise.
        
    Raises:
        ValueError: If param1 is empty.
        
    Example:
        >>> example_function("test", 42)
        True
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    return True
```

**Type Hints**:
```python
from pathlib import Path
from typing import Any

# Simple types
def process(text: str) -> int:
    return len(text)

# Optional/Union
def get_config(path: str | None = None) -> dict[str, Any]:
    return {}

# Complex types
def batch_export(notebooks: list[Notebook], output: Path) -> dict[str, bool]:
    return {}
```

---

## Writing Tests

### Test Structure

```python
import pytest
from pathlib import Path
from marimushka.export import main

def test_feature_name():
    """Test description of what is being tested."""
    # Arrange: Set up test data
    input_data = ...
    
    # Act: Execute the code being tested
    result = function_under_test(input_data)
    
    # Assert: Verify the result
    assert result == expected_value
```

### Using Fixtures

```python
# In conftest.py or at top of test file
@pytest.fixture
def sample_notebook(tmp_path):
    """Create a sample notebook for testing."""
    notebook_path = tmp_path / "sample.py"
    notebook_path.write_text("""
import marimo
mo = marimo.App()
    """)
    return notebook_path

# Use in tests
def test_with_fixture(sample_notebook):
    nb = Notebook(path=sample_notebook)
    assert nb.path.exists()
```

### Testing Guidelines

✅ **Do**:
- Test both success and error cases
- Use descriptive test names
- Test edge cases
- Use `tmp_path` for file operations
- Mock external dependencies
- Keep tests independent

❌ **Don't**:
- Test implementation details
- Create interdependent tests
- Use hardcoded paths
- Skip cleanup
- Write tests that depend on external services

### Running Tests

```bash
# All tests
make test

# Specific file
pytest tests/test_export.py

# Specific test
pytest tests/test_export.py::test_main_basic

# With output
pytest -v

# With coverage
pytest --cov=marimushka --cov-report=html
# Open: _tests/html-coverage/index.html

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

---

## Documentation

### Documentation Types

1. **Code comments** - Explain complex logic
2. **Docstrings** - Public API documentation
3. **README.md** - User guide and examples
4. **API.md** - Detailed API reference
5. **CHANGELOG.md** - Version history
6. **Other docs** - TROUBLESHOOTING.md, RECIPES.md, FAQ.md, etc.

### When to Update Documentation

| Change | Documentation to Update |
|--------|------------------------|
| New CLI flag | README.md (Usage section), API.md |
| New function | API.md (with docstring examples) |
| Bug fix | CHANGELOG.md |
| New feature | README.md, API.md, CHANGELOG.md |
| Breaking change | MIGRATION.md, CHANGELOG.md |
| Configuration option | README.md (Configuration), .marimushka.toml.example |

### Documentation Style

**Clear and concise**:
```markdown
<!-- Good -->
## Export Notebooks

Use `marimushka export` to batch-export notebooks:

```bash
uvx marimushka export --notebooks notebooks --apps apps
```

<!-- Bad -->
## The Export Command

The marimushka tool provides an export command which can be used
to export notebooks by specifying the directories...
```

**Use examples**:
```markdown
<!-- Good: Show example -->
Configure parallel workers:

```bash
uvx marimushka export --max-workers 8
```

<!-- Bad: Just describe -->
You can configure the number of parallel workers using the max-workers flag.
```

---

## Pull Request Process

### Before Submitting

**Checklist**:
- [ ] Tests pass (`make test`)
- [ ] Code is formatted (`make fmt`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (for user-facing changes)
- [ ] Commit messages follow guidelines
- [ ] Branch is up-to-date with main

### PR Requirements

1. **Clear title**: `type: brief description`
2. **Description**: What, why, how
3. **Tests**: All tests must pass
4. **Documentation**: Updated if needed
5. **Code review**: Address all comments

### Review Process

1. **Automated checks**: CI must pass
2. **Code review**: Maintainer reviews code
3. **Feedback**: Address comments
4. **Approval**: Maintainer approves
5. **Merge**: Maintainer merges PR

**Typical timeline**: 1-7 days depending on complexity

### After Merge

- Your changes will be in the next release
- You'll be credited in CHANGELOG.md
- Thank you! 🎉

---

## Getting Help

### Questions?

- 💬 [GitHub Discussions](https://github.com/jebel-quant/marimushka/discussions) - Ask questions, discuss ideas
- 📖 [CODE_TOUR.md](CODE_TOUR.md) - Understand the codebase
- 📚 [DESIGN.md](DESIGN.md) - Learn about design decisions

### Found a Bug?

- 🐛 [Open an issue](https://github.com/jebel-quant/marimushka/issues/new?template=bug_report.md)

### Have an Idea?

- 💡 [Open a discussion](https://github.com/jebel-quant/marimushka/discussions/new?category=ideas)
- For big features, discuss before implementing

---

## Code of Conduct

Be respectful, inclusive, and professional. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## Recognition

Contributors are recognized in:
- CHANGELOG.md (for each release)
- GitHub contributors page
- Special thanks section (for major contributions)

**Thank you for contributing to Marimushka! 🙏**

---

**Last updated**: 2025-01-15
