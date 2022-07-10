import time
from datetime import datetime
from clalit import ClalitScraper
from clalit_utils import get_jobs
from telegram_utils import TelegramNotifier

POLL_TIME = 5 * 60


def find_visits(cl):
    jobs = get_jobs()
    for job in jobs:
        doctor_code, clinic_id = job['doctor_code'], job['clinic_id']
        visits = cl.find_clinic_visit("DENTAL", doctor_code, clinic_id)
        if visits:
            print(visits)
            t_notifier = TelegramNotifier()
            t_notifier.send_msg(job['chat_id'], 'msg')


def main():
    cl = ClalitScraper()
    while True:
        if 7 <= datetime.now().hour < 24:
            try:
                find_visits(cl)
            except:
                pass
        time.sleep(POLL_TIME)


if __name__ == '__main__':
    main()
