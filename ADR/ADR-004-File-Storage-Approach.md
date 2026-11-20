# ADR-004: File Storage Approach

- **ADR ID:** ADR-004
- **Full name:** File Storage Approach
- **Status:** Accepted
- **Date:** 2026-11-12
- **Decision owners:** HostelEase project team
- **Related documents:** HostelEase Final PRD; Architecture Document; AGENTS.md

## 1. Context

HostelEase allows students to upload payment proofs and, optionally, attach a file to a complaint. The finalized PRD specifies the following file constraints:

- Accepted formats: JPG, PNG, and PDF.
- Maximum file size: 5 MB.
- A payment proof has one file.
- A complaint may have one optional attachment.

The system must retain payment-proof and complaint records. The PRD also states that these records are not deleted; corrections are made through edits or status changes. The system does not process payments: uploaded files are evidence of payments made outside HostelEase.

The architecture decisions supplied for this project establish a single-deployable layered monolith and identify local filesystem storage, with file-path references held in the relational database, as the file-storage approach.

## 2. Architectural Decision

**HostelEase will store uploaded files on the application's local filesystem. The relational database will store the corresponding file-path reference and the metadata needed to associate each file with its HostelEase record.**

The database will continue to store the business records and their relationships. The uploaded file contents themselves will reside in the filesystem rather than being stored as database binary data.

This decision applies to the file uploads currently specified by the PRD:
- Student payment-proof files.
- Optional complaint attachments.

No additional upload categories are introduced by this ADR.

## 3. Alternatives Considered

### 3.1 Store file contents in the relational database

The database could store each uploaded file as binary data alongside its related record.

**Reason not selected:** The agreed project architecture identifies filesystem storage with database path references. Storing the file contents in the database would depart from that decision.

### 3.2 Store files on the local filesystem and keep references in the database

The application could save uploaded file contents on the local filesystem and store a reference to each file in the relational database.

**Reason selected:** This is the file-storage approach already established in the supplied HostelEase architecture decisions. It keeps file contents separate from the structured business records while allowing the application to associate each file with its payment-proof or complaint record.

### 3.3 Use external or cloud object storage

The application could store uploaded files in an external file-storage service.

**Reason not selected:** No external storage service, provider, hosting arrangement, or integration has been specified or agreed for HostelEase. Selecting one would introduce an unapproved technology and dependency.

## 4. Consequences

### 4.1 Positive consequences

- File contents remain separate from structured relational data.
- The database can associate an uploaded file with its relevant payment-proof or complaint record through a stored reference.
- The decision is consistent with the established HostelEase architecture.
- The approach does not require an external file-storage provider or integration.

### 4.2 Trade-offs and risks

- The application must keep database references consistent with files on disk.
- A missing, moved, or inaccessible file can leave a database reference that no longer resolves.
- Database backups alone do not preserve the uploaded file contents; the filesystem files must also be included in the project's backup approach.
- The location and access permissions of stored files must be configured so that students cannot bypass application authorization and access another student's files.
- The local-filesystem approach is tied to the environment in which the application is deployed. The deployment and hosting arrangement has not yet been specified.

## 5. Constraints and Related Requirements

This ADR does not change the requirements already established in the PRD:

- **FR-04:** Students can upload a payment proof with an amount and date.
- **FR-07:** Students can submit a complaint with an optional attachment.
- **C-02:** Payment proofs and complaint attachments are restricted to JPG, PNG, or PDF, with a maximum size of 5 MB.
- **BR-05:** Payment-proof and complaint records are retained and are not deleted.
- **NFR-01:** Students must not be able to access another student's records or warden-only pages.
- **C-04:** No hosting technology or external integration has been specified.

The file-format and size restrictions remain PRD constraints; this ADR does not redefine them.

## 6. Open Questions

The following details are not established by the supplied requirements or architecture decision and must not be treated as settled implementation decisions:

1. **Storage location:** What exact directory or deployment-specific location will hold uploaded files?
2. **File naming:** What naming convention will be used to avoid filename collisions and unsafe user-supplied filenames?
3. **File access:** Should files be delivered only through an application-controlled, authorization-checked route, and what exact access rules will apply?
4. **Backup and recovery:** What backup frequency, retention period, and recovery procedure will cover filesystem uploads as well as the database?
5. **File deletion and replacement:** How should the system handle a file when its associated record is corrected, replaced, or otherwise changed, given the PRD's record-retention rules?
6. **Deployment:** What hosting and deployment environment will be used, and how will persistent filesystem storage be ensured in that environment?
7. **Validation:** Are any additional file-content checks required beyond the PRD's allowed extensions and 5 MB size limit?

These are Open Questions. This ADR does not choose answers for them.

## 7. Scope of This Decision

This ADR decides **where uploaded file contents are stored** and **how the database refers to them**. It does not decide:

- The exact directory structure or filename format.
- A cloud-storage provider or external integration.
- A malware-scanning service or other unapproved technology.
- Backup schedules or retention periods.
- New file types, upload categories, or file-size limits.
- The unresolved visitor-log retention policy (OQ-32), which concerns visitor-log records rather than uploaded files.

## 8. Summary

HostelEase stores payment-proof files and optional complaint attachments on the local filesystem. The relational database stores references that associate those files with their relevant records. This follows the file-storage approach already established in the project's architecture decisions. Implementation details that have not been agreed remain Open Questions.
