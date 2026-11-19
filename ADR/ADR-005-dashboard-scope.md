# ADR-005: Dashboard Scope — Extending to Leave Requests and Meal Opt-outs

**Status:** Accepted

## Context

FR-14 requires the warden's dashboard to show pending items with a count for each type. Originally this covered three types: payment proofs (Pending), complaints (Submitted/In Progress), and room requests (Pending) — ASR #6 (NFR-04, FR-14). The TA-added features FR-17 (leave requests) and FR-19 (meal opt-outs) introduced two more student-submitted, status/date-driven entities (ASR #11), requiring a decision on whether these also plug into the Dashboard's "one overview" aggregation (G-07).

## Alternatives Considered

1. **Extend Dashboard fully** — add Leave Requests (Pending) and Meal Opt-outs as two more counted types.
2. **Keep Dashboard scope limited** — Dashboard shows only Fee, Complaints, Rooms; Leave Requests and Meal Opt-outs get separate pages.
3. **Selected — partial extension:** add Leave Requests (Pending) as a fourth pending-item count; keep Meal Opt-outs as a separate, non-pending summary view (counts per date/meal type), not mixed into the pending-items list.

## Decision

The Dashboard is extended to include **Leave Requests with status Pending** as a fourth counted pending-item type, read via the Leave Requests module's own interface (same read-only aggregation pattern as Fee/Complaints/Rooms).

**Meal Opt-outs are NOT added to the pending-items count.** They have no warden approve/reject step (BR-04 defines their statuses as Active/Cancelled only, no state that implies a pending warden action), so they are shown on their own warden-facing opt-out summary page instead (count per date and meal type, per FR-19/AC-19.5).

This resolves OQ-31: Pending leave requests **do** count in the warden's pending-items dashboard.

## Rationale

- Leave Requests follow the exact same approve/reject lifecycle as Room Requests and Complaints — excluding them breaks the "one overview" consistency the team already committed to for other request types (G-07).
- Meal Opt-outs are informational aggregates, not warden "pending work" — bundling them into the pending-count model would misrepresent what "pending" means.
- Extending the Dashboard's read interface by one more call (to Leave Requests) is a small, contained change — it does not violate the Dashboard's existing rule of "read-only aggregator, owns no data" (ADR-001, Phase 2 decisions).

## Trade-offs / Consequences

- (+) Dashboard stays the single place the warden checks for anything needing action, consistent with G-07.
- (+) Meal Opt-outs get a summary view suited to what they actually are (a planning aggregate, not pending work).
- (−) Dashboard's interface contract grows by one read-call; AGENTS.md updated accordingly (see Module Boundaries / Dependency Rules).
- (−) If the warden/client later disagrees with resolving OQ-31 this way, this ADR will need revisiting.

## References

- Final_PRD.md: FR-14, FR-17, FR-19, BR-04, G-07, OQ-31.
- ADR-001 (Dashboard established as read-only aggregator).
- AGENTS.md (Dashboard module boundary).