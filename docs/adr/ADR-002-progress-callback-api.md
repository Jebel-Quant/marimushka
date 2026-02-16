# ADR-002: Progress Callback API Design

**Status**: Accepted

**Date**: 2025-01-16

**Deciders**: Development Team

## Context

Users need visibility into export progress for several reasons:

1. **Long-running operations**: Exporting multiple notebooks can take minutes
2. **User experience**: Users want feedback that the system is working
3. **Integration**: Applications embedding marimushka need progress updates
4. **Debugging**: Progress info helps identify which notebook causes issues

Initial implementation had no progress reporting, leading to:
- Users uncertain if the tool was working or hanging
- No way to track progress in automated scripts
- Poor experience when exporting many notebooks
- Difficulty debugging export failures

We needed to design an API that:
- Provides meaningful progress information
- Works with both parallel and sequential exports
- Doesn't impact performance significantly
- Remains simple for users to implement
- Integrates well with existing progress libraries (Rich, tqdm, etc.)

## Decision

We implemented a callback-based progress API with the following design:

### API Signature

```python
ProgressCallback = Callable[[int, int, str], None]

def main(
    ...
    on_progress: ProgressCallback | None = None,
) -> str:
    """
    Args:
        on_progress: Optional callback called after each notebook export.
                    Signature: on_progress(completed, total, notebook_name)
    """
```

### Callback Parameters

1. **`completed: int`**: Number of notebooks completed so far
2. **`total: int`**: Total number of notebooks in current batch
3. **`notebook_name: str`**: Name of the notebook just completed

### Integration Points

Callbacks are invoked at these points:

1. **After each notebook export** (parallel or sequential)
2. **Regardless of success/failure** (user can check results separately)
3. **With thread safety** (in parallel mode, callback may be called from multiple threads)

### Rich Progress Bar

Internal implementation uses Rich Progress for visual feedback:

```python
with Progress(...) as progress:
    task = progress.add_task("[green]Exporting notebooks...", total=total_notebooks)

    for result in completed_exports:
        if on_progress:
            on_progress(completed, total, notebook_name)
        progress.advance(task)
```

## Consequences

### Positive

1. **Simple API**
   - Three parameters, easy to understand
   - No complex state management
   - Works with any progress tracking system

2. **Flexible Integration**
   - Users can log to files
   - Can update custom UI
   - Can send webhooks/notifications
   - Can integrate with any progress library

3. **Non-blocking**
   - Callback doesn't slow down exports
   - Parallel exports remain parallel
   - Minimal performance overhead

4. **Debuggability**
   - Users can log progress for debugging
   - Easy to track which notebook is processing
   - Helps identify slow exports

5. **Testable**
   - Easy to test with mock callbacks
   - Can verify callback invocations
   - Clear expectations for test assertions

### Negative

1. **Thread Safety Required**
   - Callbacks in parallel mode may run concurrently
   - Users must handle thread safety in their callbacks
   - Documentation needed to explain this

2. **Limited Information**
   - Only provides counts and names
   - No timing information
   - No success/failure status
   - (By design - keeps API simple)

3. **No Built-in Rate Limiting**
   - Callback called for every notebook
   - Could be overwhelming with many notebooks
   - Users must implement their own rate limiting if needed

4. **No Progress for Individual Exports**
   - Callback only at notebook boundaries
   - No progress within a single notebook export
   - (Limitation of marimo CLI - no progress output)

### Mitigation Strategies

1. **Documentation**
   - Clear examples in docstrings
   - Warning about thread safety
   - Integration examples with Rich and tqdm

2. **Example Implementations**
   ```python
   # Simple logging
   def log_progress(completed, total, name):
       print(f"[{completed}/{total}] Exported {name}")

   # Rich integration
   def rich_progress(completed, total, name):
       console.log(f"Completed {name}")

   # Thread-safe counter
   from threading import Lock
   lock = Lock()
   def safe_progress(completed, total, name):
       with lock:
           # Update shared state safely
           pass
   ```

3. **Internal Progress Bar**
   - Rich progress bar for CLI users
   - Works independently of callback
   - Provides visual feedback by default

4. **Result Objects**
   - `BatchExportResult` provides full details
   - Users can check success/failure after completion
   - Separates progress from results

## Alternatives Considered

### Alternative 1: Event-Based System

```python
class ProgressEvent:
    completed: int
    total: int
    notebook: Notebook
    success: bool
    duration: float
```

**Pros**: More information, extensible, type-safe
**Cons**: Over-engineered, complex for simple use cases, harder to use

**Rejected because**: Too complex for the common case. Users typically just want counts and names.

### Alternative 2: Generator Pattern

```python
for result in export_notebooks(...):
    # User processes each result as it completes
    print(f"Exported {result.notebook_path}")
```

**Pros**: Pythonic, flexible, easy to understand
**Cons**: Changes API significantly, harder to use with parallel exports, blocking

**Rejected because**: Would require restructuring the entire export API and doesn't work well with parallel execution.

### Alternative 3: Observable/RxPY Pattern

```python
progress$ = export_notebooks_observable(...)
progress$.subscribe(on_next=lambda p: print(p.completed))
```

**Pros**: Reactive, composable, powerful
**Cons**: Heavy dependency, unfamiliar to most Python developers, overkill

**Rejected because**: Adds significant complexity and dependency. Not idiomatic Python.

### Alternative 4: Context Manager Protocol

```python
with ProgressTracker() as tracker:
    main(..., progress_tracker=tracker)
    # tracker updates automatically
```

**Pros**: Clean API, resource management
**Cons**: More complex, less flexible, harder to integrate

**Rejected because**: Callbacks are simpler and more flexible for this use case.

## Examples

### Basic Usage

```python
from marimushka.export import main

def progress_callback(completed, total, name):
    print(f"Progress: {completed}/{total} - {name}")

main(
    notebooks="notebooks",
    on_progress=progress_callback
)
```

### Integration with Rich

```python
from rich.console import Console
from marimushka.export import main

console = Console()

def rich_progress(completed, total, name):
    console.log(f"[green]✓[/green] {name} ({completed}/{total})")

main(
    notebooks="notebooks",
    on_progress=rich_progress
)
```

### Thread-Safe Logging

```python
import logging
from threading import Lock
from marimushka.export import main

logger = logging.getLogger(__name__)
lock = Lock()

def safe_log_progress(completed, total, name):
    with lock:
        logger.info(f"Exported {name}: {completed}/{total}")

main(
    notebooks="notebooks",
    parallel=True,
    on_progress=safe_log_progress
)
```

## Related Decisions

- [ADR-001: Module Structure Refactoring](ADR-001-module-structure-refactoring.md) - Enabled separation of progress concerns
- [ADR-005: Parallel Export Strategy](ADR-005-parallel-export-strategy.md) - Progress callbacks work with parallel exports

## Notes

- Callbacks are optional - default behavior shows Rich progress bar
- Internal Rich progress and user callbacks work together
- Thread safety is user's responsibility in parallel mode
- Simple by design - can be extended via wrapper functions if needed
