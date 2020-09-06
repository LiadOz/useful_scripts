import pickle
import os


class Scraper:
    def __init__():
        self.LOGIN_LINK = ''
    def verify_login():
        pass
    def save_cookies(self):
        if self.verify_login():
            with open(self.COOKIES_FILE, 'wb') as f:
                pickle.dump(self.session.cookies, f)

    def load_cookies(self):
        if not os.path.isfile(self.COOKIES_FILE):
            return False
        with open(self.COOKIES_FILE, 'rb') as f:
            self.session.cookies.update(pickle.load(f))
        if not self.verify_login():
            os.remove(self.COOKIES_FILE)
            return False
        return True

    def login(self):
        if self.load_cookies():
            return

        self.session.post(self.LOGIN_LINK,
                          data=self.create_login_payload())
        self.save_cookies()
    def create_login_payload():
        pass
