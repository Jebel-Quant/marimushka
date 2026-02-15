# Migration Guide

This guide helps you migrate between major versions of Marimushka.

## Table of Contents

- [Version 0.2.x → 0.3.x](#version-02x--03x)
- [Version 0.1.x → 0.2.x](#version-01x--02x)

---

## Version 0.2.x → 0.3.x

### Overview

Version 0.3.x introduces significant security enhancements, performance improvements with parallel exports, and watch mode support. This release maintains backward compatibility for most use cases.

### Breaking Changes

#### None Expected

Version 0.3.x maintains backward compatibility with 0.2.x. All existing commands and configuration should work without changes.

### New Features

#### 1. Parallel Export (Performance)

**Impact:** Significantly faster export times for projects with multiple notebooks.

**Before (0.2.x):**
```bash
uvx marimushka export
# Sequential export: ~30s for 10 notebooks
```

**After (0.3.x):**
```bash
uvx marimushka export --parallel --max-workers 4
# Parallel export: ~8s for 10 notebooks (default behavior)
```

**Migration:**
- Parallel export is enabled by default
- To use sequential export (old behavior): `uvx marimushka export --no-parallel`
- Adjust workers if needed: `uvx marimushka export --max-workers 8`

#### 2. Watch Mode

**New capability:** Automatically re-export notebooks on file changes.

```bash
# Install watch dependencies
uv add marimushka[watch]

# Start watch mode
uvx marimushka watch
```

**Use cases:**
- Development workflow with live preview
- Continuous documentation updates
- Real-time notebook testing

#### 3. Enhanced Security Features

**What changed:**
- Path traversal protection
- TOCTOU race condition prevention
- DoS protections (file size limits, timeouts)
- Audit logging support
- SRI (Subresource Integrity) for CDN resources

**Migration:**
- Enable audit logging (optional):
  ```toml
  # .marimushka.toml
  [marimushka.security]
  audit_enabled = true
  audit_log = ".marimushka-audit.log"
  ```
- Review security settings in `.marimushka.toml.example`
- No action required for basic usage

#### 4. Configuration File Support

**New capability:** `.marimushka.toml` configuration file.

**Before (0.2.x):**
```bash
# All configuration via CLI flags
uvx marimushka export --notebooks notebooks --apps apps --output _site --sandbox
```

**After (0.3.x):**
```toml
# .marimushka.toml (create once)
[marimushka]
notebooks = "notebooks"
apps = "apps"
output = "_site"
sandbox = true
parallel = true
max_workers = 4

[marimushka.security]
audit_enabled = true
max_file_size_mb = 10
```

```bash
# CLI becomes simpler
uvx marimushka export
```

**Migration steps:**
1. Copy `.marimushka.toml.example` to `.marimushka.toml`
2. Customize settings for your project
3. Remove redundant CLI flags
4. Configuration precedence: CLI > config file > defaults

### Deprecated Features

None in this release.

### Performance Improvements

| Scenario | 0.2.x | 0.3.x | Improvement |
|----------|-------|-------|-------------|
| 10 notebooks | ~30s | ~8s | **3.75x faster** |
| 50 notebooks | ~150s | ~40s | **3.75x faster** |
| Large notebook (5MB) | ~12s | ~12s | No change |

**Note:** Performance gains scale with the number of notebooks, not individual notebook size.

### API Changes

No breaking API changes. New optional parameters added:

```python
from marimushka.export import main

# New parameters (all backward compatible)
main(
    parallel=True,      # NEW: Enable parallel export (default: True)
    max_workers=4,      # NEW: Number of workers (default: 4)
    timeout=300,        # NEW: Export timeout in seconds (default: 300)
)
```

### GitHub Action Changes

#### Before (0.2.x):
```yaml
- uses: jebel-quant/marimushka@v0.2.3
  with:
    notebooks: 'notebooks'
    apps: 'apps'
```

#### After (0.3.x):
```yaml
- uses: jebel-quant/marimushka@v0.3.0
  with:
    notebooks: 'notebooks'
    apps: 'apps'
    # NEW optional inputs:
    parallel: 'true'      # Enable parallel export (default)
    max-workers: '4'      # Number of workers
```

No changes required; new inputs are optional.

### Troubleshooting

#### Issue: Parallel export fails with "Too many open files"

**Solution:**
```bash
# Reduce worker count
uvx marimushka export --max-workers 2
```

Or in `.marimushka.toml`:
```toml
[marimushka]
max_workers = 2
```

#### Issue: Watch mode not available

**Solution:**
```bash
# Install watch dependencies
uv add marimushka[watch]
# Or with pip
pip install 'marimushka[watch]'
```

#### Issue: Audit log growing too large

**Solution:**
Disable audit logging or use log rotation:
```toml
[marimushka.security]
audit_enabled = false
```

---

## Version 0.1.x → 0.2.x

### Overview

Version 0.2.x introduced Rhiza framework integration, improved project structure, and sandbox mode by default. This was a significant architectural upgrade.

### Breaking Changes

#### 1. Sandbox Mode Default

**Change:** Sandbox mode is now enabled by default.

**Before (0.1.x):**
```bash
uvx marimushka export
# Used local environment by default
```

**After (0.2.x):**
```bash
uvx marimushka export
# Uses sandbox mode by default
```

**Migration:**
- Ensure notebooks declare dependencies in `/// script` metadata:
  ```python
  # /// script
  # dependencies = ["pandas", "matplotlib"]
  # ///
  
  import pandas as pd
  import matplotlib.pyplot as plt
  ```
- To use old behavior: `uvx marimushka export --no-sandbox`
- **Recommended:** Migrate to sandbox mode for better reproducibility

#### 2. Project Structure Changes

**Change:** Rhiza framework integration changed directory layout.

**Before (0.1.x):**
```
project/
├── notebooks/
├── apps/
└── output/
```

**After (0.2.x):**
```
project/
├── notebooks/
├── apps/
├── notebooks_wasm/    # NEW: Interactive notebooks
├── book/              # NEW: Documentation
└── _site/             # Default output
```

**Migration:**
- Create `notebooks_wasm/` for interactive notebooks (optional)
- Update output path if using custom location
- No breaking changes to existing structure

#### 3. Command Changes

**Removed commands:** None

**New commands:**
```bash
uvx marimushka version  # NEW: Show version
```

### New Features

#### 1. Interactive Notebooks (WebAssembly Edit Mode)

**Before (0.1.x):**
```bash
# Only static notebooks and apps
uvx marimushka export --notebooks notebooks --apps apps
```

**After (0.2.x):**
```bash
# Add interactive editable notebooks
uvx marimushka export \
  --notebooks notebooks \
  --notebooks-wasm notebooks_wasm \
  --apps apps
```

**Use case:** Share notebooks that users can edit and run in their browser.

#### 2. Rhiza Framework Integration

**What changed:**
- Standardized development workflow
- Unified Makefile-based commands
- Automated dependency management
- Better CI/CD integration

**Migration:**
If you're developing Marimushka locally:
```bash
# Old way (0.1.x)
python -m venv venv
source venv/bin/activate
pip install -e .

# New way (0.2.x)
make install  # Uses uv, creates .venv automatically
```

#### 3. Improved GitHub Action

**Before (0.1.x):**
```yaml
- uses: jebel-quant/marimushka@v0.1.9
  with:
    notebooks_dir: 'notebooks'
```

**After (0.2.x):**
```yaml
- uses: jebel-quant/marimushka@v0.2.0
  with:
    notebooks: 'notebooks'        # Renamed
    apps: 'apps'
    notebooks_wasm: 'interactive' # NEW
```

**Migration:** Update input names in workflows.

### Deprecated Features

#### `notebooks_dir` input in GitHub Action

**Deprecated:** `notebooks_dir` (0.1.x)  
**Replaced by:** `notebooks` (0.2.x)

```yaml
# Old (deprecated but still works)
- uses: jebel-quant/marimushka@v0.2.0
  with:
    notebooks_dir: 'notebooks'

# New (recommended)
- uses: jebel-quant/marimushka@v0.2.0
  with:
    notebooks: 'notebooks'
```

### Performance Improvements

| Scenario | 0.1.x | 0.2.x | Improvement |
|----------|-------|-------|-------------|
| First export | ~5s | ~3s | **1.67x faster** |
| Template rendering | ~500ms | ~200ms | **2.5x faster** |

### API Changes

No breaking API changes. Sandbox mode parameter added:

```python
from marimushka.export import main

# New parameter (backward compatible)
main(
    notebooks="notebooks",
    apps="apps",
    sandbox=True,  # NEW: Enable sandbox mode (default: True)
)
```

### Troubleshooting

#### Issue: Notebooks fail to export with "Module not found"

**Cause:** Sandbox mode requires dependencies in notebook metadata.

**Solution:**
Add dependencies to notebook:
```python
# /// script
# dependencies = ["pandas>=2.0", "numpy"]
# ///

import pandas as pd
import numpy as np
```

Or disable sandbox:
```bash
uvx marimushka export --no-sandbox
```

#### Issue: GitHub Action workflow fails

**Cause:** Input names changed.

**Solution:**
Update workflow file:
```yaml
# Change 'notebooks_dir' to 'notebooks'
- uses: jebel-quant/marimushka@v0.2.0
  with:
    notebooks: 'notebooks'  # Updated
```

#### Issue: Build fails with "make: command not found"

**Cause:** Rhiza framework requires `make` for development.

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install

# Windows (use WSL or Git Bash)
```

---

## General Migration Tips

### 1. Test in a Branch

Always test migrations in a branch before updating production:

```bash
git checkout -b test-migration
# Test new version
git checkout main  # Revert if needed
```

### 2. Check Logs

Enable verbose logging during migration:

```bash
export MARIMUSHKA_LOG_LEVEL=DEBUG
uvx marimushka export
```

### 3. Incremental Updates

For multi-version jumps (e.g., 0.1.x → 0.3.x):
1. Update to 0.2.x first
2. Test thoroughly
3. Then update to 0.3.x

### 4. Keep Configuration Files

Preserve your configuration between updates:
- `.marimushka.toml` - Project settings
- `templates/*.html.j2` - Custom templates

### 5. Review Release Notes

Always check [CHANGELOG.md](CHANGELOG.md) for detailed release notes.

---

## Getting Help

- **Documentation:** [README.md](README.md)
- **API Reference:** [API.md](API.md)
- **Issues:** https://github.com/jebel-quant/marimushka/issues
- **Discussions:** https://github.com/jebel-quant/marimushka/discussions

---

## Version Support

| Version | Status | Support Until |
|---------|--------|---------------|
| 0.3.x | ✅ Current | Active |
| 0.2.x | ✅ Supported | Until 0.4.0 |
| 0.1.x | ⚠️ End of Life | Upgrade recommended |
