# HostelEase — Lightweight Vertical-Slice Test Report & Quality Gates (D4)

**Date:** 24 November 2026  
**Branch:** `main`  
**Test Command:** `venv\Scripts\python.exe manage.py test --noinput -v 1`  
**Latest Verified Result:** `Ran 220 tests in 195.102s` — **`OK`** (`System check identified no issues (0 silenced).`)

---

## 1. Test Suite Audit Summary

All 8 test modules are kept lightweight and focused on meaningful **Functional**, **Negative**, **Equivalence Partitioning (EP)**, and **Boundary Value Analysis (BVA)** coverage without redundant bloat:

| App / File | Slice(s) | Focus |
|---|---|---|
| `accounts/tests.py` | VS-01, VS-05 | Login/logout, password hashing & change, forced temporary password, `create_warden`, role isolation (`403`/`302`), student own-record boundary |
| `hostel/tests.py` | VS-03 | Room CRUD, capacity-1/capacity/capacity+1, capacity reduction (`occupancy` vs `occupancy - 1`), occupied room deletion block, soft-delete clear |
| `hostel/test_student_registration.py` | VS-02 | Atomic student registration (user, student, fee ledger, optional room), duplicate ID, mandatory fields, phone/fee validation, full-room rollback |
| `hostel/test_hostel_info.py` | VS-06 | Announcements, mess menu, hostel rules CRUD, empty-input rejection, student read-only access |
| `hostel/test_cycle2_e2e.py` | Cycle 2 E2E | Warden login → Room create → Student register → Occupancy check → Fee ledger check → Student login & forced password change → Hostel info |
| `finance/tests.py` | VS-04 | Zero/underpaid/exact/excess-paid EP & BVA, Pending/Rejected exclusion, mandatory reason when lowering fee below paid, immutable `FeeChange`, `403`/`302` guards |
| `operations/tests.py` | VS-07 | 1–5 star feedback validation, repeat submissions, immutability (`BR-11`), no hard delete (`BR-05`), summary aggregation & empty state |
| `operations/test_file_storage.py` | VS-08 | JPG/PNG/PDF & magic-byte validation, 0 B / 5 MB / 5 MB+1 B BVA, path-traversal sanitization, `BR-05` retention, cross-student `403` isolation |

---

## 2. Quality Gates Status (Gates 1–5)

| Slice | Gate 1: Slice Readiness | Gate 2: Functional Verification | Gate 3: Architecture / Constraint Check | Gate 4: Regression / Integration Check | Gate 5: Final Product Check |
|---|---|---|---|---|---|
| **VS-00** Foundation & Stack | Pass (ADR-006, `plan.md`) | Pass (PostgreSQL, base templates, `check` clean) | Pass (Layered monolith, Django + PostgreSQL) | Pass | Pending full VS-09–VS-20 |
| **VS-01** Auth & Access Guard | Pass (FR-02, NFR-01, ADR-003) | Pass (`accounts/tests.py`) | Pass (Server-side sessions, no JWT, `accounts.guards`) | Pass | Pending full VS-09–VS-20 |
| **VS-02** Student Registration | Pass (FR-01, OQ-21/25/26) | Pass (`hostel/test_student_registration.py`) | Pass (`transaction.atomic()`, no hard delete) | Pass (E2E verified) | Pending full VS-09–VS-20 |
| **VS-03** Room Management | Pass (FR-09, BR-06, contract) | Pass (`hostel/tests.py`) | Pass (`select_for_update()` locking, soft-clear) | Pass (E2E verified) | Pending full VS-09–VS-20 |
| **VS-04** Fee Ledger & History | Pass (FR-06, NFR-02, BR-03/10) | Pass (`finance/tests.py`) | Pass (No payment gateway C-01, immutable `FeeChange`) | Pass (E2E verified) | Pending full VS-09–VS-20 |
| **VS-05** Student Profile Boundary | Pass (FR-03, NFR-01) | Pass (`accounts/tests.py`) | Pass (Own-record isolation, no roommate exposure) | Pass | Pending full VS-09–VS-20 |
| **VS-06** Hostel Information | Pass (FR-12, AC-12.1–12.6) | Pass (`hostel/test_hostel_info.py`) | Pass (Warden CRUD, student read-only) | Pass | Pending full VS-09–VS-20 |
| **VS-07** Feedback & Summary | Pass (FR-15, BR-11, OQ-19) | Pass (`operations/tests.py`) | Pass (Immutable & non-deletable `Feedback`) | Pass | Pending full VS-09–VS-20 |
| **VS-08** Shared Local File Storage | Pass (FR-04/07, C-02, ADR-004) | Pass (`operations/test_file_storage.py`) | Pass (Local `PRIVATE_UPLOAD_ROOT`, no cloud storage) | Pass | Pending VS-16–VS-20 |
| **VS-09** Payment-Proof Submission | Pass (FR-04, C-01/02) | Pass (`finance/test_payment_proofs.py`) | Pass (Uses VS-08, no payment gateway) | Pass | Pending VS-16–VS-20 |
| **VS-10** Student Complaints | Pass (FR-07, C-02) | Pass (`operations/test_warden_complaints.py`) | Pass (8 categories, optional VS-08 attachment) | Pass | Pending VS-16–VS-20 |
| **VS-11** Room & Swap Requests | Pass (FR-10, BR-06) | Pass (`hostel` tests) | Pass (Two-step swap, capacity check) | Pass | Pending VS-16–VS-20 |
| **VS-12** Payment Verification | Pass (FR-05, NFR-02) | Pass (`finance` tests) | Pass (Atomic ledger update, remark on reject) | Pass | Pending VS-16–VS-20 |
| **VS-13** Warden Complaint Mgmt | Pass (FR-08, BR-04) | Pass (`operations/test_warden_complaints.py`) | Pass (Submitted→In Progress→Resolved) | Pass | Pending VS-16–VS-20 |
| **VS-14** Warden Feedback Summary | Pass (FR-15, AC-15.4) | Pass (`operations/tests.py`) | Pass (1–5 star aggregation) | Pass | Pending VS-16–VS-20 |
| **VS-15** Temporary Leave Requests | Pass (FR-17, BR-12, OQ-30) | Pass (`operations/test_leave_requests.py`) | Pass (Active/room/login untouched on decide) | Pass (`test_cycle5_integration.py`) | Pass |
| **VS-16** Student Left/Reactivation | Pass (FR-13, BR-09) | Pass (`hostel/test_student_lifecycle.py`) | Pass (Login disabled, room cleared, history kept) | Pass | Pass |
| **VS-17** Warden Visitor Log | Pass (FR-18, BR-13, OQ-32) | Pass (`operations` visitor tests) | Pass (Warden-only, zero student routes) | Pass | Pass |
| **VS-18** Meal Opt-Outs | Pass (FR-19, EC-50/51, ADR-005) | Pass (`operations/test_meal_optouts.py`) | Pass (Future only, separate from dashboard) | Pass | Pass |
| **VS-19** Warden Pending Dashboard | Pass (FR-14, NFR-01, ADR-005) | Pass (`dashboard` tests) | Pass (Read-only 4-module counts, meal opt-outs excluded) | Pass | Pass |
| **VS-20** Consolidated Student Home | Pass (FR-03–FR-19, NFR-01) | Pass (`accounts/test_student_home_vs20.py`) | Pass (Own-record isolation, empty states, no visitor log) | Pass (220 tests OK) | Pass |

---

## 3. Testing Evidence Table

| Slice / Requirement | Test Type | Input / Condition | Expected Result | Actual Result | Pass / Fail |
|---|---|---|---|---|---|
| VS-00 / ADR-006 | Functional | `manage.py check`, `makemigrations --check --dry-run` | 0 issues, no pending migrations | `System check identified no issues (0 silenced).`, `No changes detected` | Pass |
| VS-01 / FR-02, AC-02.1 | Functional | Valid warden & student login credentials | Redirect to respective dashboard | Redirected to warden/student dashboard (`200`) | Pass |
| VS-01 / AC-02.2, BR-09 | Negative | Wrong password; inactive user login | Denied; session not created | Denied on login page | Pass |
| VS-01 / AC-02.4 | Functional | Login with `must_change_password=True` | Confined to change-password until updated | Redirected to `/accounts/change-password/` until changed | Pass |
| VS-02 / FR-01, AC-01.1–01.4 | Functional / Negative | Valid registration vs duplicate ID / missing fields / full room | Atomic create on valid; full rollback on error | Created user+student+fee+room; 0 partial rows on error | Pass |
| VS-03 / FR-09, BR-06 | BVA / Negative | Room capacity=2: assign 2, assign 3rd; edit capacity 3→1 vs 3→2 | 3rd rejected; capacity 1 rejected, exact occupancy 2 allowed | Rejected 3rd & capacity 1; accepted capacity 2 | Pass |
| VS-03 / AC-09.4 | Negative | Delete room with active student assignment | Deletion blocked | Blocked with error message; room retained | Pass |
| VS-04 / NFR-02, AC-06.2 | EP / BVA | Total 1000 with paid 0, 400, 999.99, 1000, 1000.01; lower below paid without reason | Exact remaining/excess; lower without reason rejected | `FeeError` raised; `FeeChange` immutable (`PermissionError`) | Pass |
| VS-05 / FR-03, NFR-01 | Security / Negative | Student accesses own profile vs another student ID / warden URL | Own profile `200`; others `403` | Own `200`; warden/other-student routes `403` | Pass |
| VS-06 / FR-12 | Functional / Negative | Warden CRUD on announcements/menu/rules; blank input; student POST | Valid saved; blank rejected; student `403` | All assertions matched | Pass |
| VS-07 / FR-15, BR-11 | EP / BVA / Negative | Ratings 1–5 vs 0 or 6; edit/delete submitted feedback | 1–5 saved; 0/6 rejected; edit/delete raise `PermissionError` | All assertions matched | Pass |
| VS-08 / C-02, ADR-004 | BVA / Negative / Security | JPG/PNG/PDF; 0 B, 5 MB, 5 MB+1 B; `.exe`/spoofed PDF; cross-student GET | Valid & 5 MB saved; 0 B, 5 MB+1 B, invalid rejected; other student `403` | All 7 tests in `test_file_storage.py` passed | Pass |
| Cycle 2 E2E | Integration | Warden login → Room → Register Student → Occupancy → Fee Ledger → Student login | Full flow succeeds end-to-end with `403` on student accessing `/warden/fees/` | `Cycle2EndToEndIntegrationTests` passed | Pass |

---

## 4. Revision & Retest History

1. **VS-03 Merge Clobber (`task-378` — Failed: 5 errors, 5 failures):**
   - *Failure:* `finance` URL tests returned `404` (`config/urls.py` lost `path('warden/fees/', ...)` during VS-03 merge) and `accounts` tests raised `NoReverseMatch` (`hostel/urls.py` & `hostel/views.py` lost VS-06 routes/views; `hostel/migrations/0001_room_student.py` omitted `Announcement`, `MenuItem`, `Rule`).
   - *Fix:* Restored `warden/fees/` in `config/urls.py`, restored VS-06 routes/views/tests in `hostel/`, generated `hostel/migrations/0002_announcement_menuitem_rule.py`, and wired `Room Management` on `warden_dashboard.html`.
2. **E2E Room Detail & Password-Change Field Mismatch (`task-431` & `task-442` — Failed):**
   - *Failure:* `templates/hostel/room_detail.html` referenced `{{ assignment.student_user.username }}` (rendered blank) instead of `{{ assignment.student_id }}`; `hostel/test_hostel_info.py` had UTF-16 null bytes; E2E test posted `old_password` instead of `current_password`.
   - *Fix:* Updated `room_detail.html` to `{{ assignment.student_id }}`, rewrote `hostel/test_hostel_info.py` as UTF-8, and aligned E2E form fields.
3. **PostgreSQL `accounts_user` Schema Mismatch (Local DB):**
   - *Failure:* `create_warden` failed with `relation "accounts_user" does not exist` because `hostelease_db` still held pre-VS-01 `auth_user` tables.
   - *Fix:* Reset `public` schema on `hostelease_db` and ran `manage.py migrate` cleanly (`accounts`, `finance`, `hostel`, `operations` all `OK`).
4. **Final Passing Retest (`task-552`, 22 Nov 2026):**
   - Command: `venv\Scripts\python.exe manage.py test -v 1`
   - Output: `Ran 115 tests in 115.399s` — **`OK`** (`System check identified no issues (0 silenced).`).
