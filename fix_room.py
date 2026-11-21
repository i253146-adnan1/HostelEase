content = open('hostel/models.py', 'r').read()
props = '''
    @property
    def occupancy(self):
        return self.assignments.filter(is_active=True).count()

    @property
    def is_full(self):
        return self.occupancy >= self.capacity

    @property
    def available_slots(self):
        return self.capacity - self.occupancy

    @classmethod
    def get_pending_request_count(cls):
        return 0

'''
old = "    def __str__(self):\n        return f'Room {self.room_number}'"
content = content.replace(old, props + old)
open('hostel/models.py', 'w').write(content)
print('Done')
