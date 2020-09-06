import requests
from bs4 import BeautifulSoup
from secrets import uid, username, password
from abstract import Scraper
from functools import wraps
from tools import parse_js_object
from json import loads
from datetime import datetime

class Visit:
    # represents a doctor visit, parsed from BeautifulSoup tag
    def __init__(self, tag):
        if tag.find(class_='doctorDetalis'):
            self.title = tag.find(class_='doctorDetails')['title'].text
        else:
            self.title = tag.find(class_='doctorName').text
        self.subtitle = tag.find(class_='professionName').text
        self.date, self.time = [x.text for x in
                                tag.findAll('span', class_='visitDateTime')]
        self.location = tag.find(class_='underline clinicDetails')['title']
        self.update_link = tag.find(
            class_='updateVisitButton')['data-action-link']
        self.appointments = []

    def add_appointment(self, date, soup):
        # each appointment is a tuple of datetime and action
        for item in soup.findAll('li'):
            full_time = date + ' ' + item.find('span').text.strip()
            full_time = datetime.strptime(full_time, '%d.%m.%Y %H:%M')
            self.appointments.append(full_time)

    def __str__(self):
        return f"""Title: {self.title}
        Subtitle: {self.subtitle}
        Date and Time {self.time} \t {self.date}
        Location: {self.location}"""


class ClalitScraper(Scraper):

    ROOT = 'https://e-services.clalit.co.il'
    SERVICE_LINK = ROOT + '/OnlineWeb/Services/FamilyHomePage.aspx'
    TAMUZ = ROOT + '/OnlineWeb/Services/Tamuz'
    def __init__(self):
        self.session = requests.session()
        self.session.headers.update({'user-agent': 'Mozilla/5.0'})
        self.COOKIES_FILE = 'session.cookies'
        self.LOGIN_LINK = ClalitScraper.ROOT + '/OnlineWeb/General/Login.aspx'
        self.login()
        self.auth_scheduler()

    def verify_login(self):
        # this could be a decorator
        # You also may need to check for ZIMUN authorization
        resp = self.session.get(ClalitScraper.SERVICE_LINK)
        if resp.url != ClalitScraper.SERVICE_LINK:
            return False
        return True

    def _logged_in(func):
        @wraps(func)
        def wrapper(inst, *args, **kwargs):
            if not inst.verify_login():
                inst.login()
                inst.auth_scheduler()
            return func(inst, *args, **kwargs)
        return wrapper

    def create_login_payload(self):
        page = self.session.get(self.LOGIN_LINK)
        soup = BeautifulSoup(page.text, 'html.parser')

        payload = {}
        for tag in soup.findAll('input'):
            if 'Help' in tag.get('name'):
                continue
            payload[tag.get('name')] = tag.get('value')
        payload['__EVENTTARGET'] = 'ctl00$cphBody$_loginView$btnSend'
        payload['ctl00$cphBody$_loginView$tbCaptchaLogin'] = ''
        payload.pop('ctl00$mdModalDialogNonSecureMatser$MyButtonCtrl')

        # add user login
        TAG_PREFIX = 'ctl00$cphBody$_loginView$tb'
        payload[TAG_PREFIX + 'UserId'] = uid
        payload[TAG_PREFIX + 'UserName'] = username
        payload[TAG_PREFIX + 'Password'] = password

        return payload

    @_logged_in
    def auth_scheduler(self):
        zimun_auth = ClalitScraper.TAMUZ + '/TamuzTransferContentByService.aspx?MethodName=TransferWithAuth'
        form = BeautifulSoup(self.session.get(zimun_auth).text,
                             'html.parser').find('form')
        payload = {}
        for tag in form.findAll('input'):
            payload[tag.get('name')] = tag.get('value')
        self.session.post(ClalitScraper.ROOT + form['action'], data=payload)

    @_logged_in
    def get_visits(self):
        site = ClalitScraper.ROOT + '/Zimunet/'
        soup = BeautifulSoup(self.session.get(site).text, 'html.parser')
        visits = soup.find('div', {'id': 'visits'}).findAll('li')
        li = []
        for tag in visits:
            try:
                li.append(Visit(tag))
            except:
                pass
        return li

    def _get_visit_json(self, soup):
        parse = None
        for script in soup.findAll('script'):
            if 'availableDays' in str(script):
                parse = script
                break
        # remove a trailing comma
        string = []
        found = False
        for line in str(script).splitlines()[::-1]:
            if not found and line and line[-1] == ',':
                string.append(line[:-1])
                found = True
            else:
                string.append(line)
        string.reverse()
        string = '\r\n'.join(string)

        j = parse_js_object(string)
        return j

    @_logged_in
    def _add_month_appointments(self, visit, json_data, update_link):
        self.session.headers.update({'referer': update_link})
        times_url = ClalitScraper.ROOT + json_data['getDailyAvailableVisitUrl']
        for date in json_data['availableDays']:
            date_tuple = date.split('.')
            params = {'id': json_data['visitId'],
                    'professionType': json_data['professionType'],
                    'day': date_tuple[0].zfill(2),
                    'month': date_tuple[1].zfill(2),
                    'year': date_tuple[2],
                    'isUpdateVisit': json_data['isUpdateVisit']}
            resp = self.session.get(times_url, params=params)
            soup = BeautifulSoup(loads(
                resp.text)['data']['dailyAvailableVisits'], 'html.parser')
            visit.add_appointment(date, soup)

    @_logged_in
    def update_visit(self, title=None, subtitle=None):
        visit = None
        for x in self.get_visits():
            if x.title == title or x.subtitle == subtitle:
                visit = x
        if not visit:
            print('Invalid visit')
            return

        self.session.headers.update({'referer':
                                     ClalitScraper.ROOT + '/Zimunet/'})
        update_link = ClalitScraper.ROOT + visit.update_link
        resp = self.session.get(update_link)
        current_month_data = self._get_visit_json(BeautifulSoup(
            resp.text, 'html.parser'))['AvailableVisits']
        self._add_month_appointments(visit, current_month_data, update_link)
        return visit

    @_logged_in
    def get_diaries(self):
        dental_site = ClalitScraper.ROOT + '/Zimunet/SmileClinic/SearchSmileClinicsDiaries'
        self.session.post(dental_site, data={'SelectedSpecializationCode': 92,
                                             'SelectedAreaId' :7})

a = ClalitScraper()
visit = a.get_visits()[0]
ob = a.update_visit(visit.title)
site = ClalitScraper.ROOT + visit.update_link
a.session.headers.update({'referer':
                                ClalitScraper.ROOT + '/Zimunet/'})
resp = a.session.get(site)
j = a._get_visit_json(BeautifulSoup(resp.text, 'html.parser'))['AvailableVisits']
next_url = ClalitScraper.ROOT + j['getDailyAvailableVisitUrl']
# I need to get:
# id, professionType, day, month (both padded), year, isUpdateVisit
date = '15.9.2020'.split('.')
params = {'id': j['visitId'],
          'professionType': j['professionType'],
          'day': date[0].zfill(2),
          'month': date[1].zfill(2),
          'year': date[2],
          'isUpdateVisit': j['isUpdateVisit']}
a.session.headers.update({'referer': site})
resp = a.session.get(next_url, params=params)
soup = BeautifulSoup(loads(resp.text)['data']['dailyAvailableVisits'],
                     'html.parser')
########################
for item in soup.findAll('li'):
    print(item.find('span').text.strip())


#######################
# should search also in the next months
# could also add search time frame
