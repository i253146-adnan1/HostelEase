# HostelEase — Workflow Evidence Log

See [TEST_REPORT.md](TEST_REPORT.md) for the consolidated Quality Gates (Gates 1–5) matrix, 6-column Testing Evidence Table, and Revision & Retest History.

| Slice ID / Name | Requirements | Lead | Mode | Checks & Output | Human Decision | Plan Version |
|---|---|---|---|---|---|---|
| VS-00 Foundation | ADR-001–006 | Adnanullah | AFK verify / HITL stack | `manage.py check` & migrations clean | Accepted | v01 |
| VS-01 Auth & Access Guard | FR-02, NFR-01, ADR-003 | Farmanullah | HITL + AFK | `accounts/tests.py` pass | Accepted | v02 |
| VS-02 Student Registration | FR-01, BR-01, OQ-21/25/26 | Safiullah | HITL + AFK | `hostel/test_student_registration.py` pass (see `VS-02.md`) | Accepted | v02 |
| VS-03 Room Management | FR-09, BR-06 | Muhammad Fahad Basharat | HITL + AFK | `hostel/tests.py` pass | Accepted | v03 |
| VS-04 Fee Ledger & History | FR-06, NFR-02, BR-03/10 | Adnanullah | HITL + AFK | `finance/tests.py` pass (see `VS-04.md`) | Accepted | v02 |
| VS-05 Student Profile Boundary | FR-03, NFR-01 | Farmanullah | HITL + AFK | `accounts/tests.py` pass | Accepted | v04 |
| VS-06 Hostel Information | FR-12, AC-12.1–12.6 | Muhammad Fahad Basharat | AFK | `hostel/test_hostel_info.py` pass | Accepted | v02 |
| VS-07 Feedback & Summary | FR-15, BR-11, BR-05 | Safiullah | HITL + AFK | `operations/tests.py` pass (see `VS-07.md`) | Accepted | v04 |
| VS-08 Shared Local File Storage | FR-04/07, C-02, NFR-01, ADR-004 | Adnanullah | HITL + AFK | `operations/test_file_storage.py` pass (see `VS-08.md`) | Accepted | v04 |
| VS-09 Student Payment-Proof Submission | FR-04, BR-02/03, C-01/02 | Adnanullah | HITL + AFK | `finance/test_payment_proofs.py` pass (see `VS-09.md`) | Accepted | v05 |
| VS-10 Student Complaint Submission | FR-07, AC-07.1–07.4 | Farmanullah | AFK | `operations/test_warden_complaints.py` pass | Accepted | v05 |
| VS-11 Room & Swap Requests | FR-10, BR-06 | Muhammad Fahad Basharat | HITL + AFK | `hostel` room request tests pass (see `VS-11.md`) | Accepted | v05 |
| VS-12 Warden Payment Verification/Rejection | FR-05, NFR-02, BR-03 | Safiullah | HITL + AFK | `finance` verification tests pass (see `VS-12.md`) | Accepted | v05 |
| VS-13 Warden Complaint Management | FR-08, AC-08.1, BR-04 | Farmanullah | HITL + AFK | `operations/test_warden_complaints.py` pass | Accepted | v05 |
| VS-14 Warden Feedback Summary | FR-15, AC-15.4 | Safiullah | AFK | `operations/tests.py` pass (see `VS-07.md`) | Accepted | v05 |
| VS-15 Temporary Leave Requests | FR-17, BR-12, OQ-30 | Muhammad Fahad Basharat | HITL + AFK | `operations/test_leave_requests.py` & `test_cycle5_integration.py` pass (see `VS-15.md`) | Accepted | v05 |
| VS-16 Student Lifecycle | FR-13, BR-09 | Safiullah | HITL + AFK | `hostel/test_student_lifecycle.py` pass (see `VS-16.md`) | Accepted | v06 |
| VS-17 Warden Visitor Log | FR-18, BR-13, OQ-32 | Muhammad Fahad Basharat | HITL + AFK | `operations` visitor tests pass | Accepted | v07 |
| VS-18 Meal Opt-Outs | FR-19, EC-50/51, ADR-005 | Adnanullah | HITL + AFK | `operations/test_meal_optouts.py` pass (see `VS-18.md`) | Accepted | v07 |
| VS-19 Warden Pending Dashboard | FR-14, ADR-005 | Farmanullah | HITL + AFK | `dashboard` tests pass | Accepted | v08 |
| VS-20 Consolidated Student Home | FR-03–FR-19, NFR-01 | Adnanullah | HITL + AFK | `accounts/test_student_home_vs20.py` pass (see `VS-20.md`) | Accepted | v08 |
| VS-23 Urdu Language Support on Warden Dashboard | FR-21, AC-21.1–AC-21.3 | Adnanullah | HITL + AFK | Gate 1 Ready (Stage 4 stub in `VS-23.md`) | Not Started | v11 |

**Latest Full Suite Verification (24 Nov 2026):** `venv\Scripts\python.exe manage.py test --noinput -v 1` → `Ran 220 tests in 195.102s — OK`.
