from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from . import services
from .models import Room, RoomAssignment, RoomRequest, RoomSwapNotification, Student

User = get_user_model()


class RoomRequestVS11Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.warden = User.objects.create_user(
            username='warden_vs11',
            password='password123',
            role='warden',
            is_staff=True,
        )

        cls.user_a = User.objects.create_user(
            username='STU-101',
            password='password123',
            role='student',
            student_id='STU-101',
        )
        cls.student_a = Student.objects.create(
            student_id='STU-101',
            full_name='Alice Resident',
            contact_number='03001111111',
            guardian_name='Parent A',
            guardian_contact_number='03001111112',
            status=Student.STATUS_ACTIVE,
            user_id=cls.user_a.pk,
        )

        cls.user_b = User.objects.create_user(
            username='STU-102',
            password='password123',
            role='student',
            student_id='STU-102',
        )
        cls.student_b = Student.objects.create(
            student_id='STU-102',
            full_name='Bob Resident',
            contact_number='03002222221',
            guardian_name='Parent B',
            guardian_contact_number='03002222222',
            status=Student.STATUS_ACTIVE,
            user_id=cls.user_b.pk,
        )

        cls.user_c = User.objects.create_user(
            username='STU-103',
            password='password123',
            role='student',
            student_id='STU-103',
        )
        cls.student_c = Student.objects.create(
            student_id='STU-103',
            full_name='Charlie Left',
            contact_number='03003333331',
            guardian_name='Parent C',
            guardian_contact_number='03003333332',
            status=Student.STATUS_LEFT,
            user_id=cls.user_c.pk,
        )

        cls.room_1 = Room.objects.create(room_number='A-101', capacity=2)
        cls.room_2 = Room.objects.create(room_number='A-102', capacity=1)
        cls.room_3 = Room.objects.create(room_number='A-103', capacity=2)

        services.assign_student_to_room(cls.room_1.pk, cls.user_a.pk)
        services.assign_student_to_room(cls.room_2.pk, cls.user_b.pk)

    # --- 1. Change Requests & BR-07 / BR-08 ---

    def test_ac_10_1_submit_change_request_valid(self):
        req = services.submit_change_request('STU-101', self.room_3.pk, 'Need quieter room')
        self.assertEqual(req.student_id, 'STU-101')
        self.assertEqual(req.request_type, RoomRequest.TYPE_CHANGE)
        self.assertEqual(req.preferred_room, self.room_3)
        self.assertEqual(req.status, RoomRequest.STATUS_PENDING)

    def test_ac_10_2_ec_19_duplicate_open_request_rejected(self):
        services.submit_change_request('STU-101', self.room_3.pk, 'First request')
        with self.assertRaises(ValueError):
            services.submit_change_request('STU-101', self.room_3.pk, 'Second request')
        with self.assertRaises(ValueError):
            services.submit_swap_request('STU-101', 'STU-102', 'Swap attempt')

    def test_br_08_available_rooms_privacy(self):
        rooms = services.get_available_rooms()
        room_numbers = [r['room_number'] for r in rooms]
        self.assertIn('A-101', room_numbers)
        self.assertIn('A-103', room_numbers)
        self.assertNotIn('A-102', room_numbers)  # capacity 1, occupied by Bob

        for r in rooms:
            self.assertEqual(set(r.keys()), {'id', 'room_number', 'capacity', 'available_slots'})

        self.client.force_login(self.user_a)
        response = self.client.get(reverse('hostel:student_room_request_create'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Bob Resident')
        self.assertNotContains(response, 'STU-102')

    # --- 2. Swap Requests & Validations ---

    def test_submit_swap_request_valid_creates_consent_and_notification(self):
        req = services.submit_swap_request('STU-101', 'STU-102', 'Prefer ground floor')
        self.assertEqual(req.status, RoomRequest.STATUS_PENDING_STUDENT_CONSENT)
        self.assertEqual(req.target_student_id, 'STU-102')

        note = RoomSwapNotification.objects.get(room_request=req, recipient_student_id='STU-102')
        self.assertEqual(note.notification_type, RoomSwapNotification.TYPE_SWAP_INCOMING)
        self.assertFalse(note.is_read)

    def test_submit_swap_request_rejections(self):
        # Self-swap
        with self.assertRaises(ValueError):
            services.submit_swap_request('STU-101', 'STU-101', 'Self')

        # Non-existent target (AC-10.4 / EC-20)
        with self.assertRaises(ValueError):
            services.submit_swap_request('STU-101', 'STU-999', 'Unknown')
        self.assertEqual(RoomRequest.objects.count(), 0)

        # Inactive / Left target
        with self.assertRaises(ValueError):
            services.submit_swap_request('STU-101', 'STU-103', 'Left student')

        # Active target without active room assignment
        user_d = User.objects.create_user(
            username='STU-104', password='password123', role='student', student_id='STU-104'
        )
        Student.objects.create(
            student_id='STU-104',
            full_name='Dan Unassigned',
            contact_number='03004444441',
            guardian_name='Parent D',
            guardian_contact_number='03004444442',
            status=Student.STATUS_ACTIVE,
            user_id=user_d.pk,
        )
        with self.assertRaises(ValueError):
            services.submit_swap_request('STU-101', 'STU-104', 'No room')

        # Same room
        services.assign_student_to_room(self.room_1.pk, user_d.pk)
        with self.assertRaises(ValueError):
            services.submit_swap_request('STU-101', 'STU-104', 'Same room')

    # --- 3. Two-Step Consent Flow (OQ-04) ---

    def test_respond_to_swap_permission_and_transitions(self):
        req = services.submit_swap_request('STU-101', 'STU-102', 'Swap please')

        # Non-target cannot respond
        with self.assertRaises(PermissionError):
            services.respond_to_swap(req.pk, 'STU-101', accept=True)

        # Target rejects -> REJECTED_BY_STUDENT, hidden from warden queue
        req = services.respond_to_swap(req.pk, 'STU-102', accept=False)
        self.assertEqual(req.status, RoomRequest.STATUS_REJECTED_BY_STUDENT)
        self.assertIsNotNone(req.decided_by_student_at)
        self.assertTrue(
            RoomSwapNotification.objects.filter(
                recipient_student_id='STU-101',
                room_request=req,
                notification_type=RoomSwapNotification.TYPE_SWAP_REJECTED_BY_TARGET,
            ).exists()
        )
        self.assertEqual(services.get_pending_request_count(), 0)

        # New swap accepted -> PENDING_WARDEN_APPROVAL
        req2 = services.submit_swap_request('STU-101', 'STU-102', 'Try again')
        req2 = services.respond_to_swap(req2.pk, 'STU-102', accept=True)
        self.assertEqual(req2.status, RoomRequest.STATUS_PENDING_WARDEN_APPROVAL)
        self.assertTrue(
            RoomSwapNotification.objects.filter(
                recipient_student_id='STU-101',
                room_request=req2,
                notification_type=RoomSwapNotification.TYPE_SWAP_ACCEPTED_BY_TARGET,
            ).exists()
        )
        self.assertEqual(services.get_pending_request_count(), 1)

    # --- 4. Cancellation (AC-10.3 / BR-05) ---

    def test_ac_10_3_cancel_request_across_open_states_retains_record(self):
        # Cancel CHANGE in PENDING
        r1 = services.submit_change_request('STU-101', self.room_3.pk, 'Reason 1')
        with self.assertRaises(PermissionError):
            services.cancel_request(r1.pk, 'STU-102')
        r1 = services.cancel_request(r1.pk, 'STU-101')
        self.assertEqual(r1.status, RoomRequest.STATUS_CANCELLED)
        self.assertTrue(RoomRequest.objects.filter(pk=r1.pk).exists())

        # Cancel SWAP in PENDING_STUDENT_CONSENT
        r2 = services.submit_swap_request('STU-101', 'STU-102', 'Reason 2')
        r2 = services.cancel_request(r2.pk, 'STU-101')
        self.assertEqual(r2.status, RoomRequest.STATUS_CANCELLED)

        # Cancel SWAP in PENDING_WARDEN_APPROVAL
        r3 = services.submit_swap_request('STU-101', 'STU-102', 'Reason 3')
        services.respond_to_swap(r3.pk, 'STU-102', accept=True)
        r3 = services.cancel_request(r3.pk, 'STU-101')
        self.assertEqual(r3.status, RoomRequest.STATUS_CANCELLED)

    # --- 5. Warden Decisions & Edge Cases (EC-41, EC-43, EC-44) ---

    def test_ec_41_change_approval_blocked_when_room_full(self):
        # room_3 has capacity 2, currently 0
        req = services.submit_change_request('STU-101', self.room_3.pk, 'Move to A-103')

        # Fill room_3 before warden approves
        u1 = User.objects.create_user(username='fill1', password='p', role='student')
        u2 = User.objects.create_user(username='fill2', password='p', role='student')
        services.assign_student_to_room(self.room_3.pk, u1.pk)
        services.assign_student_to_room(self.room_3.pk, u2.pk)

        with self.assertRaises(ValueError):
            services.decide_change_request(req.pk, approve=True)

        req.refresh_from_db()
        self.assertEqual(req.status, RoomRequest.STATUS_PENDING)
        active_a = RoomAssignment.objects.get(student_id=str(self.user_a.pk), is_active=True)
        self.assertEqual(active_a.room, self.room_1)

    def test_ec_43_swap_approval_blocked_if_assignment_missing(self):
        req = services.submit_swap_request('STU-101', 'STU-102', 'Swap')
        services.respond_to_swap(req.pk, 'STU-102', accept=True)

        # Clear STU-102's assignment before warden approves
        services.clear_student_room_assignment(self.user_b.pk)

        with self.assertRaises(ValueError):
            services.decide_swap(req.pk, approve=True)

        req.refresh_from_db()
        self.assertEqual(req.status, RoomRequest.STATUS_PENDING_WARDEN_APPROVAL)
        self.assertTrue(
            RoomAssignment.objects.filter(student_id=str(self.user_a.pk), room=self.room_1, is_active=True).exists()
        )

    def test_ec_44_approval_blocked_after_cancellation(self):
        req_c = services.submit_change_request('STU-101', self.room_3.pk, 'Move')
        services.cancel_request(req_c.pk, 'STU-101')
        with self.assertRaises(ValueError):
            services.decide_change_request(req_c.pk, approve=True)

        req_s = services.submit_swap_request('STU-101', 'STU-102', 'Swap')
        services.respond_to_swap(req_s.pk, 'STU-102', accept=True)
        services.cancel_request(req_s.pk, 'STU-101')
        with self.assertRaises(ValueError):
            services.decide_swap(req_s.pk, approve=True)

    def test_decide_swap_approve_atomic_and_notifies_both(self):
        req = services.submit_swap_request('STU-101', 'STU-102', 'Swap rooms')
        services.respond_to_swap(req.pk, 'STU-102', accept=True)

        req = services.decide_swap(req.pk, approve=True, remark='Approved by warden')
        self.assertEqual(req.status, RoomRequest.STATUS_APPROVED)
        self.assertEqual(req.warden_remark, 'Approved by warden')
        self.assertIsNotNone(req.decided_by_warden_at)

        # Alice is now in room_2, Bob is now in room_1
        assign_a = RoomAssignment.objects.get(student_id=str(self.user_a.pk), is_active=True)
        assign_b = RoomAssignment.objects.get(student_id=str(self.user_b.pk), is_active=True)
        self.assertEqual(assign_a.room, self.room_2)
        self.assertEqual(assign_b.room, self.room_1)

        # Capacities preserved
        self.assertEqual(self.room_1.occupancy, 1)
        self.assertEqual(self.room_2.occupancy, 1)

        # Notifications sent to both
        self.assertTrue(
            RoomSwapNotification.objects.filter(
                recipient_student_id='STU-101',
                room_request=req,
                notification_type=RoomSwapNotification.TYPE_SWAP_APPROVED,
            ).exists()
        )
        self.assertTrue(
            RoomSwapNotification.objects.filter(
                recipient_student_id='STU-102',
                room_request=req,
                notification_type=RoomSwapNotification.TYPE_SWAP_APPROVED,
            ).exists()
        )

    # --- 6. Dashboard Count (ADR-005) ---

    def test_adr_005_get_pending_request_count(self):
        # 1 CHANGE (PENDING) -> counted
        services.submit_change_request('STU-101', self.room_3.pk, 'Change 1')
        self.assertEqual(services.get_pending_request_count(), 1)

        # 1 SWAP (PENDING_STUDENT_CONSENT) -> NOT counted
        swap_req = services.submit_swap_request('STU-102', 'STU-101', 'Swap 1')
        self.assertEqual(services.get_pending_request_count(), 1)

        # Target accepts -> PENDING_WARDEN_APPROVAL -> counted (total 2)
        services.respond_to_swap(swap_req.pk, 'STU-101', accept=True)
        self.assertEqual(services.get_pending_request_count(), 2)

    # --- 7. View Ownership & Auth Isolation (NFR-01 / BR-08) ---

    def test_view_ownership_and_auth_isolation(self):
        req_b = services.submit_change_request('STU-102', self.room_3.pk, 'Bob change')

        # Anonymous redirected to login
        resp = self.client.get(reverse('hostel:student_room_requests'))
        self.assertEqual(resp.status_code, 302)

        # Student A cannot see Student B's request or cancel it
        self.client.force_login(self.user_a)
        resp = self.client.get(reverse('hostel:student_room_requests'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'Bob change')

        resp_cancel = self.client.post(reverse('hostel:student_room_request_cancel', args=[req_b.pk]))
        self.assertEqual(resp_cancel.status_code, 403)

        # Student A cannot access warden queue
        resp_warden = self.client.get(reverse('hostel:warden_room_requests'))
        self.assertEqual(resp_warden.status_code, 403)

        # Student B views swap inbox -> unread notifications marked read
        swap_req = services.submit_swap_request('STU-101', 'STU-102', 'Swap with Bob')
        self.client.force_login(self.user_b)
        self.assertEqual(
            RoomSwapNotification.objects.filter(recipient_student_id='STU-102', is_read=False).count(),
            1,
        )
        inbox_resp = self.client.get(reverse('hostel:student_swap_inbox'))
        self.assertEqual(inbox_resp.status_code, 200)
        self.assertContains(inbox_resp, 'Swap with Bob')
        self.assertEqual(
            RoomSwapNotification.objects.filter(recipient_student_id='STU-102', is_read=False).count(),
            0,
        )

        # Student A cannot respond to a swap targeting Student B
        self.client.force_login(self.user_a)
        resp_respond = self.client.post(
            reverse('hostel:student_swap_respond', args=[swap_req.pk]),
            {'decision': 'accept'},
        )
        self.assertEqual(resp_respond.status_code, 403)

        # Warden queue shows req_b (PENDING) and hides swap_req (PENDING_STUDENT_CONSENT)
        self.client.force_login(self.warden)
        warden_resp = self.client.get(reverse('hostel:warden_room_requests'))
        self.assertEqual(warden_resp.status_code, 200)
        self.assertContains(warden_resp, 'Bob change')
        self.assertNotContains(warden_resp, 'Swap with Bob')
