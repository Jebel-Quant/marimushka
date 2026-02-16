# ADR-005: Parallel Export Strategy

**Status**: Accepted

**Date**: 2025-01-19

**Deciders**: Development Team

## Context

Exporting notebooks is I/O-bound:
- Subprocess calls to `uvx marimo export`
- Network access to download dependencies (in sandbox mode)
- File writing to disk
- Template rendering (CPU-bound but fast)

Problems with sequential export:
- 10 notebooks × 2 seconds each = 20 seconds total
- Poor CPU/network utilization
- User perception of slowness
- Wasted time when notebooks are independent

Requirements:
- Faster export for multiple notebooks
- Maintain result tracking
- Handle failures gracefully
- Support progress callbacks
- Remain testable

## Decision

Implement **parallel export using ThreadPoolExecutor**:

### Architecture

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def export_notebooks_parallel(
    notebooks: list[Notebook],
    max_workers: int = 4,
    ...
) -> BatchExportResult:
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(export_notebook, nb, ...): nb
            for nb in notebooks
        }

        for future in as_completed(futures):
            result = future.result()
            batch_result.add(result)
            # Progress callback, Rich progress update
```

### Design Decisions

1. **ThreadPoolExecutor over ProcessPoolExecutor**
   - Notebooks export via subprocess anyway (no Python GIL benefit from processes)
   - Threads share memory (easier result collection)
   - Lower overhead than processes
   - Simpler pickling/serialization

2. **Worker Count: Default 4, Max 16**
   - 4 workers = good balance for typical machines
   - 16 max prevents resource exhaustion
   - Configurable for user's hardware
   - Validated and bounded automatically

3. **as_completed() for Result Collection**
   - Process results as they finish (not in submission order)
   - Better progress feedback
   - More responsive UI
   - Natural fit for progress callbacks

4. **Optional Parallel Mode**
   - `parallel=True` (default) for speed
   - `parallel=False` for debugging
   - Sequential mode available when needed
   - Same API for both modes

### Safety Measures

- **Worker bounds**: 1-16 workers enforced
- **Error isolation**: One notebook failure doesn't affect others
- **Resource cleanup**: ThreadPoolExecutor context manager ensures cleanup
- **Progress tracking**: Thread-safe progress updates
- **Audit logging**: All operations logged

## Consequences

### Positive

1. **Performance**
   - 10 notebooks: ~20s sequential → ~6s parallel (4 workers)
   - Near-linear speedup for I/O-bound operations
   - Better resource utilization

2. **User Experience**
   - Faster exports
   - More responsive
   - Progress updates feel smoother

3. **Scalability**
   - Handles many notebooks well
   - Configurable for different hardware
   - Bounded for safety

4. **Maintained Simplicity**
   - Still returns same `BatchExportResult`
   - Progress callbacks work identically
   - API unchanged

### Negative

1. **Thread Safety Requirements**
   - Progress callbacks may execute concurrently
   - Users must handle thread safety in callbacks
   - Rich progress bar requires thread-safe updates

2. **Non-Deterministic Order**
   - Results complete in arbitrary order
   - Progress callbacks invoked out-of-order
   - Logs may be interleaved

3. **Debugging Complexity**
   - Harder to debug than sequential
   - Errors from multiple threads
   - Why `parallel=False` option exists

4. **Resource Usage**
   - Uses more memory (4 processes + main thread)
   - More CPU during export
   - Not always faster for small counts

## Performance Characteristics

### Speedup Factor

| Notebooks | Sequential | Parallel (4) | Speedup |
|-----------|------------|--------------|---------|
| 1         | 2s         | 2s           | 1.0x    |
| 2         | 4s         | 2s           | 2.0x    |
| 4         | 8s         | 2s           | 4.0x    |
| 8         | 16s        | 4s           | 4.0x    |
| 16        | 32s        | 8s           | 4.0x    |

(Assumes 2s per notebook, negligible overhead)

### When to Use Sequential

- **Debugging**: Need predictable execution order
- **Limited Resources**: Single-core machine or low memory
- **Few Notebooks**: 1-2 notebooks see no benefit
- **Explicit Testing**: Want deterministic test behavior

## Alternatives Considered

**ProcessPoolExecutor**: Unnecessary overhead, no GIL benefit
**asyncio**: Complex for subprocess I/O, no clear advantage
**Multiprocessing.Pool**: Similar to ProcessPoolExecutor
**No parallelism**: Too slow for production use
**Always parallel**: Need sequential option for debugging

## Implementation Details

### Export Function Signature

```python
def export_notebooks_parallel(
    notebooks: list[Notebook],
    output_dir: Path,
    sandbox: bool,
    bin_path: Path | None,
    max_workers: int = 4,
    progress: Progress | None = None,
    task_id: TaskID | None = None,
    timeout: int = 300,
    on_progress: ProgressCallback | None = None,
) -> BatchExportResult:
```

### Sequential Alternative

```python
def export_notebooks_sequential(
    # Same parameters except max_workers
) -> BatchExportResult:
    for nb in notebooks:
        result = nb.export(...)
        batch_result.add(result)
        if on_progress:
            on_progress(...)
```

Both return same `BatchExportResult` type.

## Testing Strategy

- **Unit tests**: Mock ThreadPoolExecutor behavior
- **Integration tests**: Real parallel exports with test notebooks
- **Property tests**: Verify parallel = sequential results (eventually)
- **Performance tests**: Measure actual speedup
- **Thread safety tests**: Verify no race conditions

## Related ADRs

- [ADR-002: Progress Callback API](ADR-002-progress-callback-api.md) - Callbacks work with parallel
- [ADR-001: Module Structure](ADR-001-module-structure-refactoring.md) - Orchestrator module
- [ADR-003: Security Model](ADR-003-security-model.md) - Worker count bounds

## Notes

- Default parallel mode covers 90% of use cases
- Sequential mode available when needed
- Future: Could add process pools for CPU-bound post-processing
- ThreadPoolExecutor is stdlib, no extra dependencies
