# Debugging Guide

This guide helps you troubleshoot issues with marimushka and understand its internal workings.

## Table of Contents

- [Debug Mode](#debug-mode)
- [Common Issues](#common-issues)
- [Debugging Techniques](#debugging-techniques)
- [Log Levels](#log-levels)
- [Performance Debugging](#performance-debugging)

## Debug Mode

Marimushka provides a `--debug` flag that enables verbose logging for troubleshooting.

### Enabling Debug Mode

```bash
# Export with debug logging
marimushka export --debug

# Watch mode with debug logging
marimushka watch --debug
```

### What Debug Mode Shows

Debug mode enables **DEBUG** level logging, which includes:

- **File discovery**: See which notebooks are found in each directory
- **Export commands**: View the exact `marimo export` commands being executed
- **Subprocess output**: Capture stdout/stderr from marimo subprocess calls
- **Template rendering**: Track template loading and variable injection
- **Parallel execution**: Monitor thread pool worker activity
- **Path validation**: See all security checks and path resolutions

**Example debug output:**

```
2026-02-15 20:35:12.123 | DEBUG    | marimushka.notebook:folder2notebooks:123 | Scanning notebooks/ for Kind.NB
2026-02-15 20:35:12.124 | DEBUG    | marimushka.notebook:_run_export_subprocess:381 | Running command: ['uvx', 'marimo', 'export', 'html', '--sandbox', 'notebooks/example.py', '-o', '_site/notebooks/example.html']
2026-02-15 20:35:15.456 | DEBUG    | marimushka.orchestrator:export_notebooks_parallel:104 | Worker 1 completed: example.py
```

## Common Issues

### 1. Executable 'uvx' not found in PATH

**Symptom:**
```
ERROR | Failed to export notebook.py: Executable 'uvx' not found in PATH
```

**Solution:**
Install `uv` and ensure `uvx` is in your PATH:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify uvx is available
which uvx
uvx --version
```

**Debug:**
Enable debug mode to see the exact command being executed:
```bash
marimushka export --debug
```

### 2. Template Not Found

**Symptom:**
```
ERROR | Template file not found: /path/to/template.html.j2
```

**Solution:**
- Check the template path is correct
- Use absolute paths or paths relative to current directory
- Verify file has `.html.j2` or `.jinja2` extension

**Debug:**
```bash
# Check what template path is being used
marimushka export --template path/to/template.html.j2 --debug

# Use built-in template explicitly
marimushka export --template src/marimushka/templates/tailwind.html.j2
```

### 3. No Notebooks Found

**Symptom:**
```
WARNING | No notebooks or apps found!
```

**Solution:**
- Verify notebook directories exist
- Check notebooks have `.py` extension
- Ensure marimo notebooks have proper structure

**Debug:**
```bash
# See which directories are being scanned
marimushka export --notebooks path/to/notebooks --debug

# List files in your notebook directory
ls -la path/to/notebooks/
```

### 4. Export Timeout

**Symptom:**
```
ERROR | Export timeout exceeded: 300 seconds
```

**Solution:**
Increase the timeout for slow notebooks:

```bash
# Increase timeout to 600 seconds (10 minutes)
marimushka export --timeout 600
```

**Debug:**
```bash
# See which notebook is taking long
marimushka export --timeout 600 --debug
```

### 5. Parallel Export Failures

**Symptom:**
Multiple notebooks failing during parallel export.

**Solution:**
Try sequential export to isolate issues:

```bash
# Disable parallel processing
marimushka export --no-parallel --debug
```

## Debugging Techniques

### 1. Isolate the Problem

Test with a minimal setup:

```bash
# Create a test directory with one notebook
mkdir test-notebooks
cp problematic-notebook.py test-notebooks/

# Try exporting just that one
marimushka export --notebooks test-notebooks --no-parallel --debug
```

### 2. Check marimo Directly

Test if the notebook works with marimo directly:

```bash
# Try running the notebook
marimo run notebook.py --sandbox

# Try exporting directly with marimo
uvx marimo export html notebook.py -o test-output.html --sandbox
```

### 3. Inspect Generated Files

Look at the exported HTML and index:

```bash
# Export and check output
marimushka export --output test-site

# Examine the generated index
cat test-site/index.html

# Check individual notebook exports
ls -la test-site/notebooks/
```

### 4. Use Python API for Control

For advanced debugging, use the Python API:

```python
from marimushka.export import main

# Custom progress callback
def debug_progress(completed, total, name):
    print(f"[DEBUG] [{completed}/{total}] {name}")

# Export with callback
main(
    notebooks="notebooks",
    apps="apps",
    on_progress=debug_progress,
)
```

### 5. Check Logs

Review the marimushka logs:

```bash
# Redirect logs to a file
marimushka export --debug 2> debug.log

# Review the log file
less debug.log

# Search for errors
grep -i "error" debug.log
```

## Log Levels

Marimushka uses the following log levels:

| Level | When to Use | What It Shows |
|-------|-------------|---------------|
| **DEBUG** | Troubleshooting | All internal operations, subprocess commands, file I/O |
| **INFO** | Normal operation | Major steps (start, scanning, exporting, completion) |
| **WARNING** | Potential issues | Missing notebooks, deprecated features |
| **ERROR** | Failures | Failed exports, template errors, validation failures |

### Filtering Logs

```bash
# Save only errors
marimushka export 2>&1 | grep ERROR > errors.log

# Count warnings
marimushka export 2>&1 | grep WARNING | wc -l

# Show only exports that failed
marimushka export --debug 2>&1 | grep "Failed to export"
```

## Performance Debugging

### Identify Slow Notebooks

Enable debug mode to see timing:

```bash
marimushka export --debug 2>&1 | grep "completed"
```

### Profile Parallel vs Sequential

Compare performance:

```bash
# Time parallel export
time marimushka export --parallel --max-workers 8

# Time sequential export
time marimushka export --no-parallel
```

### Memory Usage

Monitor memory during export:

```bash
# On Linux
/usr/bin/time -v marimushka export

# On macOS
/usr/bin/time -l marimushka export
```

### Optimize Worker Count

Experiment with different worker counts:

```bash
# Try different values (1-16)
marimushka export --max-workers 2
marimushka export --max-workers 4
marimushka export --max-workers 8
```

## Getting Help

If you're still stuck:

1. **Check existing issues**: [GitHub Issues](https://github.com/jebel-quant/marimushka/issues)
2. **Create a minimal reproduction**: Isolate the problem to a single notebook
3. **Include debug logs**: Run with `--debug` and include relevant log output
4. **Check environment**: Include Python version, OS, marimushka version
5. **Open an issue**: Provide all the above information

### Information to Include

When reporting issues, include:

```bash
# Version information
marimushka version

# Python version
python --version

# OS information
uname -a  # Linux/macOS
systeminfo  # Windows

# Debug log (relevant section only)
marimushka export --debug 2>&1 | tail -50
```

## See Also

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [FAQ.md](FAQ.md) - Frequently asked questions
- [API.md](../API.md) - Python API reference
- [SECURITY.md](../SECURITY.md) - Security features and best practices
