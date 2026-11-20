# HostelEase — Product Requirements Document (PRD)

**Project:** HostelEase — Hostel Management Website
**Course:** Introduction to Software Engineering, Section SE-3A, FAST-NUCES
**Client / Primary stakeholder:** Hostel Warden Muhammad Sulaiman
**Version:** 1.2 (Final, validated)
**Status:** Final validated PRD after independent AI critique (Claude, fresh chat, PRD only) and human validation; updated with 3 additional features given by the TAs (acting as client) during the Deliverable-2 demo — see Section 7 Business Rules (BR-12, BR-13) and FR-17 to FR-19.
**Sources:** Deliverable 1 and baseline; Decision Log (Log 1–25); Final Flows v1 (F-01 to F-10, EC-01 to EC-51); Intent and Glossary; Deliverable-2 demo TA feedback (FR-17 to FR-19).

**ID scheme:** FR = functional requirement, NFR = non-functional requirement, BR = business rule, C = constraint, F = flow, EC = edge case, AC = acceptance criterion, OQ = open question, Log = decision log row.

---

## 1. Product / Feature Overview

HostelEase is a hostel management website for a hostel run by a single Hostel Warden. It has a public home page, a student area and a warden area. The warden manages student records, fee-payment proofs, complaints, rooms, the visitor log and hostel information in one place. Students log in with credentials issued by the warden to see their own information and to submit payment proofs, complaints, room requests, temporary leave requests, meal opt-outs and feedback.

The product does not process payments. Payments are made outside the website and the warden verifies the proofs students upload.

## 2. Problem and User Need

**Problem.** Hostel administration is done through scattered, manual channels. The warden has no single place for student records, fee payments, complaints, rooms and announcements, which leads to repeated follow-ups, hard-to-find records and unclear status of pending work. Students depend on the warden for simple information.

**User need.** The Hostel Warden needs one reliable place to keep student records, fee payments, complaints, room information and hostel announcements, so that less time is spent searching and following up. Students need to check their own fee, complaint, room and hostel information without repeatedly asking the warden.

**User-level goal.** A hostel warden can run day-to-day hostel administration from one place, while students can check their own status and submit their own requests without depending on the warden for every enquiry.

**Product / system intent.** HostelEase lets the warden create student accounts, manage student records, verify payment proofs, handle complaints, manage rooms, maintain a visitor log and publish announcements, while students view only their own data and submit proofs, complaints, room requests, leave requests, meal opt-outs and feedback.

## 3. Goals

- G-01 The warden can maintain complete student records in one place.
- G-02 The warden can verify payment proofs and keep an accurate fee record.
- G-03 The warden can receive, track and resolve complaints with a visible status.
- G-04 The warden can manage room assignments, occupancy, requests and swaps.
- G-05 The warden can publish announcements, rules and the menu.
- G-06 Students can see their own fee, complaint, room and hostel information after login.
- G-07 The warden sees pending items in one overview.
- G-08 The warden can review and decide student temporary leave requests.
- G-09 The warden can maintain a visitor log for the hostel.
- G-10 The warden can see meal opt-out counts for planning; students can manage their own opt-outs.

## 4. Non-Goals

- NG-01 HostelEase does not process payments; payments happen outside the website (for example through Easypaisa or JazzCash).
- NG-02 Students do not self-register; the warden creates accounts.
- NG-03 Students cannot view other students' records, roommate names or occupancy lists.
- NG-04 Student, fee, payment-proof, complaint, feedback, room-request, leave-request and meal-opt-out records are not deleted; corrections are made by editing or changing status (rooms, announcements and menu entries may be removed, see BR-05). Visitor-log retention is open (OQ-32).
- NG-05 Refunds are not processed in the system.

## 5. Users and Stakeholders

| Role | Description |
|---|---|
| Hostel Warden (primary user, client) | Creates accounts; manages student records, fees, complaints, rooms, announcements, menu, rules and the visitor log; verifies payment proofs; decides leave requests. |
| Student (secondary user) | Logs in with warden-issued credentials; views own data; submits payment proofs, complaints, room requests, leave requests, meal opt-outs and feedback; views announcements, menu and rules. |
| Public visitor | Sees the public home page showing what the hostel offers (OQ-01, OQ-02 are open). |

## 6. Ubiquitous Language / Glossary

| Term | Agreed meaning |
|---|---|
| Warden | The Hostel Warden, the only administrator of HostelEase. |
| Student | A hostel resident with a warden-created account. |
| Fee Record | A retained record of a student's total fee, amount paid, remaining amount and payment history. Changes to the total are kept in a fee-change history. |
| Payment Proof | Evidence (JPG, PNG or PDF) uploaded by a student for a payment made outside HostelEase. Status: Pending, Verified, Rejected. |
| Complaint | A retained record where a student reports a hostel problem. Status: Submitted, In Progress, Resolved. |
| Room Request | A student request for a new room, a room change or a swap. Status: Pending, Approved, Rejected, Cancelled. |
| Room Swap | A Room Request of type "Swap": a request to exchange rooms with another student, approved or rejected by the warden. |
| Occupancy | The number of students assigned to a room, compared with its capacity (the maximum the room can hold). |
| Pending item | An item waiting for the warden: a payment proof with status Pending, a complaint with status Submitted or In Progress, a room request with status Pending, or (resolved: ADR-005) a leave request with status Pending. |
| Open request | A room request with status Pending. |
| Menu | The meal information the warden publishes for students. |
| Rules | The hostel rules the warden publishes for students. |
| Announcement | Information published by the warden for students to view after login. |
| Active / Left Student | Active: currently in the hostel. Left: has left, marked by the warden. Records are kept. |
| Leave Request | A student request to be temporarily away from the hostel for a departure-to-return date range, with a reason. Status: Pending, Approved, Rejected. Does not change the student's Active status, room assignment or login access. |
| Visitor Log Entry | A warden-only record of a visitor's name, the student being visited, the purpose of the visit, and check-in/check-out times. Never visible to students. |
| Meal Opt-out | A student's choice to skip a specific meal (breakfast, lunch or dinner) on a specific future date. Status: Active, Cancelled. |

"Pending Payment" is not a status; it means the student's remaining fee balance. "Pending" is only a payment-proof, room-request or leave-request status.

## 7. Functional Requirements

Each requirement lists its source (flow, edge cases, decision log row). Decision log row 25 (feedback) was decided by the team after the grilling session. The 8 complaint categories (provisional, OQ-18) are: Room and Furniture; Electricity and Water; Cleanliness and Hygiene; Food and Mess; Internet; Security and Safety; Behavior or Conduct of Other Residents; Other. FR-17 to FR-19 were given by the TAs acting as client during the Deliverable-2 demo.

| ID | Requirement | Source |
|---|---|---|
| FR-01 | The system shall allow the warden to register a student (mandatory fields: full name, student ID, contact number, guardian name and contact number, room number; and the total fee) with a unique student ID, and create the student account with login credentials. | F-01; EC-01 to EC-04, EC-30, EC-31; Log 6, 7 |
| FR-02 | The system shall allow users to log in; a student can change their own password; for a forgotten password the warden resets it with a temporary password that the student must change. | F-02; EC-05 to EC-08, EC-32, EC-33; Log 17 |
| FR-03 | The system shall allow a student to view only their own information (profile, room, fee record, complaints, requests) and shared hostel information, and shall not allow access to other students' data. | F-02; Log 2, 14 |
| FR-04 | The system shall allow a student to upload a payment proof (JPG, PNG or PDF, up to 5 MB) with amount and date for a payment made outside the system. | F-03; EC-09 to EC-11, EC-34, EC-35; Log 8, 18 |
| FR-05 | The system shall allow the warden to verify or reject a payment proof (with a remark on rejection); verified payments update paid amount, remaining amount and payment history, and the student sees the status. | F-03; EC-12, EC-36 to EC-38; Log 8 |
| FR-06 | The system shall allow the warden to set and change a student's total fee, record each change in a fee-change history, and record "Excess paid" when the total is below the amount paid. | F-03; EC-13, EC-36; Log 21, 22 |
| FR-07 | The system shall allow a student to submit a complaint (one of the 8 categories in the glossary note below, description, optional attachment) and view its status and the warden's remark. | F-04; EC-14, EC-15, EC-39; Log 9, 19 |
| FR-08 | The system shall allow the warden to manage complaints through Submitted, In Progress and Resolved, and to add a remark; whether the remark is mandatory on Resolved is open (OQ-12). | F-04; EC-16, EC-17, EC-40; Log 9 |
| FR-09 | The system shall allow the warden to add and remove rooms, assign, change and clear a student's room, set room capacity, and view occupancy; full rooms cannot take new assignments. | F-05; EC-18, EC-21, EC-22; Log 10, 20 |
| FR-10 | The system shall allow a student to submit a room request or swap request with a reason, and cancel it while Pending. | F-05; EC-19, EC-20, EC-44; Log 23 |
| FR-11 | The system shall allow the warden to approve or reject room requests and swaps (remark on rejection); after approval the warden updates the room assignment (both rooms for a swap, subject to OQ-04 and OQ-05). | F-05; EC-41 to EC-44; Log 23 |
| FR-12 | The system shall allow the warden to create, edit and remove announcements, menu and rules, and students to view them. | F-06; EC-23 to EC-25, EC-45; Log 11 |
| FR-13 | The system shall allow the warden to mark a student Left (login disabled, room cleared, records retained) and reactivate the same record. | F-07; EC-26 to EC-29, EC-46; Log 15, 16 |
| FR-14 | The system shall show the warden a dashboard of pending items (payment proofs with status Pending, complaints that are Submitted or In Progress, room requests with status Pending, and — resolved: ADR-005 — leave requests with status Pending) with a count for each type. | Log 4, 13 |
| FR-15 | The system shall allow a student to submit feedback (1 to 5 stars for food, rooms, washrooms and environment) repeatedly without editing, and the warden to see counts per star level per aspect. | Log 25 |
| FR-16 | The system shall allow the warden to view, search and edit student records. | F-01; Log 4, 7, 24 |
| FR-17 | The system shall allow a student to submit a temporary leave request (departure date, return date, reason), and the warden to approve or reject it; the student's Active status is unaffected. | F-08; EC-47, EC-48; TA feedback (D2 demo) |
| FR-18 | The system shall allow the warden to record a visitor log entry (visitor name, student visited, purpose, check-in/check-out time); visible only to the warden. | F-09; EC-49; TA feedback (D2 demo) |
| FR-19 | The system shall allow a student to opt out of a specific meal (breakfast/lunch/dinner) on a future date, cancel it before that date, and the warden to see opt-out counts per date and meal type. | F-10; EC-50, EC-51; TA feedback (D2 demo) |

## 8. Non-Functional Requirements

| ID | Requirement (verifiable) | Verification |
|---|---|---|
| NFR-01 | Security and privacy: except for the public home page, only authenticated users can access the system; a student account is denied access to any other student's record and to every warden-only page (including the visitor log). | Using a student account, open the warden pages and another student's record from the menu and by entering the page address directly; every attempt is denied. |
| NFR-02 | Fee consistency: after every payment verification and every total-fee change, remaining = the larger of (total fee minus verified payments) and zero, and any amount paid above the total is shown as "Excess paid". | Check the fee record after each verification and each fee change. |
| NFR-03 | Usability (provisional, team target): with 2 first-time test users, each completes "register a student" and "verify a payment proof" without help in under 10 minutes. | Trial with 2 test users who have not used the system before. |
| NFR-04 | Performance (provisional, team target): the login page, student fee page and warden dashboard show their content within 3 seconds, measured from request to visible content, on a normal broadband connection. | Timed check of the three pages. |

NFR-03 and NFR-04 targets were set by the team; the client has not given them (see Assumptions and OQ-17). The rule that records are never deleted is stated once, in BR-05.

---

## 9. Business Rules and Constraints

**Business rules**

| ID | Rule | Source |
|---|---|---|
| BR-01 | The warden creates all student accounts and issues credentials; students do not self-register. | F-01; Log 6 |
| BR-02 | Payments happen outside the system; the system only records proofs and warden verification. | F-03; Log 8 |
| BR-03 | Only Verified payment proofs change the paid amount, remaining amount and payment history. | F-03; Log 8 |
| BR-04 | Allowed statuses: payment proof = Pending, Verified, Rejected; complaint = Submitted, In Progress, Resolved; room request (including swaps) = Pending, Approved, Rejected, Cancelled; student = Active, Left; leave request = Pending, Approved, Rejected; meal opt-out = Active, Cancelled. "Excess paid" is a recorded amount, not a status. | Log 8, 9, 23 |
| BR-05 | Student, fee, payment-proof, complaint, feedback, room-request records (including swaps), leave-request records, meal-opt-out records, payment history and fee-change history are never deleted; corrections are by edit or status change. Visitor-log retention is open (OQ-32). Rooms, announcements and menu entries may be removed (a room only if no students are assigned). | F-05, F-07; Log 24 |
| BR-06 | A room cannot exceed its capacity; capacity cannot be set below current occupancy; a full room cannot take new assignments. | F-05; Log 10, 20 |
| BR-07 | A student may have only one open room request and may cancel it while Pending. | F-05; Log 23 |
| BR-08 | A student sees only their own data; roommate names, occupancy lists and the visitor log are warden-only. | F-02; Log 14 |
| BR-09 | A student marked Left cannot log in; reactivation uses the same record and keeps all history. | F-07; Log 15, 16 |
| BR-10 | Lowering the total fee below the amount paid needs a reason; remaining becomes zero and the difference is recorded as "Excess paid"; any refund happens outside the system. | F-03; Log 22 |
| BR-11 | Submitted feedback cannot be edited. | Log 25 |
| BR-12 | An approved leave request does not change a student's Active status, room assignment, or login access. | F-08; TA feedback (D2 demo) |
| BR-13 | Visitor log entries are visible only to the warden; no student-facing access exists. | F-09; TA feedback (D2 demo) |

**Constraints**

| ID | Constraint | Source |
|---|---|---|
| C-01 | HostelEase does not process payments (no online payment processing). | Log 8 |
| C-02 | Payment proofs and complaint attachments: JPG, PNG or PDF only, 5 MB maximum (provisional, OQ-18); one file per proof; one optional attachment per complaint. | Log 18 |
| C-03 | Warden-only administration: student records, fee verification, complaints, rooms, announcements and the visitor log are controlled by the warden. | Log 1, 4 |
| C-04 | No technology, hosting or external integration has been specified. | Baseline |

## 10. Main User Flows / Scenarios

### F-01 — Register a student

- **Trigger:** A new student is admitted to the hostel.
- **Actors:** Warden (student receives credentials).
- **Main flow:**
  1. Warden opens "Add student".
  2. Enters mandatory fields (name, student ID, contact, guardian name and contact, room number) and optional fields.
  3. Enters the total fee.
  4. System validates and creates the record and account.
  5. Warden gives the credentials to the student.
- **Successful outcome:** Active student record, fee record with paid = 0.

### F-02 — Login, password change, password reset

- **Trigger:** Student opens the site to log in, or forgets the password.
- **Actors:** Student, Warden.
- **Main flow:**
  1. Student enters ID and password.
  2. System verifies and opens the student page.
  3. Student can change the password by entering the current one.
  4. If forgotten, the warden resets it with a temporary password and the student must set a new one at next login.
- **Successful outcome:** Student accesses only their own data.

### F-03 — Fee payment and proof verification

- **Trigger:** Student pays the fee via an external platform (Easypaisa, JazzCash, etc.).
- **Actors:** Student, Warden.
- **Main flow:**
  1. Student pays outside the website.
  2. Logs in and uploads the proof with amount and date.
  3. System validates the file and saves it as "Pending".
  4. It appears in the warden's pending items.
  5. Warden reviews and marks "Verified" or "Rejected" (with remark).
  6. On Verified, paid, remaining and history update.
  7. Student sees the status.
- **Successful outcome:** Fee record reflects only verified payments.

### F-04 — Complaint to resolution

- **Trigger:** Student has a hostel issue.
- **Actors:** Student, Warden.
- **Main flow:**
  1. Student selects a category and writes a description (optional attachment).
  2. System saves as "Submitted".
  3. Warden sees it in pending items.
  4. Warden sets "In Progress".
  5. Warden sets "Resolved" (remark mandatory or optional: OQ-12).
  6. Student sees the status and remark.
- **Successful outcome:** Complaint is marked Resolved.

### F-05 — Room assignment, request and swap

- **Trigger:** Warden assigns a room, or the student needs a room or change.
- **Actors:** Warden, Student.
- **Main flow:**
  1. Student submits a request (new room, change, or swap) with a reason.
  2. Status "Pending".
  3. Warden approves or rejects (remark on reject).
  4. On approval, warden updates the assignment (both rooms for a swap).
  5. Student sees the result.
- **Successful outcome:** Room occupancy stays consistent with capacity.

### F-06 — Announcements and menu

- **Trigger:** Warden has news or a menu change.
- **Actors:** Warden, Student.
- **Main flow:**
  1. Warden creates or edits an announcement or menu.
  2. System saves it.
  3. Students see it after login.
  4. Warden removes outdated items.
- **Successful outcome:** Students see current hostel information.

### F-07 — Student leaves and reactivation

- **Trigger:** Student leaves the hostel, or returns.
- **Actors:** Warden.
- **Main flow:**
  1. Warden marks the student "Left".
  2. Login is disabled and the room is cleared.
  3. Records are kept.
  4. On return, the warden reactivates the same record and assigns a room again.
- **Successful outcome:** History is preserved, with no duplicate record.

### F-08 — Temporary leave request

- **Trigger:** Student needs to leave the hostel temporarily.
- **Actors:** Student, Warden.
- **Main flow:**
  1. Student submits a leave request with departure date, return date and reason.
  2. System saves it as "Pending".
  3. Warden reviews and approves or rejects (remark on reject).
  4. Student sees the result.
- **Successful outcome:** Leave request resolved; student's Active status, room assignment and login access are unchanged throughout.

### F-09 — Visitor log entry

- **Trigger:** A visitor arrives to meet a student.
- **Actors:** Warden.
- **Main flow:**
  1. Warden opens "Add visitor".
  2. Enters visitor name, the student being visited, purpose, and check-in time.
  3. System saves the entry.
  4. Warden records check-out time when the visitor leaves.
- **Successful outcome:** Visitor log entry created and retained; visible only to the warden.

### F-10 — Meal opt-out

- **Trigger:** Student will not be present for a specific upcoming meal.
- **Actors:** Student, Warden.
- **Main flow:**
  1. Student selects a future date and meal type (breakfast/lunch/dinner) and opts out.
  2. System saves the opt-out.
  3. Student may cancel it before that meal's date.
  4. Warden views total opt-out counts per date and meal type.
- **Successful outcome:** Opt-out counts available to the warden for meal planning.

## 11. Edge Cases and Failure Conditions

### F-01 — Register a student

- **EC-01:** Duplicate student ID.
- **EC-02:** Mandatory field missing.
- **EC-03:** Invalid contact number.
- **EC-04:** Chosen room is full.
- **EC-30:** Student/account creation encounters a failure after the other part has been created.
- **EC-31:** The total fee entered is invalid.

### F-02 — Login, password change, password reset

- **EC-05:** Wrong credentials.
- **EC-06:** Account disabled (student marked Left).
- **EC-07:** Wrong current password during change.
- **EC-08:** Temporary password not changed.
- **EC-32:** Temporary password is unusable.
- **EC-33:** Repeated failed login attempts. (Open Question 11: whether any lockout rule applies.)

### F-03 — Fee payment and proof verification

- **EC-09:** Invalid file type or size.
- **EC-10:** Amount greater than remaining.
- **EC-11:** Same proof uploaded twice. (Open Question 14: what counts as a duplicate.)
- **EC-12:** Proof rejected. (Open Question 8: what the student does after rejection.)
- **EC-13:** Warden reduces total below amount paid ("Excess paid").
- **EC-34:** Payment proof is uploaded when the remaining balance is already zero.
- **EC-35:** Two pending payment proofs together exceed the remaining fee.
- **EC-36:** Fee total changes while a payment proof is Pending.
- **EC-37:** Warden attempts to verify or change the status of a payment proof more than once.
- **EC-38:** Uploaded proof is technically valid but its contents cannot be verified, or the entered amount/date does not match the proof.
- _Reference: If the student is marked Left while a payment proof is pending, see EC-46 in F-07._

### F-04 — Complaint to resolution

- **EC-14:** Category or description missing.
- **EC-15:** Invalid attachment.
- **EC-16:** Student unhappy after Resolved. (Open Question 3: whether a Resolved complaint can be reopened.)
- **EC-17:** Student leaves with an open complaint. (See EC-46 in F-07.)
- **EC-39:** Student submits multiple complaints describing the same issue.
- **EC-40:** Warden attempts to resolve a complaint without a remark. (Open Question 12: whether the remark is mandatory.)
- _Reference: If the student is marked Left while a complaint or other pending item remains, see EC-46 in F-07._

### F-05 — Room assignment, request and swap

- **EC-18:** Target room full.
- **EC-19:** Student already has an open request.
- **EC-20:** Swap target student or room not found.
- **EC-21:** Capacity lowered below occupancy.
- **EC-22:** Removing a room that still has students.
- **EC-41:** Room becomes full between request submission and approval (or between validation and record creation).
- **EC-42:** Room is removed while a request targeting it is Pending.
- **EC-43:** A student's room assignment changes before an approved swap takes effect, or the swap would violate room capacity.
- **EC-44:** Warden attempts to approve a room request after the student has cancelled it.
- _Open Questions: Whether the other student must agree to a swap (OQ 4), and when an approved swap takes effect (OQ 5)._

### F-06 — Announcements and menu

- **EC-23:** Empty title or message.
- **EC-24:** Menu not yet set.
- **EC-25:** Student tries to edit (blocked).
- **EC-45:** No announcements or menu entries are available to display.
- _Open Question: Whether announcements and menu are also visible on the public page (OQ 2)._

### F-07 — Student leaves and reactivation

- **EC-26:** Student leaves with a remaining balance.
- **EC-27:** Open request or complaint at leaving. (See EC-46.)
- **EC-28:** Reactivated but room unavailable. (Open Question 15: what happens when no room is available on reactivation.)
- **EC-29:** Student is marked Left by mistake.
- **EC-46:** Student is marked Left while pending payment proofs, room requests/swaps, complaints, or other pending items remain. (Open Question 13: what happens to pending items.)

### F-08 — Temporary leave request

- **EC-47:** Return date is before or equal to the departure date.
- **EC-48:** Student already has a Pending or Approved leave request. (Open Question: is only one open leave request allowed, like room requests? OQ-30)

### F-09 — Visitor log entry

- **EC-49:** Warden enters a student ID/name that does not match any existing student record.

### F-10 — Meal opt-out

- **EC-50:** Student tries to opt out of a meal for a past date.
- **EC-51:** Student tries to cancel an opt-out after that meal's date has already passed.

### Edge-case coverage

Every edge case describes a situation. The expected response is given by an acceptance criterion, or by an Open Question where the behaviour is not yet decided.

| Edge case | Covered by |
|---|---|
| EC-01 | AC-01.2 |
| EC-02 | AC-01.3 |
| EC-03 | AC-01.3 |
| EC-04 | AC-01.4 |
| EC-05 | AC-02.2 |
| EC-06 | AC-13.2 |
| EC-07 | AC-02.3 |
| EC-08 | AC-02.4 |
| EC-09 | AC-04.2 |
| EC-10 | OQ-20 |
| EC-11 | OQ-14 |
| EC-12 | OQ-08 |
| EC-13 | AC-06.2 |
| EC-14 | AC-07.2 |
| EC-15 | AC-07.3 |
| EC-16 | OQ-03 |
| EC-17 | OQ-13 (see EC-46) |
| EC-18 | AC-09.2 |
| EC-19 | AC-10.2 |
| EC-20 | AC-10.4 |
| EC-21 | AC-09.3 |
| EC-22 | AC-09.4 |
| EC-23 | AC-12.2 |
| EC-24 | AC-12.5 |
| EC-25 | AC-12.4 |
| EC-26 | AC-13.1, OQ-13 |
| EC-27 | OQ-13 (see EC-46) |
| EC-28 | OQ-15 |
| EC-29 | AC-13.3 |
| EC-30 | OQ-21 |
| EC-31 | OQ-21 |
| EC-32 | OQ-25 |
| EC-33 | OQ-11, OQ-25 |
| EC-34 | OQ-20 |
| EC-35 | OQ-20 |
| EC-36 | OQ-22 |
| EC-37 | OQ-22 |
| EC-38 | OQ-22 |
| EC-39 | OQ-23 |
| EC-40 | OQ-12 |
| EC-41 | AC-11.3 |
| EC-42 | OQ-24 |
| EC-43 | OQ-24 |
| EC-44 | AC-11.4 |
| EC-45 | AC-12.5 |
| EC-46 | OQ-13 |
| EC-47 | AC-17.2 |
| EC-48 | AC-17.3, OQ-30 |
| EC-49 | AC-18.2 |
| EC-50 | AC-19.2 |
| EC-51 | AC-19.4 |

---

## 12. Acceptance Criteria

### FR-01 Register a student
- **AC-01.1** (FR-01) **Given** the warden is on "Add student" and all mandatory fields and the total fee are valid with a unique student ID, **When** the warden submits, **Then** the student record and account are created, a fee record with paid = 0 exists, and the credentials are available for the warden to give to the student.
- **AC-01.2** (FR-01, EC-01) **Given** a record with the same student ID exists, **When** the warden submits another registration with that ID, **Then** the registration is rejected and no new record is created.
- **AC-01.3** (FR-01, EC-02, EC-03) **Given** a mandatory field is missing or the contact number is invalid, **When** the warden submits, **Then** the registration is not saved.
- **AC-01.4** (FR-01, EC-04) **Given** the chosen room is full, **When** the warden submits the registration with that room, **Then** the student is not assigned to that room (whether the registration is rejected or saved without a room is open: OQ-21).

### FR-02 Login and passwords
- **AC-02.1** (FR-02) **Given** a user with valid credentials, **When** the user logs in, **Then** the user reaches the interface for their role (student or warden).
- **AC-02.2** (FR-02, EC-05) **Given** wrong credentials, **When** a user tries to log in, **Then** access is denied and the user stays on the login page.
- **AC-02.3** (FR-02, EC-07) **Given** a logged-in student, **When** the student enters a wrong current password to change it, **Then** the change is rejected; **and when** the correct current password is entered, **then** the new password replaces the old one.
- **AC-02.4** (FR-02, EC-08) **Given** the warden has reset a student's password to a temporary one, **When** the student logs in with it, **Then** the student must set a new password before continuing.

### FR-03 Own data only
- **AC-03.1** (FR-03) **Given** a logged-in student, **When** the student opens their profile, fee record, complaints and requests, **Then** only that student's own information is shown.
- **AC-03.2** (FR-03, NFR-01) **Given** a logged-in student, **When** the student tries to open another student's record, a roommate list, an occupancy list, the visitor log or a warden-only page, **Then** access is denied and no data of other students is shown.

### FR-04 Upload payment proof
- **AC-04.1** (FR-04) **Given** a logged-in student, **When** the student uploads a JPG, PNG or PDF of 5 MB or less with an amount and date, **Then** the proof is saved with status Pending and appears in the warden's pending items. (Rules for zero balance, amounts above the remaining balance and several pending proofs are open: OQ-20.)
- **AC-04.2** (FR-04, EC-09) **Given** a file of another type or larger than 5 MB, **When** the student uploads it, **Then** the upload is rejected and no proof is saved.

### FR-05 Verify or reject payment proof
- **AC-05.1** (FR-05) **Given** a Pending proof, **When** the warden marks it Verified, **Then** the paid amount increases by the proof amount, remaining equals total minus verified payments, the payment history shows it, and the student sees the status.
- **AC-05.2** (FR-05) **Given** a Pending proof, **When** the warden marks it Rejected with a remark, **Then** paid and remaining amounts do not change and the student sees the status and remark.

### FR-06 Total fee and fee-change history
- **AC-06.1** (FR-06) **Given** a student's fee record, **When** the warden changes the total fee, **Then** the old total, new total, date and reason (if entered) are recorded in the fee-change history and the existing payment history is unchanged.
- **AC-06.2** (FR-06, EC-13) **Given** a new total below the amount paid, **When** the warden changes it with a reason, **Then** remaining shows zero and "Excess paid" equals paid minus the new total; **and when** no reason is entered, **then** the change is not saved.

### FR-07 Submit a complaint
- **AC-07.1** (FR-07) **Given** a logged-in student, **When** the student selects a category, enters a description (optional attachment) and submits, **Then** the complaint is saved with status Submitted and appears in the warden's pending items.
- **AC-07.2** (FR-07, EC-14) **Given** the category or description is missing, **When** the student submits, **Then** the complaint is not saved.
- **AC-07.3** (FR-07, EC-15) **Given** an attachment that is not JPG, PNG or PDF or exceeds 5 MB, **When** the student submits, **Then** the attachment is rejected.
- **AC-07.4** (FR-07) **Given** a submitted complaint, **When** the student opens it, **Then** the student sees its status and any remark the warden added.

### FR-08 Manage complaints
- **AC-08.1** (FR-08) **Given** a Submitted complaint, **When** the warden sets In Progress and later Resolved (adding a remark), **Then** each status is saved and the student can see the status and remark.
- Whether the remark is mandatory (EC-40) and whether a Resolved complaint can be reopened (EC-16) are open (OQ-12, OQ-03) and cannot be tested yet.

### FR-09 Room assignment and capacity
- **AC-09.1** (FR-09) **Given** a room with free capacity, **When** the warden assigns a student, **Then** the assignment and occupancy are saved and the student can see their room number.
- **AC-09.2** (FR-09, EC-18) **Given** a full room, **When** the warden assigns another student, **Then** the assignment is not made.
- **AC-09.3** (FR-09, EC-21) **Given** a room with students assigned, **When** the warden sets capacity below the current occupancy, **Then** the change is rejected; **and when** the capacity is increased, **then** it is saved.
- **AC-09.4** (FR-09, EC-22) **Given** a room with students assigned, **When** the warden tries to remove it, **Then** removal is not allowed.

### FR-10 Student room requests
- **AC-10.1** (FR-10) **Given** a student with no open request, **When** the student submits a request with a type, a preferred room or swap target, and a reason, **Then** it is saved with status Pending.
- **AC-10.2** (FR-10, EC-19) **Given** a student with an open request, **When** the student submits another, **Then** it is rejected.
- **AC-10.3** (FR-10) **Given** a Pending request, **When** the student cancels it, **Then** its status becomes Cancelled and the record is retained.
- **AC-10.4** (FR-10, EC-20) **Given** a swap request naming a student or room that does not exist, **When** the student submits, **Then** the request is rejected and not saved.

### FR-11 Decide room requests
- **AC-11.1** (FR-11) **Given** a Pending request, **When** the warden approves it, **Then** the status is Approved and the student sees the result; once the warden updates the room assignment, the student sees the new room number.
- **AC-11.2** (FR-11) **Given** a Pending request, **When** the warden rejects it with a remark, **Then** the status is Rejected and no room assignment changes.
- **AC-11.3** (FR-11, EC-41) **Given** the target room became full after the request, **When** the warden tries to assign the student to it, **Then** the assignment is not made and the student's room is unchanged.
- **AC-11.4** (FR-11, EC-44) **Given** a request the student has Cancelled, **When** the warden tries to approve it, **Then** approval is not possible.
- Swap consent and effective time are open (OQ-04, OQ-05) and cannot be tested yet.

### FR-12 Announcements, menu and rules
- **AC-12.1** (FR-12) **Given** a title and message, **When** the warden publishes an announcement, **Then** students see it after login.
- **AC-12.2** (FR-12, EC-23) **Given** an empty title or message, **When** the warden publishes, **Then** it is rejected and not shown to students.
- **AC-12.3** (FR-12) **Given** a published announcement, menu entry or rule, **When** the warden edits or removes it, **Then** students see the updated or removed state the next time they open the page.
- **AC-12.4** (FR-12, EC-25) **Given** a logged-in student, **When** the student tries to create, edit or remove an announcement, menu entry or rule, **Then** the action is not allowed.
- **AC-12.5** (FR-12, EC-24, EC-45) **Given** no announcements or menu have been published, **When** a student opens that page, **Then** the page shows no entries and no error.
- **AC-12.6** (FR-12) **Given** the warden enters the menu and rules, **When** a student opens the menu and rules pages after login, **Then** the published menu and rules are shown.

### FR-13 Mark Left and reactivate
- **AC-13.1** (FR-13) **Given** an active student, **When** the warden marks the student Left, **Then** login is disabled, the room is cleared, and all records are retained.
- **AC-13.2** (FR-13, EC-06) **Given** a student marked Left, **When** the student tries to log in, **Then** access is denied.
- **AC-13.3** (FR-13, EC-29) **Given** a student marked Left, **When** the warden reactivates the student, **Then** the student's login works again, the earlier records and history are visible on the same student record, no second record exists for that student ID, and the room field is empty until the warden assigns a room.
- Pending items at the time of leaving (EC-46) and no room on reactivation (EC-28) are open (OQ-13, OQ-15).

### FR-14 Warden dashboard
- **AC-14.1** (FR-14) **Given** payment proofs with status Pending, complaints that are Submitted or In Progress, and room requests with status Pending, **When** the warden opens the dashboard, **Then** each item type is listed with its count. (resolved: ADR-005)
- **AC-14.2** (FR-14, NFR-01) **Given** a logged-in student, **When** the student tries to open the dashboard, **Then** access is denied.

### FR-15 Feedback
- **AC-15.1** (FR-15) **Given** a logged-in student, **When** the student rates food, rooms, washrooms and environment from 1 to 5 stars and submits, **Then** the feedback is saved.
- **AC-15.2** (FR-15) **Given** a student who has submitted feedback, **When** the student submits again, **Then** the new entry is saved separately and the earlier entry is unchanged.
- **AC-15.3** (FR-15, BR-11) **Given** submitted feedback, **When** the student tries to edit it, **Then** editing is not allowed.
- **AC-15.4** (FR-15) **Given** submitted feedback, **When** the warden opens the feedback summary, **Then** the number of ratings at each star level is shown separately for each aspect.

### FR-16 Student records
- **AC-16.1** (FR-16) **Given** registered students, **When** the warden searches by name or student ID, **Then** the matching student records are listed and can be opened.
- **AC-16.2** (FR-16, BR-05) **Given** a student record, **When** the warden edits a student's details and saves, **Then** the updated details are shown and no delete option exists for the record.

### FR-17 Temporary leave request
- **AC-17.1** (FR-17) **Given** a departure date, a return date after the departure date, and a reason, **When** the student submits a leave request, **Then** it is saved with status Pending.
- **AC-17.2** (FR-17, EC-47) **Given** a return date before or equal to the departure date, **When** the student submits, **Then** the request is not saved.
- **AC-17.3** (FR-17, EC-48) **Given** a student with a Pending or Approved leave request, **When** the student submits another, **Then** it is rejected (subject to OQ-30).
- **AC-17.4** (FR-17, BR-12) **Given** a Pending leave request, **When** the warden approves or rejects it (remark on reject), **Then** the status updates, the student's Active status, room assignment and login access are unchanged, and the student sees the result.

### FR-18 Visitor log
- **AC-18.1** (FR-18) **Given** an existing student ID, **When** the warden enters the visitor's name, purpose and check-in time, **Then** the entry is saved.
- **AC-18.2** (FR-18, EC-49) **Given** a student ID that does not match any existing record, **When** the warden submits, **Then** the entry is not saved.
- **AC-18.3** (FR-18) **Given** a saved visitor entry without a check-out time, **When** the warden records the check-out time, **Then** the entry is updated.
- **AC-18.4** (FR-18, BR-13, NFR-01) **Given** a logged-in student, **When** the student tries to open the visitor log, **Then** access is denied.

### FR-19 Meal opt-out
- **AC-19.1** (FR-19) **Given** a future date and a meal type (breakfast/lunch/dinner), **When** the student opts out, **Then** the opt-out is saved with status Active.
- **AC-19.2** (FR-19, EC-50) **Given** a past date, **When** the student tries to opt out, **Then** the opt-out is not saved.
- **AC-19.3** (FR-19) **Given** an Active opt-out for a date that has not yet passed, **When** the student cancels it, **Then** its status becomes Cancelled and the record is retained.
- **AC-19.4** (FR-19, EC-51) **Given** an opt-out whose meal date has already passed, **When** the student tries to cancel it, **Then** the cancellation is not allowed.
- **AC-19.5** (FR-19) **Given** saved opt-outs, **When** the warden opens the meal opt-out summary, **Then** the total count is shown per date and meal type.

### Non-functional requirements
- **AC-NFR-01** (NFR-01) Using a student account, every attempt to open another student's record, the visitor log, or a warden-only page, from the menu or by entering the page address, is denied.
- **AC-NFR-02** (NFR-02) After each verification and each fee change, remaining equals the larger of (total minus verified payments) and zero, and any excess paid is shown as "Excess paid".
- **AC-NFR-03** (NFR-03) With 2 first-time test users, each completes "register a student" and "verify a payment proof" without help in under 10 minutes.
- **AC-NFR-04** (NFR-04) The login page, student fee page and warden dashboard each show their content within 3 seconds, measured from request to visible content, on a normal broadband connection.

---

## 13. Assumptions

- A-01 The 3-second page load, the 10-minute task time and the 2-user usability trial are project targets set by the team, not by the client (OQ-17).
- A-02 The 8 complaint categories and the 5 MB file limit were proposed during grilling and still need the warden's confirmation (OQ-18). They are binding for this PRD until the warden says otherwise.
- A-03 Feedback with 1 to 5 star ratings (Log 25) was decided by the team after the grilling session and is not yet confirmed by the client (OQ-19).
- A-04 No separate notification feature is assumed. Students see statuses on their own pages. Whether any notifications are needed is open (OQ-16).
- A-05 FR-17 to FR-19 were given by the TAs acting as the client during the Deliverable-2 demo and are treated as binding client requirements for Deliverable 3.

---

## 14. Open Questions

These are not decided. Do not treat them as requirements.

| ID | Open question | Related |
|---|---|---|
| OQ-01 | Is the public visitor a separate role? | FR-12 |
| OQ-02 | Are announcements and menu visible on the public page, and what does the public home page show? | FR-12 |
| OQ-03 | Can a Resolved complaint be reopened? | FR-08, EC-16 |
| OQ-04 | Must the other student agree to a room swap? | FR-10, FR-11 |
| OQ-05 | When does an approved swap take effect? | FR-11 |
| OQ-06 | Does the room fee differ by room? | FR-06, FR-09 |
| OQ-07 | How does a room change affect the fee? | FR-06, FR-11 |
| OQ-08 | What does the student do after a payment proof is rejected, and is a re-upload a duplicate? | FR-05, EC-12 |
| OQ-09 | How is the first warden account created, and how does the warden change or recover their own password? | FR-02 |
| OQ-10 | Should the system record refunds (tracking only)? Refund processing itself is a non-goal (NG-05). | FR-06, BR-10 |
| OQ-11 | Is there a lockout after repeated failed logins? | FR-02, EC-33 |
| OQ-12 | Is a remark mandatory when marking a complaint Resolved? | FR-08, EC-40 |
| OQ-13 | What happens to pending items, the open balance and the session when a student is marked Left? | FR-13, EC-17, EC-26, EC-27, EC-46 |
| OQ-14 | What counts as a duplicate payment proof? | FR-04, EC-11 |
| OQ-15 | What happens on reactivation when the former room is no longer available? | FR-13, EC-28 |
| OQ-16 | Are notifications needed, and for which events? | FR-14 |
| OQ-17 | Does the warden accept the NFR targets (3-second load, 2-user trial, 10 minutes)? | NFR-03, NFR-04 |
| OQ-18 | Does the warden confirm the 8 complaint categories and the 5 MB limit (phone photos may exceed it)? | FR-07, C-02 |
| OQ-19 | Does feedback need a text comment, are all four aspects required, is there a limit per student, and does the summary count every entry or one per student? | FR-15 |
| OQ-20 | Can a student upload a proof at zero balance, for more than the remaining balance, or when pending proofs together exceed it? | FR-04, EC-10, EC-34, EC-35 |
| OQ-21 | If the room is full at registration, is the registration rejected or saved without a room? What happens if creating the record or account fails partway, or the total fee is invalid? | FR-01, EC-04, EC-30, EC-31 |
| OQ-22 | What are the validation rules (contact format, fee and amount limits), may the warden adjust the amount at verification, what does "verify" check, can a Verified proof be corrected, and what happens when the fee total changes while a proof is Pending? | FR-05, EC-36, EC-37, EC-38 |
| OQ-23 | What happens when a student submits several complaints for the same issue? | FR-07, EC-39 |
| OQ-24 | What happens when a room fills, is removed, or an assignment changes while a request is Pending or before a swap takes effect? | FR-10, FR-11, EC-42, EC-43 |
| OQ-25 | How are initial and temporary passwords set and delivered, what is "unusable", and what password rules apply? | FR-02, EC-32 |
| OQ-26 | How are cash or offline payments and existing students' opening balances entered? | FR-05, FR-06 |
| OQ-27 | What are the allowed status transitions for proofs, complaints and requests? | BR-04 |
| OQ-28 | What room and student information may a student see to make a request or swap, and which profile data may students edit? | FR-03, FR-10 |
| OQ-29 | Is the fee one-time or per period, with due dates and currency rules? | FR-06 |
| OQ-30 | Is only one open leave request allowed per student, like room requests? | FR-17, EC-48 |
| OQ-31 | Resolved — see ADR-005. | FR-14, FR-17 |
| OQ-32 | Are visitor log entries covered by the never-delete rule (BR-05), and is there a retention limit? | FR-18, BR-05 |
| OQ-33 | Is there a same-day cutoff time before a meal after which a student cannot cancel an opt-out? | FR-19, EC-51 |

---

## 15. Traceability

**Goals to requirements**

| Goal | Requirements |
|---|---|
| G-01 Maintain student records in one place | FR-01, FR-13, FR-16 |
| G-02 Verify payment proofs and keep an accurate fee record | FR-04, FR-05, FR-06, NFR-02 |
| G-03 Receive, track and resolve complaints | FR-07, FR-08 |
| G-04 Manage rooms, requests and swaps | FR-09, FR-10, FR-11 |
| G-05 Publish announcements, rules and menu | FR-12 |
| G-06 Students see their own information | FR-02, FR-03, FR-15, NFR-01 |
| G-07 Warden sees pending items in one overview | FR-14 |
| G-08 Review and decide student temporary leave requests | FR-17 |
| G-09 Maintain a visitor log | FR-18 |
| G-10 See meal opt-out counts for planning | FR-19 |

**Need to acceptance criteria**

| User need | User goal | Requirement | Acceptance criteria |
|---|---|---|---|
| Keep student records in one place | Run administration from one place | FR-01, FR-13, FR-16 | AC-01.x, AC-13.x, AC-16.x |
| Accurate fee and payments | Run administration from one place | FR-04, FR-05, FR-06, NFR-02 | AC-04.x, AC-05.x, AC-06.x, AC-NFR-02 |
| Handle complaints | Run administration from one place | FR-07, FR-08 | AC-07.x, AC-08.1 |
| Manage rooms | Run administration from one place | FR-09, FR-10, FR-11 | AC-09.x, AC-10.x, AC-11.x |
| Share hostel information | Students check status themselves | FR-12 | AC-12.x |
| Students see their own data | Students check status themselves | FR-02, FR-03, FR-15, NFR-01 | AC-02.x, AC-03.x, AC-15.x, AC-NFR-01 |
| See pending work | Run administration from one place | FR-14 | AC-14.x |
| Easy to use and responsive | Both | NFR-03, NFR-04 | AC-NFR-03, AC-NFR-04 |
| Manage temporary leave | Run administration from one place / students self-manage | FR-17 | AC-17.x |
| Track visitors | Run administration from one place | FR-18 | AC-18.x |
| Plan meals via opt-outs | Both | FR-19 | AC-19.x |