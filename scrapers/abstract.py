import pickle
import os
from functools import wraps
from requests import Session

from config import user_agent

# A base class for all scrapers
# A subclass may implement login mechanism to its websites
# The login mechanism is comprised of _login and _verify_login methods
class Scraper:
    def __init__(self):
        self.session = Session()
        self.session.headers.update({'user-agent': user_agent})

    def save_cookies(self):
        with open(self.COOKIES_FILE, 'wb') as f:
            pickle.dump(self.session.cookies, f)

    def load_cookies(self):
        if not os.path.isfile(self.COOKIES_FILE):
            return False
        with open(self.COOKIES_FILE, 'rb') as f:
            self.session.cookies.update(pickle.load(f))
        return True

    # tries to load cookies and if the user is not still logged in it uses
    # the children's method of login and saves the cookies
    # load_cookies should be false if you know the cookies are already invalid
    def login(self, load_cookies=True):
        if load_cookies:
            self.load_cookies()
            if self._verify_login():
                return
        self._login()
        self.save_cookies()

# used to verify the scraper is logged in
def _logged_in(func):
    @wraps(func)
    def wrapper(inst, *args, **kwargs):
        if not inst._verify_login():
            inst.login(load_cookies=False)
        return func(inst, *args, **kwargs)
    return wrapper
