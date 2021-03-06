from secrets import pushbullet_api_key
import requests

class Notify:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Access-Token': pushbullet_api_key})

    def send_notification(self, title, body):
        payload = {'type': 'note',
                   'title': title,
                   'body': body}
        self.session.post('https://api.pushbullet.com/v2/pushes', data=payload)
