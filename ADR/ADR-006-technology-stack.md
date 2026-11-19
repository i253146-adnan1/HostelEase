# ADR-006: Technology Stack

**Status:** Accepted — Team-approved for D4  
**Date:** 2026-11-19  
**Project:** HostelEase

## 1. Context

The D3 architecture selected a layered monolith and relational database but did not select a specific backend framework or database engine.

The D4 implementation plan records the team's selection of Django and PostgreSQL for the local implementation.

## 2. Decision

The HostelEase implementation will use:

| Concern | Selected technology |
|---|---|
| Backend framework | Django 6.1.3 |
| Database | PostgreSQL |
| Frontend | Django templates, HTML, CSS and Bootstrap 5 |
| Authentication | Django authentication with server-side sessions |
| Database access | Django ORM and migrations |
| File storage | Django-managed local filesystem |
| Testing | Django test framework |
| Execution | Local development environment |

## 3. Architectural compatibility

This technology stack preserves ADR-001's accepted layered-monolith architecture.

The application remains a single deployable system organized into presentation, business-logic and data-access layers.

PostgreSQL is within the relational database family permitted by ADR-002.

Authentication continues to follow ADR-003. File storage continues to follow ADR-004.

No microservices, separate SPA architecture, payment gateway or unapproved external service will be introduced.

## 4. Consequences

- Django provides server-side request handling, templates, authentication and ORM support.
- PostgreSQL provides relational persistence and transactional database operations.
- Django migrations provide controlled schema-change history.
- The selected stack supports local execution and the project's acceptance-testing requirements.

## 5. Approval

This decision records the technology selection already approved in the D4 implementation plan.

**Related decisions:** ADR-001, ADR-002, ADR-003, ADR-004 and ADR-005.