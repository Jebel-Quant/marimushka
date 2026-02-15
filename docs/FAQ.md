# Frequently Asked Questions (FAQ)

Quick answers to common questions about Marimushka.

## Table of Contents

- [General Questions](#general-questions)
- [Installation & Setup](#installation--setup)
- [Usage & Features](#usage--features)
- [Performance & Optimization](#performance--optimization)
- [Deployment & CI/CD](#deployment--cicd)
- [Security & Best Practices](#security--best-practices)
- [Troubleshooting](#troubleshooting)

---

## General Questions

### What is Marimushka?

Marimushka is a tool for exporting [marimo](https://marimo.io) notebooks to HTML/WebAssembly format with custom styling. It creates beautiful, interactive web versions of your notebooks that can be shared with anyone - no Python installation required.

---

### Why "Marimushka"?

The name is a playful combination of "marimo" (the reactive Python notebook) and "matryoshka" (Russian nesting dolls), reflecting how Marimushka packages marimo notebooks into portable HTML containers.

---

### What's the difference between Marimushka and `marimo export`?

| Feature | marimo export | Marimushka |
|---------|--------------|------------|
| Export single notebook | ✅ Yes | ✅ Yes |
| Batch export | ❌ No | ✅ Yes |
| Index page generation | ❌ No | ✅ Yes |
| Custom templates | ❌ No | ✅ Yes |
| CI/CD integration | ⚠️ Manual | ✅ GitHub Action |
| Parallel export | ❌ No | ✅ Yes |
| Watch mode | ❌ No | ✅ Yes |

**TL;DR**: Marimushka wraps `marimo export` with batch processing, templates, and automation.

---

### Is Marimushka free?

Yes! Marimushka is open-source and licensed under the [MIT License](LICENSE). Free to use, modify, and distribute.

---

### Do I need Python to view exported notebooks?

**No**. That's the point! Exported notebooks are:
- **Static HTML** (notebooks/): Just open in any browser
- **WebAssembly** (apps/notebooks_wasm/): Python runs entirely in the browser via WebAssembly

Viewers don't need Python, pip, or any setup. Just a modern web browser.

---

## Installation & Setup

### How do I install Marimushka?

**Recommended** (no installation):
```bash
uvx marimushka export
```

**Alternative** (install as dependency):
```bash
uv add marimushka
# or
pip install marimushka
```

See: [README.md](README.md#installation)

---

### What are the system requirements?

- **Python**: 3.10 or higher
- **marimo**: Installed automatically as dependency
- **uv/uvx**: Recommended (but pip works too)
- **OS**: Linux, macOS, or Windows

---

### Do I need to install marimo separately?

**No**. Marimushka installs marimo automatically as a dependency.

---

### Can I use Marimushka without `uvx`?

Yes, use `pip`:
```bash
pip install marimushka
marimushka export
```

But `uvx` is recommended because it:
- Doesn't require installation
- Always uses the latest version
- Avoids dependency conflicts

---

## Usage & Features

### What notebook types does Marimushka support?

Three types:

1. **Static notebooks** (`notebooks/`):
   - Export command: `marimo export html`
   - File size: ~100 KB
   - Interactive: No (read-only)
   - Use case: Documentation, reports

2. **Interactive notebooks** (`notebooks_wasm/`):
   - Export command: `marimo export html-wasm --mode edit`
   - File size: ~2 MB
   - Interactive: Yes (editable code)
   - Use case: Tutorials, learning

3. **Apps** (`apps/`):
   - Export command: `marimo export html-wasm --mode run --no-show-code`
   - File size: ~2 MB
   - Interactive: Yes (run-only, code hidden)
   - Use case: Tools, dashboards

See: [README.md](README.md#project-structure)

---

### Can I customize the index page?

**Yes!** Use custom Jinja2 templates:

```bash
uvx marimushka export --template templates/custom.html.j2
```

See: [src/marimushka/templates/README.md](../src/marimushka/templates/README.md) for examples and [RECIPES.md](RECIPES.md#custom-templates) for real-world patterns.

---

### How do I exclude certain notebooks from export?

**Option 1**: Move them outside the notebook directories

**Option 2**: Custom Python script with filtering:
```python
from marimushka.notebook import folder2notebooks, Kind

notebooks = folder2notebooks("notebooks", Kind.NB)
filtered = [nb for nb in notebooks if not nb.path.stem.startswith("_draft")]
```

See: [RECIPES.md - Recipe 10](RECIPES.md#recipe-10-filtered-export)

---

### Can I export notebooks from multiple directories?

**Yes**. Use the `--notebooks`, `--apps`, and `--notebooks-wasm` flags:

```bash
uvx marimushka export \
  --notebooks docs/notebooks \
  --apps tools/apps \
  --notebooks-wasm tutorials/interactive
```

---

### Does Marimushka work with marimo's `/// script` metadata?

**Yes, and it's required** for sandbox mode (default). Example:

```python
# /// script
# dependencies = ["pandas>=2.0", "matplotlib", "numpy"]
# ///

import pandas as pd
import matplotlib.pyplot as plt
```

This tells marimo (and Marimushka) which packages to install when exporting.

---

### What's sandbox mode?

Sandbox mode (`--sandbox`, default: enabled) runs notebook exports in an isolated environment. Benefits:

- **Reproducibility**: Doesn't depend on your local environment
- **Security**: Isolated from host filesystem
- **Portability**: Works anywhere with the same dependencies

**Requirement**: Notebooks must declare dependencies in `/// script` metadata.

Disable with `--no-sandbox` if needed:
```bash
uvx marimushka export --no-sandbox
```

See: [SECURITY.md](SECURITY.md#sandbox-mode)

---

## Performance & Optimization

### How fast is Marimushka?

Performance depends on:
- Number of notebooks
- Notebook complexity
- Parallel workers

**Benchmarks** (10 notebooks):
- Sequential: ~30 seconds
- Parallel (4 workers): ~8 seconds (3.75x faster)

**Note**: Speedup scales with number of notebooks, not individual size.

---

### How do I make exports faster?

1. **Enable parallel export** (default):
   ```bash
   uvx marimushka export --parallel --max-workers 4
   ```

2. **Increase workers** (more CPUs):
   ```bash
   uvx marimushka export --max-workers 8
   ```

3. **Use static notebooks** instead of WebAssembly when possible

4. **Optimize notebook code**:
   - Cache expensive computations
   - Reduce data processing
   - Minimize plot complexity

---

### Why are WebAssembly exports so large?

WebAssembly exports (~2 MB) include:
- Python interpreter (via Pyodide)
- Core Python libraries
- Your notebook code

This allows full Python execution in the browser without a server.

**Static notebooks** (~100 KB) are much smaller but non-interactive.

---

### Can I reduce output file size?

**For static notebooks**: Already optimized (~100 KB)

**For WebAssembly**: File size is mostly fixed due to Python runtime. Options:
1. Use static notebooks when interactivity isn't needed
2. Compress assets before including in notebooks
3. Minimize inline data

---

## Deployment & CI/CD

### How do I deploy to GitHub Pages?

Use the Marimushka GitHub Action:

```yaml
name: Deploy
on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: jebel-quant/marimushka@v0.2.3
      - uses: actions/upload-pages-artifact@v2
        with:
          path: artifacts/marimushka
      - uses: actions/deploy-pages@v2
```

See: [README.md - GitHub Action](README.md#github-action) and [RECIPES.md - Recipe 4](RECIPES.md#recipe-4-github-pages-with-github-actions)

---

### Can I deploy to Netlify/Vercel/AWS?

**Yes!** Marimushka generates static files that work anywhere:

- **Netlify**: See [RECIPES.md - Recipe 5](RECIPES.md#recipe-5-deploy-to-netlify)
- **AWS S3**: See [RECIPES.md - Recipe 6](RECIPES.md#recipe-6-deploy-to-aws-s3--cloudfront)
- **Vercel**: Similar to Netlify
- **Any static host**: Just upload `_site/` directory

---

### Does Marimushka work with GitLab CI?

**Yes!** See [RECIPES.md - Recipe 7](RECIPES.md#recipe-7-gitlab-cicd) for a complete example.

---

### How do I set up automatic deployments?

Use GitHub Actions, GitLab CI, or any CI/CD platform:

1. **Trigger**: On push to main branch
2. **Export**: Run `uvx marimushka export`
3. **Deploy**: Upload `_site/` (or `artifacts/marimushka/`) to your host

See: [RECIPES.md - CI/CD Integration](RECIPES.md#cicd-integration)

---

## Security & Best Practices

### Is Marimushka secure?

Yes. Marimushka includes multiple security layers:

- **Path traversal protection**
- **Sandboxed template rendering**
- **Subprocess timeout enforcement**
- **Input validation**
- **DoS protections** (file size limits, worker bounds)
- **Audit logging** (optional)

See: [SECURITY.md](SECURITY.md) for details.

---

### Should I use sandbox mode in production?

**Yes, always**. Sandbox mode:
- Ensures reproducibility
- Prevents filesystem access
- Isolates notebook execution

Only disable for development/debugging.

---

### Can I scan for vulnerabilities?

**Yes**. Run security checks:

```bash
# Check dependencies
pip-audit

# Scan with safety
safety check

# CodeQL scan (for contributors)
make security
```

---

### How do I report a security issue?

**Don't open a public issue**. Email [contact@jqr.ae](mailto:contact@jqr.ae) with details.

See: [SECURITY.md - Reporting a Vulnerability](SECURITY.md#reporting-a-vulnerability)

---

## Troubleshooting

### Why isn't my template working?

Common issues:

1. **File not found**: Check path is correct
2. **Syntax error**: Validate Jinja2 syntax
3. **Wrong variables**: Use `notebooks`, `apps`, `notebooks_wasm`

See: [TROUBLESHOOTING.md - Template Issues](TROUBLESHOOTING.md#template-issues)

---

### Why do exports fail with `ModuleNotFoundError`?

You're likely using sandbox mode without declaring dependencies:

```python
# Add this to notebook
# /// script
# dependencies = ["pandas", "matplotlib"]
# ///
```

Or disable sandbox: `uvx marimushka export --no-sandbox`

See: [TROUBLESHOOTING.md - Sandbox Mode Issues](TROUBLESHOOTING.md#sandbox-mode-issues)

---

### Why is parallel export not working?

Check:

1. **Enabled?** `--parallel` (default: enabled)
2. **Worker count**: Try reducing: `--max-workers 2`
3. **File descriptors**: Increase limit: `ulimit -n 4096`

See: [TROUBLESHOOTING.md - Performance Issues](TROUBLESHOOTING.md#performance-issues)

---

### How do I enable debug logging?

```bash
export MARIMUSHKA_LOG_LEVEL=DEBUG
uvx marimushka export
```

Or in Python:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

### Where can I get help?

1. **Documentation**:
   - [README.md](README.md) - Getting started
   - [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
   - [RECIPES.md](RECIPES.md) - Usage patterns
   - [API.md](API.md) - Programmatic usage

2. **Community**:
   - [GitHub Issues](https://github.com/jebel-quant/marimushka/issues)
   - [GitHub Discussions](https://github.com/jebel-quant/marimushka/discussions)

3. **Security**:
   - Email: [contact@jqr.ae](mailto:contact@jqr.ae)

---

## Configuration

### Can I configure Marimushka via a file?

**Yes!** Create `.marimushka.toml`:

```toml
[marimushka]
output = "_site"
notebooks = "notebooks"
apps = "apps"
sandbox = true
parallel = true
max_workers = 4

[marimushka.security]
audit_enabled = true
max_file_size_mb = 10
```

See: [README.md - Configuration File](README.md#configuration-file)

---

### What's the configuration precedence?

```
CLI flags > .marimushka.toml > defaults
```

Example:
```bash
# Config file says: max_workers = 4
# CLI overrides:
uvx marimushka export --max-workers 8  # Uses 8
```

---

### Can I use environment variables?

**Not directly**, but you can use shell variables:

```bash
NOTEBOOKS_DIR=docs/notebooks
uvx marimushka export --notebooks $NOTEBOOKS_DIR
```

Or in scripts:
```python
import os
from marimushka.export import main

main(notebooks=os.getenv('NOTEBOOKS_DIR', 'notebooks'))
```

---

## Contributing

### How can I contribute?

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Code style guidelines
- Testing requirements
- Pull request process

---

### Where's the source code?

GitHub: https://github.com/jebel-quant/marimushka

---

### How do I report a bug?

[Open an issue](https://github.com/jebel-quant/marimushka/issues/new) with:
- Marimushka version (`uvx marimushka version`)
- Operating system
- Full error message
- Steps to reproduce

---

### Can I request features?

**Yes!** [Open a feature request](https://github.com/jebel-quant/marimushka/issues/new) or start a [discussion](https://github.com/jebel-quant/marimushka/discussions).

---

## Miscellaneous

### Does Marimushka work offline?

**Partially**:
- ✅ Export process: Works offline (if marimo is installed)
- ❌ CDN resources: Default template uses CDN (Tailwind CSS)
- ✅ Exported files: Work offline once exported

For fully offline templates, self-host CSS/JS resources.

---

### Can I use Marimushka commercially?

**Yes**. MIT License allows commercial use. See [LICENSE](LICENSE).

---

### What's the roadmap?

Check:
- [GitHub Issues](https://github.com/jebel-quant/marimushka/issues) (planned features)
- [GitHub Projects](https://github.com/jebel-quant/marimushka/projects) (roadmap)
- [Discussions](https://github.com/jebel-quant/marimushka/discussions) (ideas)

---

### How do I stay updated?

- ⭐ Star the repo: https://github.com/jebel-quant/marimushka
- 👁️ Watch releases
- 📰 Check [CHANGELOG.md](CHANGELOG.md) for release notes

---

## Still Have Questions?

**Didn't find your answer?**

1. Search [existing issues](https://github.com/jebel-quant/marimushka/issues)
2. Check [discussions](https://github.com/jebel-quant/marimushka/discussions)
3. [Ask a question](https://github.com/jebel-quant/marimushka/discussions/new?category=q-a)

**Found a mistake in this FAQ?**

[Open an issue](https://github.com/jebel-quant/marimushka/issues/new) or [submit a PR](CONTRIBUTING.md)!

---

**Last updated**: 2025-01-15
