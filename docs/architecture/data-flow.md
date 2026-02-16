# Data Flow Architecture

This document describes the data flow through the marimushka system using Mermaid diagrams. These diagrams illustrate how data moves between components during various operations.

## Export Process Flow

The main export process handles notebook export from input to HTML output:

```mermaid
flowchart TB
    Start([User calls main]) --> LoadConfig[Load Configuration]
    LoadConfig --> InitAudit[Initialize AuditLogger]
    InitAudit --> ValidateTemplate[Validate Template File]
    ValidateTemplate --> DiscoverNotebooks[Discover Notebooks<br/>folder2notebooks]

    DiscoverNotebooks --> CheckEmpty{Any notebooks<br/>found?}
    CheckEmpty -->|No| ReturnEmpty([Return empty string])
    CheckEmpty -->|Yes| GenerateIndex[Generate Index]

    GenerateIndex --> ExportAll[Export All Notebooks]

    ExportAll --> ParallelCheck{Parallel<br/>export?}
    ParallelCheck -->|Yes| ParallelExport[Export Notebooks Parallel]
    ParallelCheck -->|No| SequentialExport[Export Notebooks Sequential]

    ParallelExport --> ThreadPool[ThreadPoolExecutor]
    ThreadPool --> ExportWorkers[Multiple Export Workers]
    ExportWorkers --> NotebookExport[Notebook.export]

    SequentialExport --> NotebookExport

    NotebookExport --> BuildCommand[Build marimo Command]
    BuildCommand --> RunSubprocess[Run uvx marimo export]
    RunSubprocess --> CaptureOutput[Capture stdout/stderr]
    CaptureOutput --> CheckReturnCode{Return<br/>code == 0?}

    CheckReturnCode -->|No| LogFailure[Log Export Failure]
    CheckReturnCode -->|Yes| SetPermissions[Set File Permissions]

    LogFailure --> ResultFailed[NotebookExportResult.failed]
    SetPermissions --> LogSuccess[Log Export Success]
    LogSuccess --> ResultSuccess[NotebookExportResult.succeeded]

    ResultFailed --> BatchResult[BatchExportResult]
    ResultSuccess --> BatchResult

    BatchResult --> AllComplete{All<br/>complete?}
    AllComplete -->|No| ExportWorkers
    AllComplete -->|Yes| RenderTemplate[Render Jinja2 Template]

    RenderTemplate --> WriteIndex[Write index.html]
    WriteIndex --> ReturnHTML([Return HTML string])

    style Start fill:#e1f5e1
    style ReturnEmpty fill:#ffe1e1
    style ReturnHTML fill:#e1f5e1
    style NotebookExport fill:#fff4e1
    style RenderTemplate fill:#e1e5ff
    style BatchResult fill:#f0e1ff
```

## Watch Mode Flow

Watch mode monitors filesystem changes and triggers re-exports:

```mermaid
flowchart TB
    Start([marimushka watch]) --> InitWatcher[Initialize File Watcher<br/>watchfiles]
    InitWatcher --> RegisterPaths[Register Watch Paths<br/>notebooks, apps, notebooks_wasm]

    RegisterPaths --> WaitForChange[Wait for File Change]
    WaitForChange --> ChangeDetected{Change<br/>detected?}

    ChangeDetected -->|No| WaitForChange
    ChangeDetected -->|Yes| DebounceWait[Debounce Timer<br/>wait 100ms]

    DebounceWait --> MoreChanges{More changes<br/>pending?}
    MoreChanges -->|Yes| DebounceWait
    MoreChanges -->|No| LogChange[Log Changed Files]

    LogChange --> CheckFileType{File type?}
    CheckFileType -->|.py| TriggerExport[Trigger Export]
    CheckFileType -->|.j2/.jinja2| TriggerExport
    CheckFileType -->|Other| WaitForChange

    TriggerExport --> CallMain[Call main function]
    CallMain --> ExportProcess[Full Export Process]
    ExportProcess --> ReportResult{Export<br/>successful?}

    ReportResult -->|Yes| LogSuccess[Log Success Message]
    ReportResult -->|No| LogError[Log Error Message]

    LogSuccess --> WaitForChange
    LogError --> WaitForChange

    style Start fill:#e1f5e1
    style WaitForChange fill:#fff4e1
    style ExportProcess fill:#e1e5ff
    style LogSuccess fill:#e1f5e1
    style LogError fill:#ffe1e1
```

## Template Rendering Flow

Template rendering processes notebook data into HTML:

```mermaid
flowchart TB
    Start([render_template]) --> LoadTemplate[Load Jinja2 Template]
    LoadTemplate --> CreateSandbox[Create SandboxedEnvironment]

    CreateSandbox --> GetTemplate[Get Template Instance]
    GetTemplate --> PrepareContext[Prepare Template Context]

    PrepareContext --> ContextNotebooks[notebooks: list]
    PrepareContext --> ContextApps[apps: list]
    PrepareContext --> ContextWasm[notebooks_wasm: list]

    ContextNotebooks --> RenderTemplate[template.render]
    ContextApps --> RenderTemplate
    ContextWasm --> RenderTemplate

    RenderTemplate --> ProcessVars[Process Template Variables]
    ProcessVars --> LoopNotebooks{For each<br/>notebook}

    LoopNotebooks --> AccessProps[Access Notebook Properties]
    AccessProps --> DisplayName[display_name]
    AccessProps --> HTMLPath[html_path]
    AccessProps --> NotebookPath[path]
    AccessProps --> NotebookKind[kind]

    DisplayName --> RenderHTML[Render HTML Elements]
    HTMLPath --> RenderHTML
    NotebookPath --> RenderHTML
    NotebookKind --> RenderHTML

    RenderHTML --> MoreNotebooks{More<br/>notebooks?}
    MoreNotebooks -->|Yes| LoopNotebooks
    MoreNotebooks -->|No| FinalHTML[Complete HTML String]

    FinalHTML --> LogAudit[Log Template Render Event]
    LogAudit --> ReturnHTML([Return HTML])

    style Start fill:#e1f5e1
    style CreateSandbox fill:#fff4e1
    style RenderTemplate fill:#e1e5ff
    style ReturnHTML fill:#e1f5e1
```

## Progress Callback Flow

Progress callbacks notify users of export progress:

```mermaid
flowchart TB
    Start([Export Started]) --> InitProgress[Initialize Progress Tracking]
    InitProgress --> CountTotal[Count Total Notebooks]

    CountTotal --> StartExport[Begin Export Loop]
    StartExport --> ExportNotebook[Export Single Notebook]

    ExportNotebook --> IncrementCompleted[Increment Completed Count]
    IncrementCompleted --> CheckCallback{Progress<br/>callback<br/>provided?}

    CheckCallback -->|No| UpdateProgress
    CheckCallback -->|Yes| CallCallback[Call on_progress callback]

    CallCallback --> PassParams[Pass Parameters:<br/>completed, total, name]
    PassParams --> UserFunction[User Function Executes]
    UserFunction --> UserActions[User Actions:<br/>- Log progress<br/>- Update UI<br/>- Send notifications]

    UserActions --> UpdateProgress[Update Rich Progress Bar]
    UpdateProgress --> MoreNotebooks{More<br/>notebooks?}

    MoreNotebooks -->|Yes| ExportNotebook
    MoreNotebooks -->|No| FinalCallback{Final<br/>callback?}

    FinalCallback -->|Yes| CallFinal[Call callback<br/>completed == total]
    FinalCallback -->|No| Complete

    CallFinal --> Complete([Export Complete])

    style Start fill:#e1f5e1
    style CallCallback fill:#fff4e1
    style UserFunction fill:#e1e5ff
    style Complete fill:#e1f5e1
```

## Audit Logging Flow

Audit logging tracks security-relevant events:

```mermaid
flowchart TB
    Start([Security Event Occurs]) --> CreateEntry[Create Audit Entry]
    CreateEntry --> AddTimestamp[Add UTC Timestamp]
    AddTimestamp --> AddEventType[Add Event Type]

    AddEventType --> AddDetails[Add Event Details]
    AddDetails --> CheckEnabled{Audit<br/>logging<br/>enabled?}

    CheckEnabled -->|No| Skip([Skip Logging])
    CheckEnabled -->|Yes| LogStructured[Log to Structured Logger<br/>loguru]

    LogStructured --> CheckFile{Log file<br/>configured?}
    CheckFile -->|No| Complete
    CheckFile -->|Yes| WriteFile[Write JSON to File]

    WriteFile --> AppendMode[Open in Append Mode]
    AppendMode --> SerializeJSON[Serialize Entry to JSON]
    SerializeJSON --> WriteLine[Write Line + Newline]

    WriteLine --> FlushBuffer[Flush Buffer]
    FlushBuffer --> CheckError{Write<br/>successful?}

    CheckError -->|No| LogError[Log Error to stderr]
    CheckError -->|Yes| Complete([Audit Logged])

    LogError --> Complete

    style Start fill:#e1f5e1
    style LogStructured fill:#fff4e1
    style WriteFile fill:#e1e5ff
    style Complete fill:#e1f5e1
    style Skip fill:#ffe1e1
```

## Dependency Injection Flow

Dependency injection provides components with their dependencies:

```mermaid
flowchart TB
    Start([Application Start]) --> CreateDeps{Create<br/>Dependencies}

    CreateDeps -->|Default| DefaultFactory[create_dependencies]
    CreateDeps -->|From File| FileFactory[create_dependencies_from_config_file]
    CreateDeps -->|Test| TestFactory[create_test_dependencies]
    CreateDeps -->|Custom| CustomFactory[Dependencies constructor]

    DefaultFactory --> CheckAuditLog{Audit log<br/>path<br/>provided?}
    CheckAuditLog -->|Yes| CreateAudit[Create AuditLogger<br/>with log file]
    CheckAuditLog -->|No| DefaultAudit[Use default AuditLogger]

    CreateAudit --> CheckConfig{Config<br/>provided?}
    DefaultAudit --> CheckConfig

    CheckConfig -->|Yes| UseConfig[Use provided config]
    CheckConfig -->|No| DefaultConfig[Create default MarimushkaConfig]

    UseConfig --> BuildDeps[Build Dependencies Instance]
    DefaultConfig --> BuildDeps

    FileFactory --> LoadTOML[Load TOML Config]
    LoadTOML --> ParseConfig[Parse Configuration]
    ParseConfig --> ExtractAudit[Extract Audit Settings]
    ExtractAudit --> ExtractConfig[Extract Config Values]
    ExtractConfig --> BuildDeps

    TestFactory --> CreateTestAudit[Create test AuditLogger<br/>in tmp_dir]
    CreateTestAudit --> DefaultTestConfig[Use default config]
    DefaultTestConfig --> BuildDeps

    CustomFactory --> DirectConstruct[Direct Construction]
    DirectConstruct --> BuildDeps

    BuildDeps --> DepsReady[Dependencies Ready]
    DepsReady --> PassToMain[Pass to main function]

    PassToMain --> InjectOrchestrator[Inject into orchestrator]
    InjectOrchestrator --> InjectNotebook[Inject into notebook.export]
    InjectNotebook --> InjectValidators[Inject into validators]

    InjectValidators --> UseComponents[Components Use Dependencies]
    UseComponents --> AuditEvents[Audit events logged]
    UseComponents --> ConfigSettings[Config settings applied]

    AuditEvents --> Complete([Execution Complete])
    ConfigSettings --> Complete

    style Start fill:#e1f5e1
    style BuildDeps fill:#fff4e1
    style DepsReady fill:#e1e5ff
    style Complete fill:#e1f5e1
```

## Key Data Structures

### NotebookExportResult

```python
@dataclass(frozen=True)
class NotebookExportResult:
    notebook_path: Path      # Input notebook
    success: bool            # Export succeeded?
    output_path: Path | None # HTML output (if success)
    error: ExportError | None # Error details (if failure)
```

### BatchExportResult

```python
@dataclass
class BatchExportResult:
    results: list[NotebookExportResult]  # All results

    @property
    def total(self) -> int               # Count of all
    def succeeded(self) -> int           # Count of successes
    def failed(self) -> int              # Count of failures
    def all_succeeded(self) -> bool      # All successful?
    def failures(self) -> list           # Failed results
    def successes(self) -> list          # Successful results
```

### Dependencies

```python
@dataclass
class Dependencies:
    audit_logger: AuditLogger             # Audit event logger
    config: MarimushkaConfig              # Configuration settings

    def with_audit_logger(...)            # Update audit logger
    def with_config(...)                  # Update config
```

## Performance Characteristics

### Parallel Export

- **Concurrency**: ThreadPoolExecutor with configurable workers (default: 4)
- **Bounded**: Worker count limited to 1-16 for security
- **Non-blocking**: Progress callbacks don't block export threads
- **Error isolation**: Individual notebook failures don't affect others

### Sequential Export

- **Deterministic**: Predictable order for debugging
- **Lower overhead**: No thread pool management
- **Simpler debugging**: Easier to trace execution
- **Progress tracking**: Callbacks in exact notebook order

### Template Rendering

- **Sandboxed**: SandboxedEnvironment prevents code execution
- **Single pass**: All notebooks rendered in one template pass
- **Memory efficient**: Lazy iteration over notebook lists
- **Fast**: Jinja2 optimized rendering

## Error Handling

All flows include error handling at each step:

1. **Validation errors** → TemplateNotFoundError, NotebookInvalidError
2. **Export errors** → ExportSubprocessError, ExportExecutableNotFoundError
3. **Rendering errors** → TemplateRenderError
4. **I/O errors** → IndexWriteError
5. **Security errors** → Caught and sanitized before logging

Each error is:
- Logged with sanitized paths
- Captured in audit log
- Included in result objects
- Propagated with context
