# ADR-003: Authentication/Access Boundary

- **Status:** Accepted
- **Decision:** Server-side session authentication (not JWT), enforced by a cross-cutting Auth & Access Guard.

## Context

HostelEase has two authenticated user roles: Warden and Student. The Final PRD establishes that, except for the public homepage, access requires authentication. Students may view only their own records and shared hostel information; other students' records and warden-only pages (including the visitor log) must remain inaccessible to students. Unauthorized access must be denied even when a protected page is opened directly by URL (NFR-01, FR-03, BR-08, BR-13, AC-NFR-01).

The project architecture and `AGENTS.md` specify server-side sessions for authentication, explicitly reject JWT, and require the Auth & Access Guard to run before requests reach other modules. The guard is cross-cutting; access checks are not to be duplicated inside individual feature modules.

## Decision

HostelEase will use **server-side sessions for authentication, not JWT**. A shared **Auth & Access Guard** will act as a cross-cutting boundary and run before a request reaches the application’s feature modules.

The guard is responsible for enforcing authentication and the role/access boundary established by the PRD. In particular, it must preserve public homepage access, require authentication for protected areas, deny students access to warden-only pages, and prevent students from accessing other students' records.

This decision selects the authentication approach and guard responsibility. It does not select a specific framework, session store, cookie configuration, session timeout, or other session lifecycle settings.

## Alternatives Considered

1. **JWT-based authentication — rejected.** The project's `AGENTS.md` explicitly records server-side sessions as the selected authentication approach and states “not JWT.” JWT is therefore not the project's chosen approach. No further JWT-specific evaluation or claimed technical disadvantage is recorded in the supplied Phase 2 materials.
2. **Duplicated authentication/authorization checks inside each feature module — rejected.** `AGENTS.md` explicitly requires the Auth & Access Guard to run before every request reaches another module and says not to duplicate access checks inside individual modules. The selected design centralizes this cross-cutting responsibility.
3. **Server-side sessions with a cross-cutting Auth & Access Guard — selected.** This is the approach explicitly specified by `AGENTS.md` and the Phase 2 architecture component list (Auth Guard). It aligns with the PRD's authenticated-area and role/data-isolation requirements.

## Rationale

- It follows the team's recorded technology decision: server-side sessions, not JWT (`AGENTS.md`).
- A guard that runs before feature modules provides one consistent enforcement point for authentication and access control, as required by `AGENTS.md`.
- Central enforcement supports the PRD requirement to deny unauthorized access through both navigation and direct URL access (NFR-01 and AC-NFR-01).
- The approach preserves the distinction between Warden and Student permissions and student-owned records (FR-03, BR-08, BR-13).

## Consequences

### Positive

- Authentication and access enforcement have a single, cross-cutting responsibility.
- Feature modules do not need to duplicate the same access guard logic.
- The selected approach directly supports the PRD's role and record-visibility restrictions.

### Constraints / implications

- The guard must execute before protected feature-module handling.
- The public homepage must remain accessible without authentication.
- Student access must be limited to the student's own records; warden-only pages and records must be denied.
- A student marked **Left** cannot log in; reactivation restores access to the same retained record (FR-13, BR-09).
- Session lifecycle and configuration details are not settled by this ADR and must not be inferred from the choice of server-side sessions.

## Open Questions

The following details remain open in the Final PRD or are not specified in the Phase 2 architecture materials:

1. How is the first Warden account created, and how does the Warden change or recover their own password? (OQ-09)
2. Is there a lockout after repeated failed login attempts? (OQ-11)
3. What happens to a student's active session and pending items when the student is marked **Left**? (OQ-13)
4. What are the initial/temporary password delivery rules, the meaning of an unusable temporary password, and the password rules? (OQ-25)
5. What session expiration, inactivity timeout, logout, renewal, and invalidation rules apply? These details are not specified in the supplied decision records.
6. What session framework/store and cookie configuration will be used? No specific technology is selected in the supplied architecture materials.

## References

- `AGENTS.md` — “Auth & Access Guard runs before every request reaches another module”; “Server-side sessions for auth (not JWT)”.
- `architecture.md` — Phase 2 major component list includes Auth Guard.
- HostelEase Final PRD — FR-02, FR-03, FR-13; NFR-01; BR-08, BR-09, BR-13; AC-02.1–AC-02.4; AC-03.1–AC-03.2; AC-13.1–AC-13.3; AC-NFR-01; OQ-09, OQ-11, OQ-13, OQ-25.
- `ADR-001-architecture-style.md` — identifies the Auth Guard as a cross-cutting concern supported by the layered architecture.
