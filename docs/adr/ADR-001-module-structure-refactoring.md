# ADR-001: Module Structure Refactoring

**Status**: Accepted

**Date**: 2025-01-15

**Deciders**: Development Team

## Context

The initial implementation of marimushka placed most functionality in a single `export.py` module, which grew to over 400 lines. This monolithic structure made the codebase difficult to:

- Test individual components in isolation
- Understand the separation of concerns
- Maintain and extend with new features
- Navigate for new contributors

Key pain points:
- Export logic, template rendering, and orchestration were intermingled
- Notebook abstraction was mixed with CLI concerns
- Progress tracking and parallel execution were tightly coupled
- Security and audit logging code was scattered throughout

## Decision

We decided to refactor the monolithic `export.py` into focused modules with clear responsibilities:

1. **`notebook.py`**: Core notebook abstraction
   - `Notebook` dataclass representing marimo notebooks
   - `Kind` enum for export types (NB, NB_WASM, APP)
   - `folder2notebooks()` utility for discovery
   - Export logic encapsulated in `Notebook.export()`

2. **`orchestrator.py`**: Export orchestration and coordination
   - `export_notebooks_parallel()` for concurrent exports
   - `export_notebooks_sequential()` for ordered exports
   - `export_all_notebooks()` for batch operations
   - `generate_index()` for index page creation
   - Template rendering coordination

3. **`export.py`**: Public Python API
   - `main()` function as primary entry point
   - Parameter validation and defaults
   - High-level workflow coordination
   - Clean interface for library users

4. **`cli.py`**: Command-line interface (already separate)
   - Typer-based CLI application
   - Argument parsing and validation
   - User-friendly error messages

5. **`security.py`**: Security utilities
   - Path validation and sanitization
   - File permission management
   - Input validation helpers
   - DoS prevention (file size limits, worker bounds)

6. **`audit.py`**: Audit logging
   - `AuditLogger` class for security events
   - Structured logging with timestamps
   - File-based audit trail
   - Global instance management

7. **`validators.py`**: Input validation
   - Template file validation
   - Path traversal prevention
   - File existence checks

8. **`config.py`**: Configuration management
   - `MarimushkaConfig` dataclass
   - TOML file loading
   - Default value management

9. **`exceptions.py`**: Exception hierarchy
   - Custom exception classes
   - Result types (`NotebookExportResult`, `BatchExportResult`)
   - Type definitions (`ProgressCallback`)

10. **`dependencies.py`**: Dependency injection
    - `Dependencies` container for injectable components
    - Factory functions for different scenarios
    - Test helpers

## Consequences

### Positive

1. **Improved Testability**
   - Each module can be tested independently
   - Easier to mock dependencies
   - Test coverage increased from 85% to 94%+

2. **Better Maintainability**
   - Clear responsibility boundaries
   - Easier to locate functionality
   - Reduced cognitive load when reading code

3. **Enhanced Extensibility**
   - New features can be added to appropriate modules
   - Less risk of breaking unrelated functionality
   - Cleaner extension points

4. **Stronger Type Safety**
   - Better type hints throughout
   - IDE support improved (autocomplete, navigation)
   - Easier to catch type errors

5. **Improved Documentation**
   - Module-level docstrings explain purpose
   - Function signatures are self-documenting
   - Examples can be more focused

6. **Better Security**
   - Security concerns centralized in `security.py`
   - Audit logging separated for clarity
   - Easier to audit security-critical code

### Negative

1. **More Files**
   - 10 modules instead of 2-3
   - More navigation required
   - Potential for circular import issues (mitigated by careful design)

2. **Initial Learning Curve**
   - New contributors need to understand module organization
   - More concepts to learn upfront
   - Requires reading architecture documentation

3. **Import Overhead**
   - More imports needed in some files
   - Slightly more verbose imports
   - (Minimal impact on performance)

4. **Refactoring Cost**
   - Significant upfront effort to restructure
   - All tests needed updating
   - Documentation needed rewriting

### Mitigation Strategies

1. **Documentation**
   - Added comprehensive CLAUDE.md explaining structure
   - Module docstrings describe purpose and relationships
   - Data flow diagrams show component interaction

2. **Clear Exports**
   - Main `__init__.py` exports key components
   - Users don't need to know internal structure
   - Public API remains simple

3. **Dependency Injection**
   - Dependencies passed explicitly
   - Avoids hidden coupling
   - Makes testing easier

4. **Architecture Diagrams**
   - Visual representation of module relationships
   - Data flow diagrams show interactions
   - Helps onboarding

## Alternatives Considered

### Alternative 1: Keep Monolithic Structure

**Pros**: Simpler file structure, everything in one place
**Cons**: Continued maintenance burden, poor testability, harder to understand

**Rejected because**: The pain points were already significant and would only worsen as features were added.

### Alternative 2: Microservices/Plugin Architecture

**Pros**: Maximum flexibility, true separation
**Cons**: Massive over-engineering for CLI tool, complex plugin system, slower execution

**Rejected because**: Overkill for the problem space. Current approach provides sufficient modularity without architectural overhead.

### Alternative 3: Functional Programming Approach

**Pros**: Pure functions, easier reasoning, immutable data
**Cons**: Awkward in Python, state management complexity, less idiomatic

**Rejected because**: While functional principles are used where appropriate, full FP would fight against Python's strengths.

## Related Decisions

- [ADR-002: Progress Callback API Design](ADR-002-progress-callback-api.md) - Influenced by modular structure
- [ADR-003: Security Model](ADR-003-security-model.md) - Enabled by `security.py` module
- [ADR-005: Parallel Export Strategy](ADR-005-parallel-export-strategy.md) - Made possible by `orchestrator.py`

## Notes

This refactoring was completed in phases:

1. Phase 1: Extract `notebook.py` and `exceptions.py`
2. Phase 2: Create `orchestrator.py` and move export logic
3. Phase 3: Add `security.py`, `audit.py`, `validators.py`
4. Phase 4: Create `config.py` and `dependencies.py`

Each phase maintained test coverage and backward compatibility.
