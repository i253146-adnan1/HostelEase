# HostelEase — Hostel Management Website

**Course:** Introduction to Software Engineering (SE-1001)  
**Project:** HostelEase  
**Project Type:** Academic Software Engineering Project  
**Repository:** https://github.com/i253146-adnan1/hostelease

---

## 1. Project Overview

HostelEase is a web-based hostel management system designed for a hostel operated by a single Hostel Warden.

The system provides a centralized platform where the warden can manage hostel operations, while students can access their own information and submit requests without depending on the warden for every routine enquiry.

HostelEase aims to reduce manual administrative work, improve record management, and make student-related matters easier to track.

The application has three main areas:

- **Public Area:** A public-facing home page introducing the hostel.
- **Student Portal:** Students can access their own records and submit permitted requests.
- **Warden Portal:** The warden manages students, rooms, payments, complaints, and other hostel operations.

## 2. Problem Statement

Hostel administration often involves scattered records, manual communication, and repeated follow-ups between students and the warden.

This can make it difficult to maintain accurate information, track pending requests, verify payments, and communicate hostel updates.

HostelEase addresses these problems by providing one centralized website for hostel administration and student self-service.

## 3. Main Features

The approved Product Requirements Document (PRD v1.2) defines the following functional areas.

### Student Management
- Register students through the warden.
- Maintain student profiles and records.
- Search and edit student information.
- Mark students as Left and reactivate existing records.

### Authentication and Access Control
- Separate Student and Warden access.
- Warden-issued student credentials.
- Student password changes.
- Warden-managed password resets.
- Restrict students to their own records.

### Rooms and Room Requests
- Add and manage hostel rooms.
- Define room capacity.
- Assign and change student rooms.
- Track room occupancy.
- Handle room-change and room-swap requests.

### Fee and Payments
- Maintain student fee records.
- Allow students to submit payment proofs.
- Allow the warden to verify or reject submitted proofs.
- Maintain payment history and fee-change history.
- Calculate remaining or excess paid amounts using verified payments.

**Note:** HostelEase does not process online payments or integrate a payment gateway. Payments take place outside the application; the system records and verifies submitted payment proofs.

### Complaints
- Students can submit complaints.
- Support approved complaint categories.
- Allow optional complaint attachments.
- Warden-managed complaint status and remarks.
- Students can view complaint status.

### Hostel Information
- Manage announcements.
- Publish and update hostel menus.
- Publish and update hostel rules.
- Allow students to view shared hostel information.

### Feedback
Students can submit star ratings for:
- Food
- Rooms
- Washrooms
- Environment

The warden can view rating summaries.

### Leave Requests
- Students can submit temporary leave requests.
- Warden can approve or reject requests.
- Students can view request status.

### Visitor Log
- Warden can maintain visitor records.
- Record visitor name, student visited, purpose, and check-in/check-out times.
- Visitor records are restricted to the warden.

### Meal Opt-Outs
- Students can opt out of breakfast, lunch, or dinner for a future date.
- Students can cancel eligible opt-outs.
- Warden can view meal opt-out counts by date and meal type.

### Warden Dashboard
The dashboard provides a read-only overview of pending:
- Payment proofs
- Complaints
- Room requests
- Leave requests
- English/Urdu language toggle with RTL layout support when Urdu is active (planned in VS-23)

Meal opt-outs have a separate summary view.

## 4. Technology Stack

| Component | Technology |
|---|---|
| Backend | Python |
| Web Framework | Django 6.1.3 |
| Database | PostgreSQL |
| Database Driver | Psycopg 3.3.9 |
| Frontend | Django Templates, HTML, CSS |
| UI Framework | Bootstrap 5 (planned/approved stack) |
| Database Access | Django ORM |
| Authentication | Django authentication and server-side sessions |
| Environment Variables | python-dotenv |
| Image Processing | Pillow |
| File Storage | Local filesystem |
| Testing | Django Test Framework |
| Version Control | Git and GitHub |

## 5. Django Applications

The current Django settings register the following project applications:

| Application | General Responsibility |
|---|---|
| `accounts` | Authentication and access control |
| `hostel` | Hostel and student-related functionality |
| `finance` | Fees and payment-related functionality |
| `operations` | Operational workflows |

The logical feature modules are organized according to the approved project architecture. Their exact implementation responsibilities may be distributed across these Django applications.

## 6. Project Architecture

HostelEase follows a **layered monolithic architecture**, organized around presentation, business logic, and data access.

Important architectural principles include:

- Each feature module owns its own data.
- Modules communicate through their defined service interfaces.
- The Dashboard is a read-only aggregator and does not own business data.
- Authentication and access control are cross-cutting responsibilities.
- Uploaded files are stored on the local filesystem, with references maintained in the database.
- The application uses a relational database.
- Student and warden permissions must remain separate.
- Records covered by retention rules must not be hard-deleted.

The architecture and implementation constraints are documented in `architecture.md`, `AGENTS.md`, and the `ADR/` directory.

## 7. Repository Structure

The project uses Django's standard project structure.

Important files and directories include:

| File / Directory | Purpose |
|---|---|
| `manage.py` | Django command-line utility |
| `config/` | Django project configuration |
| `accounts/` | Accounts application |
| `hostel/` | Hostel application |
| `finance/` | Finance application |
| `operations/` | Operations application |
| `templates/` | Shared Django templates |
| `media/` | Uploaded media files |
| `requirements.txt` | Python dependencies |
| `.env` | Local environment configuration |
| `README.md` | Project documentation |

Additional documentation files include `PRD.md`, `architecture.md`, `AGENTS.md`, `plan.md`, and the `ADR/` directory.

## 8. Installation and Local Setup

### Prerequisites

Install the following software:

- Python 3.15
- PostgreSQL
- Git

The project dependencies are listed in `requirements.txt`.

### Step 1 — Clone the Repository

Open PowerShell and run:

```powershell
git clone https://github.com/i253146-adnan1/hostelease.git
cd hostelease
```

### Step 2 — Create a Virtual Environment

```powershell
py -3.15 -m venv venv
```

Activate the environment:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 3 — Install Dependencies

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install the project dependencies:

```powershell
pip install -r requirements.txt
```

### Step 4 — Configure PostgreSQL

Create a PostgreSQL database named:

```text
hostelease_db
```

The current Django settings use these database environment variables:

| Variable | Default Value |
|---|---|
| `DB_NAME` | `hostelease_db` |
| `DB_USER` | `postgres` |
| `DB_PASSWORD` | Empty string |
| `DB_HOST` | `localhost` |
| `DB_PORT` | `5432` |

### Step 5 — Create the `.env` File

Create a `.env` file in the project root.

Example:

```env
DB_NAME=hostelease_db
DB_USER=postgres
DB_PASSWORD=your_postgresql_password
DB_HOST=localhost
DB_PORT=5432
```

Replace `your_postgresql_password` with the password configured for your local PostgreSQL user.

The project loads environment variables using `python-dotenv`.

**Security:** Never commit `.env`, database passwords, secret keys, or other credentials to GitHub.

### Step 6 — Apply Database Migrations

```powershell
python manage.py migrate
```

### Step 7 — Create a Warden/Admin Account

The standard Django admin account can be created with:

```powershell
python manage.py createsuperuser
```

Follow the terminal instructions to create the account.

Use this account only if the project's current authentication and warden setup supports Django superuser access.

### Step 8 — Run the Development Server

```powershell
python manage.py runserver
```

Open the local development address:

```text
http://127.0.0.1:8000/
```

## 9. Testing

HostelEase uses Django's testing framework.

Run the test suite using:

```powershell
python manage.py test
```

Important areas for testing include:

- Authentication and role-based access.
- Student data isolation.
- Room capacity and assignments.
- Fee calculations and payment verification.
- Complaint workflows.
- Leave request rules.
- Visitor-log access restrictions.
- Meal opt-out date rules.

Test coverage and results should be documented as implementation progresses.

## 10. Project Documentation

| Document | Purpose |
|---|---|
| `PRD.md` | Approved product requirements |
| `architecture.md` | System architecture and module responsibilities |
| `AGENTS.md` | Instructions and constraints for AI coding agents |
| `ADR/` | Architecture Decision Records |
| `README.md` | Project overview and setup instructions |
| `plan.md` | Living implementation plan and vertical-slice progress |
| Workflow Evidence Log | Evidence of AI-assisted development and human review |
| Group Contribution Log | Team contribution records |

## 11. Development Approach

HostelEase is being developed through small, testable vertical slices.

Each slice should:

1. Follow the approved PRD and architecture.
2. Respect module boundaries and ADR decisions.
3. Implement required functionality across the relevant layers.
4. Include appropriate tests.
5. Be reviewed by a human team member.
6. Be integrated into the shared project.
7. Have progress and evidence recorded.

The implementation plan is maintained in `plan.md`.

## 12. Team Members and Responsibilities

| Member | Primary D4 Responsibility |
|---|---|
| Muhammad Fahad Basharat | Rooms and room-request workflow; integration coordination |
| Safiullah | Student Management, data model conventions, and database integrity |
| Adnanullah | Authentication and access guard; security review |
| Farmanullah | Shared UI/layout, file storage, hostel information, and local run/deployment documentation |

## 13. Project Constraints

The following constraints must be preserved:

- No online payment processing or payment gateway.
- No student self-registration.
- Students must not access other students' private records.
- Visitor Log is warden-only.
- No JWT-based authentication; server-side sessions are required.
- No microservices; retain the approved layered-monolith architecture.
- No cloud file-storage integration without an approved decision.
- Room capacity must never be exceeded.
- Temporary leave requests must not change a student's Active status, room assignment, or login access.
- Retained records must not be hard-deleted where prohibited by the PRD.

## 14. Current Development Status

HostelEase is complete for Deliverable 4 (`VS-00` through `VS-22`, plus Auth/Password-Recovery Overhaul, Student Management Password Reset, and Weekly Breakfast/Dinner Mess Menu Table).

### Quick Local Run & Seed Commands
```powershell
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py seed_main_warden
venv\Scripts\python.exe manage.py seed_hostel_info
venv\Scripts\python.exe manage.py runserver
```
- **Main Warden Credentials:** `adnan` / `adnan@1302` (change via `/accounts/change-password/` after setup).
- **Full Test Suite:** `venv\Scripts\python.exe manage.py test --noinput -v 1`
- **Final Report:** See `Final_Report.md` for architecture summary, CCP Analysis, and limitations.

Features should only be described as completed after implementation, testing, review, and acceptance.

## 15. Project Objective

The final objective is to deliver a working, locally runnable hostel management website that helps the warden manage hostel operations efficiently and allows students to access their own information and submit permitted requests through a centralized platform.

---

**GitHub Repository:** https://github.com/i253146-adnan1/hostelease