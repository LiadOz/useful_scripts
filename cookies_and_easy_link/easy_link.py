#!./env/bin/python
from bs4 import BeautifulSoup
import os
import re
import pickle
import requests

# This module is used to log in to tau video site
# the script to gets a link to plug to vlc for certain page

session = requests.Session()
MAIN_PAGE = "https://video.tau.ac.il/index.php?lang=en"
COOKIES_FILE = "cookies.ck"


def logged_in():
    page = session.get(MAIN_PAGE)
    s = BeautifulSoup(page.text, 'html.parser')
    if s.input['name'] == 'username':
        return False
    return True


def load_cookies():
    if not os.path.isfile(COOKIES_FILE):
        return False
    with open(COOKIES_FILE, 'rb') as f:
        session.cookies.update(pickle.load(f))
    return True


def save_cookies():
    with open(COOKIES_FILE, 'wb') as f:
        pickle.dump(session.cookies, f)


def log_in():
    if load_cookies():
        return

    payload = {}
    page = session.get(MAIN_PAGE)
    s = BeautifulSoup(page.text, 'html.parser')

    for x in s.findAll('input'):
        payload[x.get('name')] = x.get('value')
    payload['username'] = input('Enter username: ')
    payload['passwd'] = input('Enter password: ')

    session.post(MAIN_PAGE, data=payload)
    save_cookies()


def get_link():
    link = input("Enter link: ")
    page = session.get(link)
    s = BeautifulSoup(page.text, 'html.parser')
    try:
        return re.search('http.*m3u8', str(s)).group(0)
    except Exception:
        print("Invalid link")
        return ""


if __name__ == '__main__':
    log_in()
    while(not logged_in()):
        log_in()
        c = input("Login failed - try again?: ")
        if c != 'yes':
            break
    if logged_in():
        link = get_link()
        print(link)
        create_file(link)
