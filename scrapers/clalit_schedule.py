import logging
import time
from datetime import datetime
from clalit import ClalitScraper
from clalit_utils import get_jobs, remove_entry
from telegram_utils import TelegramNotifier

POLL_TIME = 5 * 60
REPORTED_VISITS = 10


def _create_message(visit_dates):
    formatted_visits = [
            f"found visit on: {visit_data.strftime('%H:%M:%S %d/%m/%Y')}"
            for visit_data in visit_dates[:REPORTED_VISITS]]
    msg = '\n'.join(formatted_visits)
    remaining_visits = len(visit_dates) - REPORTED_VISITS
    if remaining_visits:
        msg += f'\n(omitted {remaining_visits} results)'
    return msg


def find_visits(c_scraper):
    jobs = get_jobs()
    for job in jobs:
        doctor_code, clinic_id = job['doctor_code'], job['clinic_id']
        visit_dates = c_scraper.find_clinic_visit(
                "DENTAL", doctor_code, clinic_id)
        if visit_dates:
            chat_id = job['chat_id']
            logging.info("found visits for user %s", chat_id)
            t_notifier = TelegramNotifier()
            t_notifier.send_msg(chat_id, _create_message(visit_dates))
            remove_entry(chat_id)


def main():
    c_scraper = ClalitScraper()
    while True:
        if 7 <= datetime.now().hour < 24:
            try:
                find_visits(c_scraper)
            except:
                pass
        time.sleep(POLL_TIME)


if __name__ == '__main__':
    logging.basicConfig(filename='clalit_server.log', level=logging.INFO)
    logging.info('Starting server')
    main()
