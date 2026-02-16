# ADR-003: Security Model

**Status**: Accepted

**Date**: 2025-01-17

**Deciders**: Development Team

## Context

Marimushka processes user-provided files (notebooks, templates), executes subprocesses (marimo export), and writes files to disk. This introduces several security concerns:

1. **Path Traversal**: Malicious paths like `../../etc/passwd` could access unintended files
2. **Code Execution**: Template injection could execute arbitrary Python code
3. **DoS Attacks**: Extremely large files could exhaust memory/disk
4. **Subprocess Security**: Command injection or unintended executable execution
5. **File Permissions**: Exported files might have overly permissive permissions
6. **TOCTOU Races**: Time-of-check-time-of-use vulnerabilities
7. **Information Leakage**: Error messages exposing sensitive paths

Without proper security measures:
- Users could accidentally or intentionally access files outside intended directories
- Template authors could execute arbitrary code
- System resources could be exhausted
- Sensitive information could leak in error messages
- Security audits would be impossible

## Decision

We implemented a comprehensive security model with multiple layers:

### 1. Path Validation (`security.py`)

**Path Traversal Prevention**:
```python
def validate_path_traversal(path: Path, base_dir: Path | None) -> Path:
    """Validates paths don't escape base directory."""
    resolved = path.resolve(strict=False)
    if base_dir:
        resolved.relative_to(base_dir.resolve(strict=False))
    return resolved
```

Applied to:
- Template paths
- Output directories
- Notebook paths
- Binary paths

**File Validation**:
```python
def validate_file_path(file_path: Path, allowed_extensions: list[str] | None) -> Path:
    """Validates file existence, type, and extension."""
```

Checks:
- File exists
- Is regular file (not directory, symlink, device)
- Has allowed extension

**Binary Path Validation**:
```python
def validate_bin_path(bin_path: Path, whitelist: list[Path] | None) -> Path:
    """Validates binary directories with optional whitelist."""
```

### 2. Sandboxing

**Jinja2 Template Sandboxing**:
```python
env = SandboxedEnvironment(
    loader=jinja2.FileSystemLoader(template_dir),
    autoescape=jinja2.select_autoescape(["html", "xml"])
)
```

- Prevents code execution in templates
- Enforces autoescape for HTML/XML
- Restricts available functions/filters

**Marimo Sandbox Mode**:
```python
cmd = ["uvx", "marimo", "export", "html", "--sandbox", ...]
```

- Runs notebooks in isolated environment
- Prevents access to system resources
- Configurable per export

### 3. Resource Limits

**File Size Limits**:
```python
def validate_file_size(file_path: Path, max_size_bytes: int = 10MB) -> bool:
    """Prevents processing of oversized files."""
```

- Default 10MB limit for templates
- Configurable via `max_file_size_mb`
- Prevents DoS via large files

**Worker Bounds**:
```python
def validate_max_workers(max_workers: int, min_workers: int = 1, max_allowed: int = 16) -> int:
    """Bounds parallel worker count."""
```

- Minimum 1 worker
- Maximum 16 workers (prevents resource exhaustion)
- Automatic clamping to valid range

**Subprocess Timeout**:
```python
result = subprocess.run(cmd, timeout=timeout)  # Default 300s
```

- Prevents hanging processes
- Configurable timeout
- Graceful cleanup on timeout

### 4. Secure File Operations

**Safe File Opening**:
```python
def safe_open_file(file_path: Path, mode: str) -> int:
    """Opens file with O_NOFOLLOW to prevent symlink attacks."""
    fd = os.open(file_path, flags | os.O_NOFOLLOW, mode=0o600)
    return fd
```

**Secure Permissions**:
```python
def set_secure_file_permissions(file_path: Path, mode: int = 0o644) -> None:
    """Sets restrictive permissions on exported files."""
```

- Default 644 (rw-r--r--)
- Owner has write, others read-only
- Configurable via `file_permissions`

### 5. Input Sanitization

**Error Message Sanitization**:
```python
def sanitize_error_message(error_msg: str, sensitive_patterns: list[str] | None) -> str:
    """Removes absolute paths and sensitive info from error messages."""
    # Redacts: /home/user/secret/file.py -> <redacted_path>/file.py
```

- Removes absolute paths
- Keeps filenames for debugging
- Custom pattern redaction
- Prevents information leakage

### 6. Audit Logging

**Structured Audit Trail**:
```python
class AuditLogger:
    def log_path_validation(...)
    def log_export(...)
    def log_template_render(...)
    def log_file_access(...)
```

- All security-relevant operations logged
- JSON format for parsing
- UTC timestamps
- Optional file output
- Success/failure tracking

### 7. Configuration Security

**Security Settings in Config**:
```toml
[marimushka.security]
audit_enabled = true
audit_log = "audit.log"
max_file_size_mb = 10
file_permissions = "0o644"
```

- Centralized security configuration
- Explicit enable/disable
- Documented defaults
- Override in special cases

## Consequences

### Positive

1. **Defense in Depth**
   - Multiple security layers
   - One breach doesn't compromise system
   - Complementary protections

2. **Auditability**
   - All operations logged
   - Can trace security events
   - Facilitates compliance
   - Helps debugging security issues

3. **Configurable Security**
   - Can tighten for production
   - Can relax for development
   - Explicit configuration
   - Sensible defaults

4. **Safe by Default**
   - Sandboxing enabled by default
   - Path validation always on
   - Resource limits enforced
   - Secure permissions set automatically

5. **Prevention of Common Vulnerabilities**
   - Path traversal blocked
   - Code injection prevented
   - DoS mitigated
   - TOCTOU races reduced
   - Information leakage minimized

6. **Compliance Ready**
   - Audit logs for compliance
   - Security configurations documented
   - Best practices followed
   - Security-first design

### Negative

1. **Performance Overhead**
   - Path validation adds checks
   - Sandboxing is slower than direct execution
   - File operations have extra steps
   - (Overhead is minimal, ~1-2%)

2. **Complexity**
   - More code to maintain
   - Security module adds concepts
   - Configuration options more complex
   - Learning curve for contributors

3. **Potential False Positives**
   - Valid paths might be rejected
   - Legitimate use cases might be blocked
   - Requires configuration understanding

4. **Testing Burden**
   - Security features need thorough testing
   - Edge cases must be covered
   - Mock setups more complex

### Mitigation Strategies

1. **Comprehensive Testing**
   - Dedicated `test_security.py`
   - Property-based testing for edge cases
   - Integration tests for real scenarios
   - Current: 89% coverage in security.py

2. **Clear Documentation**
   - Security model documented in ADR
   - Configuration options explained
   - Examples for common scenarios
   - Warnings about security implications

3. **Gradual Degradation**
   - Can disable sandboxing if needed
   - Audit logging optional (enabled by default)
   - Resource limits configurable
   - Balance security vs usability

4. **Error Messages**
   - Clear errors when security blocks action
   - Explain what was blocked and why
   - Suggest valid alternatives
   - Don't leak sensitive information

## Security Threat Model

### Threats Addressed

1. **T1: Malicious Template**
   - **Threat**: Template executes arbitrary code
   - **Mitigation**: Jinja2 SandboxedEnvironment
   - **Residual Risk**: Low - sandbox prevents code execution

2. **T2: Path Traversal**
   - **Threat**: Access files outside intended directories
   - **Mitigation**: Path validation, relative path checks
   - **Residual Risk**: Very Low - comprehensive validation

3. **T3: Resource Exhaustion**
   - **Threat**: DoS via large files or many workers
   - **Mitigation**: File size limits, worker bounds, timeouts
   - **Residual Risk**: Low - multiple limits enforced

4. **T4: Code Injection**
   - **Threat**: Inject code via notebook or subprocess
   - **Mitigation**: Marimo sandbox, subprocess validation
   - **Residual Risk**: Low - marimo sandbox trusted

5. **T5: Information Disclosure**
   - **Threat**: Leak sensitive paths in errors
   - **Mitigation**: Error sanitization, audit logging
   - **Residual Risk**: Low - paths redacted systematically

6. **T6: Permission Escalation**
   - **Threat**: Create world-writable files
   - **Mitigation**: Explicit permission setting (644)
   - **Residual Risk**: Very Low - enforced on all outputs

7. **T7: TOCTOU Race Conditions**
   - **Threat**: File replaced between check and use
   - **Mitigation**: O_NOFOLLOW, avoid symlinks
   - **Residual Risk**: Low - symlinks rejected

### Threats Not Addressed

1. **Network Attacks**: Marimushka doesn't make network calls
2. **Privilege Escalation**: Runs with user's permissions
3. **Supply Chain**: Trusts uvx, marimo, dependencies
4. **Physical Access**: Can't protect against local root user

## Alternatives Considered

### Alternative 1: No Security Features

**Pros**: Simpler code, better performance
**Cons**: Vulnerable to all threats, unusable in production

**Rejected because**: Unacceptable security posture for any production use.

### Alternative 2: Containers/VMs Only

**Pros**: Strong isolation
**Cons**: Requires Docker/VM, complex setup, slow

**Rejected because**: Overkill for CLI tool. Security at wrong layer.

### Alternative 3: Whitelist Everything

**Pros**: Maximum security
**Cons**: Unusable - users must configure every path

**Rejected because**: Too restrictive. Security should be transparent.

### Alternative 4: Capability-Based Security

**Pros**: Fine-grained control, explicit permissions
**Cons**: Complex implementation, Python ecosystem not designed for it

**Rejected because**: Not practical in Python. Better suited for systems languages.

## Related Decisions

- [ADR-001: Module Structure Refactoring](ADR-001-module-structure-refactoring.md) - Enabled `security.py` module
- [ADR-004: Template System Design](ADR-004-template-system-design.md) - Sandboxed templates
- All ADRs benefit from security infrastructure

## Compliance Considerations

This security model supports:

- **OWASP Top 10**: Addresses injection, broken access control, security misconfiguration
- **CWE**: Prevents common weakness types (path traversal, code injection)
- **Security Audits**: Audit logs facilitate reviews
- **Least Privilege**: Minimal permissions by default

## Notes

- Security is never "done" - requires ongoing vigilance
- New features should consider security implications
- Regular security reviews recommended
- Report security issues privately to maintainers
