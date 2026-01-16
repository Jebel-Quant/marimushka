# Changelog

All notable changes to Marimushka are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Parallel export**: Notebooks now export in parallel by default (4 workers), significantly improving export speed for large projects
- **Progress bar**: Rich progress bar shows export progress in the CLI
- **Watch mode**: New `marimushka watch` command for automatic re-export on file changes (requires `watchfiles` package)
- **Input validation**: Early validation of template paths with clear error messages
- **CLI options**: `--parallel/--no-parallel` and `--max-workers` flags for controlling parallel execution
- **Optional dependency**: `watchfiles` available as optional `[watch]` extra

### Changed
- Synced with Rhiza framework updates
- Improved error handling with fail-fast behavior for invalid templates

## [0.2.3] - 2025-01-10

### Changed
- Updated version number
- Cleaned up README documentation
- Added bash fragment syntax validation to README tests

### Fixed
- Lock file maintenance updates

## [0.2.2] - 2024-12-27

### Added
- Coverage badge showing test coverage percentage
- PyPI downloads badge in README

### Changed
- Moved to dependency groups in `pyproject.toml`
- Improved test coverage to 100%

### Fixed
- Marimushka executable discovery in test suite

## [0.2.1] - 2024-12-20

### Fixed
- Executable resolution with fallback mechanism
- Subprocess security issues

### Changed
- Aligned README header with rhiza-tools format
- Added CodeFactor badge

## [0.2.0] - 2024-12-15

### Added
- Rhiza framework integration
- Book documentation system
- Renovate for automated dependency updates

### Changed
- Migrated to Rhiza project structure
- Updated GitHub Actions workflows
- Bumped actions/upload-artifact from v5 to v6

### Removed
- Deprecated configuration files
- Old test configuration templates

### Fixed
- Command construction for sandbox option

## [0.1.9] - 2024-12-01

### Fixed
- Sandbox flag command construction

### Changed
- Code formatting improvements

## [0.1.8] - 2024-11-25

### Added
- Sandbox mode support (`--sandbox` / `--no-sandbox` flags)
- Isolated environment execution for notebook exports

### Changed
- Default behavior now uses sandbox mode for safer exports

## [0.1.7] - 2024-11-20

### Added
- `notebooks_wasm` directory support for interactive WebAssembly notebooks
- Edit mode for WebAssembly exports

### Changed
- Three-tier notebook classification: static HTML, interactive WASM, and apps

## [0.1.6] - 2024-11-15

### Added
- GitHub Action for CI/CD integration
- Artifact generation for GitHub Pages deployment

### Changed
- Improved template variable documentation

## [0.1.5] - 2024-11-10

### Added
- Custom template support via `--template` flag
- Tailwind CSS default template

### Changed
- Jinja2 template rendering with autoescape

## [0.1.0] - 2024-10-15

### Added
- Initial stable release
- CLI interface using Typer
- Export marimo notebooks to HTML format
- Export marimo apps to WebAssembly format
- Jinja2 template system for index page generation
- Recursive directory scanning for notebooks
- Loguru-based logging
- Rich terminal output

## [0.0.x] - 2024-09 to 2024-10

### Added
- Initial development releases
- Core export functionality
- Basic CLI structure
- Project scaffolding

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
