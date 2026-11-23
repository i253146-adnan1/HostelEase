# HostelEase — Implementation Decision Log

This log records implementation-phase decisions resolving Open Questions (`OQ-xx`) from `PRD.md` (v1.2), continuing from the Deliverable 1/2 Decision Log (`Log 1–25`).

---

## Log 26 — Room Swap Consent, Effective Time & Pending-State Validation (Resolves OQ-04, OQ-05; Partial OQ-24)

- **Date:** 2026-11-22
- **Slice:** VS-11 (Room-Change & Two-Step Room-Swap Requests)
- **Lead:** Muhammad Fahad Basharat
- **Related PRD items:** OQ-04, OQ-05, OQ-24, FR-10, FR-11, BR-04, BR-05, BR-06, BR-07, BR-08, EC-41, EC-42, EC-43, ADR-005
- **Status:** Adopted for implementation (flagged for client/TA confirmation)

### Context
- **OQ-04:** Must the other student agree to a room swap?
- **OQ-05:** When does an approved swap take effect?
- **BR-04** lists base room-request statuses as `Pending`, `Approved`, `Rejected`, `Cancelled`.

### Decision
1. **Two-Step Swap Consent (OQ-04):**
   - Room-swap requests (`request_type = SWAP`) require explicit in-app consent from the target student before entering the warden's approval queue.
   - Upon submission by the requester, a swap request enters `PENDING_STUDENT_CONSENT` and creates an in-app `RoomSwapNotification` (`SWAP_INCOMING`) for the target student.
   - If the target student declines, the request terminates as `REJECTED_BY_STUDENT` and never appears in the warden's approval queue.
   - If the target student accepts, the request transitions to `PENDING_WARDEN_APPROVAL` and enters the warden's approval queue.
2. **Immediate Atomic Effect on Warden Approval (OQ-05):**
   - When the warden approves a swap (`PENDING_WARDEN_APPROVAL` → `APPROVED`), the system atomically swaps both students' active `RoomAssignment` records within a database transaction (`@transaction.atomic` with `select_for_update()`), after re-validating that both students are `Active` and hold active room assignments (EC-43).
   - Both students receive in-app notifications (`SWAP_APPROVED` or `SWAP_REJECTED_BY_WARDEN`).
3. **Room-Change Statuses:**
   - Room-change requests (`request_type = CHANGE`) use the standard statuses: `PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`.
4. **Dashboard Scope (ADR-005):**
   - `get_pending_request_count()` counts only `CHANGE` requests in `PENDING` and `SWAP` requests in `PENDING_WARDEN_APPROVAL` (excluding `PENDING_STUDENT_CONSENT` and `REJECTED_BY_STUDENT`).
5. **BR-04 Extension Note:**
   - This decision extends BR-04's listed room-request statuses (`PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`) with `PENDING_STUDENT_CONSENT`, `REJECTED_BY_STUDENT`, and `PENDING_WARDEN_APPROVAL` for the `SWAP` sub-type, and is flagged for client/TA confirmation.
6. **OQ-24 (Partial Resolution — Pending-State Changes & Edge Cases EC-41, EC-42, EC-43):**
   - **EC-41 (Room becomes full before approval):** `decide_change_request()` locks the preferred `Room` with `select_for_update()` inside `@transaction.atomic` and re-checks `not room.is_full`, blocking approval cleanly if the room is now full.
   - **EC-43 (Assignment changes or capacity conflicts before swap takes effect):** `decide_swap()` re-validates both students as `Active` via `StudentService.validate_active_student()` and locks their active `RoomAssignment` rows with `select_for_update()` inside `@transaction.atomic`. If either student is no longer active, lacks an active `RoomAssignment`, or both are now in the same room, approval is blocked and aborted cleanly without modifying any assignments.
   - **EC-42 (Room removed while a request targeting it is Pending — Out of Scope / Still Open):** VS-03's `Room` model does not have a soft-delete/deactivation status field (`room_delete` performs `room.delete()`). `RoomRequest.preferred_room` uses `on_delete=models.PROTECT`, which prevents database-level deletion of a `Room` referenced by any `RoomRequest`, but full soft-removal/deactivation handling for `EC-42` remains out of scope for VS-11 and is still open under OQ-24.

---

## Log 27 — Complaint Status Transitions & Resolution Remark (Resolves OQ-03, OQ-12)

- **Date:** 2026-11-23
- **Slice:** VS-13 (Warden Complaint Management)
- **Related PRD items:** OQ-03, OQ-12, FR-08, AC-08.1, BR-04, BR-05, EC-16, EC-40
- **Status:** Adopted for implementation (flagged for client/TA confirmation)

### Context
- **OQ-03 (EC-16):** Can a `Resolved` complaint be reopened?
- **OQ-12 (EC-40):** Is a remark mandatory when marking a complaint `Resolved`?

### Decision
1. **No Reopen Action (`OQ-03`):** Complaints follow a strict forward-only lifecycle `Submitted → In Progress → Resolved`. Once `Resolved`, no reopen or backward transition is permitted.
2. **Mandatory Remark on Resolution (`OQ-12`):** Transitioning a complaint from `In Progress` to `Resolved` requires a non-empty `warden_remark`. Remark is optional when moving from `Submitted` to `In Progress`.
