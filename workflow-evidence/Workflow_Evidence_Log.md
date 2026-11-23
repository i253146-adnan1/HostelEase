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

**Latest Full Suite Verification (22 Nov 2026):** `venv\Scripts\python.exe manage.py test -v 1` → `Ran 115 tests in 115.399s — OK`.
