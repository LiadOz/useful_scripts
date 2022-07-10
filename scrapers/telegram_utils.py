import json
import requests


def get_token():
    with open("/etc/clalit_config.json", 'r') as config_file:
        config = json.load(config_file)
        token = config.get('TELEGRAM_TOKEN', None)
        assert token, 'Bot token not found'
    return token


class TelegramNotifier:
    def __init__(self):
        self._token = get_token()

    def send_msg(self, chat_id, text):
        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        requests.get(url, params={'CHAT_ID': chat_id, 'text': text})
