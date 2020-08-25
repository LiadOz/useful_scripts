import json
from datetime import datetime


class ResFile(object):
    def __init__(self):
        with open('reservations.json', 'r') as f:
            self.entries = set(json.load(f)['entries'])

    def add_reservation(self, date, hour, room):
        # date in format day/month/year
        try:
            datetime.strptime(date + hour, '%d/%m/%Y%H:%M')
        except ValueError:
            print('wrong date or hour format')
            return
        self.entries.add(f'{date}-{hour}-{room}')

    def save(self):
        with open('reservations.json', 'w') as f:
            json.dump({'entries': list(self.entries)}, f, indent=4)


r = ResFile()
r.add_reservation('01/01/1999', '00:00', '084')
r.add_reservation('02/01/1999', '00:00', '084')
r.add_reservation('03/01/1999', '00:00', '074')
r.add_reservation('04/01/1999', '00:00', '074')
r.add_reservation('04/01/1999', '00:00', '074')
r.save()
