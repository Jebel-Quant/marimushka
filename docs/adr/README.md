# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the marimushka project. ADRs document significant architectural decisions made during development, including the context, decision, and consequences.

## ADR Format

Each ADR follows this structure:

1. **Title**: Short descriptive title
2. **Status**: Proposed, Accepted, Deprecated, Superseded
3. **Context**: Background and problem being solved
4. **Decision**: The architectural decision made
5. **Consequences**: Positive and negative outcomes

## ADR Index

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](ADR-001-module-structure-refactoring.md) | Module Structure Refactoring | Accepted |
| [ADR-002](ADR-002-progress-callback-api.md) | Progress Callback API Design | Accepted |
| [ADR-003](ADR-003-security-model.md) | Security Model | Accepted |
| [ADR-004](ADR-004-template-system-design.md) | Template System Design | Accepted |
| [ADR-005](ADR-005-parallel-export-strategy.md) | Parallel Export Strategy | Accepted |

## Creating New ADRs

When making a significant architectural decision:

1. Copy the template from `ADR-template.md`
2. Number it sequentially (ADR-XXX)
3. Fill in all sections
4. Submit for review
5. Update this index when accepted

## References

- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) by Michael Nygard
- [ADR GitHub Organization](https://adr.github.io/)
