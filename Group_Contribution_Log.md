# HostelEase — Group Contribution Log (Deliverable 3)

Each row lists the member's contribution and the shared-AI-project chat reference. All members can explain the complete architecture in the demo.

| Member | Activity / artefact led | Contribution made | Chat reference |
|--------|-------------------------|-------------------|----------------|
| Muhammad Fahad Basharat (Role-01) | ASR identification; decision-session facilitation; ADR-001; ADR-005; PRD v1.2 update coordination | Reviewed Final_PRD.md to identify 11 ASRs/drivers; facilitated the architectural-decision session (style, data store, file storage, auth); wrote ADR-001 (layered monolith); updated Final_PRD.md to v1.2 after TA-added features (FR-17–19); wrote and finalized ADR-005 (Dashboard scope); led AI-agent context handoff and iteration-1 refinement (architecture.md clarification, OQ-31 note). | T1 ASR – M1; T2 Decisions – M1; [shared AI project chat — PRD v1.2 update] |
| Safiullah (Role-02) | AGENTS.md; ADR-002 | Drafted AGENTS.md (module boundaries, dependency rules, constraints, approval-required actions, ambiguity handling) and updated it after ADR-005/new modules; wrote ADR-002 (relational database persistence decision). | shared AI project chat |
| Adnanullah (Role-03) | ADR-003; AI-proposal context handoff + evaluation (Phase 6) | Wrote ADR-003 (server-side session + cross-cutting Auth Guard); set up the empty workspace, gave the AI agent (Claude Code) the full architectural context (PRD v1.2, architecture.md, AGENTS.md, ADR-001 to 005), and evaluated the proposed module structure against the architecture (no ADR violations, no unjustified dependencies). | shared AI project chat |
| Farmanullah (Role-04) | architecture.md consolidation; ADR-004; submission packaging | Consolidated architecture.md (system overview through Mermaid diagram and ADR links) from Phases 1–2 and the ADRs; wrote ADR-004 (local filesystem + DB path reference for file storage); compiled the final submission package (architecture.md, AGENTS.md, /ADR, evidence docx, Group Contribution Log, Final_PRD.md). | shared AI project chat |

## D4 Implementation Contributions

| Member | Date | Slice ID / Activity | Contribution made | Evidence / Branch |
|---|---|---|---|---|
| Safiullah (Role-02) | 21 Nov 2026 | VS-02 Student registration & initial fee/account creation | Implemented Student model, room assignment integration, atomic registration transaction, one-time credential handover, contact number validation, and automated test suite (14 test methods) for FR-01, AC-01.1–AC-01.4, OQ-21, OQ-25, OQ-26. | `feature/VS-02-student-registration`, `workflow-evidence/VS-02.md` |
| Adnanullah (Role-03) | 21 Nov 2026 | VS-04 Fee ledger & fee-change history | Implemented FeeRecord, immutable FeeChange, Payment ledger, and fee change history views with 20 unit/regression tests. | `feature/VS-04-fee-ledger`, `workflow-evidence/VS-04.md` |
| Farmanullah (Role-04) | 21 Nov 2026 | VS-01 Authentication & access guard | Implemented login, password change, forced password change middleware, and role-based guards with 18 tests. | `feature/VS-01-auth-guard` |
| Muhammad Fahad Basharat (Role-01) | 21 Nov 2026 | VS-06 Hostel info: announcements, menu, rules | Implemented warden CRUD and student read-only views for announcements, menu, and rules with 16 tests. | `feature/VS-06-hostel-information` |
