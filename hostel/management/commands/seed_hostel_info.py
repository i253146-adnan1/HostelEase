from django.core.management.base import BaseCommand

from hostel.models import Announcement, MenuItem, Rule

ANNOUNCEMENTS = [
    (
        'Dhobi (Laundry) Schedule — Thursday & Sunday',
        'The hostel dhobi (laundry service) comes twice a week on Thursday and Sunday from 9:00 AM to 1:00 PM. Please keep your clothes tagged and ready before 9:00 AM.',
    ),
    (
        'Night Quiet Hours',
        'Quiet hours are observed daily from 11:00 PM to 6:00 AM in all corridors and rooms so residents can rest and study peacefully.',
    ),
    (
        'Monthly Fee Proof Reminder',
        'Residents are reminded to upload their monthly fee payment proof through the Fees & Proofs page before the 10th of each month.',
    ),
]

RULES = [
    (
        'Hostel Gate & Curfew Timing',
        'The main hostel gate closes at 10:30 PM. Residents returning late must have an approved leave request or prior permission from the warden.',
    ),
    (
        'Visitor Policy',
        'All visitors must be logged at the warden desk with valid ID. Visiting hours are 9:00 AM to 8:00 PM; overnight guests are not allowed.',
    ),
    (
        'Room Cleanliness & Property Care',
        'Keep rooms and shared areas clean. Report any maintenance or plumbing/electrical issues promptly via the Complaints portal.',
    ),
    (
        'Restricted Electrical Appliances',
        'For fire and electrical safety, high-wattage heaters, induction stoves, and unauthorized irons are not permitted in rooms.',
    ),
    (
        'Mess & Meal Opt-Out Policy',
        'Submit a Meal Opt-Out in advance on the portal if you will be away so mess planning stays accurate.',
    ),
]

MESS_MENU = [
    ('Monday', 'Breakfast', 'Paratha, Omelette, Chai'),
    ('Monday', 'Lunch', 'Daal Chawal, Fresh Salad'),
    ('Monday', 'Dinner', 'Chicken Karahi, Roti, Raita'),
    ('Tuesday', 'Breakfast', 'Naan Chana, Chai'),
    ('Tuesday', 'Lunch', 'Aloo Matar, Roti'),
    ('Tuesday', 'Dinner', 'Beef Pulao, Raita, Salad'),
    ('Wednesday', 'Breakfast', 'Toast, Boiled Eggs, Jam, Chai'),
    ('Wednesday', 'Lunch', 'Lobia Masala, Boiled Rice'),
    ('Wednesday', 'Dinner', 'Chicken Handi, Naan'),
    ('Thursday', 'Breakfast', 'Aloo Paratha, Yogurt, Chai'),
    ('Thursday', 'Lunch', 'Kari Pakora, Steamed Rice'),
    ('Thursday', 'Dinner', 'Chicken Korma, Roti'),
    ('Friday', 'Breakfast', 'Paratha, Egg Bhurji, Chai'),
    ('Friday', 'Lunch', 'Chicken Biryani, Raita, Salad'),
    ('Friday', 'Dinner', 'Daal Fry, Mixed Sabzi, Roti'),
    ('Saturday', 'Breakfast', 'Paratha, Fried Egg, Chai'),
    ('Saturday', 'Lunch', 'Chana Masala, Roti'),
    ('Saturday', 'Dinner', 'Chicken Tikka, Naan, Mint Chutney'),
    ('Sunday', 'Breakfast', 'Halwa Puri, Chana, Chai'),
    ('Sunday', 'Lunch', 'Daal Makhani, Jeera Rice'),
    ('Sunday', 'Dinner', 'Chicken Roast, Naan, Salad'),
]


class Command(BaseCommand):
    """Seed default hostel announcements, rules, and weekly mess menu."""

    help = 'Seed hostel announcements (including dhobi schedule), rules, and weekly mess menu.'

    def handle(self, *args, **options):
        ann_created = 0
        for title, message in ANNOUNCEMENTS:
            _, created = Announcement.objects.get_or_create(
                title=title,
                defaults={'message': message},
            )
            if created:
                ann_created += 1

        rule_created = 0
        for title, description in RULES:
            _, created = Rule.objects.get_or_create(
                title=title,
                defaults={'description': description},
            )
            if created:
                rule_created += 1

        menu_created = 0
        for day, meal, items in MESS_MENU:
            _, created = MenuItem.objects.get_or_create(
                day_of_week=day,
                meal_type=meal,
                defaults={'items': items},
            )
            if created:
                menu_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded hostel info: {ann_created} announcements, {rule_created} rules, {menu_created} menu items created.'
            )
        )
