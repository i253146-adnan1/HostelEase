# VS-03 Room Service Contract

**Owner:** Muhammad Fahad Basharat  
**Feature:** Room Catalogue, Assignment and Capacity Enforcement  
**Status:** Proposed — pending team agreement

## 1. Module responsibility

The Rooms module owns room records, room assignments, occupancy calculations and room capacity enforcement.

It must not directly query or modify Student Management tables.

## 2. Proposed RoomService interface

- `list_rooms()` — Return the room catalogue and occupancy information.
- `get_room(room_id)` — Retrieve room details.
- `create_room(room_number, capacity)` — Create a room.
- `update_room(room_id, room_number, capacity)` — Update room details after capacity validation.
- `assign_student(student_id, room_id)` — Assign an existing student if capacity is available.
- `change_student_room(student_id, new_room_id)` — Change the student's room.
- `clear_student_room(student_id)` — Clear the current room assignment.
- `get_occupancy(room_id)` — Return current assigned-student count.
- `get_student_room(student_id)` — Return the student's current room.

## 3. Student Management integration

The Rooms module will use a Student Management service interface to validate student identity.

Proposed dependency:

`StudentService.exists(student_id)`

The exact method name and student identifier format must be agreed with the VS-02 owner.

The Rooms module will not create a duplicate Student model or use a direct foreign-key relationship to another module's private table.

## 4. Business rules

- A room cannot exceed its capacity.
- A full room rejects new assignments.
- Capacity cannot be reduced below current occupancy.
- A room with assigned students cannot be removed.
- Occupancy must reflect current room assignments.
- Assignment operations must preserve data consistency.

## 5. Integration

VS-02 may call `RoomService.assign_student(student_id, room_id)` during student registration.

The final method signatures and identifier format require agreement between VS-02 and VS-03 owners.

## 6. Approval

- VS-03 owner: Pending
- VS-02 owner: Pending
- Integration reviewer: Pending