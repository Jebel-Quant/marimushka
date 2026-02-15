# Design Decisions and Trade-offs

This document explains the key design decisions made in Marimushka and the trade-offs considered.

## Table of Contents

- [Architecture Decisions](#architecture-decisions)
- [Technology Choices](#technology-choices)
- [Security Design](#security-design)
- [Performance Trade-offs](#performance-trade-offs)
- [API Design](#api-design)
- [Future Considerations](#future-considerations)

---

## Architecture Decisions

### 1. Wrapper Around `marimo export`

**Decision**: Marimushka wraps the `marimo export` CLI rather than using marimo's Python API directly.

**Rationale**:
- **Stability**: CLI is more stable than internal APIs
- **Isolation**: Subprocess execution provides process isolation
- **Compatibility**: Works across marimo versions without tight coupling
- **Simplicity**: Easier to maintain and debug

**Trade-offs**:
- ✅ **Pros**: Stable interface, better isolation, easier testing
- ❌ **Cons**: Slower than direct API calls, subprocess overhead
- 🔄 **Mitigation**: Use parallel execution to amortize subprocess costs

**Alternatives Considered**:
1. **Direct Python API**: Rejected due to API instability and tight coupling
2. **Hybrid approach**: Considered but adds complexity without clear benefits

---

### 2. Parallel Export by Default

**Decision**: Enable parallel export with 4 workers by default.

**Rationale**:
- Most users have 4+ CPU cores
- 3.75x speedup for typical projects (10+ notebooks)
- Modern Python has good multiprocessing support

**Trade-offs**:
- ✅ **Pros**: Significantly faster exports, better resource utilization
- ❌ **Cons**: More complex error handling, higher memory usage
- 🔄 **Mitigation**: Bounded workers (max 16), `--no-parallel` option

**Performance Data**:
```
10 notebooks:
  Sequential: ~30s
  Parallel (4): ~8s (3.75x faster)

50 notebooks:
  Sequential: ~150s
  Parallel (4): ~40s (3.75x faster)
```

**Alternatives Considered**:
1. **Sequential default**: Rejected due to poor user experience
2. **Auto-detect CPU count**: Considered but 4 workers work well across systems
3. **Async/await**: Rejected due to subprocess I/O dominance

---

### 3. Three-Tier Notebook Classification

**Decision**: Support three distinct notebook types:
- Static HTML (`notebooks/`)
- Interactive WASM (`notebooks_wasm/`)
- Apps (`apps/`)

**Rationale**:
- Different use cases require different export modes
- Clear separation helps users understand trade-offs
- Flexible deployment options

**Trade-offs**:
| Type | Size | Interactive | Code Visible | Use Case |
|------|------|-------------|--------------|----------|
| Static | ~100 KB | ❌ | ✅ | Documentation |
| Interactive | ~2 MB | ✅ | ✅ | Tutorials |
| Apps | ~2 MB | ✅ | ❌ | Tools |

**Alternatives Considered**:
1. **Single mode**: Rejected as too limiting
2. **Two modes only**: Rejected as apps need code hidden
3. **Automatic detection**: Rejected due to ambiguity

---

### 4. Jinja2 Template System

**Decision**: Use Jinja2 for index page generation with sandboxed environment.

**Rationale**:
- Industry-standard templating
- Powerful and flexible
- Good security features (sandboxed mode)
- Familiar to most Python developers

**Trade-offs**:
- ✅ **Pros**: Flexible, secure, well-documented
- ❌ **Cons**: Another dependency, learning curve for templates
- 🔄 **Mitigation**: Provide excellent default template, comprehensive docs

**Security Features**:
- Sandboxed environment prevents code execution
- Autoescape enabled by default
- Path validation before loading templates

**Alternatives Considered**:
1. **Plain Python strings**: Rejected due to lack of features
2. **Mustache**: Rejected as less powerful
3. **React/Vue SSG**: Rejected as too heavy and complex

---

## Technology Choices

### 1. UV/UVX for Distribution

**Decision**: Recommend `uvx` as primary installation method.

**Rationale**:
- No installation required
- Always latest version
- Avoids dependency conflicts
- Fast package resolution

**Trade-offs**:
- ✅ **Pros**: Frictionless user experience, no version conflicts
- ❌ **Cons**: Requires users to install `uv` first
- 🔄 **Mitigation**: Also support pip installation

**User Experience**:
```bash
# No installation
uvx marimushka export

vs.

# Traditional approach
pip install marimushka
marimushka export
```

**Alternatives Considered**:
1. **pipx**: Similar but `uv` is faster
2. **Docker**: Too heavy for simple CLI tool
3. **Binary distribution**: Complex to maintain across platforms

---

### 2. Typer for CLI

**Decision**: Use Typer for CLI framework.

**Rationale**:
- Automatic help generation
- Type hints for validation
- Rich terminal output integration
- Modern Python practices

**Trade-offs**:
- ✅ **Pros**: Great UX, type-safe, extensible
- ❌ **Cons**: Dependency overhead (small)
- 🔄 **Mitigation**: Benefits outweigh costs

**Alternatives Considered**:
1. **Click**: Rejected as Typer builds on Click with better DX
2. **argparse**: Rejected due to verbose API
3. **Fire**: Rejected due to less control over UX

---

### 3. Loguru for Logging

**Decision**: Use Loguru for structured logging.

**Rationale**:
- Beautiful colored output
- Simple API
- Structured logging support
- Rotation and retention features

**Trade-offs**:
- ✅ **Pros**: Better UX, simpler API than stdlib logging
- ❌ **Cons**: Another dependency
- 🔄 **Mitigation**: Widely used, stable library

**Alternatives Considered**:
1. **stdlib logging**: Rejected due to complex configuration
2. **structlog**: Rejected as more complex than needed
3. **Rich logging**: Considered but Loguru has better API

---

### 4. Pathlib Over os.path

**Decision**: Use `pathlib.Path` for all file operations.

**Rationale**:
- Modern Python idiom (3.4+)
- Object-oriented interface
- Cross-platform compatibility
- Better composability

**Trade-offs**:
- ✅ **Pros**: Cleaner code, fewer bugs, better API
- ❌ **Cons**: Slightly slower than `os.path` (negligible)
- 🔄 **Mitigation**: Performance difference is minimal

**Alternatives Considered**:
1. **os.path**: Rejected as less ergonomic
2. **Mixed approach**: Rejected for consistency

---

## Security Design

### 1. Sandbox Mode by Default

**Decision**: Enable sandbox mode by default for notebook exports.

**Rationale**:
- Reproducibility: Doesn't depend on local environment
- Security: Isolates notebook execution
- Best practice: Forces explicit dependency declaration

**Trade-offs**:
- ✅ **Pros**: Better security, reproducibility, portability
- ❌ **Cons**: Requires dependency metadata, slower first export
- 🔄 **Mitigation**: Clear docs, `--no-sandbox` escape hatch

**User Impact**:
```python
# Required in notebooks for sandbox mode
# /// script
# dependencies = ["pandas", "numpy"]
# ///
```

**Alternatives Considered**:
1. **No sandbox default**: Rejected due to security/reproducibility concerns
2. **Opt-in sandbox**: Rejected as users forget to enable

---

### 2. Path Traversal Protection

**Decision**: Validate all paths to prevent directory traversal attacks.

**Rationale**:
- Common vulnerability in file-handling tools
- Defense in depth
- User trust

**Implementation**:
```python
# Resolve to absolute path
path = Path(user_input).resolve()

# Verify within allowed directory
if not path.is_relative_to(base_dir):
    raise SecurityError("Path traversal attempt")
```

**Trade-offs**:
- ✅ **Pros**: Prevents directory traversal attacks
- ❌ **Cons**: Slight performance overhead (minimal)
- 🔄 **Mitigation**: Caching resolved paths

---

### 3. Subprocess Timeout Enforcement

**Decision**: All subprocess calls have configurable timeout (default 300s).

**Rationale**:
- Prevents indefinite hangs
- DoS protection
- Better user experience

**Trade-offs**:
- ✅ **Pros**: Prevents hangs, predictable behavior
- ❌ **Cons**: May timeout legitimate long-running notebooks
- 🔄 **Mitigation**: Configurable timeout, clear error messages

---

### 4. Bounded Parallelism

**Decision**: Limit parallel workers to 1-16 range.

**Rationale**:
- Prevents resource exhaustion
- DoS protection
- System stability

**Trade-offs**:
- ✅ **Pros**: Prevents system overload
- ❌ **Cons**: Caps maximum speedup
- 🔄 **Mitigation**: 16 workers sufficient for most cases

---

## Performance Trade-offs

### 1. Parallel vs Sequential Export

**Measurement**:
```
10 notebooks:
  Sequential: ~30s
  Parallel (4): ~8s
  Speedup: 3.75x

Overhead per notebook:
  Subprocess spawn: ~100ms
  Process pool: ~50ms
  Template render: ~200ms
```

**Trade-off Analysis**:
- Parallel overhead becomes negligible with >3 notebooks
- Memory usage: 4x (one process per worker)
- Worth it for typical projects (5+ notebooks)

---

### 2. Static vs WebAssembly Exports

**Measurement**:
```
Static HTML:
  Size: ~100 KB
  Load time: <100ms
  Interactive: No

WebAssembly:
  Size: ~2 MB
  Load time: ~1-2s
  Interactive: Yes
  Includes: Python runtime + libraries
```

**Trade-off**: Size vs interactivity
- Use static for documentation (fast, small)
- Use WASM for tutorials (interactive, larger)

---

### 3. Template Caching

**Decision**: Don't cache compiled templates (render on each export).

**Rationale**:
- Template changes are common during development
- Caching complexity not worth benefits
- Single export per run in CI/CD

**Trade-offs**:
- ✅ **Pros**: Simpler code, always up-to-date
- ❌ **Cons**: Re-parse template (~200ms overhead)
- 🔄 **Mitigation**: Template parsing is fast enough

**Alternatives Considered**:
1. **LRU cache**: Rejected due to added complexity
2. **File watcher invalidation**: Rejected as overkill

---

## API Design

### 1. Immutable `Notebook` Dataclass

**Decision**: Use `@dataclass(frozen=True)` for Notebook.

**Rationale**:
- Immutability prevents bugs
- Thread-safe for parallel export
- Clear intent

**Trade-offs**:
- ✅ **Pros**: Thread-safe, predictable, hashable
- ❌ **Cons**: Can't modify after creation
- 🔄 **Mitigation**: Create new instances if needed

---

### 2. Enum for Notebook Kinds

**Decision**: Use `Enum` for notebook types rather than strings.

**Rationale**:
- Type safety
- Autocomplete in IDEs
- Centralized command definitions

**Trade-offs**:
- ✅ **Pros**: Type-safe, self-documenting, IDE-friendly
- ❌ **Cons**: Slightly more verbose
- 🔄 **Mitigation**: Provide `from_str()` convenience method

---

### 3. Configuration Precedence

**Decision**: CLI flags > config file > defaults

**Rationale**:
- Matches user expectations
- Allows per-command overrides
- Common pattern in CLI tools

**Example**:
```bash
# Config file: max_workers = 4
uvx marimushka export --max-workers 8
# Uses 8 (CLI override)
```

---

## Future Considerations

### 1. Watch Mode Optimization

**Current**: Re-export all notebooks on any change

**Future**: Incremental export (only changed notebooks)

**Challenges**:
- Dependency tracking between notebooks
- Template changes affect all notebooks
- Complexity vs benefit trade-off

---

### 2. Plugin System

**Potential**: Allow custom export processors

**Example**:
```python
# Future API
@marimushka.register_processor
def pdf_export(notebook: Notebook) -> Path:
    # Custom PDF generation
    pass
```

**Considerations**:
- API stability
- Documentation burden
- Maintenance overhead

---

### 3. Remote Storage Backends

**Potential**: Direct export to S3, GCS, Azure Blob

**Example**:
```bash
# Future
uvx marimushka export --output s3://bucket/notebooks/
```

**Trade-offs**:
- Adds many dependencies
- Complex credential management
- Better as separate tool?

---

### 4. Notebook Validation

**Potential**: Pre-export validation (syntax, imports, metadata)

**Benefits**:
- Catch errors early
- Better user experience
- Faster iteration

**Challenges**:
- May be slow for large projects
- Duplicate work (marimo also validates)

---

## Design Principles

Throughout Marimushka's design, we follow these principles:

1. **Security First**: Default to secure options
2. **User Experience**: Optimize for common case, allow customization
3. **Performance**: Fast enough, not fastest possible
4. **Simplicity**: Prefer simple solutions over complex optimizations
5. **Compatibility**: Work across platforms and marimo versions
6. **Maintainability**: Code quality over cleverness

---

## Questions or Suggestions?

Have thoughts on these design decisions? [Open a discussion](https://github.com/jebel-quant/marimushka/discussions)!

Found a better approach? [Open an issue](https://github.com/jebel-quant/marimushka/issues) or [submit a PR](CONTRIBUTING.md)!

---

**Last updated**: 2025-01-15  
**Maintainers**: @Jebel-Quant team
