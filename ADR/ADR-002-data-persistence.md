# ADR-002: Data Persistence

- **ADR ID:** ADR-002
- **Full name:** Data Persistence
- **Status:** Accepted
- **Date:** 2026-11-12
- **Project:** HostelEase — Hostel Management Website
- **Related decisions:** ADR-001 (Architecture Style); ADR-004 (File Storage Approach)
- **Related requirements:** FR-01 to FR-19; BR-04 to BR-05; BR-10; NFR-01 to NFR-02; C-04

## 1. Context

HostelEase is a hostel management website used by one Hostel Warden and hostel students. It maintains connected records for student accounts and profiles, fee records, payment proofs and verification history, complaints, room assignments and requests, announcements, menu and rules, feedback, temporary leave requests, visitor-log entries, and meal opt-outs.

These records have relationships and business rules that must remain consistent. Examples include:

- A student has a unique student ID and associated account and fee record.
- Verified payment proofs, rather than pending or rejected proofs, affect the fee record.
- Fee changes and payment history must be retained.
- Room occupancy must not exceed room capacity.
- Student, fee, payment-proof, complaint, feedback, room-request, leave-request, and meal-opt-out records are retained rather than hard-deleted.
- Students may access only their own records, while the warden has administrative access.
- The application must preserve records when a student is marked Left and later reactivated.

The architecture is described as a layered monolith in ADR-001. During Phase 2 architectural-decision facilitation, the team already decided to use a **relational database** (MySQL/PostgreSQL family) over NoSQL for this reason: the fee-consistency invariant (NFR-02) and the room-capacity invariant (BR-06) are far safer to enforce with relational constraints/transactions than with application-layer checks in a NoSQL store. This ADR formally records that team decision. The specific engine (MySQL vs PostgreSQL) and hosting arrangement remain open — C-04 confirms no technology or hosting was specified by the client.

## 2. Decision Drivers

1. **Data integrity:** Related records and business rules must remain consistent.
2. **Relationship support:** Student, fee, payment, room, complaint, and request records have clear relationships.
3. **Historical retention:** Required histories and retained records must not be lost through ordinary application operations.
4. **Access control:** Persistence access must support the role and ownership restrictions in NFR-01 and BR-08.
5. **Fit with ADR-001:** Persistence must be usable by the layered-monolith application without introducing an unapproved distributed architecture.
6. **Technology neutrality on engine/hosting:** The PRD authorizes the relational family but not a specific engine or hosting provider.

## 3. Alternatives Considered

### Option A — Relational database (selected)

Store structured application records in a relational database, using relationships and constraints to protect record integrity.

**Advantages**
- Represents relationships between students, fees, payments, rooms, complaints, and requests directly.
- Supports transactions for operations that update related records (e.g. a verified payment updating paid/remaining/history together).
- Supports constraints and queries needed for validation, history, occupancy, and dashboard summaries.

**Disadvantages**
- Requires a schema and database administration.
- Schema changes must be managed as the application evolves.

### Option B — Non-relational database (rejected)

**Reason not selected:** NFR-02 (fee consistency) and BR-06 (room-capacity invariant) would have to be enforced entirely in the application layer rather than via relational constraints/transactions — higher risk of inconsistency, with no project requirement justifying the flexibility a non-relational store would offer.

### Option C — File-based persistence for application records (rejected)

**Reason not selected:** Relationships, concurrent updates, and the PRD's integrity constraints (fee, occupancy) would need substantial application-level handling; unsuitable for this record-connected domain.

## 4. Decision

**Use a relational database (MySQL or PostgreSQL) as the primary persistence mechanism for structured HostelEase application records.** This is compatible with the layered-monolith architecture (ADR-001).

This ADR does not select the specific engine (MySQL vs PostgreSQL), hosting location, backup schedule, recovery objectives, or migration tooling — these remain Open Questions below.

Uploaded payment proofs and complaint attachments are files, not ordinary structured records; their storage is governed by ADR-004 and is not overridden here.

## 5. Consequences

### Positive consequences

- Structured records can be related through defined keys and constraints.
- Transactions keep multi-step updates consistent (e.g. verified payment → fee totals → payment history).
- Queries support warden searches, student-specific views, occupancy, and dashboard counts.
- Retained records/histories are represented without relying on file-based record management.

### Trade-offs and responsibilities

- The team must define and maintain a database schema.
- Database changes need a controlled migration process (tool not yet selected).
- A relational database does not by itself guarantee NFR-01's access isolation — the application/Auth Guard must still enforce it.
- Backup, restoration, retention, and operational-monitoring policies still need decisions.

## 6. Requirements and Traceability

- **FR-01, FR-03, FR-05, FR-06, FR-07 to FR-19:** Creation, retrieval, updating, and retention of structured records.
- **BR-04 and BR-05:** Defined statuses and retention of specified records and histories.
- **BR-06:** Room capacity and occupancy constraints.
- **BR-08 and NFR-01:** Student data isolation and warden-only access.
- **NFR-02:** Fee consistency after payment verification and total-fee changes.
- **C-04:** No specific database engine or hosting provider has been specified.

## 7. Open Questions

1. **Database engine:** MySQL or PostgreSQL?
2. **Hosting:** Local dev environment, institutional server, or elsewhere?
3. **Backup and recovery:** Frequency, retention period, recovery expectations?
4. **Migration approach:** Which schema/version migration mechanism?
5. **Database operations:** Who administers production data access?
6. **Visitor-log retention (OQ-32):** Still unresolved; the choice of relational DB does not decide this policy.
7. **File metadata:** Which file metadata is stored with proofs/attachments? Coordinate with ADR-004.

## 8. Related ADRs

- **ADR-001 — Architecture Style:** Establishes the layered-monolith architecture this persistence mechanism runs in.
- **ADR-004 — File Storage Approach:** Defines how uploaded files are stored and referenced; not overridden by this ADR.