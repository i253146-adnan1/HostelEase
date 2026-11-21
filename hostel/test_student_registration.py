from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from finance import services as finance_services
from finance.models import FeeChange, FeeRecord, Payment
from . import room_service, student_service
from .models import Room, RoomAssignment, Student
from .room_service import RoomError, RoomFullError, RoomNotFoundError
from .student_service import (
    DuplicateStudentError,
    StudentError,
    StudentValidationError,
)

User = get_user_model()
D = Decimal


class StudentRegistrationServiceTests(TestCase):
    """Test student_service.register_student and core business rules (VS-02)."""

    def setUp(self):
        self.warden = User.objects.create_user(
            username='warden1',
            password='WardenPassword123',
            role='warden',
            is_staff=True,
        )
        self.room1 = room_service.create_room('101', capacity=2)
        self.room_single = room_service.create_room('102', capacity=1)

    def test_ac_01_1_successful_registration(self):
        """Valid registration creates student, user, fee record, and room assignment."""
        result = student_service.register_student(
            full_name='Ali Khan',
            student_id='STU-001',
            contact_number='03001234567',
            guardian_name='Akbar Khan',
            guardian_contact_number='03007654321',
            room_identifier=self.room1.id,
            total_fee='20000.00',
            opening_paid='0',
            email='ali@example.com',
            address='House 1, Street 2, Islamabad',
            created_by='warden1',
        )

        # 1. Student record created
        student = result['student']
        self.assertEqual(student.student_id, 'STU-001')
        self.assertEqual(student.full_name, 'Ali Khan')
        self.assertEqual(student.status, Student.STATUS_ACTIVE)
        self.assertTrue(student_service.exists('STU-001'))

        # 2. User account created
        user = result['user']
        self.assertEqual(user.username, 'STU-001')
        self.assertEqual(user.role, 'student')
        self.assertTrue(user.must_change_password)
        self.assertFalse(user.password.startswith('plain'))
        # Password check
        temp_pwd = result['temporary_password']
        self.assertTrue(user.check_password(temp_pwd))

        # 3. Room assignment created and occupancy updated
        assignment = result['room_assignment']
        self.assertEqual(assignment.room, self.room1)
        self.assertEqual(assignment.student_id, 'STU-001')
        self.assertTrue(assignment.is_active)
        self.assertEqual(room_service.get_occupancy(self.room1.id), 1)

        # 4. Fee record created with paid=0, remaining=total_fee
        ledger = result['ledger']
        self.assertEqual(ledger['total_fee'], D('20000.00'))
        self.assertEqual(ledger['paid_amount'], D('0.00'))
        self.assertEqual(ledger['remaining_amount'], D('20000.00'))
        self.assertEqual(ledger['excess_paid'], D('0.00'))

        fee_rec = FeeRecord.objects.get(student_ref=student.id)
        self.assertEqual(fee_rec.total_fee, D('20000.00'))
        self.assertEqual(FeeChange.objects.filter(fee_record=fee_rec).count(), 1)

    def test_ac_01_2_duplicate_student_id_rejected(self):
        """EC-01: Duplicate student ID must be rejected, creating no new record."""
        student_service.register_student(
            full_name='Ali Khan',
            student_id='STU-DUP',
            contact_number='03001234567',
            guardian_name='Akbar Khan',
            guardian_contact_number='03007654321',
            room_identifier=self.room1.id,
            total_fee='15000.00',
        )

        initial_student_count = Student.objects.count()
        initial_user_count = User.objects.count()

        with self.assertRaises(DuplicateStudentError):
            student_service.register_student(
                full_name='Second Person',
                student_id='STU-DUP',
                contact_number='03111234567',
                guardian_name='Other Guardian',
                guardian_contact_number='03117654321',
                room_identifier=self.room1.id,
                total_fee='15000.00',
            )

        self.assertEqual(Student.objects.count(), initial_student_count)
        self.assertEqual(User.objects.count(), initial_user_count)

    def test_ac_01_3_missing_mandatory_fields_rejected(self):
        """EC-02: Missing any mandatory field raises StudentValidationError."""
        valid_kwargs = {
            'full_name': 'Ali Khan',
            'student_id': 'STU-MISSING',
            'contact_number': '03001234567',
            'guardian_name': 'Akbar Khan',
            'guardian_contact_number': '03007654321',
            'room_identifier': self.room1.id,
            'total_fee': '15000.00',
        }

        mandatory_fields = [
            'full_name',
            'student_id',
            'contact_number',
            'guardian_name',
            'guardian_contact_number',
            'room_identifier',
            'total_fee',
        ]

        for field in mandatory_fields:
            kwargs = valid_kwargs.copy()
            kwargs[field] = ''
            with self.subTest(missing_field=field):
                with self.assertRaises((StudentValidationError, StudentError)):
                    student_service.register_student(**kwargs)

    def test_ac_01_3_invalid_contact_numbers_rejected(self):
        """EC-03: Invalid contact numbers must be rejected."""
        base_kwargs = {
            'full_name': 'Ali Khan',
            'student_id': 'STU-PHONE',
            'contact_number': '03001234567',
            'guardian_name': 'Akbar Khan',
            'guardian_contact_number': '03007654321',
            'room_identifier': self.room1.id,
            'total_fee': '15000.00',
        }

        invalid_phones = ['abc1234567', '12345', 'not-a-number', '++92300000000000000000']
        for bad_phone in invalid_phones:
            # Bad student phone
            kw = base_kwargs.copy()
            kw['contact_number'] = bad_phone
            with self.subTest(bad_student_phone=bad_phone):
                with self.assertRaises(StudentValidationError):
                    student_service.register_student(**kw)

            # Bad guardian phone
            kw = base_kwargs.copy()
            kw['guardian_contact_number'] = bad_phone
            with self.subTest(bad_guardian_phone=bad_phone):
                with self.assertRaises(StudentValidationError):
                    student_service.register_student(**kw)

    def test_ac_01_4_and_oq_21_full_room_registration_transaction_rolls_back(self):
        """EC-04, OQ-21: Chosen room full rejects registration and rolls back transaction."""
        # Fill room 102 (capacity 1)
        student_service.register_student(
            full_name='First Student',
            student_id='STU-IN-ROOM',
            contact_number='03001111111',
            guardian_name='Guardian One',
            guardian_contact_number='03002222222',
            room_identifier=self.room_single.id,
            total_fee='10000.00',
        )
        self.assertEqual(room_service.get_occupancy(self.room_single.id), 1)

        # Attempt to register second student into room 102
        initial_students = Student.objects.count()
        initial_users = User.objects.count()
        initial_assignments = RoomAssignment.objects.count()
        initial_fees = FeeRecord.objects.count()

        with self.assertRaises(StudentValidationError) as ctx:
            student_service.register_student(
                full_name='Second Student',
                student_id='STU-REJECTED',
                contact_number='03003333333',
                guardian_name='Guardian Two',
                guardian_contact_number='03004444444',
                room_identifier=self.room_single.id,
                total_fee='10000.00',
            )

        self.assertIn('full', str(ctx.exception).lower())

        # Assert complete rollback: no partial records created (OQ-21, EC-30)
        self.assertEqual(Student.objects.count(), initial_students)
        self.assertEqual(User.objects.count(), initial_users)
        self.assertEqual(RoomAssignment.objects.count(), initial_assignments)
        self.assertEqual(FeeRecord.objects.count(), initial_fees)
        self.assertFalse(Student.objects.filter(student_id='STU-REJECTED').exists())
        self.assertFalse(User.objects.filter(username='STU-REJECTED').exists())

    def test_ec_31_invalid_fee_rolls_back_transaction(self):
        """EC-31, OQ-21: Invalid total fee rolls back entire registration."""
        initial_students = Student.objects.count()
        initial_users = User.objects.count()
        initial_assignments = RoomAssignment.objects.count()

        invalid_fees = ['-100', 'not_money', '10.555', 'NaN']
        for bad_fee in invalid_fees:
            with self.subTest(bad_fee=bad_fee):
                with self.assertRaises(StudentValidationError):
                    student_service.register_student(
                        full_name='Bad Fee Student',
                        student_id=f'STU-FEE-{bad_fee}',
                        contact_number='03005555555',
                        guardian_name='Guardian',
                        guardian_contact_number='03006666666',
                        room_identifier=self.room1.id,
                        total_fee=bad_fee,
                    )

        # No records created
        self.assertEqual(Student.objects.count(), initial_students)
        self.assertEqual(User.objects.count(), initial_users)
        self.assertEqual(RoomAssignment.objects.count(), initial_assignments)

    def test_oq_26_opening_balance_recorded(self):
        """OQ-26: Initial fee and opening verified paid amount recorded correctly."""
        result = student_service.register_student(
            full_name='Student With Advance',
            student_id='STU-OPENING',
            contact_number='03008888888',
            guardian_name='Guardian Advance',
            guardian_contact_number='03009999999',
            room_identifier=self.room1.id,
            total_fee='30000.00',
            opening_paid='5000.00',
        )

        ledger = result['ledger']
        self.assertEqual(ledger['total_fee'], D('30000.00'))
        self.assertEqual(ledger['paid_amount'], D('5000.00'))
        self.assertEqual(ledger['remaining_amount'], D('25000.00'))

        student = result['student']
        payment = Payment.objects.filter(student_ref=student.id).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, Payment.STATUS_VERIFIED)
        self.assertEqual(payment.amount, D('5000.00'))
        self.assertEqual(payment.source, Payment.SOURCE_OPENING)

    def test_room_service_capacity_reduction_protection(self):
        """Room capacity cannot be reduced below current occupancy (BR-06, AC-09.3)."""
        student_service.register_student(
            full_name='Student In Room',
            student_id='STU-CAP-CHECK',
            contact_number='03001234567',
            guardian_name='Guardian',
            guardian_contact_number='03007654321',
            room_identifier=self.room1.id,
            total_fee='10000.00',
        )
        self.assertEqual(room_service.get_occupancy(self.room1.id), 1)

        # Capacity is 2, current occupancy is 1. Reducing to 1 is OK; reducing to 0 raises RoomError
        room_service.update_room(self.room1.id, capacity=1)
        with self.assertRaises(RoomError):
            room_service.update_room(self.room1.id, capacity=0)


class StudentRegistrationViewTests(TestCase):
    """Test HTTP views, access control, and UI integration for VS-02."""

    def setUp(self):
        self.warden = User.objects.create_user(
            username='warden_view',
            password='WardenPassword123',
            role='warden',
            is_staff=True,
        )
        self.student = User.objects.create_user(
            username='student_view',
            password='StudentPassword123',
            role='student',
        )
        self.room = room_service.create_room('201', capacity=2)

    def test_nfr_01_anonymous_user_redirected_to_login(self):
        """Anonymous access to warden student registration is redirected to login."""
        urls = [
            reverse('hostel:warden_student_list'),
            reverse('hostel:warden_student_create'),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/accounts/login/', response.url)

    def test_nfr_01_student_denied_access_to_warden_registration(self):
        """Student role receives 403 Forbidden on warden student registration routes."""
        self.client.force_login(self.student)
        urls = [
            reverse('hostel:warden_student_list'),
            reverse('hostel:warden_student_create'),
        ]
        for url in urls:
            get_resp = self.client.get(url)
            self.assertEqual(get_resp.status_code, 403)

            post_resp = self.client.post(url, {})
            self.assertEqual(post_resp.status_code, 403)

    def test_warden_can_view_registration_form(self):
        """Warden can open the registration form and see available rooms."""
        self.client.force_login(self.warden)
        response = self.client.get(reverse('hostel:warden_student_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Register New Student')
        self.assertContains(response, 'Room 201')

    def test_warden_submits_valid_registration_via_post(self):
        """Warden submits form and sees the credentials handover screen."""
        self.client.force_login(self.warden)
        payload = {
            'student_id': 'STU-WEB-001',
            'full_name': 'Bilal Ahmed',
            'contact_number': '03001239876',
            'guardian_name': 'Ahmed Raza',
            'guardian_contact_number': '03007654321',
            'room': str(self.room.id),
            'total_fee': '22000.00',
            'opening_paid': '2000.00',
            'email': 'bilal@example.com',
            'address': 'Lahore, Pakistan',
        }
        response = self.client.post(reverse('hostel:warden_student_create'), payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Student Registered Successfully')
        self.assertContains(response, 'STU-WEB-001')
        self.assertContains(response, 'Bilal Ahmed')
        self.assertContains(response, 'One-Time Student Credentials')

        # Check that user can log in and is forced to change password (AC-02.4, OQ-25)
        created_user = User.objects.get(username='STU-WEB-001')
        self.assertTrue(created_user.must_change_password)

    def test_warden_submits_full_room_shows_error_message(self):
        """Submitting a full room renders error message on form without crashing."""
        self.client.force_login(self.warden)
        full_room = room_service.create_room('999', capacity=1)
        student_service.register_student(
            full_name='Resident A',
            student_id='STU-999-A',
            contact_number='03001112222',
            guardian_name='Guardian A',
            guardian_contact_number='03003334444',
            room_identifier=full_room.id,
            total_fee='10000.00',
        )

        payload = {
            'student_id': 'STU-999-B',
            'full_name': 'Resident B',
            'contact_number': '03005556666',
            'guardian_name': 'Guardian B',
            'guardian_contact_number': '03007778888',
            'room': str(full_room.id),
            'total_fee': '10000.00',
        }
        response = self.client.post(reverse('hostel:warden_student_create'), payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'full')
        self.assertFalse(Student.objects.filter(student_id='STU-999-B').exists())

    def test_warden_student_list_and_detail_views(self):
        """Warden can view student list and student detail."""
        self.client.force_login(self.warden)
        res = student_service.register_student(
            full_name='Tariq Aziz',
            student_id='STU-LIST-01',
            contact_number='03001113333',
            guardian_name='Aziz Khan',
            guardian_contact_number='03004445555',
            room_identifier=self.room.id,
            total_fee='18000.00',
        )
        student = res['student']

        # List view
        list_resp = self.client.get(reverse('hostel:warden_student_list'))
        self.assertEqual(list_resp.status_code, 200)
        self.assertContains(list_resp, 'STU-LIST-01')
        self.assertContains(list_resp, 'Tariq Aziz')
        self.assertContains(list_resp, 'Room 201')

        # Detail view
        detail_resp = self.client.get(reverse('hostel:warden_student_detail', args=[student.pk]))
        self.assertEqual(detail_resp.status_code, 200)
        self.assertContains(detail_resp, 'Tariq Aziz')
        self.assertContains(detail_resp, 'Room 201')
        self.assertContains(detail_resp, 'Fee Ledger Overview')
        self.assertContains(detail_resp, 'Fee Change History')
