# Changelog

All notable changes to Marimushka are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

#### Parallel Export (Performance Enhancement) 🚀
- **Parallel export**: Notebooks now export in parallel by default (4 workers), significantly improving export speed for large projects
  - **Performance impact**: 3.75x faster for projects with 10+ notebooks
  - **Example**:
    ```bash
    # Enable parallel export with 4 workers (default)
    uvx marimushka export --parallel --max-workers 4
    
    # Disable for sequential export
    uvx marimushka export --no-parallel
    ```
  - **API usage**:
    ```python
    from marimushka.export import main
    main(parallel=True, max_workers=4)
    ```
  - See: [Performance documentation](README.md#performance)

#### Watch Mode 👁️
- **Watch mode**: New `marimushka watch` command for automatic re-export on file changes
  - **Requires**: `watchfiles` package (install with `uv add marimushka[watch]`)
  - **Use case**: Development workflow with live preview
  - **Example**:
    ```bash
    # Watch for changes and auto-export
    uvx marimushka watch --notebooks notebooks --apps apps
    ```
  - See: [Watch mode documentation](API.md#watch-command)

#### Enhanced User Experience 🎨
- **Progress bar**: Rich progress bar shows export progress in the CLI with real-time updates
  - Shows completed/total notebooks
  - Displays percentage and time elapsed
  - **Example output**:
    ```
    Exporting notebooks ━━━━━━━━━━━━━━━━━━━━━━ 10/10 100% 0:00:08
    ```

#### Input Validation 🛡️
- **Input validation**: Early validation of template paths with clear error messages
  - Prevents cryptic Jinja2 errors
  - **Example error**:
    ```
    Error: Template file not found: /path/to/missing.html.j2
    Please check the path and try again.
    ```

#### CLI Options ⚙️
- **CLI options**: New flags for controlling parallel execution
  - `--parallel/--no-parallel`: Enable/disable parallel export
  - `--max-workers <N>`: Set number of parallel workers (1-16, default: 4)
  - **Example**:
    ```bash
    uvx marimushka export --parallel --max-workers 8
    ```

#### Optional Dependencies 📦
- **Optional dependency**: `watchfiles` available as optional `[watch]` extra
  - Install with: `uv add marimushka[watch]`
  - Only required for watch mode functionality

### Changed

#### Framework Updates 🔄
- **Synced with Rhiza framework updates**: Improved development workflow and CI/CD integration
  - Updated Makefile includes
  - Better dependency management
  - Enhanced testing infrastructure
  - **Migration**: No action required for end users

#### Error Handling 🐛
- **Improved error handling**: Fail-fast behavior for invalid templates
  - Template validation happens before export starts
  - Clear error messages with actionable guidance
  - **Example**:
    ```bash
    # Before: Cryptic Jinja2 error after processing
    # After: Clear validation error before processing starts
    Error: Template file does not exist: custom.html.j2
    ```

### Performance Improvements

| Scenario | Before | After | Improvement |
|----------|--------|-------|-------------|
| 10 notebooks | ~30s | ~8s | **3.75x faster** |
| 50 notebooks | ~150s | ~40s | **3.75x faster** |
| Single large notebook | ~12s | ~12s | No change |

**Note**: Performance gains scale with the number of notebooks, not individual notebook size.

### Upgrade Path

**From 0.2.x to Unreleased:**

No breaking changes. All existing commands work as-is. New features are opt-in.

1. **Enable parallel export** (already default):
   ```bash
   uvx marimushka export  # Already uses parallel by default
   ```

2. **Try watch mode** (optional):
   ```bash
   uv add marimushka[watch]
   uvx marimushka watch
   ```

3. **Adjust performance** (optional):
   ```bash
   uvx marimushka export --max-workers 8  # More workers for faster export
   ```

See: [MIGRATION.md](MIGRATION.md) for detailed upgrade instructions.

---

## [0.2.3] - 2025-01-10

### Changed
- **Version number**: Updated version number for consistency
  - Aligns with semantic versioning guidelines
  
- **README documentation**: Cleaned up README documentation
  - Improved formatting and clarity
  - Better examples for common use cases
  - See: [README.md](README.md)
  
- **Bash fragment syntax**: Added bash fragment syntax validation to README tests
  - Ensures code examples in documentation are valid
  - Prevents documentation drift

### Fixed
- **Lock file maintenance**: Lock file maintenance updates
  - Updated dependencies to latest compatible versions
  - Improved security posture
  - **Impact**: No user-facing changes

### Performance
- No performance changes in this release

### Upgrade Path

**From 0.2.2 to 0.2.3:**

No breaking changes. Drop-in replacement:
```bash
# Update to latest version
uv add marimushka@0.2.3
# Or with uvx
uvx marimushka@0.2.3 export
```

---

## [0.2.2] - 2024-12-27

### Added

#### Test Coverage Improvements 📊
- **Coverage badge**: Coverage badge showing test coverage percentage
  - **Result**: Achieved 100% test coverage
  - Displayed in README with link to detailed coverage report
  - **Example**: ![Coverage](https://img.shields.io/endpoint?url=...)
  - See: [Coverage Report](https://jebel-quant.github.io/marimushka/tests/html-coverage/)

- **PyPI downloads badge**: PyPI downloads badge in README
  - Tracks package adoption and usage
  - **Example**: ![Downloads](https://static.pepy.tech/personalized-badge/marimushka...)
  - See: [PyPI Stats](https://pepy.tech/project/marimushka)

### Changed

#### Dependency Management 🔧
- **Dependency groups**: Moved to dependency groups in `pyproject.toml`
  - Better organization of development vs. production dependencies
  - Easier maintenance and understanding
  - **Migration**:
    ```toml
    # Before (0.2.1)
    [project.dependencies]
    # All dependencies mixed together
    
    # After (0.2.2)
    [project.dependencies]
    # Core dependencies only
    
    [dependency-groups]
    dev = ["pytest", "ruff", ...]
    ```
  - See: [pyproject.toml](pyproject.toml)

#### Test Coverage 🧪
- **Improved test coverage**: Test coverage improved to 100%
  - All code paths now tested
  - Edge cases covered
  - Better regression prevention
  - **Impact**: Higher quality and fewer bugs

### Fixed

#### Test Suite Reliability 🔍
- **Marimushka executable discovery**: Fixed executable discovery in test suite
  - Tests now work in all environments
  - Better CI/CD reliability
  - **Technical detail**: Improved fallback mechanism for finding `uvx` binary

### Performance
- No significant performance changes

### Upgrade Path

**From 0.2.1 to 0.2.2:**

No breaking changes. Simple update:
```bash
uv add marimushka@0.2.2
```

---

## [0.2.1] - 2024-12-20

### Fixed

#### Security Fixes 🔒
- **Executable resolution**: Fixed executable resolution with fallback mechanism
  - More robust `uvx` binary discovery
  - Better error messages when `uvx` not found
  - **Example**:
    ```python
    # Now tries multiple locations:
    # 1. User-specified bin_path
    # 2. System PATH
    # 3. Common installation directories
    ```
  - See: [SECURITY.md](SECURITY.md#subprocess-execution)

- **Subprocess security**: Fixed subprocess security issues
  - Prevented potential command injection
  - Improved argument sanitization
  - **Impact**: Critical security fix, upgrade recommended
  - See: [Security Advisory](https://github.com/jebel-quant/marimushka/security)

### Changed

#### Documentation Updates 📚
- **README header**: Aligned README header with rhiza-tools format
  - Consistent branding across Rhiza ecosystem
  - Better visual presentation
  
- **CodeFactor badge**: Added CodeFactor badge
  - Shows code quality metrics
  - See: [CodeFactor Report](https://www.codefactor.io/repository/github/jebel-quant/marimushka)

### Performance
- No performance changes

### Upgrade Path

**From 0.2.0 to 0.2.1:**

⚠️ **Security update - upgrade recommended**

```bash
# Update immediately for security fixes
uv add marimushka@0.2.1
```

**What to check after upgrade:**
- Verify exports still work: `uvx marimushka export`
- Check logs for any executable resolution warnings

---

## [0.2.0] - 2024-12-15

### Added

#### Framework Integration 🏗️
- **Rhiza framework integration**: Full integration with Rhiza framework
  - Standardized project structure
  - Unified development workflow
  - Better CI/CD automation
  - **Impact**: Easier contribution and maintenance
  - See: [CONTRIBUTING.md](CONTRIBUTING.md)

- **Book documentation**: Book documentation system
  - Comprehensive user guide
  - Better organized documentation
  - **Access**: `make book` to build locally
  - See: [book/](book/)

- **Renovate**: Renovate for automated dependency updates
  - Keeps dependencies up-to-date automatically
  - Security updates applied promptly
  - See: [renovate.json](renovate.json)

### Changed

#### Project Structure 📂
- **Migrated to Rhiza**: Migrated to Rhiza project structure
  - New directory layout
  - Better organization
  - **Example**:
    ```
    project/
    ├── .rhiza/          # Rhiza framework files
    ├── book/            # Documentation book
    ├── src/             # Source code
    └── tests/           # Test suite
    ```

- **GitHub Actions**: Updated GitHub Actions workflows
  - Aligned with Rhiza CI/CD patterns
  - Better test automation
  - See: [.github/workflows/](.github/workflows/)

- **Artifact upload**: Bumped actions/upload-artifact from v5 to v6
  - Improved reliability
  - Better performance

### Removed

#### Cleanup 🧹
- **Deprecated configuration**: Deprecated configuration files removed
  - Cleaned up project root
  - Reduced confusion
  
- **Old test templates**: Old test configuration templates removed
  - Modernized test infrastructure

### Fixed

#### Bug Fixes 🐛
- **Sandbox option**: Command construction for sandbox option
  - Sandbox flag now properly passed to marimo export
  - **Example**:
    ```bash
    # Now correctly generates:
    uvx marimo export html --sandbox notebook.py
    ```

### Breaking Changes

#### Sandbox Mode Default ⚠️
- **⚠️ BREAKING**: Sandbox mode is now **enabled by default**
  - **Impact**: Notebooks must declare dependencies in metadata
  - **Why**: Better reproducibility and security
  - **Example**:
    ```python
    # /// script
    # dependencies = ["pandas", "matplotlib"]
    # ///
    
    import pandas as pd
    import matplotlib.pyplot as plt
    ```
  
- **Migration**:
  ```bash
  # Option 1: Add dependencies to notebooks (recommended)
  # See above example
  
  # Option 2: Disable sandbox (not recommended)
  uvx marimushka export --no-sandbox
  ```

### Performance
- No significant performance changes

### Upgrade Path

**From 0.1.x to 0.2.0:**

⚠️ **Breaking changes - review before upgrading**

1. **Update notebooks with dependencies**:
   ```python
   # Add this to the top of each notebook
   # /// script
   # dependencies = ["package1", "package2"]
   # ///
   ```

2. **Update GitHub Action inputs**:
   ```yaml
   # Before
   - uses: jebel-quant/marimushka@v0.1.9
     with:
       notebooks_dir: 'notebooks'
   
   # After
   - uses: jebel-quant/marimushka@v0.2.0
     with:
       notebooks: 'notebooks'  # Renamed
   ```

3. **Test locally**:
   ```bash
   uvx marimushka@0.2.0 export
   # Verify all notebooks export successfully
   ```

See: [MIGRATION.md](MIGRATION.md#version-01x--02x) for detailed migration guide.

---

## [0.1.9] - 2024-12-01

### Fixed
- **Sandbox flag command construction**: Fixed how sandbox flag is passed to marimo export command
  - Resolved issue where `--sandbox` was not being properly included in subprocess call
  - **Impact**: Sandbox mode now works correctly
  - See: [PR #XXX](https://github.com/jebel-quant/marimushka/pulls)

### Changed
- **Code formatting**: Code formatting improvements using ruff
  - Improved code consistency
  - Better readability

### Upgrade Path

**From 0.1.8 to 0.1.9:**

Bug fix release, no breaking changes:
```bash
uv add marimushka@0.1.9
```

---

## [0.1.8] - 2024-11-25

### Added

#### Sandbox Mode Support 🔒
- **Sandbox mode**: Support for sandbox mode with `--sandbox` / `--no-sandbox` flags
  - Isolated environment execution for notebook exports
  - Prevents notebooks from accessing host filesystem
  - **Example**:
    ```bash
    # Enable sandbox (safer, recommended)
    uvx marimushka export --sandbox
    
    # Disable sandbox (use local environment)
    uvx marimushka export --no-sandbox
    ```
  - **API usage**:
    ```python
    from marimushka.export import main
    main(sandbox=True)  # Enable sandbox mode
    ```
  - See: [SECURITY.md](SECURITY.md#sandbox-mode)

### Changed
- **Default behavior**: Default behavior now uses sandbox mode for safer exports
  - **Why**: Improved security and reproducibility
  - **Migration**: Add dependency declarations to notebooks (see 0.2.0 notes)

### Performance
- No performance impact from sandbox mode

### Upgrade Path

**From 0.1.7 to 0.1.8:**

Sandbox mode added but not yet default:
```bash
uv add marimushka@0.1.8

# Try sandbox mode (optional in this version)
uvx marimushka export --sandbox
```

---

## [0.1.7] - 2024-11-20

### Added

#### Interactive Notebooks 🎮
- **`notebooks_wasm` directory**: Support for interactive WebAssembly notebooks
  - Notebooks exported in "edit mode" allowing code modification
  - Full Python runtime in browser via WebAssembly
  - **Example project structure**:
    ```
    project/
    ├── notebooks/       # Static HTML (view-only)
    ├── notebooks_wasm/  # Interactive (editable)
    └── apps/            # Apps (run mode, code hidden)
    ```
  
- **Edit mode**: Edit mode for WebAssembly exports
  - Users can modify and run code in browser
  - No Python installation required
  - **Export command**:
    ```bash
    uvx marimushka export --notebooks-wasm notebooks_wasm
    ```

### Changed

#### Notebook Classification 📋
- **Three-tier classification**: Three-tier notebook classification system
  - **Static HTML** (`notebooks/`): Fast, lightweight, view-only
  - **Interactive WASM** (`notebooks_wasm/`): Editable, full Python in browser
  - **Apps** (`apps/`): Run mode, code hidden, clean UI
  
  **Comparison**:
  
  | Type | Export Mode | Code Visible | Editable | File Size | Use Case |
  |------|-------------|--------------|----------|-----------|----------|
  | Static | `html` | ✅ Yes | ❌ No | ~100 KB | Documentation |
  | Interactive | `html-wasm --mode edit` | ✅ Yes | ✅ Yes | ~2 MB | Tutorials |
  | App | `html-wasm --mode run --no-show-code` | ❌ No | ❌ No | ~2 MB | Tools |
  
  See: [README.md](README.md#project-structure)

### Performance
- WebAssembly exports are larger (~2 MB vs ~100 KB) but enable browser execution

### Upgrade Path

**From 0.1.6 to 0.1.7:**

New feature, no breaking changes:
```bash
uv add marimushka@0.1.7

# Use new interactive notebooks feature
mkdir notebooks_wasm
cp notebooks/*.py notebooks_wasm/  # Copy notebooks to make interactive
uvx marimushka export --notebooks-wasm notebooks_wasm
```

---

## [0.1.6] - 2024-11-15

### Added

#### GitHub Action 🚀
- **GitHub Action**: GitHub Action for CI/CD integration
  - Automate notebook exports in GitHub workflows
  - **Example usage**:
    ```yaml
    - name: Export notebooks
      uses: jebel-quant/marimushka@v0.1.6
      with:
        notebooks: 'notebooks'
        apps: 'apps'
    ```
  - See: [action.yml](action.yml)

- **Artifact generation**: Artifact generation for GitHub Pages deployment
  - Exports automatically uploaded as GitHub artifact
  - Ready for Pages deployment
  - **Example workflow**:
    ```yaml
    - uses: jebel-quant/marimushka@v0.1.6
    - uses: actions/upload-pages-artifact@v2
      with:
        path: artifacts/marimushka
    ```
  - See: [README.md](README.md#example-export-and-deploy-to-github-pages)

### Changed
- **Template documentation**: Improved template variable documentation
  - Better examples for custom templates
  - Clearer explanation of available variables
  - See: [templates/README.md](templates/README.md)

### Upgrade Path

**From 0.1.5 to 0.1.6:**

New feature, no breaking changes:
```bash
uv add marimushka@0.1.6

# Use in GitHub Actions (see README for full example)
```

---

## [0.1.5] - 2024-11-10

### Added

#### Template System 🎨
- **Custom template support**: Custom template support via `--template` flag
  - Use Jinja2 templates for full customization
  - **Example**:
    ```bash
    uvx marimushka export --template templates/custom.html.j2
    ```
  - See: [templates/README.md](templates/README.md#creating-custom-templates)

- **Tailwind CSS template**: Tailwind CSS default template
  - Modern, responsive design
  - Color-coded sections
  - Mobile-friendly layout
  - See: [templates/tailwind.html.j2](templates/tailwind.html.j2)

### Changed

#### Template Engine 🔧
- **Jinja2 rendering**: Jinja2 template rendering with autoescape
  - Prevents XSS vulnerabilities
  - Safer template rendering
  - **Technical detail**: Uses `jinja2.sandbox.SandboxedEnvironment`
  - See: [SECURITY.md](SECURITY.md#template-rendering)

### Upgrade Path

**From 0.1.0 to 0.1.5:**

New customization features:
```bash
uv add marimushka@0.1.5

# Try custom templates
uvx marimushka export --template templates/custom.html.j2
```

---

## [0.1.0] - 2024-10-15

### Added

#### Initial Release 🎉
- **CLI interface**: CLI interface using Typer
  - Modern command-line experience
  - Clear help messages
  - **Example**:
    ```bash
    uvx marimushka --help
    uvx marimushka export --help
    ```

- **HTML export**: Export marimo notebooks to HTML format
  - Static, self-contained HTML files
  - No server required
  - **Example**:
    ```bash
    uvx marimushka export --notebooks notebooks
    ```

- **WebAssembly export**: Export marimo apps to WebAssembly format
  - Full Python runtime in browser
  - No backend needed
  - **Example**:
    ```bash
    uvx marimushka export --apps apps
    ```

- **Template system**: Jinja2 template system for index page generation
  - Customizable landing page
  - Lists all notebooks and apps
  - See: [templates/README.md](templates/README.md)

- **Directory scanning**: Recursive directory scanning for notebooks
  - Finds all `.py` files automatically
  - No manual listing needed

- **Logging**: Loguru-based logging
  - Beautiful, informative logs
  - Configurable verbosity

- **Rich output**: Rich terminal output
  - Colored, formatted console output
  - Progress indicators
  - **Example output**:
    ```
    ✓ Found 5 notebooks
    ✓ Found 3 apps
    ✓ Exported 8 files
    ```

### Initial Performance Baseline

| Scenario | Time |
|----------|------|
| 5 notebooks | ~15s |
| 10 notebooks | ~30s |
| Single app | ~8s |

---

## [0.0.x] - 2024-09 to 2024-10

### Added
- **Development releases**: Initial development releases
  - Core export functionality
  - Basic CLI structure
  - Project scaffolding
- **Experimentation**: Early feature experimentation and prototyping

**Note**: 0.0.x releases were for internal development and testing. First stable release is 0.1.0.

[Unreleased]: https://github.com/jebel-quant/marimushka/compare/v0.2.3...HEAD
[0.2.3]: https://github.com/jebel-quant/marimushka/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/jebel-quant/marimushka/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/jebel-quant/marimushka/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/jebel-quant/marimushka/compare/v0.1.9...v0.2.0
[0.1.9]: https://github.com/jebel-quant/marimushka/compare/v0.1.8...v0.1.9
[0.1.8]: https://github.com/jebel-quant/marimushka/compare/v0.1.7...v0.1.8
[0.1.7]: https://github.com/jebel-quant/marimushka/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/jebel-quant/marimushka/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/jebel-quant/marimushka/compare/v0.1.0...v0.1.5
[0.1.0]: https://github.com/jebel-quant/marimushka/releases/tag/v0.1.0

---

## Legend

- 🚀 Performance improvement
- 🎨 User experience enhancement
- 🔒 Security improvement
- 🐛 Bug fix
- 📚 Documentation update
- 🔧 Technical change
- ⚠️ Breaking change
- 🎉 Major milestone

---

## Release Support

See [MIGRATION.md](MIGRATION.md#version-support) for version support policy.

---

## Contributing

Found a bug or have a feature request? Please [open an issue](https://github.com/jebel-quant/marimushka/issues/new).

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.
