from abstract import Scraper
from bs4 import BeautifulSoup


class Typeracer(Scraper):
    ROOT = 'https://data.typeracer.com'
    HISTORY = ROOT + '/pit/race_history'
    # number of races to ask from typeracer
    N = 1000

    def __init__(self, username, universe='play'):
        super().__init__()
        self.username = username
        self.universe = universe

    # a generator which returns races user races in reverse order
    # a race is a tuple of (#, Speed (WPM), Accuracy (%))
    def user_races(self):
        link = None
        while True:
            resp = self._get_races_resp(link)
            for race in self._iterate_races(resp):
                yield race

            link = self._get_resp_next_race(resp)
            if link is None:
                break

    # returns response for races link
    # if no link is provided then the first page is returned
    def _get_races_resp(self, link=None):
        resp = None
        if not link:
            params = {'user': self.username,
                      'universe': self.universe, 'n': self.N}
            resp = self.session.get(self.HISTORY, params=params)
        else:
            resp = self.session.get(link)
        return resp.text

    # returns the next link for a response
    # if no next link exists then None is returned
    def _get_resp_next_race(self, resp):
        soup = BeautifulSoup(resp, 'html.parser')
        next_url = None
        for link in soup.findAll('a'):
            if 'older' in link.text:
                next_url = self.HISTORY + link['href']
        return next_url

    def _iterate_races(self, resp):
        soup = BeautifulSoup(resp, 'html.parser')
        for race in soup.find(class_='scoresTable').findAll('tr')[1:]:
            number, speed, accuracy = race.findAll('td')[:3]
            yield (number.text, speed.text.split(' ')[0],
                   accuracy.text.strip())


def save_user_races(username, file_name, start_race=0):
    user = Typeracer(username)
    with open(file_name, 'w') as f:
        f.write("#, Speed, Accuracy\n")
        for num, speed, acc in user.user_races():
            if int(num) < start_race:
                break
            f.write(f"{num}, {speed}, {acc}\n")
