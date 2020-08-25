import requests
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup

password = os.environ.get('tau')
username = 'liadoz'
url = 'https://schedule.tau.ac.il/scilib/Web/index.php'
payload = {
    'email': username,
    'password': password,
    'resume': '',
    'rememberMe': '',
    'login': 'submit'
}
headers = {'User-Agent': 'Mozilla/5.0'}

s = requests.Session()
s.post(url, data=payload)
page = s.get(url)
soup = BeautifulSoup(page.text, features='html.parser')
# getting a table for a date
tables = soup.findAll('table', {'class': 'reservations'})

# table of reservations
d = tables[0].findAll('tr')
# each table entry is one of three classes:
# reservable - can be reserved
# reserved - already reserved
# pasttime - cant be reserved anymore


def reserve_link(link):
    soup = BeautifulSoup(s.get(link).text, features='html.parser')
    inputs = soup.findAll('input')
    reservation_payload = {}
    reservation_payload['reservationDescription'] = ''

    for field in inputs:
        name = field.get('name')
        if(name is not None):
            reservation_payload[name] = field.get('value', '')
    periods = soup.findAll('option', selected='selected')
    reservation_payload['beginPeriod'] = periods[0]['value']
    reservation_payload['endPeriod'] = periods[1]['value']
    server = 'https://schedule.tau.ac.il/scilib/Web/ajax/reservation_save.php'
    resp = s.post(server, headers=headers, data=reservation_payload)

    soup = BeautifulSoup(resp.text, features='html.parser')
    return soup


class Reservation(object):
    def __init__(self, time, hours, data):
        self.data = data
        self.time = time
        self.end = time + hours
        self.reserved_by = data.getText()

    def reserve(self):
        return reserve_link(self.get_url())

    def get_url(self):
        gateway = 'https://schedule.tau.ac.il/scilib/Web/'
        url = gateway + self.data['data-href'] + '&sd=' + self.data['data-start'] + '&ed=' + self.data['data-end']
        return url

    def __str__(self):
        return f"Reservation from {self.time} to {self.end} by {self.reserved_by}"


class RoomTable(object):
    def __init__(self, room_table, start_time):
        try:
            self.name = room_table.span.getText()
        except:
            self.name = room_table.a.getText()

        self.room_id = self.name.split(' ')[1]
        self.capacity = tuple(re.findall(r'\d+', self.name.split(' ')[-2]))

        self.reservations = []
        for entry in room_table.findAll('td')[1:]:
            added_time = int(entry['colspan'])
            self.reservations.append(Reservation(
                start_time, added_time, entry))
            start_time += added_time


class DayTable(object):
    def __init__(self, day_table):
        day_info = day_table.findAll('tr')
        self.date = datetime.strptime(day_info[0].td.getText(), '%A, %d/%m/%Y')
        self.start_time = datetime.strptime(
            day_info[0].findAll('td')[1].getText(), '%H:%M').hour
        self.rooms = {}
        for room in day_info[1:]:
            item = RoomTable(room, self.start_time)
            self.rooms[item.room_id] = item


def get_date_table(dest_date):
    # gets a datetime object and returns the DayTable
    url_date = dest_date.strftime('%Y-%m-%d')
    url = f'https://schedule.tau.ac.il/scilib/Web/schedule.php?sd={url_date}'
    page = s.get(url)
    soup = BeautifulSoup(page.text, features='html.parser')
    days = [DayTable(x) for x
            in soup.findAll('table', {'class': 'reservations'})]
    for day in days:
        if day.date.date() == dest_date.date():
            return day
    return None


# day = get_date_table(datetime.today())
date = datetime.strptime('27/01/2020', '%d/%m/%Y')
day = get_date_table(date)
take = day.rooms['018'].reservations[-2]


def easy_as_py():
    while(True):
        resp = take.reserve()
        print(resp.text)
        if 'future' not in resp.text:
            break

# import sched, time
# def hi():
#     print('time')
# s = sched.scheduler(time.time)
# s.enterabs(time.strptime('18:15', '%H:%M'), 0, hi)
# s.run()
