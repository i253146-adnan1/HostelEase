from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from hostel.models import Room, RoomAssignment, Student
from operations import leave_service
from operations.leave_service import LeaveService
from operations.models import LeaveRequest

User = get_user_model()


class LeaveRequestVS15Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.warden = User.objects.create_user(
            username='warden_vs15',
            password='password123',
            role='warden',
            is_staff=True,
        )

        cls.user_a = User.objects.create_user(
            username='STU-201',
            password='password123',
            role='student',
            student_id='STU-201',
        )
        cls.student_a = Student.objects.create(
            student_id='STU-201',
            full_name='Amina Leave',
            contact_number='03003333331',
            guardian_name='Guardian A',
            guardian_contact_number='03003333332',
            status=Student.STATUS_ACTIVE,
            user_id=cls.user_a.pk,
        )

        cls.user_b = User.objects.create_user(
            username='STU-202',
            password='password123',
            role='student',
            student_id='STU-202',
        )
        cls.student_b = Student.objects.create(
            student_id='STU-202',
            full_name='Bilal Leave',
            contact_number='03004444441',
            guardian_name='Guardian B',
            guardian_contact_number='03004444442',
            status=Student.STATUS_ACTIVE,
            user_id=cls.user_b.pk,
        )

        cls.user_left = User.objects.create_user(
            username='STU-203',
            password='password123',
            role='student',
            student_id='STU-203',
        )
        cls.student_left = Student.objects.create(
            student_id='STU-203',
            full_name='Left Student',
            contact_number='03005555551',
            guardian_name='Guardian L',
            guardian_contact_number='03005555552',
            status=Student.STATUS_LEFT,
            user_id=cls.user_left.pk,
        )

        cls.room = Room.objects.create(room_number='L-101', capacity=2)
        cls.assignment_a = RoomAssignment.objects.create(
            room=cls.room,
            student_id=cls.student_a.student_id,
            is_active=True,
        )

        cls.dep = date(2026, 12, 1)
        cls.ret = date(2026, 12, 5)

    def _snapshot_student_a(self):
        student = Student.objects.get(pk=self.student_a.pk)
        user = User.objects.get(pk=self.user_a.pk)
        assignments = list(
            RoomAssignment.objects.filter(student_id=student.student_id)
            .order_by('id')
            .values_list('id', 'room_id', 'is_active')
        )
        return {
            'student_status': student.status,
            'assignments': assignments,
            'user_is_active': user.is_active,
            'user_role': user.role,
            'must_change_password': user.must_change_password,
        }

    def test_ac_17_1_valid_submission_saves_as_pending(self):
        req = leave_service.submit_leave_request(
            self.student_a.student_id,
            self.dep,
            self.ret,
            'Family wedding in Lahore',
        )
        self.assertEqual(req.student_id, 'STU-201')
        self.assertEqual(req.departure_date, self.dep)
        self.assertEqual(req.return_date, self.ret)
        self.assertEqual(req.status, LeaveRequest.STATUS_PENDING)
        self.assertIsNone(req.decided_by_warden_at)
        self.assertEqual(LeaveRequest.objects.count(), 1)

    def test_ac_17_2_ec_47_invalid_dates_rejected_nothing_saved(self):
        with self.assertRaises(ValueError):
            leave_service.submit_leave_request(
                self.student_a.student_id,
                self.dep,
                self.dep,
                'Same day return',
            )
        with self.assertRaises(ValueError):
            leave_service.submit_leave_request(
                self.student_a.student_id,
                self.dep,
                self.dep - timedelta(days=1),
                'Return before departure',
            )
        self.assertEqual(LeaveRequest.objects.count(), 0)

    def test_ac_17_3_ec_48_one_open_request_per_student_and_rejected_allows_resubmit(self):
        first = leave_service.submit_leave_request(
            self.student_a.student_id, self.dep, self.ret, 'First leave'
        )
        # Cannot submit while PENDING
        with self.assertRaises(ValueError):
            leave_service.submit_leave_request(
                self.student_a.student_id,
                self.dep + timedelta(days=10),
                self.ret + timedelta(days=10),
                'Second leave while pending',
            )

        # Approve first -> still open (APPROVED), cannot submit another
        leave_service.decide_leave_request(first.pk, 'APPROVE')
        with self.assertRaises(ValueError):
            leave_service.submit_leave_request(
                self.student_a.student_id,
                self.dep + timedelta(days=10),
                self.ret + timedelta(days=10),
                'Second leave while approved',
            )

        # Student B has a REJECTED request -> CAN submit again
        rejected_req = leave_service.submit_leave_request(
            self.student_b.student_id, self.dep, self.ret, 'Will be rejected'
        )
        leave_service.decide_leave_request(rejected_req.pk, 'REJECT', remark='Exams scheduled')
        resubmitted = leave_service.submit_leave_request(
            self.student_b.student_id,
            self.dep + timedelta(days=15),
            self.ret + timedelta(days=15),
            'After exams',
        )
        self.assertEqual(resubmitted.status, LeaveRequest.STATUS_PENDING)

    def test_ac_17_4_br_12_warden_approve_and_reject_preserve_student_room_and_login(self):
        self.client.force_login(self.user_a)
        before_approve = self._snapshot_student_a()

        req1 = leave_service.submit_leave_request(
            self.student_a.student_id, self.dep, self.ret, 'Medical checkup'
        )
        decided1 = leave_service.decide_leave_request(req1.pk, 'APPROVE', remark='Safe travels')
        self.assertEqual(decided1.status, LeaveRequest.STATUS_APPROVED)
        self.assertEqual(decided1.warden_remark, 'Safe travels')
        self.assertIsNotNone(decided1.decided_by_warden_at)

        after_approve = self._snapshot_student_a()
        self.assertEqual(after_approve, before_approve)
        # Verify student_a can still log in and access student leave requests
        resp_a = self.client.get(reverse('operations:student_leave_requests'))
        self.assertEqual(resp_a.status_code, 200)
        self.assertTrue(self.client.login(username='STU-201', password='password123'))

        # Test approve without remark and reject with/without remark on a second request
        req2 = leave_service.submit_leave_request(
            self.student_b.student_id, self.dep, self.ret, 'Short trip'
        )
        decided2 = leave_service.decide_leave_request(req2.pk, 'APPROVE')
        self.assertEqual(decided2.status, LeaveRequest.STATUS_APPROVED)
        self.assertIsNone(decided2.warden_remark)

        req3 = LeaveRequest.objects.create(
            student_id=self.student_a.student_id,
            departure_date=self.dep + timedelta(days=20),
            return_date=self.ret + timedelta(days=20),
            reason='Another trip',
            status=LeaveRequest.STATUS_PENDING,
        )
        # Reject without remark fails
        with self.assertRaises(ValueError):
            leave_service.decide_leave_request(req3.pk, 'REJECT', remark='   ')
        req3.refresh_from_db()
        self.assertEqual(req3.status, LeaveRequest.STATUS_PENDING)

        before_reject = self._snapshot_student_a()
        decided3 = leave_service.decide_leave_request(req3.pk, 'REJECT', remark='Mandatory lab week')
        self.assertEqual(decided3.status, LeaveRequest.STATUS_REJECTED)
        self.assertEqual(decided3.warden_remark, 'Mandatory lab week')
        self.assertIsNotNone(decided3.decided_by_warden_at)
        self.assertEqual(self._snapshot_student_a(), before_reject)

    def test_only_pending_can_be_decided(self):
        req = leave_service.submit_leave_request(
            self.student_a.student_id, self.dep, self.ret, 'Trip'
        )
        leave_service.decide_leave_request(req.pk, 'APPROVE', remark='OK')

        with self.assertRaises(ValueError):
            leave_service.decide_leave_request(req.pk, 'REJECT', remark='Changed mind')

        req_b = leave_service.submit_leave_request(
            self.student_b.student_id, self.dep, self.ret, 'Trip B'
        )
        leave_service.decide_leave_request(req_b.pk, 'REJECT', remark='No')
        with self.assertRaises(ValueError):
            leave_service.decide_leave_request(req_b.pk, 'APPROVE')

    def test_adr_005_get_pending_count_counts_only_pending(self):
        self.assertEqual(leave_service.get_pending_count(), 0)
        self.assertEqual(LeaveService.get_pending_count(), 0)

        r1 = leave_service.submit_leave_request(self.student_a.student_id, self.dep, self.ret, 'R1')
        r2 = leave_service.submit_leave_request(self.student_b.student_id, self.dep, self.ret, 'R2')
        self.assertEqual(leave_service.get_pending_count(), 2)

        leave_service.decide_leave_request(r1.pk, 'APPROVE')
        self.assertEqual(leave_service.get_pending_count(), 1)

        leave_service.decide_leave_request(r2.pk, 'REJECT', remark='Denied')
        self.assertEqual(leave_service.get_pending_count(), 0)
        self.assertEqual(LeaveService.get_pending_count(), 0)

    def test_ownership_and_auth_isolation(self):
        req_b = leave_service.submit_leave_request(
            self.student_b.student_id, self.dep, self.ret, 'Secret Bilal Leave'
        )

        # Anonymous redirected
        anon_resp = self.client.get(reverse('operations:student_leave_requests'))
        self.assertEqual(anon_resp.status_code, 302)

        # Student A cannot see Student B's request
        self.client.force_login(self.user_a)
        list_resp = self.client.get(reverse('operations:student_leave_requests'))
        self.assertEqual(list_resp.status_code, 200)
        self.assertNotContains(list_resp, 'Secret Bilal Leave')

        # Student A cannot submit on behalf of Student B (spoofed student_id ignored)
        create_resp = self.client.post(
            reverse('operations:student_leave_request_create'),
            {
                'student_id': 'STU-202',
                'departure_date': '2026-12-10',
                'return_date': '2026-12-12',
                'reason': 'Amina own leave',
            },
        )
        self.assertEqual(create_resp.status_code, 302)
        created = LeaveRequest.objects.get(reason='Amina own leave')
        self.assertEqual(created.student_id, 'STU-201')

        # Student A cannot access warden queue or decide endpoint
        self.assertEqual(self.client.get(reverse('operations:warden_leave_requests')).status_code, 403)
        self.assertEqual(
            self.client.post(
                reverse('operations:warden_decide_leave_request', args=[req_b.pk]),
                {'action': 'approve'},
            ).status_code,
            403,
        )
        req_b.refresh_from_db()
        self.assertEqual(req_b.status, LeaveRequest.STATUS_PENDING)

    def test_inactive_student_rejected_and_br_05_no_hard_delete(self):
        with self.assertRaises(ValueError):
            leave_service.submit_leave_request(
                self.student_left.student_id, self.dep, self.ret, 'Left student'
            )

        req = leave_service.submit_leave_request(
            self.student_a.student_id, self.dep, self.ret, 'Retained record'
        )
        with self.assertRaises(PermissionError):
            req.delete()
        self.assertTrue(LeaveRequest.objects.filter(pk=req.pk).exists())
