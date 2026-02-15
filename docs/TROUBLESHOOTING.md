# Troubleshooting Guide

This guide helps you diagnose and fix common issues with Marimushka.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Export Issues](#export-issues)
- [Template Issues](#template-issues)
- [Performance Issues](#performance-issues)
- [GitHub Action Issues](#github-action-issues)
- [Sandbox Mode Issues](#sandbox-mode-issues)
- [Configuration Issues](#configuration-issues)
- [Getting More Help](#getting-more-help)

---

## Installation Issues

### Problem: `uvx: command not found`

**Symptoms:**
```bash
$ uvx marimushka
-bash: uvx: command not found
```

**Solution:**

Install `uv` (which includes `uvx`):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or use pip
pip install uv
```

**Verification:**
```bash
uvx --version
```

---

### Problem: `ModuleNotFoundError: No module named 'marimushka'`

**Symptoms:**
```bash
$ python -c "import marimushka"
ModuleNotFoundError: No module named 'marimushka'
```

**Solution:**

This usually happens when trying to import directly instead of using `uvx`:

```bash
# ❌ Don't do this
python -c "import marimushka"

# ✅ Use uvx instead
uvx marimushka export
```

If you need to import in Python:
```bash
# Install as dependency
uv add marimushka
# Or with pip
pip install marimushka
```

---

### Problem: `Permission denied` when installing

**Symptoms:**
```bash
$ uv add marimushka
error: Permission denied (os error 13)
```

**Solutions:**

1. **Don't use sudo** (recommended):
   ```bash
   uv add marimushka --user
   ```

2. **Use virtual environment** (best practice):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   uv add marimushka
   ```

3. **Fix ownership** (if needed):
   ```bash
   sudo chown -R $USER:$USER ~/.local
   ```

---

## Export Issues

### Problem: `Template file not found`

**Symptoms:**
```bash
$ uvx marimushka export --template custom.html.j2
Error: Template file not found: custom.html.j2
```

**Solutions:**

1. **Check file path**:
   ```bash
   # Use absolute path
   uvx marimushka export --template /full/path/to/custom.html.j2
   
   # Or relative to current directory
   uvx marimushka export --template ./templates/custom.html.j2
   ```

2. **Verify file exists**:
   ```bash
   ls -la templates/custom.html.j2
   ```

3. **Use default template**:
   ```bash
   # Omit --template flag to use built-in template
   uvx marimushka export
   ```

---

### Problem: Notebook export fails with `ModuleNotFoundError`

**Symptoms:**
```bash
$ uvx marimushka export
Error exporting notebook.py: ModuleNotFoundError: No module named 'pandas'
```

**Solutions:**

#### Solution 1: Add dependencies to notebook (recommended)

```python
# /// script
# dependencies = ["pandas>=2.0", "matplotlib", "numpy"]
# ///

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
```

#### Solution 2: Disable sandbox mode

```bash
uvx marimushka export --no-sandbox
```

⚠️ **Warning**: Disabling sandbox uses your local environment and may reduce reproducibility.

#### Solution 3: Install missing packages

```bash
# If using --no-sandbox, ensure packages are installed
uv add pandas matplotlib numpy
```

**Verification:**
```bash
# Test notebook locally first
uvx marimo run notebook.py --sandbox
```

---

### Problem: Export timeout

**Symptoms:**
```bash
$ uvx marimushka export
Error: Export timed out after 300 seconds
```

**Solutions:**

1. **Increase timeout**:
   ```bash
   # Set longer timeout (in seconds)
   export MARIMUSHKA_TIMEOUT=600
   uvx marimushka export
   ```

   Or in `.marimushka.toml`:
   ```toml
   [marimushka]
   timeout = 600
   ```

2. **Check for infinite loops**:
   - Review notebook code for potential infinite loops
   - Add timeout to expensive computations

3. **Export individually**:
   ```bash
   # Export specific notebook
   uvx marimo export html notebook.py -o _site/notebooks/
   ```

---

### Problem: Parallel export crashes

**Symptoms:**
```bash
$ uvx marimushka export --parallel
OSError: [Errno 24] Too many open files
```

**Solutions:**

1. **Reduce worker count**:
   ```bash
   uvx marimushka export --max-workers 2
   ```

   Or in `.marimushka.toml`:
   ```toml
   [marimushka]
   max_workers = 2
   ```

2. **Increase file descriptor limit** (Linux/macOS):
   ```bash
   ulimit -n 4096
   ```

3. **Use sequential export**:
   ```bash
   uvx marimushka export --no-parallel
   ```

---

### Problem: No notebooks found

**Symptoms:**
```bash
$ uvx marimushka export
No notebooks found in notebooks/
No apps found in apps/
```

**Solutions:**

1. **Check directory structure**:
   ```bash
   ls -la notebooks/
   ls -la apps/
   ```

2. **Verify .py files exist**:
   ```bash
   find notebooks/ -name "*.py"
   ```

3. **Specify correct directories**:
   ```bash
   uvx marimushka export \
     --notebooks my_notebooks \
     --apps my_apps
   ```

4. **Check file permissions**:
   ```bash
   chmod 644 notebooks/*.py
   ```

---

## Template Issues

### Problem: Template syntax error

**Symptoms:**
```bash
$ uvx marimushka export --template custom.html.j2
jinja2.exceptions.TemplateSyntaxError: unexpected '}'
```

**Solutions:**

1. **Check Jinja2 syntax**:
   ```html
   <!-- ❌ Wrong -->
   {{ notebook.name }
   
   <!-- ✅ Correct -->
   {{ notebook.display_name }}
   ```

2. **Validate template**:
   ```python
   from jinja2 import Environment, FileSystemLoader
   env = Environment(loader=FileSystemLoader('.'))
   env.get_template('custom.html.j2')  # Will show errors
   ```

3. **Use default template**:
   ```bash
   # Test without custom template
   uvx marimushka export
   ```

---

### Problem: Template variables not working

**Symptoms:**
```html
<!-- In template: -->
{{ notebooks }}
<!-- Output: -->
[]
```

**Solutions:**

1. **Check directory has notebooks**:
   ```bash
   ls notebooks/*.py
   ```

2. **Use correct variable names**:
   ```html
   <!-- Available variables: -->
   {{ notebooks }}        <!-- List of static notebooks -->
   {{ notebooks_wasm }}   <!-- List of interactive notebooks -->
   {{ apps }}            <!-- List of apps -->
   ```

3. **Debug template**:
   ```html
   <!-- Add debug output -->
   <pre>
   Notebooks: {{ notebooks | length }}
   Apps: {{ apps | length }}
   Interactive: {{ notebooks_wasm | length }}
   </pre>
   ```

---

### Problem: Template rendering XSS warning

**Symptoms:**
```
Warning: Untrusted user input in template
```

**Solution:**

Templates use sandboxed Jinja2 by default. If you see this warning:

1. **Don't disable autoescape**:
   ```html
   <!-- ❌ Don't do this -->
   {{ user_input | safe }}
   
   <!-- ✅ Autoescape enabled by default -->
   {{ user_input }}
   ```

2. **Review template for security issues**

See: [SECURITY.md](SECURITY.md#template-rendering)

---

## Performance Issues

### Problem: Export is very slow

**Symptoms:**
```bash
$ time uvx marimushka export
# Takes > 2 minutes for 10 notebooks
```

**Solutions:**

1. **Enable parallel export** (if disabled):
   ```bash
   uvx marimushka export --parallel --max-workers 4
   ```

2. **Increase worker count** (for many notebooks):
   ```bash
   uvx marimushka export --max-workers 8
   ```

3. **Profile slow notebooks**:
   ```bash
   # Export individually to find slow ones
   time uvx marimo export html notebook1.py
   time uvx marimo export html notebook2.py
   ```

4. **Optimize notebook code**:
   - Remove expensive computations
   - Cache results
   - Reduce data processing

---

### Problem: High memory usage

**Symptoms:**
```bash
$ uvx marimushka export
# Memory usage > 4GB
```

**Solutions:**

1. **Reduce parallel workers**:
   ```bash
   uvx marimushka export --max-workers 2
   ```

2. **Use sequential export**:
   ```bash
   uvx marimushka export --no-parallel
   ```

3. **Increase system memory** or **export in batches**

---

### Problem: Large output files

**Symptoms:**
```bash
$ du -sh _site/
500M    _site/
```

**Solutions:**

1. **Use static notebooks** instead of WebAssembly:
   ```bash
   # Smaller files (~100 KB vs ~2 MB)
   uvx marimushka export --notebooks notebooks --apps ""
   ```

2. **Optimize notebook assets**:
   - Compress images before including
   - Reduce plot complexity
   - Minimize inline data

3. **Check file size limits**:
   ```toml
   # .marimushka.toml
   [marimushka.security]
   max_file_size_mb = 10
   ```

---

## GitHub Action Issues

### Problem: Action fails with `Template not found`

**Symptoms:**
```yaml
- uses: jebel-quant/marimushka@v0.2.3
  with:
    template: 'templates/custom.html.j2'
# Error: Template file not found
```

**Solutions:**

1. **Ensure template is in repository**:
   ```bash
   git add templates/custom.html.j2
   git commit -m "Add custom template"
   git push
   ```

2. **Use correct path** (relative to repo root):
   ```yaml
   with:
     template: 'templates/custom.html.j2'  # ✅ Correct
     # Not: './templates/custom.html.j2'
   ```

3. **Check file in repository**:
   ```bash
   git ls-files | grep templates
   ```

---

### Problem: Action artifact not found

**Symptoms:**
```yaml
- uses: actions/download-artifact@v3
  with:
    name: marimushka
# Error: Artifact not found
```

**Solutions:**

1. **Check artifact was created**:
   - Go to Actions tab → Workflow run → Artifacts section

2. **Use correct artifact name**:
   ```yaml
   - uses: actions/download-artifact@v3
     with:
       name: marimushka  # Fixed name from action
   ```

3. **Ensure action completed successfully**:
   - Check previous step logs
   - Verify notebooks were exported

---

### Problem: GitHub Pages deployment fails

**Symptoms:**
```
Error: ENOENT: no such file or directory, stat '_site/index.html'
```

**Solutions:**

1. **Verify export succeeded**:
   ```yaml
   - uses: jebel-quant/marimushka@v0.2.3
   
   - name: Check output
     run: ls -la artifacts/marimushka/
   ```

2. **Use correct path for deployment**:
   ```yaml
   - uses: JamesIves/github-pages-deploy-action@v4
     with:
       folder: artifacts/marimushka  # Correct path
   ```

3. **Check GitHub Pages settings**:
   - Settings → Pages → Source: gh-pages branch

---

## Sandbox Mode Issues

### Problem: Sandbox mode too restrictive

**Symptoms:**
```bash
$ uvx marimushka export --sandbox
Error: Cannot access /path/to/data.csv
```

**Solutions:**

1. **Include data in notebook** (recommended):
   ```python
   # Embed small datasets directly
   data = {
       'col1': [1, 2, 3],
       'col2': [4, 5, 6]
   }
   df = pd.DataFrame(data)
   ```

2. **Use URLs for external data**:
   ```python
   # Load from URL
   df = pd.read_csv('https://example.com/data.csv')
   ```

3. **Disable sandbox** (not recommended):
   ```bash
   uvx marimushka export --no-sandbox
   ```

---

### Problem: Dependencies not found in sandbox

**Symptoms:**
```bash
$ uvx marimushka export --sandbox
ModuleNotFoundError: No module named 'custom_package'
```

**Solutions:**

1. **Add to dependencies**:
   ```python
   # /// script
   # dependencies = ["custom_package==1.0.0"]
   # ///
   ```

2. **Use standard library** (when possible)

3. **Disable sandbox** (temporary workaround):
   ```bash
   uvx marimushka export --no-sandbox
   ```

---

## Configuration Issues

### Problem: `.marimushka.toml` not being used

**Symptoms:**
```bash
$ uvx marimushka export
# Uses default settings, ignores .marimushka.toml
```

**Solutions:**

1. **Check file location**:
   ```bash
   # Must be in current directory
   ls -la .marimushka.toml
   ```

2. **Verify TOML syntax**:
   ```bash
   # Check for syntax errors
   python -c "import tomli; tomli.load(open('.marimushka.toml', 'rb'))"
   ```

3. **Check configuration precedence**:
   - CLI flags override config file
   - Config file overrides defaults
   
   ```bash
   # CLI flag takes precedence
   uvx marimushka export --output custom_output
   # Uses 'custom_output', not config file setting
   ```

---

### Problem: Invalid configuration value

**Symptoms:**
```bash
$ uvx marimushka export
Error: Invalid value for max_workers: must be between 1 and 16
```

**Solutions:**

1. **Check value ranges**:
   ```toml
   [marimushka]
   max_workers = 4  # Valid: 1-16
   timeout = 300    # Valid: > 0
   ```

2. **Fix configuration**:
   ```toml
   # .marimushka.toml
   [marimushka]
   max_workers = 4  # Fixed
   ```

3. **Use default values**:
   ```bash
   # Temporarily ignore config
   mv .marimushka.toml .marimushka.toml.bak
   uvx marimushka export
   ```

---

## Getting More Help

### Enable Debug Logging

```bash
# Set log level
export MARIMUSHKA_LOG_LEVEL=DEBUG
uvx marimushka export
```

Or in Python:
```python
from marimushka.export import main
import logging
logging.basicConfig(level=logging.DEBUG)
main()
```

### Check Version

```bash
uvx marimushka version
```

### Search Documentation

- **README**: [README.md](README.md) - Getting started
- **API Reference**: [API.md](API.md) - Programmatic usage
- **Security**: [SECURITY.md](SECURITY.md) - Security considerations
- **Migration**: [MIGRATION.md](MIGRATION.md) - Version upgrades
- **FAQ**: [FAQ.md](FAQ.md) - Frequently asked questions
- **Recipes**: [RECIPES.md](RECIPES.md) - Usage patterns

### Report Issues

If you can't find a solution:

1. **Search existing issues**: https://github.com/jebel-quant/marimushka/issues

2. **Open a new issue** with:
   - Marimushka version (`uvx marimushka version`)
   - Operating system and version
   - Full error message
   - Steps to reproduce
   - Expected vs actual behavior

3. **Join discussions**: https://github.com/jebel-quant/marimushka/discussions

### Quick Reference

```bash
# Common troubleshooting commands

# Check version
uvx marimushka version

# Test with verbose output
uvx marimushka export --verbose

# Test single notebook
uvx marimo export html notebook.py --sandbox

# Check directory structure
ls -la notebooks/ apps/ notebooks_wasm/

# Validate configuration
python -c "import tomli; print(tomli.load(open('.marimushka.toml', 'rb')))"

# Check disk space
df -h

# Check memory usage
free -h

# Check file descriptors limit
ulimit -n
```

---

## Known Issues

### Marimo Version Compatibility

**Issue**: Older marimo versions may not support all features.

**Solution**: Update marimo:
```bash
uvx marimo --version
# If < 0.8.0, update:
uv add marimo@latest
```

### Windows Path Issues

**Issue**: Backslashes in paths on Windows.

**Solution**: Use forward slashes or raw strings:
```python
# ✅ Use forward slashes
main(template="templates/custom.html.j2")

# ✅ Or use raw strings
main(template=r"templates\custom.html.j2")
```

### Large Notebook Memory

**Issue**: Very large notebooks (> 100 MB) may cause memory issues.

**Workaround**: Split into smaller notebooks or reduce data size.

---

**Last updated**: 2025-01-15  
**Applies to**: Marimushka 0.2.x and 0.3.x
