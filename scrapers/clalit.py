import re
from bs4 import BeautifulSoup
from abstract import Scraper
from tools import parse_js_object, iterate_months
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from abstract import _logged_in
import json

with open("/etc/clalit_config.json") as config_file:
    config = json.load(config_file)
    uid = config.get('U_ID')
    username = config.get('USERNAME')
    password = config.get('PASSWORD')


class Visit:
    # represents a doctor visit, parsed from BeautifulSoup tag
    def __init__(self, tag):
        if tag.find(class_='doctorDetalis'):
            self.title = tag.find(class_='doctorDetails')['title'].text
        else:
            self.title = tag.find(class_='doctorName').text
        self.subtitle = tag.find(class_='professionName').text
        self.date, self.time = [
            x.text for x in tag.findAll('span', class_='visitDateTime')
        ]
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
    LOGIN_LINK = ROOT + '/OnlineWeb/General/Login.aspx'
    SERVICE_LINK = ROOT + '/OnlineWeb/Services/FamilyHomePage.aspx'
    TAMUZ = ROOT + '/OnlineWeb/Services/Tamuz'
    COOKIES_FILE = 'clalit.cookies'

    def __init__(self):
        super().__init__()

    def _login(self):
        # this method is activated when login function is performed
        self.session.post(self.LOGIN_LINK, data=self._create_login_payload())
        self._auth_scheduler()

    def _verify_login(self):
        resp = self.session.get(ClalitScraper.SERVICE_LINK)
        if resp.url != ClalitScraper.SERVICE_LINK:
            return False
        return True

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


    @_logged_in
    # returns all scheduled visits
    def find_clinic_visit(self, sched_type, spec_code, clinic_code,
                          area_id="7", start_time=datetime.now(),
                          end_time=datetime.now() + relativedelta(months=1),
                          blacklist=set(), whitelist=set()):
        if sched_type == "DENTAL":
            url = "/Zimunet/SmileClinic/SearchSmileClinicsDiaries"
        else:
            raise ValueError("not implemented")

        payload = {
            "SelectedSpecializationCode": spec_code,
            "SelectedAreaId": area_id,
        }
        page = self.session.post(
            ClalitScraper.ROOT + url, data=payload)
        link = self._find_clinic_link(clinic_code, page)
        if not link:
            return []
        data = self._get_visit_data(link)
        self.login()
        self.session.headers.update(
            {'referer': ClalitScraper.ROOT + link})
        return self._find_appointments(
            data, start_time, end_time, blacklist, whitelist)

    def _find_clinic_link(self, clinic_code, page):
        soup = BeautifulSoup(page.json()['data'], 'html.parser')
        for clinic in soup.find_all("li", class_='diary'):
            if clinic.find_all('span')[0].text.strip() == clinic_code:
                return clinic.find(
                    'a', {'id': 'CreateVisitButton'}).get('data-action-link')

        next_page = soup.find('a', {'title': "הבא"})
        if next_page:
            page = self.session.get(ClalitScraper.ROOT +
                                    next_page.get('data-action-link'))
            return self._find_clinic_link(clinic_code, page)
        else:
            return ''

    # finds appointments between start_time and end_time
    # without passing time frame it sets to the next month
    # blacklist / whitelist is a set of dates (without time!)
    @_logged_in
    def reschedule_appointment(self,
                               title=None,
                               subtitle=None,
                               start_time=datetime.now(),
                               end_time=datetime.now() +
                               relativedelta(months=1),
                               blacklist=set(),
                               whitelist=set()):
        visit = self._find_visit(title, subtitle)
        data = self._get_visit_data(visit.update_link)
        self.session.headers.update(
            {'referer': ClalitScraper.ROOT + visit.update_link})
        return self._find_appointments(data, start_time, end_time,
                                       blacklist, whitelist)

    @_logged_in
    def _find_appointments(self, data, start_time, end_time,
                           blacklist, whitelist):
        def filter_date(date):
            if date.date() in whitelist:
                return True
            if date < start_time or date > end_time or date.date(
            ) in blacklist:
                return False
            return True

        result = []
        for month in iterate_months(start_time, end_time):
            for date in self._get_month_available_days(data, month.month,
                                                       month.year):
                days = self._get_day_available_hours(data, date)
                result.extend([x for x in days if filter_date(x)])
        return result

    def _create_login_payload(self):
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

    # authorizes the scheduling system in the website
    def _auth_scheduler(self):
        zimun_auth = ClalitScraper.TAMUZ + '/TamuzTransferContentByService.aspx?MethodName=TransferWithAuth'
        form = BeautifulSoup(self.session.get(zimun_auth).text,
                             'html.parser').find('form')
        payload = {}
        for tag in form.findAll('input'):
            payload[tag.get('name')] = tag.get('value')
        self.session.post(f"{ClalitScraper.ROOT}/{form['action']}", data=payload)

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

        result = re.search(r'z.init(.*);', parse.text, re.DOTALL).group(1)
        j = parse_js_object(result)
        return j

    @_logged_in
    # returns the days in which there is an open appointment
    # this assumes that the header is set to appointment update link
    def _get_month_available_days(self,
                                  data,
                                  month=datetime.now().month,
                                  year=datetime.now().year):
        params = {
            'id': data['visitId'],
            'professionType': data['professionType'],
            'month': str(month).zfill(2),
            'year': year,
            'isUpdateVisit': data['isUpdateVisit']
        }
        resp = self.session.get(ClalitScraper.ROOT +
                                data['getMonthlyAvailableVisitUrl'],
                                params=params).json()
        if not resp['errorType']:
            return [
                datetime.strptime(date, '%d.%m.%Y')
                for date in resp['data']['availableDays']
            ]
        return []

    @_logged_in
    # returns datetime objects of available appointments
    # this assumes that the header is set to appointment update link
    def _get_day_available_hours(self, data, date):
        day, month, year = date.day, date.month, date.year
        params = {
            'id': data['visitId'],
            'professionType': data['professionType'],
            'day': str(day).zfill(2),
            'month': str(month).zfill(2),
            'year': year,
            'isUpdateVisit': data['isUpdateVisit']
        }
        get_url = ClalitScraper.ROOT + data['getDailyAvailableVisitUrl']
        resp = self.session.get(get_url, params=params).json()['data']
        soup = BeautifulSoup(resp['dailyAvailableVisits'], 'html.parser')
        items = []
        for item in soup.findAll('li'):
            time = item.span.text.strip().split(':')
            items.append(date +
                         timedelta(hours=int(time[0]), minutes=int(time[1])))
        return items

    @_logged_in
    def _get_visit_data(self, link):
        self.session.headers.update(
            {'referer': ClalitScraper.ROOT + '/Zimunet/'})
        update_link = ClalitScraper.ROOT + link
        resp = self.session.get(update_link)
        return self._get_visit_json(BeautifulSoup(
            resp.text, 'html.parser'))['AvailableVisits']
