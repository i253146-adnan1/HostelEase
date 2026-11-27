# HostelEase — Final Project Report (Deliverable 4)

**Project:** SE-1001 — Introduction to Software Engineering  
**Product:** HostelEase (Hostel Management System)  
**Submission Date:** 27 November 2026  
**Team Members:** Fahad, Safiullah, Adnanullah, Farmanullah  
**Repository:** https://github.com/i253146-adnan1/HostelEase  

---

## 1. Executive Summary & Implemented Scope

HostelEase is a locally runnable, role-isolated Django + PostgreSQL web application built using an AI-native, vertical-slice development workflow (`VS-00` through `VS-22`, plus post-integration authentication, profile, and hostel-info enhancements).

### Core Implemented Capabilities
- **Authentication, Access Control & Account Lifecycle (`VS-01`, `VS-16`, Auth Overhaul):**
  - Server-side session authentication (`ADR-003`) with `@login_required_guard`, `@warden_required`, `@student_required`, and `ForcePasswordChangeMiddleware`.
  - **Main Warden (`adnan`) & Sub-Warden Hierarchy:** Hardcoded/seeded Main Warden (`seed_main_warden`), sub-warden creation (`Add Warden`) without overwriting the active warden session, Main Warden-only self-service **Forgot Password** (verified via registered Email + Mobile Number), Main Warden-controlled **Sub-Warden & Student Password Reset** with 24-hour expiring temporary passwords, and **Warden Profile** management (`Name`, `Email`, `Mobile Number`, `Password`, `Display Picture`).
  - **Student Lifecycle (`VS-02`, `VS-16`):** Student registration with room allocation and initial fee ledger, handover credentials with Copy button, Mark Left (disabling login and freeing room capacity without hard deletion per `BR-05`), and Reactivation.
- **Rooms & Two-Step Swap Workflow (`VS-03`, `VS-11`):**
  - Room catalogue CRUD, live capacity enforcement (`BR-06`), direct student room-change requests, and two-step peer-consent room swaps (`AWAITING_PEER` → `PENDING_WARDEN_APPROVAL` → atomic swap execution).
- **Fee Ledger & Payment Proof Verification (`VS-04`, `VS-09`, `VS-12`):**
  - Immutable `FeeChange` audit trail (`NFR-02`), student proof upload (`JPG/PNG/PDF`, ≤ 5 MB) via shared local file storage (`VS-08`, `ADR-004`), and transactional `select_for_update` verification/rejection preventing double-counting (`EC-37`).
- **Operations, Hostel Info & Dashboards (`VS-05`–`VS-07`, `VS-10`, `VS-13`–`VS-22`):**
  - Complaints workflow (`Submitted → In Progress → Resolved`), temporary Leave Requests (`EC-47`), Warden-only Visitor Log (`BR-13`, `EC-49`), Meal Opt-Outs (`EC-50`, `EC-51`), 4-category Facility Feedback (`BR-11`), Announcements, Rules, editable weekly **Breakfast & Dinner Mess Menu Table** with changeable timings (`MessTiming`), read-only **Warden Pending Dashboard** (`ADR-005`), consolidated **Student Home** (`VS-20`), UI polish (`VS-21`), and profile **Display Picture** (`VS-22`).

---

## 2. Architecture & Implementation Summary

HostelEase follows a **Layered Monolith** (`ADR-001`) backed by **PostgreSQL** (`ADR-002`) with strict module boundaries enforced across five Django apps (`accounts`, `hostel`, `finance`, `operations`, `dashboard`) and documented in `AGENTS.md` and `architecture.md`:
- **Cross-Cutting Auth Boundary (`accounts`):** Guards and middleware execute before any module view; students receive styled `403` responses on warden/other-student routes.
- **Service-Interface Communication:** Modules communicate through explicit service functions (e.g., `dashboard.services.get_warden_pending_summary` aggregates counts from `finance`, `hostel`, and `operations` without owning any database tables per `ADR-005`).
- **Local Filesystem Media (`ADR-004`):** Payment proofs, complaint attachments, and profile avatars are stored locally under `media/` with validated file extensions/sizes and database path references.

---

## 3. Key Challenges, Revisions & AI Iteration Evidence

1. **Cross-Module Context Shadowing (`hostel` / `accounts`):** During live QA of Student Registration, passing `'user'` in the registration result dictionary shadowed Django's `request.user` in `base.html`, causing the confirmation navbar to display the newly created student instead of the logged-in warden. Fixed by renaming the context key to `created_user`.
2. **Scope Revision (`VS-23` Rejection/Removal):** After prototyping and reviewing an English/Urdu toggle (`VS-23`) on the Warden Dashboard, the team decided to remove the Urdu localization layer (`76c6ba9`) to keep the UI uniform in English while preserving all underlying Auth Overhaul and Student Management enhancements.
3. **UI Contrast & Usability Refinements:** Fixed Bootstrap `btn-outline-*` + `bg-white` hover contrast where button labels disappeared on hover (`b917e6d`), fixed `available_slots` display in the room dropdown (`23bf4eb`), and converted the Mess Menu into an inline-editable Monday–Sunday Breakfast & Dinner table (`235de15`).
4. **Immutable Audit & Atomic Concurrency:** Enforced `FeeChange` append-only immutability and `transaction.atomic()` + `select_for_update()` for fee verification and room-swap execution.

---

## 4. Complex Computing Problem (CCP) Analysis

### 4.1 Problem Statement
Standard off-the-shelf CRUD templates or simple spreadsheets fail to manage a hostel because multiple interdependent invariants must hold simultaneously under concurrent user actions: room capacity limits must never be exceeded during swaps or approvals, financial balances must never be double-counted or silently overwritten, role boundaries must strictly hide warden-only records (such as Visitor Logs per `BR-13`), and temporary credential resets must enforce time-bounded first-login password changes without disrupting active warden sessions.

### 4.2 Complexity Drivers
- **Multi-Party State Machines & Atomicity:** Two-step room swaps require peer consent before warden approval and must swap two `RoomAssignment` records atomically without violating capacity constraints.
- **Financial Auditability (`NFR-02`):** Fee totals and verified payments cannot be edited destructively; every total-fee adjustment requires an immutable `FeeChange` audit entry, and concurrent verification clicks must be idempotent (`EC-37`).
- **Strict Role & Record Isolation (`NFR-01`, `BR-13`):** Students must never access other students' records or any Visitor Log endpoint, while Wardens must be split into Main Warden vs. Sub-Warden privileges for password recovery.
- **Module Boundary Constraints (`AGENTS.md`, `ADR-005`):** The Dashboard must aggregate live counts across four modules with zero owned DB tables and zero direct cross-module table joins.

### 4.3 Engineering Trade-Offs
- **Layered Monolith vs. Microservices (`ADR-001`):** Chose a modular Django monolith with service-interface boundaries over separate microservices. This sacrificed independent service deployment in exchange for ACID database transactions across room swaps and fee verification, simpler local execution, and faster delivery within the 10-day semester window.
- **Server-Side Sessions vs. Stateless JWT (`ADR-003`):** Chose Django server-side sessions so forced password changes (`ForcePasswordChangeMiddleware`), role checks, and immediate account deactivation (`Mark Left`) take effect on the very next request without token-revocation infrastructure.
- **Local Filesystem Storage vs. Cloud Object Storage (`ADR-004`):** Chose validated local disk storage (`≤ 5 MB`, `JPG/PNG/PDF/WEBP`) over S3/cloud buckets so the entire system runs offline/locally with zero external service keys.

### 4.4 Alternative Approaches Considered
1. **Microservices with REST + JWT:** Rejected due to distributed transaction complexity for atomic room swaps/payment verification and excessive setup overhead for a single-hostel local deployment (`ADR-001`, `ADR-003`).
2. **Direct Cross-App ORM Queries in Views/Dashboard:** Rejected because coupling views directly to other modules' tables breaks encapsulation and violates `AGENTS.md` / `ADR-005`; replaced with explicit service functions (`get_warden_pending_summary`, `student_service`, `finance.services`).

### 4.5 System Integration
All five Django apps share a single PostgreSQL database (`ADR-002`) and unified `base.html` navigation shell, with `accounts.guards` acting as the single enforcement gate:
- `hostel` calls `finance.services` for initial ledger creation on student registration and `accounts` handles user credentials/resets.
- `operations` validates `student_id` via `hostel` interfaces (`EC-49`) and stores attachments via `operations.storage_service` (`VS-08`).
- `dashboard` reads pending counts read-only from `finance`, `hostel`, and `operations` (`ADR-005`).

### 4.6 Solution Evaluation
- **Correctness & Regression:** Verified via automated Django test suites across `accounts`, `dashboard`, `finance`, `hostel`, and `operations` (covering functional, negative, EP/BVA, concurrency/idempotency, and role-isolation checks; see `workflow-evidence/TEST_REPORT.md`).
- **Performance (`NFR-04`):** Dashboard load test (`test_nfr_04_warden_dashboard_loads_within_3_seconds`) verified response time well under the 3.0-second threshold.
- **Live End-to-End QA:** Walked through all Warden, Sub-Warden, and Student flows in a live browser against PostgreSQL with zero HTTP 500s and zero JS console errors.

### 4.7 Scalability & Feasibility
- **Current Feasibility:** Ideal for a single hostel (hundreds of residents) on a single Django + PostgreSQL instance with local media storage.
- **Scaling Path:** Moving to multi-hostel or cloud scale would require adding a `hostel_id` tenant foreign key, replacing local `media/` with S3-compatible object storage (`ADR-004` revision), adding Redis caching for dashboard summary counts, and running Gunicorn behind Nginx with managed PostgreSQL backups.

### 4.8 Ethical, Security & Societal Impact
- **Privacy & Least Privilege:** Student records, fee ledgers, and complaints are strictly scoped to the owning student (`NFR-01`); Visitor Logs are restricted to wardens (`BR-13`) to protect resident privacy.
- **Credential Hygiene:** Passwords are stored using Django's salted PBKDF2 hashing; temporary passwords expire after 24 hours and force immediate change on login (`ForcePasswordChangeMiddleware`).
- **Auditability & Fairness:** Non-destructive status transitions (`BR-05`) and immutable `FeeChange` history (`NFR-02`) prevent silent tampering with student financial records.

---

## 5. Limitations & Known Issues

- **Single-Hostel / Single-Main-Warden Scope:** Designed for one hostel with one Main Warden (`adnan`); multi-campus tenancy is out of scope.
- **No Online Payment Gateway (`C-01`):** Fee payments rely on manual proof upload and warden verification by design.
- **Open PRD Questions Preserved (`AGENTS.md`):** `OQ-30` (one open leave request at a time), `OQ-32` (visitor-log retention policy), and `OQ-33` (meal opt-out cancellation cutoff) remain documented rather than silently altered.
- **Local Seed Credentials:** `seed_main_warden` provides initial dev/demo credentials (`adnan` / `adnan@1302`); for live deployment, the Main Warden should immediately change the password via **Change Password**.

---

## 6. Group Contribution Summary

Detailed slice-by-slice and cycle-by-cycle records are maintained in [Group_Contribution_Log.md](file:///d:/HostelEase/Group_Contribution_Log.md) and [Workflow_Evidence_Log.md](file:///d:/HostelEase/workflow-evidence/Workflow_Evidence_Log.md):
- **Fahad (Role-01):** Rooms (`VS-03`), Room Requests & Two-Step Swaps (`VS-11`), Leave Requests (`VS-15`), Visitor Log (`VS-17`).
- **Safiullah (Role-02):** Student Registration (`VS-02`), Facility Feedback (`VS-07`), Payment Verification (`VS-12`), Feedback Summary (`VS-14`), Student Lifecycle (`VS-16`).
- **Adnanullah (Role-03):** Project Foundation (`VS-00`, `ADR-006`), Fee Ledger (`VS-04`), Hostel Info (`VS-06`), Local File Storage (`VS-08`), Payment Proof Submission (`VS-09`), Meal Opt-Outs (`VS-18`), Student Home (`VS-20`), UI Polish (`VS-21`), Profile Avatar (`VS-22`), Auth/Reset Overhaul & Mess Menu Table.
- **Farmanullah (Role-04):** Authentication & Access Guards (`VS-01`), Student Profile (`VS-05`), Complaint Submission (`VS-10`), Complaint Management (`VS-13`), Warden Pending Dashboard (`VS-19`).

---

## 7. Local Execution & Access Instructions

```powershell
# 1. Activate virtual environment and apply migrations
venv\Scripts\python.exe manage.py migrate

# 2. Seed Main Warden (purges dummy accounts) and default hostel announcements/rules/menu
venv\Scripts\python.exe manage.py seed_main_warden
venv\Scripts\python.exe manage.py seed_hostel_info

# 3. Start local server
venv\Scripts\python.exe manage.py runserver
```

- **URL:** `http://127.0.0.1:8000/`
- **Main Warden Login:** `adnan` / `adnan@1302`
- **Full Test Suite:** `venv\Scripts\python.exe manage.py test --noinput -v 1`
