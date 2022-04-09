import subprocess


class WindowsNotify:
    def send_notification(self, msg):
        subprocess.call(f'wsl-notify-send.exe "{msg}"', shell=True)


class MacNotify:
    def send_notification(self, msg):
        CMD = '''
        on run argv
        display notification (item 2 of argv) with title (item 1 of argv)
        end run
        '''
        subprocess.call(['osascript', '-e', CMD, 'notification', msg])


def notification_factory(notify_type):
    if notify_type == 'windows':
        return WindowsNotify()
    elif notify_type == 'mac':
        return MacNotify()
    else:
        raise RuntimeError('invalid notify type')



# class Notify:
#     def __init__(self):
#         self.session = requests.Session()
#         self.session.headers.update({'Access-Token': pushbullet_api_key})

#     def send_notification(self, title, body):
#         payload = {'type': 'note',
#                    'title': title,
#                    'body': body}
#         self.session.post('https://api.pushbullet.com/v2/pushes', data=payload)
