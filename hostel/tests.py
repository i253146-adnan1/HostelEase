from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Announcement, MenuItem, Rule

User = get_user_model()


class HostelInfoTests(TestCase):
    def setUp(self):
        self.warden = User.objects.create_user(
            username='warden',
            password='warden-password-123',
            is_staff=True,
        )
        self.student = User.objects.create_user(
            username='student1',
            password='student-password-123',
            is_staff=False,
        )

    def test_ac_12_1_warden_publishes_announcement(self):
        self.client.force_login(self.warden)
        response = self.client.post(
            reverse('hostel:announcement_create'),
            {'title': 'Water Supply Notice', 'message': 'Maintenance from 2 PM to 4 PM.'},
        )
        self.assertRedirects(response, reverse('hostel:warden_announcements'))
        self.assertEqual(Announcement.objects.count(), 1)

        self.client.force_login(self.student)
        student_resp = self.client.get(reverse('hostel:student_announcements'))
        self.assertEqual(student_resp.status_code, 200)
        self.assertContains(student_resp, 'Water Supply Notice')
        self.assertContains(student_resp, 'Maintenance from 2 PM to 4 PM.')

    def test_ac_12_2_empty_title_or_message_rejected(self):
        self.client.force_login(self.warden)

        for payload in [
            {'title': '', 'message': 'Valid message'},
            {'title': '   ', 'message': 'Valid message'},
            {'title': 'Valid title', 'message': ''},
            {'title': 'Valid title', 'message': '   '},
        ]:
            response = self.client.post(reverse('hostel:announcement_create'), payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(Announcement.objects.count(), 0)

        self.client.force_login(self.student)
        student_resp = self.client.get(reverse('hostel:student_announcements'))
        self.assertEqual(student_resp.status_code, 200)
        self.assertContains(student_resp, 'No announcements have been published yet.')

    def test_ac_12_2_empty_menu_and_rule_rejected(self):
        self.client.force_login(self.warden)

        menu_resp = self.client.post(
            reverse('hostel:menu_create'),
            {'day_of_week': 'Monday', 'meal_type': 'Breakfast', 'items': '   '},
        )
        self.assertEqual(menu_resp.status_code, 200)
        self.assertEqual(MenuItem.objects.count(), 0)

        rule_resp = self.client.post(
            reverse('hostel:rule_create'),
            {'title': '', 'description': 'Quiet hours after 11 PM.'},
        )
        self.assertEqual(rule_resp.status_code, 200)
        self.assertEqual(Rule.objects.count(), 0)

    def test_ac_12_3_warden_can_edit_and_remove_entries(self):
        ann = Announcement.objects.create(title='Old Title', message='Old message')
        menu = MenuItem.objects.create(day_of_week='Monday', meal_type='Lunch', items='Rice and Dal')
        rule = Rule.objects.create(title='Curfew', description='Gate closes at 10 PM')

        self.client.force_login(self.warden)

        # Edit all three
        self.assertRedirects(
            self.client.post(
                reverse('hostel:announcement_edit', args=[ann.pk]),
                {'title': 'New Title', 'message': 'Updated message'},
            ),
            reverse('hostel:warden_announcements'),
        )
        self.assertRedirects(
            self.client.post(
                reverse('hostel:menu_edit', args=[menu.pk]),
                {'day_of_week': 'Tuesday', 'meal_type': 'Dinner', 'items': 'Biryani'},
            ),
            reverse('hostel:warden_menu'),
        )
        self.assertRedirects(
            self.client.post(
                reverse('hostel:rule_edit', args=[rule.pk]),
                {'title': 'Updated Curfew', 'description': 'Gate closes at 10:30 PM'},
            ),
            reverse('hostel:warden_rules'),
        )

        # Verify student sees updated content
        self.client.force_login(self.student)
        self.assertContains(self.client.get(reverse('hostel:student_announcements')), 'New Title')
        self.assertContains(self.client.get(reverse('hostel:student_menu')), 'Biryani')
        self.assertContains(self.client.get(reverse('hostel:student_rules')), 'Updated Curfew')

        # Remove all three as warden
        self.client.force_login(self.warden)
        self.assertRedirects(
            self.client.post(reverse('hostel:announcement_delete', args=[ann.pk])),
            reverse('hostel:warden_announcements'),
        )
        self.assertRedirects(
            self.client.post(reverse('hostel:menu_delete', args=[menu.pk])),
            reverse('hostel:warden_menu'),
        )
        self.assertRedirects(
            self.client.post(reverse('hostel:rule_delete', args=[rule.pk])),
            reverse('hostel:warden_rules'),
        )

        self.assertEqual(Announcement.objects.count(), 0)
        self.assertEqual(MenuItem.objects.count(), 0)
        self.assertEqual(Rule.objects.count(), 0)

        # Verify student sees removed state
        self.client.force_login(self.student)
        self.assertNotContains(self.client.get(reverse('hostel:student_announcements')), 'New Title')
        self.assertNotContains(self.client.get(reverse('hostel:student_menu')), 'Biryani')
        self.assertNotContains(self.client.get(reverse('hostel:student_rules')), 'Updated Curfew')

    def test_ac_12_4_student_cannot_create_edit_or_remove(self):
        ann = Announcement.objects.create(title='Notice', message='Body')
        menu = MenuItem.objects.create(day_of_week='Wednesday', meal_type='Lunch', items='Pasta')
        rule = Rule.objects.create(title='Silence', description='Keep noise down')

        self.client.force_login(self.student)

        forbidden_gets = [
            reverse('hostel:warden_announcements'),
            reverse('hostel:announcement_create'),
            reverse('hostel:announcement_edit', args=[ann.pk]),
            reverse('hostel:announcement_delete', args=[ann.pk]),
            reverse('hostel:warden_menu'),
            reverse('hostel:menu_create'),
            reverse('hostel:menu_edit', args=[menu.pk]),
            reverse('hostel:menu_delete', args=[menu.pk]),
            reverse('hostel:warden_rules'),
            reverse('hostel:rule_create'),
            reverse('hostel:rule_edit', args=[rule.pk]),
            reverse('hostel:rule_delete', args=[rule.pk]),
        ]
        for url in forbidden_gets:
            self.assertEqual(self.client.get(url).status_code, 403, f'GET {url} should be 403')

        self.assertEqual(
            self.client.post(
                reverse('hostel:announcement_create'),
                {'title': 'Hacked', 'message': 'Nope'},
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse('hostel:menu_edit', args=[menu.pk]),
                {'day_of_week': 'Friday', 'meal_type': 'Dinner', 'items': 'Changed'},
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(reverse('hostel:rule_delete', args=[rule.pk])).status_code,
            403,
        )

        # Confirm no records were created, modified, or deleted
        self.assertEqual(Announcement.objects.count(), 1)
        self.assertEqual(MenuItem.objects.get(pk=menu.pk).items, 'Pasta')
        self.assertEqual(Rule.objects.count(), 1)

    def test_ac_12_5_empty_state_renders_without_error(self):
        self.client.force_login(self.student)

        ann_resp = self.client.get(reverse('hostel:student_announcements'))
        menu_resp = self.client.get(reverse('hostel:student_menu'))
        rules_resp = self.client.get(reverse('hostel:student_rules'))

        self.assertEqual(ann_resp.status_code, 200)
        self.assertEqual(menu_resp.status_code, 200)
        self.assertEqual(rules_resp.status_code, 200)
        self.assertContains(ann_resp, 'No announcements have been published yet.')
        self.assertContains(menu_resp, 'No menu entries have been published yet.')
        self.assertContains(rules_resp, 'No hostel rules have been published yet.')

    def test_ac_12_6_menu_and_rules_shown_to_authenticated_students(self):
        self.client.force_login(self.warden)
        self.client.post(
            reverse('hostel:menu_create'),
            {'day_of_week': 'Friday', 'meal_type': 'Dinner', 'items': 'Chicken Karahi and Naan'},
        )
        self.client.post(
            reverse('hostel:rule_create'),
            {'title': 'Visitor Hours', 'description': 'Visitors allowed from 4 PM to 7 PM.'},
        )

        self.client.force_login(self.student)
        menu_resp = self.client.get(reverse('hostel:student_menu'))
        rules_resp = self.client.get(reverse('hostel:student_rules'))

        self.assertEqual(menu_resp.status_code, 200)
        self.assertContains(menu_resp, 'Friday')
        self.assertContains(menu_resp, 'Dinner')
        self.assertContains(menu_resp, 'Chicken Karahi and Naan')

        self.assertEqual(rules_resp.status_code, 200)
        self.assertContains(rules_resp, 'Visitor Hours')
        self.assertContains(rules_resp, 'Visitors allowed from 4 PM to 7 PM.')

    def test_public_home_page_does_not_show_hostel_info(self):
        Announcement.objects.create(title='Secret Notice', message='Internal only')
        MenuItem.objects.create(day_of_week='Monday', meal_type='Breakfast', items='Omelette')
        Rule.objects.create(title='Internal Rule', description='Students only')

        home_resp = self.client.get(reverse('home'))
        self.assertEqual(home_resp.status_code, 200)
        self.assertNotContains(home_resp, 'Secret Notice')
        self.assertNotContains(home_resp, 'Omelette')
        self.assertNotContains(home_resp, 'Internal Rule')
