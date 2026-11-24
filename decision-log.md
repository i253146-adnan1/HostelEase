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

## Log 27 — One Open Leave Request per Student & No Student Cancellation (Resolves OQ-30)

- **Date:** 2026-11-23
- **Slice:** VS-15 (Student Temporary Leave Request and Warden Decision)
- **Lead:** Muhammad Fahad Basharat
- **Related PRD items:** OQ-30, FR-17, BR-05, BR-12, F-08, EC-47, EC-48, AC-17.1–AC-17.4, ADR-005
- **Status:** Adopted for implementation (cancellation scope flagged for client/TA confirmation)

### Context
- **OQ-30:** Is only one open leave request allowed per student, like room requests?
- **EC-48 / AC-17.3:** Student already has a `Pending` or `Approved` leave request.
- **AGENTS.md & plan.md:** `AGENTS.md` already instructs enforcing one open (`Pending`/`Approved`) leave request per student unless `OQ-30` is resolved otherwise, and `plan.md` records that the team selected this behaviour.
- **Scope check (AC-17.1–AC-17.4 vs VS-11):** Unlike Room Requests in VS-11 (`AC-10.3`), `AC-17.1–AC-17.4` do not describe any student-initiated cancellation or withdrawal of a leave request.

### Decision
1. **One Open Leave Request per Student (Resolves OQ-30):**
   - One open leave request per student is enforced, where open means status `Pending` or `Approved` — this aligns `AGENTS.md`'s existing instruction with PRD `OQ-30` and closes it formally.
   - A student with an existing `PENDING` or `APPROVED` `LeaveRequest` cannot submit another (`EC-48` / `AC-17.3`). A student with only `REJECTED` history may submit a new leave request.
2. **No Student-Initiated Cancel Action (Flagged for Client/TA Confirmation):**
   - `AC-17.1–AC-17.4` do not describe any student-initiated cancellation/withdrawal of a leave request (unlike Room Requests in VS-11). Therefore this slice does **not** implement a cancel action for leave requests.
   - **Flagged for Client/TA:** Worth raising with the client/TA if a student-initiated cancel capability is later wanted (for example, cancelling a `PENDING` or `APPROVED` leave request before departure).
3. **No Side Effects on Student Status, Room, or Login (BR-12 / AC-17.4) & Record Retention (BR-05):**
   - Warden approval or rejection updates only the `LeaveRequest` record (`status`, `warden_remark`, `decided_by_warden_at`) and never modifies `Student.status`, `RoomAssignment`, or `User`/session access.
   - Leave request records are never hard-deleted (`BR-05`).
