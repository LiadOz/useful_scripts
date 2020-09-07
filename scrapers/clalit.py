import requests
from bs4 import BeautifulSoup
from secrets import uid, username, password
from abstract import Scraper
from functools import wraps
from tools import parse_js_object, iterate_months
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

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

    def __str__(self):
        return f"Title: {self.title}\n \
        Subtitle: {self.subtitle}\n \
        Date and Time {self.time} \t {self.date} \n \
        Location: {self.location}"


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
    # authorizes the scheduling system in the website
    def auth_scheduler(self):
        zimun_auth = ClalitScraper.TAMUZ + '/TamuzTransferContentByService.aspx?MethodName=TransferWithAuth'
        form = BeautifulSoup(self.session.get(zimun_auth).text,
                             'html.parser').find('form')
        payload = {}
        for tag in form.findAll('input'):
            payload[tag.get('name')] = tag.get('value')
        self.session.post(ClalitScraper.ROOT + form['action'], data=payload)

    @_logged_in
    # returns all scheduled visits
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

    def _find_visit(self, title=None, subtitle=None):
        visit = None
        for x in self.get_visits():
            if x.title == title or x.subtitle == subtitle:
                return x
        raise ValueError('invalid visit')

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
    # returns the days in which there is an open appointment
    # this assumes that the header is set to appointment update link
    def _get_month_available_days(self, data,
                                  month=datetime.now().month,
                                  year=datetime.now().year):
        params = {'id': data['visitId'],
                   'professionType': data['professionType'],
                   'month': str(month).zfill(2), 'year': year,
                   'isUpdateVisit': data['isUpdateVisit']}
        resp = self.session.get(
            ClalitScraper.ROOT + data['getMonthlyAvailableVisitUrl'],
            params=params).json()
        if not resp['errorType']:
            return [datetime.strptime(date, '%d.%m.%Y')
                    for date in resp['data']['availableDays']]
        return []

    @_logged_in
    # returns datetime objects of available appointments
    # this assumes that the header is set to appointment update link
    def _get_day_available_hours(self, data, date):
        day, month, year = date.day, date.month, date.year
        params = {'id': data['visitId'],
                'professionType': data['professionType'],
                'day': str(day).zfill(2),
                'month': str(month).zfill(2),
                'year': year,
                'isUpdateVisit': data['isUpdateVisit']}
        get_url = ClalitScraper.ROOT + data['getDailyAvailableVisitUrl']
        resp = self.session.get(get_url, params=params).json()['data']
        soup = BeautifulSoup(resp['dailyAvailableVisits'], 'html.parser')
        items = []
        for item in soup.findAll('li'):
            time = item.span.text.strip().split(':')
            items.append(date + timedelta(
                hours=int(time[0]), minutes=int(time[1])))
        return items


    @_logged_in
    def _get_visit_data(self, visit):
        self.session.headers.update({'referer':
                                     ClalitScraper.ROOT + '/Zimunet/'})
        update_link = ClalitScraper.ROOT + visit.update_link
        resp = self.session.get(update_link)
        return self._get_visit_json(BeautifulSoup(
            resp.text, 'html.parser'))['AvailableVisits']

    @_logged_in
    # finds appointments between start_time and end_time
    # blacklist / whitelist is a set of dates (without time!)
    def find_appointments(self, title=None, subtitle=None,
                         start_time=datetime.now(),
                         end_time=datetime.now() + relativedelta(months=3),
                         blacklist=set(), whitelist=set()):
        visit = self._find_visit(title, subtitle)
        data = self._get_visit_data(visit)
        self.session.headers.update(
            {'referer': ClalitScraper.ROOT + visit.update_link})
        result = []

        def filter_date(date):
            if date.date() in whitelist:
                return True
            if date < start_time or date > end_time or date.date() in blacklist:
                return False
            return True

        for month in iterate_months(start_time, end_time):
            for date in \
                self._get_month_available_days(data, month.month, month.year):
                days = self._get_day_available_hours(data, date)
                result.extend([x for x in days if filter_date(x)])
        return result
