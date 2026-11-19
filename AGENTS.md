# AGENTS.md — Instructions for AI Coding Agent

## Project Intent
HostelEase: single-warden hostel management site. See PRD.md 
(v1.2) and architecture.md before writing any code.

## Module Boundaries (must preserve)
- Auth & Access Guard, Student Management, Fee & Payments, Complaints, 
  Rooms, Hostel Info, Feedback, Dashboard, File Storage, Leave Requests, 
  Visitor Log, Meal Opt-Outs — each is a separate module/folder.
- Dashboard must NOT own its own data tables — read-only aggregation 
  only, via other modules' service functions. Per ADR-005, Dashboard 
  reads: Fee & Payments (pending proofs), Complaints (Submitted/In 
  Progress), Rooms (pending requests), and Leave Requests (pending). 
  Meal Opt-Outs is NOT read by the Dashboard — it has its own separate 
  warden-facing summary view.
- Visitor Log has no student-facing routes or APIs at all (BR-13) — not 
  even for the visitor's own student. Warden-only, end to end.
- No module may directly query/write another module's database table. 
  Communication only through that module's defined service interface.

## Dependency / Interface Rules
- Auth & Access Guard runs before every request reaches another module 
  (cross-cutting — do not duplicate access checks inside individual 
  modules).
- Visitor Log must validate the referenced student ID against Student 
  Management's interface (not a direct table join) before saving an 
  entry (EC-49).
- Leave Requests must never modify a student's Active status, room 
  assignment, or login access (BR-12) — these stay entirely within 
  Student Management's ownership.

## Constraints
- No online payment processing / no payment-gateway integration (C-01). 
  Do not add one.
- Records are never hard-deleted (BR-05) — use status fields, not 
  DELETE. This includes leave-request and meal-opt-out records. 
  Visitor-log retention is open (OQ-32) — do not hard-delete visitor 
  entries without raising it as a question.
- Uploaded files (proofs/attachments): JPG/PNG/PDF, ≤5MB, stored on 
  local filesystem with DB path reference — not cloud storage.
- Leave request: return date must be after the departure date (EC-47); 
  one open (Pending/Approved) leave request per student unless OQ-30 is 
  resolved otherwise.
- Meal opt-out: cannot be created for a past date (EC-50); cannot be 
  cancelled after its meal date has passed (EC-51).

## Technology (already decided — do not change without raising as new ADR)
- Relational DB (MySQL/PostgreSQL) — see ADR-002.
- Server-side sessions for auth (not JWT) — see ADR-003.
- Layered monolith (not microservices) — see ADR-001.
- Local filesystem + DB path reference for file storage — see ADR-004.
- Dashboard scope (which modules it reads from) — see ADR-005.

## Actions requiring human approval before proceeding
- Introducing any new framework, database, or external service.
- Changing any module boundary defined above.
- Anything conflicting with an existing ADR (001–005).

## Handling Ambiguity
- If PRD.md has an Open Question (OQ-xx) relevant to a task, flag 
  it — do not assume an answer and implement silently. This includes 
  OQ-30 (one leave request at a time?), OQ-32 (visitor-log retention), 
  and OQ-33 (opt-out cancellation cutoff).
- Respect all ADRs in /ADR/. If a conflict appears, stop and ask.