from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from . import services
from .models import Room, RoomAssignment

User = get_user_model()


class RoomModuleTests(TestCase):
    def setUp(self):
        self.warden = User.objects.create_user(
            username='warden',
            password='password123',
            is_staff=True,
        )
        self.student1 = User.objects.create_user(
            username='student1',
            password='password123',
            is_staff=False,
        )
        self.student2 = User.objects.create_user(
            username='student2',
            password='password123',
            is_staff=False,
        )

    def test_ac_09_1_assign_to_room_with_free_capacity(self):
        self.client.force_login(self.warden)
        room = Room.objects.create(room_number='101', capacity=2)

        response = self.client.post(
            reverse('hostel:room_assign', args=[room.pk]),
            {'user_id': self.student1.pk},
        )

        self.assertRedirects(response, reverse('hostel:room_detail', args=[room.pk]))
        self.assertTrue(
            RoomAssignment.objects.filter(
                room=room,
                student_id=str(self.student1.pk),
                is_active=True,
            ).exists()
        )

    def test_ac_09_2_full_room_rejects_assignment(self):
        self.client.force_login(self.warden)
        room = Room.objects.create(room_number='102', capacity=1)
        services.assign_student_to_room(room.pk, self.student1.pk)

        with self.assertRaises(ValueError):
            services.assign_student_to_room(room.pk, self.student2.pk)

        response = self.client.post(
            reverse('hostel:room_assign', args=[room.pk]),
            {'user_id': self.student2.pk},
            follow=True,
        )

        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('full' in m.lower() for m in msgs))
        self.assertEqual(
            RoomAssignment.objects.filter(room=room, is_active=True).count(),
            1,
        )

    def test_ac_09_3_capacity_cannot_be_reduced_below_occupancy(self):
        self.client.force_login(self.warden)
        room = Room.objects.create(room_number='103', capacity=3)
        services.assign_student_to_room(room.pk, self.student1.pk)
        services.assign_student_to_room(room.pk, self.student2.pk)

        response = self.client.post(
            reverse('hostel:room_edit', args=[room.pk]),
            {'room_number': '103', 'capacity': 1},
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('capacity', form.errors)
        self.assertContains(response, '2 students assigned')

        room.refresh_from_db()
        self.assertEqual(room.capacity, 3)

        # BVA: reducing capacity to exact current occupancy (2) is allowed
        ok_resp = self.client.post(
            reverse('hostel:room_edit', args=[room.pk]),
            {'room_number': '103', 'capacity': 2},
        )
        self.assertRedirects(ok_resp, reverse('hostel:room_list'))
        room.refresh_from_db()
        self.assertEqual(room.capacity, 2)

    def test_ac_09_4_room_with_assigned_students_cannot_be_removed(self):
        self.client.force_login(self.warden)
        room = Room.objects.create(room_number='104', capacity=2)
        services.assign_student_to_room(room.pk, self.student1.pk)

        response = self.client.post(
            reverse('hostel:room_delete', args=[room.pk]),
            follow=True,
        )

        self.assertTrue(Room.objects.filter(pk=room.pk).exists())
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('cannot remove' in m.lower() for m in msgs))

    def test_room_create_valid(self):
        self.client.force_login(self.warden)
        response = self.client.post(
            reverse('hostel:room_create'),
            {'room_number': '201', 'capacity': 4},
        )

        self.assertRedirects(response, reverse('hostel:room_list'))
        self.assertTrue(Room.objects.filter(room_number='201', capacity=4).exists())

    def test_room_create_zero_capacity_rejected(self):
        self.client.force_login(self.warden)
        response = self.client.post(
            reverse('hostel:room_create'),
            {'room_number': '202', 'capacity': 0},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertFalse(Room.objects.filter(room_number='202').exists())

    def test_room_edit_valid_increase_capacity(self):
        self.client.force_login(self.warden)
        room = Room.objects.create(room_number='203', capacity=2)

        response = self.client.post(
            reverse('hostel:room_edit', args=[room.pk]),
            {'room_number': '203', 'capacity': 5},
        )

        self.assertRedirects(response, reverse('hostel:room_list'))
        room.refresh_from_db()
        self.assertEqual(room.capacity, 5)

    def test_clear_assignment_soft_deletes(self):
        self.client.force_login(self.warden)
        room = Room.objects.create(room_number='204', capacity=2)
        assignment = services.assign_student_to_room(room.pk, self.student1.pk)

        response = self.client.post(
            reverse('hostel:room_clear_assignment', args=[assignment.pk]),
        )

        self.assertRedirects(response, reverse('hostel:room_detail', args=[room.pk]))
        assignment.refresh_from_db()
        self.assertFalse(assignment.is_active)
        self.assertEqual(room.occupancy, 0)

    def test_non_staff_user_redirected_from_room_list(self):
        self.client.force_login(self.student1)
        response = self.client.get(reverse('hostel:room_list'))

        self.assertNotEqual(response.status_code, 200)
        self.assertRedirects(response, '/accounts/login/', fetch_redirect_response=False)

    def test_pending_request_count_placeholder(self):
        self.assertEqual(Room.get_pending_request_count(), 0)
        self.assertEqual(services.get_pending_request_count(), 0)
